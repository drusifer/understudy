// Sprint 3 UND-10 (ARCH §3, §5, ADR-0012/0013): the app hooks an MCP sketch
// gets - it never writes any. The server's tools are the moves; a sketch
// may list fixed calls (`calls:`) and values for open arguments
// (`values:`). A tool whose required argument has nothing to choose from
// is left out, said once, and offered as soon as a result supplies values.
// Where the run ends is the sketch's to say, with the `showing` guard.

import { candidatesFor, MAX_CANDIDATES } from '../fill.mjs';
import { answerRows } from '../rows.mjs';
import { LRUCache } from 'lru-cache';
import { isInputReference } from '../inputs.mjs';
import { gate, score, shortlist } from '../engine.mjs';

const RESULT_CHARS = 2000;
const EARLIER_CHARS = 1000;
// How many answered calls a deciding sketch remembers (least recently used forgotten first).
export const ANSWERED_CALLS = 200;

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
function movesFor(tool, { calls, values, last, decided, pick, inputs }) {
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
      if (decision) decisions.push(decision.record);
      const list = listedFor(listed[name], inputs);
      const argument = decision ? decidedArgument(name, schema, decision, pick) : listedArgument(name, schema, list, last);
      if (argument.why) return { id: idOf(tool, fixed), why: argument.why };
      open.push(argument);
    }
    const about = tool.description ? ` - ${tool.description}` : '';
    const fixing = Object.keys(fixed).length > 0 ? ` with ${JSON.stringify(fixed)}` : '';
    const move = { id: idOf(tool, fixed), what: `call ${nameOf(tool)}${fixing}${about}`, call: { ...(tool.server && { server: tool.server }), tool: tool.name, arguments: fixed }, open };
    if (decisions.length === 0) return move;
    return { ...move, decided: decisions };
  });
}

// A listed value may be one of the run's inputs (`{ input: tickets }`, sprint 7).
const listedFor = (listed, inputs) => (isInputReference(listed) ? [inputs[listed.input]] : listed);

/**
 * A decided argument as a move's open argument (its shortlist), or why not.
 */
function decidedArgument(name, schema, decision, pick) {
  if (decision.candidates.length === 0) return { why: `argument "${name}" ${decision.why}` };
  // The final pick (UND-24) is for a ranked argument; any other is chosen as usual.
  return { name, schema, candidates: decision.candidates, isDecided: true, ...(pick && decision.isRanked && { instructions: pick.instructions }) };
}

/**
 * Any other open argument: what the sketch lists, the schema allows or the
 * last answer offers (ADR-0013), or why not.
 */
function listedArgument(name, schema, listed, last) {
  const candidates = candidatesFor(schema, { listed, last });
  if (candidates.length > 0) return { name, schema, candidates };
  return { why: `argument "${name}" (${schema.type ?? 'any'}) has nothing to choose from; list values for it in sketch.yaml` };
}

const callKey = ({ server = null, tool, arguments: arguments_ = {} }) => JSON.stringify([server ?? null, tool, arguments_]);
const hasAsk = (entry) => Object.values(entry.scores ?? {}).some((factor) => factor.ask);
const isAsked = (entry, field) => Boolean(entry.scores?.[field]?.ask);
const valuesOf = (answers) => Object.fromEntries(Object.entries(answers).map(([field, answer]) => [field, answer.value]));

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
 *   decide?: Record<string, { field?: string, join?: string, gates?: object, scores?: object, shortlist?: object }> }} sketch
 */
export function mcpApp({ calls = [], values = {}, decide = {}, pick = null, questions = {} } = {}) {
  const warned = new Set();
  // UND-23: Jev's Score answers, once per row per run - `${question}|${row}`
  // to { value 0..1, step it was asked at }. Rows waiting for one are asked
  // together on the next look.
  const scored = new Map();
  let waitingScores = new Map();
  let step = 0;
  // What each tool last answered (a deciding sketch only), for Jev's view,
  // and every call that answered, by tool and arguments.
  const saidBy = new Map();
  const answeredCalls = new LRUCache({ max: ANSWERED_CALLS });
  // UND-25: where each decided argument stood at the last look.
  const standing = new Map();
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
  function decided(key, argument, { isQuiet = false } = {}) {
    const entry = decide[key];
    if (!entry) return null;
    const ranked = [];
    let reused = 0;
    const removed = [];
    const waiting = [];
    const fresh = rows.valuesOf(entry.field ?? argument).filter(({ value }) => !spent.get(key).has(value));
    for (const { value, row } of fresh) {
      const { result, reusing } = judged(entry, value, row);
      reused += reusing;
      if (result.removed) removed.push({ value, why: result.removed });
      else if (result.missing) waiting.push({ value, missing: result.missing, ...(entry.join && { about: row[entry.join] }) });
      else ranked.push({ value, factors: result.factors, total: result.total });
    }
    if (!isQuiet) sayHeld(key, argument, waiting.filter((each) => !isAsked(entry, each.missing)));
    const heldBack = waiting.map(({ value, missing, about }) => ({ value, missing: about === undefined ? missing : `${missing} for ${about}` }));
    // UND-22: with scores, Jev chooses from the shortlist, best first.
    const table = entry.scores ? shortlist(ranked, entry.shortlist).slice(0, MAX_CANDIDATES) : null;
    // Owner, 2026-10-16: decide only once every value's facts are in -
    // unless one already scores a perfect 1 (nothing can beat it).
    const isPerfect = table?.[0]?.total === 1;
    const isWaiting = heldBack.length > 0 && !isPerfect;
    const candidates = isWaiting ? [] : (table ?? ranked.slice(0, MAX_CANDIDATES)).map((each) => each.value);
    const jev = hasAsk(entry) ? { jev: { asked: scored.values().filter((each) => each.step === step).toArray().length, reused } } : {};
    const record = { argument: key, ...(table && { table }), removed, held: heldBack, ...jev };
    standing.set(key, { seen: rows.valuesOf(entry.field ?? argument).length, shortlisted: candidates.length, held: heldBack.length, removed });
    return { candidates, why: whyNone(heldBack, removed), record, isRanked: Boolean(entry.scores) };
  }

  /**
   * One value through its gates and scores, and how many Jev answers it
   * reused; a Score it waits for is queued for the next look.
   */
  function judged(entry, value, row) {
    const facts = rows.factsOf(row, entry.join);
    const passed = gate(facts, entry.gates, { inputs: app.inputs });
    if (!passed.pass) return { result: passed, reusing: 0 };
    const about = entry.join ? row[entry.join] : value;
    const answers = answersFor(entry.scores, about);
    const result = score(facts, entry.scores, { weights: app.weights, answers: valuesOf(answers) });
    if (result.ask) waitingScores.set(`${result.ask}|${about}`, { ask: result.ask, about, facts });
    return { result, reusing: Object.values(answers).filter((each) => each.step < step).length };
  }

  /**
   * The Score answers known for a row, by factor.
   */
  function answersFor(factors = {}, about) {
    const answers = {};
    for (const [field, factor] of Object.entries(factors)) {
      const known = factor.ask && scored.get(`${factor.ask}|${about}`);
      if (known) answers[field] = known;
    }
    return answers;
  }

  /**
   * Asks Jev every Score the decided arguments are waiting for, in one
   * request: each row's `looks_at` field in the state, one question per
   * row (ADR-0020). Answers are kept for the run.
   */
  async function askScores(judge) {
    if (waitingScores.size === 0) return;
    const waiting = waitingScores.values().toArray();
    waitingScores = new Map();
    // UND-40: a score question sees the run's inputs too.
    const state = { rows: {}, ...(Object.keys(app.inputs).length > 0 && { inputs: app.inputs }) };
    const asked = {};
    for (const [index, { ask, facts }] of waiting.entries()) {
      const id = `r${index + 1}`;
      const question = questions[ask];
      state.rows[id] = { [question.looks_at]: facts[question.looks_at] ?? null };
      asked[id] = { type: 'score', instructions: `About \`rows.${id}.${question.looks_at}\`: ${question.instructions}`, criteria: question.levels };
    }
    const response = await judge.systemOne({ state, questions: asked });
    for (const [index, { ask, about }] of waiting.entries()) {
      const answer = response.answers?.[`r${index + 1}`];
      const top = questions[ask].levels.length - 1;
      if (typeof answer?.score === 'number') scored.set(`${ask}|${about}`, { value: Math.min(1, Math.max(0, answer.score / top)), step });
    }
  }
  let looked = { tools: [], last: null };
  // Values come from the last answer that was not an error: a refused
  // call must not take away what the one before it offered.
  let answered = null;
  const app = {
    // Set by the run: one stderr line, e.g. a tool not offered.
    notify: null,
    // Set by the run: the person's inputs (UND-24), e.g. { mood: 'fun', centre: 7 },
    // and the weight each weight input gives its factors, e.g. { centre: 2.1 }.
    inputs: {},
    weights: {},

    /**
     * The moves a view offers, and the ones it cannot, with why.
     */
    moves(view, options = {}) {
      if (view.last && !view.last.isError) answered = view.last;
      rows.remember(view.last);
      if (Object.keys(decide).length > 0 && view.last && !view.last.isError) {
        saidBy.set(nameOf({ server: view.last.server, name: view.last.tool }), view.last.text.slice(0, EARLIER_CHARS));
        answeredCalls.set(callKey(view.last), true);
      }
      // A refused call spends nothing.
      if (spending.length > 0 && view.last?.isError) for (const [key, value] of spending) spent.get(key).delete(value);
      spending = [];
      const found = view.tools.flatMap((tool) => movesFor(tool, { calls, values, last: answered, decided: (key, argument) => decided(key, argument, options), pick, inputs: app.inputs }));
      // Owner, 2026-10-16: a deciding sketch keeps every answer, so a call
      // already answered with the same arguments is not made again.
      const all = found.map((move) => (move.open?.length === 0 && answeredCalls.get(callKey(move.call))
        ? { id: move.id, why: 'already answered with these arguments - its answer is kept' }
        : move));
      const blocked = all.filter((move) => move.why);
      for (const { id, why } of blocked) {
        if (warned.has(id)) continue;
        warned.add(id);
        app.notify?.(`not offering ${id} yet - ${why}`);
      }
      return { offered: all.filter((move) => !move.why), blocked };
    },
    phase: (view) => (app.moves(view).offered.length > 0 ? 'asking' : 'waiting'),
    /**
     * Before the phase is read: the Scores decided values wait for are
     * asked (a look that finds nothing new asks nothing).
     */
    /**
     * Where each decided argument stands: values seen, shortlisted, held
     * back - for the `nothing_qualifies` guard (ADR-0021).
     */
    decisions: () => Object.fromEntries([...standing].map(([key, { seen, shortlisted, held: waiting }]) => [key, { seen, shortlisted, held: waiting }])),
    /**
     * What the gates and zero scores removed, per argument and field - for
     * the walked-away line and sentence.
     */
    leaving() {
      const removed = {};
      for (const [key, each] of standing) {
        const counts = {};
        for (const { why } of each.removed) {
          const rule = why.startsWith('none of any') ? 'any' : why.split(' ', 1)[0];
          counts[rule] = (counts[rule] ?? 0) + 1;
        }
        if (Object.keys(counts).length > 0) removed[key] = counts;
      }
      const parts = Object.entries(removed).flatMap(([key, counts]) => Object.entries(counts).map(([rule, count]) => `${rule} removed ${count} ${key.split('.').at(-1)}${count === 1 ? '' : 's'}`));
      return { removed, sentence: `walked away - nothing qualified: ${parts.join('; ') || 'nothing was offered'}` };
    },
    async prepare(view, judge) {
      if (Object.values(decide).every((entry) => !hasAsk(entry))) return;
      app.moves(view, { isQuiet: true });
      await askScores(judge);
    },
    project(view) {
      // `options` offers the moves of the view projected last (play
      // projects, then asks for options, from one look).
      looked = view;
      const { last } = view;
      const lastTool = last ? nameOf({ server: last.server, name: last.tool }) : null;
      // A deciding sketch plays several calls before it acts: Jev sees what
      // each other tool last said too, so it need not ask again (sprint 5 live run).
      const others = Object.entries(Object.fromEntries(saidBy)).filter(([tool]) => tool !== lastTool);
      return {
        tools: view.tools.map((tool) => described(tool)),
        last_call: last ? { tool: lastTool, arguments: last.arguments, failed: last.isError, said: last.text.slice(0, RESULT_CHARS) } : null,
        ...(others.length > 0 && { earlier: Object.fromEntries(others) }),
      };
    },
    options: () => app.moves(looked).offered,
    act(move) {
      step += 1;
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
