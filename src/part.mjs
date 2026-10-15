// Sprint 1 UND-3: an example directory, loaded and checked as a whole
// before anything starts.
//
//   <dir>/adapter.mjs          what the app looks like and which moves it offers (docs/ADAPTERS.md)
//   <dir>/part/turn.yaml       the statechart (`machine.mjs` checks it)
//   <dir>/part/questions.yaml  what Jev is asked (TypeSafe question definitions)
//
// Every mistake is refused HERE as a `UsageError` naming the file and the
// path in it - never found halfway through a run (recard US-129 Gate 1).

import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import YAML from 'yaml';
import { UsageError } from './errors.mjs';
import { parseTurn, unknown } from './machine.mjs';
import { genericLibrary, mergeLibraries } from './library.mjs';
import { checkInstruction } from './strategyFile.mjs';

const NEEDS = 'an example directory needs adapter.mjs, part/turn.yaml and part/questions.yaml';
const QUESTION_TYPES = ['noul', 'choice', 'score'];
const TARGET_KINDS = new Set(['process', 'page']);
const APP_HOOKS = ['phase', 'project', 'options', 'act'];

/**
 * A path as the author would type it: relative inside the current
 * directory, absolute outside it (never `../../..`).
 */
export function shown(file) {
  const relative = path.relative(process.cwd(), file);
  return relative.startsWith('..') || path.isAbsolute(relative) ? path.resolve(file) : relative;
}

function requireFile(directory, name) {
  const file = path.join(directory, name);
  if (!existsSync(file)) throw new UsageError(`${shown(directory)}: no ${name} - ${NEEDS}`);
  return file;
}

function readYaml(file) {
  try {
    return YAML.parse(readFileSync(file, 'utf8')) ?? {};
  } catch (error) {
    throw new UsageError(`${shown(file)}: not valid YAML - ${error.message.split('\n', 1)[0].replace(/:$/, '')}`);
  }
}

/**
 * Loads `<dir>/adapter.mjs` and checks its shape; nothing in it is called.
 * @param {string} directory
 * @returns {Promise<object>} the adapter (its default export)
 */
export async function loadAdapter(directory) {
  const file = requireFile(directory, 'adapter.mjs');
  let adapter;
  try {
    ({ default: adapter } = await import(pathToFileURL(path.resolve(file)).href));
  } catch (error) {
    throw new UsageError(`${shown(file)}: could not be loaded - ${error.message}`);
  }
  const fail = (message) => { throw new UsageError(`${shown(file)}: ${message}`); };
  if (!adapter || typeof adapter !== 'object') fail('needs a default export - see docs/ADAPTERS.md');
  if (typeof adapter.name !== 'string' || adapter.name === '') fail('name must be a non-empty string - see docs/ADAPTERS.md');
  if (!TARGET_KINDS.has(adapter.target?.kind)) fail(`target.kind must be "process" or "page" (got ${JSON.stringify(adapter.target?.kind ?? null)})`);
  for (const hook of APP_HOOKS) {
    if (typeof adapter.app?.[hook] !== 'function') fail(`app.${hook} must be a function - see docs/ADAPTERS.md`);
  }
  const kinds = Object.entries(adapter.library ?? {});
  for (const [kind, names] of kinds) {
    const entries = Object.entries(names ?? {});
    for (const [name, entry] of entries) {
      if (typeof entry?.doc !== 'string' || entry.doc === '') fail(`library.${kind}.${name} needs a one-line doc`);
    }
  }
  return adapter;
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

function checkQuestions(file, questions) {
  const fail = (where, message) => { throw new UsageError(`${shown(file)}: ${where}: ${message}`); };
  if (typeof questions !== 'object' || Array.isArray(questions)) fail('(top)', 'a questions file maps each question name to its definition');
  for (const [name, question] of Object.entries(questions)) {
    if (!QUESTION_TYPES.includes(question?.type)) fail(`${name}.type`, unknown('question type', question?.type, QUESTION_TYPES));
    if (typeof question.instructions !== 'string') fail(`${name}.instructions`, 'every question needs instructions');
    for (const [where, text] of proseOf(name, question)) {
      const complaint = checkInstruction(text);
      if (complaint) throw new UsageError(`${shown(file)}: ${where} ${complaint}`);
    }
  }
}

/**
 * Loads and checks a whole example directory. Starts nothing, calls
 * nothing: `services` is empty until the run fills it (target, judge...).
 * @param {string} directory
 */
export async function loadPart(directory) {
  const adapter = await loadAdapter(directory);
  const turnFile = requireFile(directory, path.join('part', 'turn.yaml'));
  const questionsFile = requireFile(directory, path.join('part', 'questions.yaml'));
  const questions = readYaml(questionsFile);
  checkQuestions(questionsFile, questions);
  const text = readFileSync(turnFile, 'utf8');
  readYaml(turnFile); // a YAML mistake is reported as one, with its line
  const services = { questions };
  let library;
  try {
    library = mergeLibraries(genericLibrary(services), adapter.library ?? {});
  } catch (error) {
    throw new UsageError(`${shown(path.join(directory, 'adapter.mjs'))}: ${error.message}`);
  }
  let compiled;
  try {
    compiled = parseTurn(text, { file: shown(turnFile), library, questions: Object.keys(questions) });
  } catch (error) {
    throw new UsageError(error.message);
  }
  const states = Object.keys(compiled.config.states).length - 1; // not the reserved stop state
  return { directory, adapter, questions, machine: compiled.machine, services, states };
}

/**
 * `understudy check`: the load, and one line saying what was checked.
 * @param {string} directory
 */
export async function checkPart(directory) {
  const { adapter, questions, states } = await loadPart(directory);
  const count = Object.keys(questions).length;
  return `${shown(directory)}: part OK - ${states} states, ${count} question${count === 1 ? '' : 's'}, adapter ${adapter.name} (${adapter.target.kind})`;
}

/**
 * `understudy library <dir>`: that adapter's own names.
 * @param {string} directory
 */
export async function adapterLibrary(directory) {
  const adapter = await loadAdapter(directory);
  return { name: adapter.name, library: adapter.library ?? {} };
}
