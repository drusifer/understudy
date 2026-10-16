// Sprint 3 UND-10 (ARCH §3, §5, ADR-0012/0013): the app hooks an MCP sketch
// gets - it never writes any. The server's tools are the moves; a sketch
// may list fixed calls (`calls:`) and values for open arguments
// (`values:`). A tool whose required argument has nothing to choose from
// is left out, said once, and offered as soon as a result supplies values.
// Where the run ends is the sketch's to say, with the `showing` guard.

import { candidatesFor } from '../fill.mjs';

const RESULT_CHARS = 2000;

/**
 * A fixed call's id: its tool and the arguments it fixes.
 */
function idOf(tool, fixed) {
  const given = Object.entries(fixed).map(([name, value]) => name + '=' + (typeof value === 'string' ? value : JSON.stringify(value)));
  return given.length === 0 ? `tool:${tool}` : `tool:${tool}(${given.join(',')})`;
}

/**
 * The moves one tool offers: each fixed call the sketch lists for it, or
 * the tool itself. Each open argument carries its candidates; a required
 * one with none makes the move unavailable, with the reason.
 */
function movesFor(tool, { calls, values, last }) {
  const properties = tool.inputSchema?.properties ?? {};
  const required = new Set(tool.inputSchema?.required);
  const listed = values[tool.name] ?? {};
  const fixedCalls = calls.filter((call) => call.tool === tool.name).map((call) => call.arguments ?? {});
  return (fixedCalls.length > 0 ? fixedCalls : [{}]).map((fixed) => {
    const open = [];
    for (const [name, schema] of Object.entries(properties)) {
      if (Object.hasOwn(fixed, name) || !(required.has(name) || Object.hasOwn(listed, name))) continue;
      const candidates = candidatesFor(schema, { listed: listed[name], last });
      if (candidates.length === 0) {
        return { id: idOf(tool.name, fixed), why: `argument "${name}" (${schema.type ?? 'any'}) has nothing to choose from; list values for it in sketch.yaml` };
      }
      open.push({ name, schema, candidates });
    }
    const about = tool.description ? ` - ${tool.description}` : '';
    const fixing = Object.keys(fixed).length > 0 ? ` with ${JSON.stringify(fixed)}` : '';
    return { id: idOf(tool.name, fixed), what: `call ${tool.name}${fixing}${about}`, call: { tool: tool.name, arguments: fixed }, open };
  });
}

/**
 * What Jev reads about a tool: its name, what it does, its arguments.
 */
function described(tool) {
  const properties = tool.inputSchema?.properties ?? {};
  const required = new Set(tool.inputSchema?.required);
  const arguments_ = Object.fromEntries(Object.entries(properties).map(([name, schema]) => [
    name, [schema.type, schema.description, required.has(name) ? null : 'optional'].filter(Boolean).join(' - '),
  ]));
  return { name: tool.name, does: tool.description ?? '', arguments: arguments_ };
}

/**
 * The generic MCP app for one sketch.
 * @param {{ calls?: { tool: string, arguments?: object }[], values?: Record<string, Record<string, unknown[]>> }} sketch
 */
export function mcpApp({ calls = [], values = {} } = {}) {
  const warned = new Set();
  let looked = { tools: [], last: null };
  // Values come from the last answer that was not an error: a refused
  // call must not take away what the one before it offered.
  let answered = null;
  const app = {
    // Set by the run: one stderr line, e.g. a tool not offered.
    notify: null,

    /**
     * The moves a view offers, and the ones it cannot, with why.
     */
    moves(view) {
      if (view.last && !view.last.isError) answered = view.last;
      const all = view.tools.flatMap((tool) => movesFor(tool, { calls, values, last: answered }));
      const blocked = all.filter((move) => move.why);
      for (const { id, why } of blocked) {
        if (warned.has(id)) continue;
        warned.add(id);
        app.notify?.(`not offering ${id} yet - ${why}`);
      }
      return { offered: all.filter((move) => !move.why), blocked };
    },
    phase: (view) => (app.moves(view).offered.length > 0 ? 'asking' : 'waiting'),
    project(view) {
      // `options` offers the moves of the view projected last (play
      // projects, then asks for options, from one look).
      looked = view;
      const { last } = view;
      return {
        tools: view.tools.map((tool) => described(tool)),
        last_call: last ? { tool: last.tool, arguments: last.arguments, failed: last.isError, said: last.text.slice(0, RESULT_CHARS) } : null,
      };
    },
    options: () => app.moves(looked).offered,
    act(move) {
      return { actions: [{ tool: move.call.tool, arguments: { ...move.call.arguments, ...move.filled } }] };
    },
    /**
     * Why nothing is offered - for the run's no-first-move / stalled line.
     */
    idle(view) {
      if (view.tools.length === 0) return 'the server lists no tools';
      const reasons = app.moves(view).blocked.map(({ id, why }) => `${id} - ${why}`);
      return `nothing can be offered: ${reasons.join('; ')}`;
    },
  };
  return app;
}
