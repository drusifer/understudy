// Sprint 3 UND-9 (ADR-0011): a sketch - one `sketch.yaml`, loaded and
// checked as a whole before anything starts.
//
//   <dir>/sketch.yaml   name, target, player, steps, questions, turn (the statechart);
//                       for an MCP server also calls and values (ADR-0012/0013)
//   <dir>/hooks.mjs     only where the sketch names it (`app: hooks.mjs`): how to read the app
//
// Every mistake is refused HERE as a `UsageError` naming the file and the
// path in it - never found halfway through a run (recard US-129 Gate 1).

import { existsSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import YAML from 'yaml';
import { UsageError } from './errors.mjs';
import { parseTurn, unknown } from './machine.mjs';
import { genericLibrary, mergeLibraries } from './library.mjs';
import { checkInstruction } from './strategyFile.mjs';
import { pageApp } from './apps/page.mjs';
import { mcpApp } from './apps/mcp.mjs';
import { resolveServers } from './mcpConfig.mjs';

const SKETCH = 'sketch.yaml';
const GUIDE = 'see docs/SKETCHES.md';
const KEYS = ['name', 'description', 'target', 'app', 'player', 'steps', 'questions', 'turn', 'calls', 'values'];
const QUESTION_TYPES = ['noul', 'choice', 'score'];
// The fields a kind cannot do without, with what each one is for.
const REQUIRED = {
  process: { command: 'the program to start, e.g. node' },
  http: { url: 'where the API is, e.g. http://127.0.0.1:{port}', state: 'the path a look GETs, e.g. /status' },
};
// The fields each kind of target takes; anything else is a mistake, named at load.
const TARGET_FIELDS = { process: ['command', 'args'], page: ['root', 'page'], http: ['command', 'args', 'url', 'state'], mcp: ['server', 'servers', 'config'] };
// Kinds with a built-in app, made for each sketch; the others read their
// app through hooks.mjs. An MCP server is only ever played by its own.
const GENERIC_APPS = { page: () => pageApp, mcp: (sketch) => mcpApp({ calls: sketch.calls, values: sketch.values }) };
const ONLY_GENERIC = new Set(['mcp']);
const APP_HOOKS = ['phase', 'project', 'options', 'act'];

/**
 * A path as the author would type it: relative inside the current
 * directory, absolute outside it (never `../../..`).
 */
export function shown(file) {
  const relative = path.relative(process.cwd(), file);
  return relative.startsWith('..') || path.isAbsolute(relative) ? path.resolve(file) : relative;
}

/**
 * The sketch file a command names: a directory holding `sketch.yaml`, or
 * the file itself. A directory in the old adapter/part layout is told so.
 * @param {string} location
 * @returns {{ file: string, directory: string }}
 */
export function findSketch(location) {
  if (!existsSync(location)) throw new UsageError(`${shown(location)}: no such sketch - give a directory holding ${SKETCH}, e.g. examples/cli`);
  if (statSync(location).isFile()) return { file: location, directory: path.dirname(location) };
  const file = path.join(location, SKETCH);
  if (existsSync(file)) return { file, directory: location };
  if (existsSync(path.join(location, 'adapter.mjs')) || existsSync(path.join(location, 'part'))) {
    throw new UsageError(`${shown(location)}: no ${SKETCH} - adapter.mjs and part/ are no longer read; ${GUIDE}`);
  }
  throw new UsageError(`${shown(location)}: no ${SKETCH} - a sketch is a directory holding ${SKETCH}; ${GUIDE}`);
}

function readSketch(file) {
  let data;
  try {
    data = YAML.parse(readFileSync(file, 'utf8'));
  } catch (error) {
    throw new UsageError(`${shown(file)}: not valid YAML - ${error.message.split('\n', 1)[0].replace(/:$/, '')}`);
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new UsageError(`${shown(file)}: a sketch is a mapping of ${KEYS.join(', ')} - ${GUIDE}`);
  return data;
}

const isMapping = (value) => Boolean(value) && typeof value === 'object' && !Array.isArray(value);

/**
 * The top level: known keys, a name, and the shapes of the small ones.
 */
function checkTop(sketch, fail) {
  const extra = Object.keys(sketch).find((key) => !KEYS.includes(key));
  if (extra) fail(extra, `not a sketch key (known: ${KEYS.join(', ')})`);
  if (typeof sketch.name !== 'string' || sketch.name === '') fail('name', `must be a non-empty string - ${GUIDE}`);
  if (sketch.description !== undefined && typeof sketch.description !== 'string') fail('description', 'must be text');
  if (sketch.player !== undefined && !isMapping(sketch.player)) fail('player', 'must be a mapping, e.g. { floor: 0.4 }');
  if (sketch.steps !== undefined && !(Number.isSafeInteger(sketch.steps) && sketch.steps > 0)) fail('steps', `must be a positive whole number (got ${JSON.stringify(sketch.steps)})`);
  if (!isMapping(sketch.questions)) fail('questions', 'needs a mapping of each question name to its definition');
  if (!isMapping(sketch.turn)) fail('turn', 'needs the statechart: a mapping with `initial` and `states`');
}

/**
 * A known kind, and only the fields that kind takes.
 */
function checkTarget(target, fail) {
  const names = Object.keys(TARGET_FIELDS).map((kind) => JSON.stringify(kind));
  const kinds = `${names.slice(0, -1).join(', ')} or ${names.at(-1)}`;
  if (!isMapping(target)) fail('target', `needs a mapping with a kind: ${kinds}`);
  const known = TARGET_FIELDS[target.kind];
  if (!known) fail('target.kind', `must be ${kinds} (got ${JSON.stringify(target.kind ?? null)})`);
  const extra = Object.keys(target).find((field) => field !== 'kind' && !known.includes(field));
  if (extra) fail(`target.${extra}`, `not a ${target.kind} target field (known: ${known.join(', ')})`);
  const missing = Object.keys(REQUIRED[target.kind] ?? {}).find((field) => typeof target[field] !== 'string' || target[field] === '');
  if (missing) fail(`target.${missing}`, `required for ${target.kind === 'http' ? 'an' : 'a'} ${target.kind} target (${REQUIRED[target.kind][missing]})`);
  if (target.kind === 'http' && target.url.includes('{port}') && !target.command) {
    fail('target.url', 'has {port} but no command to start - give the full URL of a running service, or a command');
  }
}

/**
 * The target as the run starts it: an MCP one carries its servers'
 * entries, resolved from the sketch or the file it names. One server
 * keeps no name in play (ids stay `tool:<name>`); several are named.
 */
function resolvedTarget(target, { file, directory }) {
  if (target.kind !== 'mcp') return target;
  const servers = resolveServers(target, { directory, shownFile: shown(file), shown });
  return { kind: 'mcp', servers: servers.length === 1 ? [{ ...servers[0], name: null }] : servers };
}

/**
 * `calls:` and `values:` - the generic MCP app's settings, nothing else's.
 */
function checkCalls(sketch, fail) {
  for (const key of ['calls', 'values']) {
    if (sketch[key] !== undefined && sketch.target.kind !== 'mcp') fail(key, 'only for an mcp target');
  }
  checkCallList(sketch.calls ?? [], fail);
  checkValues(sketch.values ?? {}, fail);
}

function checkCallList(calls, fail) {
  if (!Array.isArray(calls)) fail('calls', 'must be a list of { tool, arguments }');
  for (const [index, call] of calls.entries()) {
    const where = `calls[${index}]`;
    if (!isMapping(call) || typeof call.tool !== 'string' || call.tool === '') fail(where, 'needs tool: <name> (and arguments: { ... } to fix some)');
    const extra = Object.keys(call).find((key) => key !== 'tool' && key !== 'arguments');
    if (extra) fail(`${where}.${extra}`, 'not a call field (known: tool, arguments)');
    if (call.arguments !== undefined && !isMapping(call.arguments)) fail(`${where}.arguments`, 'must map argument names to values');
  }
}

function checkValues(values, fail) {
  if (!isMapping(values)) fail('values', 'must map each tool to { <argument>: [values...] }');
  for (const [tool, arguments_] of Object.entries(values)) {
    if (!isMapping(arguments_)) fail(`values.${tool}`, 'must map each argument to a list of values');
    for (const [name, list] of Object.entries(arguments_)) {
      if (!Array.isArray(list) || list.length === 0) fail(`values.${tool}.${name}`, 'must be a non-empty list of values to choose from');
    }
  }
}

/**
 * The app: the kind's built-in one when the sketch names no hooks, else
 * `hooks.mjs` (or whatever `app:` names) next to the sketch.
 * @returns {Promise<{ app: object, library: object, hooks: string|null }>}
 */
async function loadApp(sketch, { file, directory }, fail) {
  const generic = GENERIC_APPS[sketch.target.kind];
  if (sketch.app !== undefined && ONLY_GENERIC.has(sketch.target.kind)) {
    fail('app', `an ${sketch.target.kind} target is played by the generic MCP app - remove app: (use calls: and values:) - ${GUIDE}`);
  }
  if (sketch.app === undefined) {
    if (!generic) fail('app', `a ${sketch.target.kind} target needs hooks that read the app, e.g. app: hooks.mjs - ${GUIDE}`);
    return { app: generic(sketch), library: {}, hooks: null };
  }
  if (typeof sketch.app !== 'string' || sketch.app === '') fail('app', 'must name a module next to the sketch, e.g. hooks.mjs');
  const hooksFile = path.resolve(directory, sketch.app);
  if (!existsSync(hooksFile)) fail('app', `${sketch.app} not found next to ${path.basename(file)}`);
  let module;
  try {
    module = await import(pathToFileURL(path.resolve(hooksFile)).href);
  } catch (error) {
    throw new UsageError(`${shown(hooksFile)}: could not be loaded - ${error.message}`);
  }
  const hooksFail = (message) => { throw new UsageError(`${shown(hooksFile)}: ${message}`); };
  const app = module.default;
  if (!isMapping(app)) hooksFail(`needs a default export with ${APP_HOOKS.join(', ')} - ${GUIDE}`);
  for (const hook of APP_HOOKS) {
    if (typeof app[hook] !== 'function') hooksFail(`${hook} must be a function - ${GUIDE}`);
  }
  const library = module.library ?? {};
  checkLibrary(library, hooksFail);
  return { app, library, hooks: sketch.app };
}

/**
 * Every name the hooks add says what it means.
 */
function checkLibrary(library, fail) {
  for (const [kind, names] of Object.entries(library)) {
    const entries = Object.entries(names ?? {});
    for (const [name, entry] of entries) {
      if (typeof entry?.doc !== 'string' || entry.doc === '') fail(`library.${kind}.${name} needs a one-line doc`);
    }
  }
}

/**
 * Every piece of prose Jev reads in one question, labelled by its path.
 */
function proseOf(name, question) {
  const prose = [[`${name}.instructions`, question.instructions ?? '']];
  if (question.criteria && !Array.isArray(question.criteria)) {
    for (const [key, text] of Object.entries(question.criteria)) prose.push([`${name}.criteria.${key}`, String(text)]);
  }
  const levels = (question.levels ?? []).entries();
  for (const [index, level] of levels) prose.push([`${name}.levels[${index}]`, String(level)]);
  return prose;
}

function checkQuestions(questions, fail) {
  for (const [name, question] of Object.entries(questions)) {
    if (!QUESTION_TYPES.includes(question?.type)) fail(`questions.${name}.type`, unknown('question type', question?.type, QUESTION_TYPES));
    if (typeof question.instructions !== 'string') fail(`questions.${name}.instructions`, 'every question needs instructions');
    for (const [where, text] of proseOf(name, question)) {
      const complaint = checkInstruction(text);
      if (complaint) fail(`questions.${where}`, complaint);
    }
  }
}

/**
 * Loads and checks a whole sketch. Starts nothing, calls nothing:
 * `services` is empty until the run fills it (target, judge...).
 * @param {string} location a directory holding sketch.yaml, or the file
 */
export async function loadSketch(location) {
  const { file, directory } = findSketch(location);
  const sketch = readSketch(file);
  const fail = (where, message) => { throw new UsageError(`${shown(file)}: ${where}: ${message}`); };
  checkTop(sketch, fail);
  checkTarget(sketch.target, fail);
  const target = resolvedTarget(sketch.target, { file, directory });
  checkCalls(sketch, fail);
  checkQuestions(sketch.questions, fail);
  const { app, library: own, hooks } = await loadApp(sketch, { file, directory }, fail);
  const services = { questions: sketch.questions };
  let library;
  try {
    library = mergeLibraries(genericLibrary(services), own);
  } catch (error) {
    throw new UsageError(`${shown(path.join(directory, hooks ?? ''))}: ${error.message}`);
  }
  let compiled;
  try {
    compiled = parseTurn(sketch.turn, { file: shown(file), library, questions: Object.keys(sketch.questions) });
  } catch (error) {
    throw new UsageError(error.message);
  }
  return {
    directory, file, name: sketch.name, target, player: sketch.player ?? {}, steps: sketch.steps ?? null,
    app, library: own, hooks, questions: sketch.questions, turn: sketch.turn, machine: compiled.machine, services,
    states: Object.keys(compiled.config.states).length - 1, // not the reserved stop state
  };
}

/**
 * `understudy check`: the load, and one line saying what was checked.
 * @param {string} location
 */
export async function checkSketch(location) {
  const { directory, name, target, hooks, questions, states } = await loadSketch(location);
  const count = Object.keys(questions).length;
  return `${shown(directory)}: sketch OK - ${name} (${target.kind}, ${hooks ?? 'generic app'}) - ${states} states, ${count} question${count === 1 ? '' : 's'}`;
}

/**
 * `understudy library <sketch>`: the names its hooks add.
 * @param {string} location
 */
export async function sketchLibrary(location) {
  const { name, library } = await loadSketch(location);
  return { name, library };
}
