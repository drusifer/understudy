// Sprint 3 UND-10 (ARCH §3, §5, ADR-0012/0013): the app hooks an MCP sketch
// gets - it never writes any. The server's tools are the moves; a sketch
// may list fixed calls (`calls:`) and values for open arguments
// (`values:`). A tool whose required argument has nothing to choose from
// is left out, said once, and offered as soon as a result supplies values.
// Where the run ends is the sketch's to say, with the `showing` guard.

import { candidatesFor, MAX_CANDIDATES } from '../fill.mjs';
import { answerRows } from '../rows.mjs';
import { gate } from '../engine.mjs';

const RESULT_CHARS = 2000;

/**
 * A tool's name as the moves say it: `<server>/<tool>` when the sketch
 * plays several servers, so same-named tools never mix (ADR-0022).
 */
const nameOf = (tool) => (tool.server ? `${tool.server}/${tool.name}` : tool.name);

/**
 * A fixed call's id: its tool and the arguments it fixes.
 */
function idOf(tool, fixed) {
  const given = Object.entries(fixed).map(([name, value]) => name + '=' + (typeof value === 'string' ? value : JSON.stringify(value)));
  return given.length === 0 ? `tool:${nameOf(tool)}` : `tool:${nameOf(tool)}(${given.join(',')})`;
}

/**
 * The moves one tool offers: each fixed call the sketch lists for it, or
 * the tool itself. Each open argument carries its candidates; a required
 * one with none makes the move unavailable, with the reason.
 */
function movesFor(tool, { calls, values, last, decided }) {
  const properties = tool.inputSchema?.properties ?? {};
  const required = new Set(tool.inputSchema?.required);
  const listed = values[nameOf(tool)] ?? {};
  const fixedCalls = calls.filter((call) => call.tool === nameOf(tool)).map((call) => call.arguments ?? {});
  return (fixedCalls.length > 0 ? fixedCalls : [{}]).map((fixed) => {
    const open = [];
    const decisions = [];
    for (const [name, schema] of Object.entries(properties)) {
      const decision = decided(`${nameOf(tool)}.${name}`, name);
      const isOpen = decision || required.has(name) || Object.hasOwn(listed, name);
      if (!isOpen || Object.hasOwn(fixed, name)) continue;
      if (decision) {
        decisions.push(decision.record);
        if (decision.candidates.length === 0) return { id: idOf(tool, fixed), why: `argument "${name}" ${decision.why}` };
        open.push({ name, schema, candidates: decision.candidates });
        continue;
      }
      const candidates = candidatesFor(schema, { listed: listed[name], last });
      if (candidates.length === 0) {
        return { id: idOf(tool, fixed), why: `argument "${name}" (${schema.type ?? 'any'}) has nothing to choose from; list values for it in sketch.yaml` };
      }
      open.push({ name, schema, candidates });
    }
    const about = tool.description ? ` - ${tool.description}` : '';
    const fixing = Object.keys(fixed).length > 0 ? ` with ${JSON.stringify(fixed)}` : '';
    const move = { id: idOf(tool, fixed), what: `call ${nameOf(tool)}${fixing}${about}`, call: { ...(tool.server && { server: tool.server }), tool: tool.name, arguments: fixed }, open };
    return decisions.length > 0 ? { ...move, decided: decisions } : move;
  });
}

/**
 * Why a decided argument offers nothing: waiting, all removed, or no rows yet.
 */
function whyNone(heldBack, removed) {
  if (heldBack.length > 0) return `is waiting for ${heldBack.map((each) => each.missing).join(', ')}`;
  if (removed.length > 0) return `has nothing that passes its gates (${removed.length} removed)`;
  return 'has nothing to choose from yet';
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
  return { name: nameOf(tool), does: tool.description ?? '', arguments: arguments_ };
}

/**
 * The generic MCP app for one sketch.
 * @param {{ calls?: { tool: string, arguments?: object }[], values?: Record<string, Record<string, unknown[]>>,
 *   decide?: Record<string, { field?: string, join?: string, gates?: object }> }} sketch
 */
export function mcpApp({ calls = [], values = {}, decide = {} } = {}) {
  const warned = new Set();
  const rows = answerRows({ notify: (line) => app.notify?.(line) });
  // ADR-0017: a decided value used in a call that answered is spent - the
  // answer is remembered, so asking again gains nothing.
  const spent = new Map(Object.keys(decide).map((key) => [key, new Set()]));
  let spending = [];
  const held = new Set();

  /**
   * Says once per value that it is held back, and what for.
   */
  function sayHeld(key, argument, waiting) {
    for (const { value, missing, about } of waiting) {
      if (held.has(`${key}=${value}`)) continue;
      held.add(`${key}=${value}`);
      const film = about === undefined ? '' : ` for "${about}"`;
      app.notify?.(`holding back ${argument} ${value} - no "${missing}"${film} yet`);
    }
  }

  /**
   * A decided argument's values (UND-21): from the remembered rows, not
   * spent, through its gates - the ones left, and what was removed or
   * held back and why.
   */
  function decided(key, argument) {
    const entry = decide[key];
    if (!entry) return null;
    const candidates = [];
    const removed = [];
    const waiting = [];
    const fresh = rows.valuesOf(entry.field ?? argument).filter(({ value }) => !spent.get(key).has(value));
    for (const { value, row } of fresh) {
      const result = gate(rows.factsOf(row, entry.join), entry.gates);
      if (result.removed) removed.push({ value, why: result.removed });
      else if (result.missing) waiting.push({ value, missing: result.missing, ...(entry.join && { about: row[entry.join] }) });
      else candidates.push(value);
    }
    sayHeld(key, argument, waiting);
    const heldBack = waiting.map(({ value, missing, about }) => ({ value, missing: about === undefined ? missing : `${missing} for ${about}` }));
    return { candidates: candidates.slice(0, MAX_CANDIDATES), why: whyNone(heldBack, removed), record: { argument: key, removed, held: heldBack } };
  }
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
      rows.remember(view.last);
      // A refused call spends nothing.
      if (spending.length > 0 && view.last?.isError) for (const [key, value] of spending) spent.get(key).delete(value);
      spending = [];
      const all = view.tools.flatMap((tool) => movesFor(tool, { calls, values, last: answered, decided }));
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
        last_call: last ? { tool: nameOf({ server: last.server, name: last.tool }), arguments: last.arguments, failed: last.isError, said: last.text.slice(0, RESULT_CHARS) } : null,
      };
    },
    options: () => app.moves(looked).offered,
    act(move) {
      spending = Object.entries(move.filled ?? {}).map(([name, value]) => [`${nameOf({ server: move.call.server, name: move.call.tool })}.${name}`, value]).filter(([key]) => spent.has(key));
      for (const [key, value] of spending) spent.get(key).add(value);
      return { actions: [{ ...move.call, arguments: { ...move.call.arguments, ...move.filled } }] };
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
