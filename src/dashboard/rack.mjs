// Sprint 6 UND-27, UND-28 (ARCH §3, ADR-0023): the dashboard's sketch rack -
// every sketch in a folder, and what the console needs to draw one: its
// inputs as controls, the factors each weight drives, its statechart.
// Sketches are found by directory name; nothing outside the folder is read.

import { existsSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { UsageError } from '../errors.mjs';
import { loadSketch } from '../sketch.mjs';
import { turnGraph } from '../watch/turnGraph.mjs';

const SKETCH = 'sketch.yaml';

/**
 * The folder's sketch directories, by name, sorted.
 * @throws {UsageError} not a folder, or no sketch in it
 */
export function sketchNames(folder) {
  if (!existsSync(folder) || !statSync(folder).isDirectory()) throw new UsageError(`${folder} is not a folder of sketches - give a folder holding sketch directories, e.g. examples`);
  const names = readdirSync(folder, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith('.') && existsSync(path.join(folder, entry.name, SKETCH)))
    .map((entry) => entry.name)
    .toSorted((a, b) => a.localeCompare(b));
  if (names.length === 0) throw new UsageError(`${folder} holds no sketches - each sketch is a directory with a ${SKETCH}`);
  return names;
}

const SHORT = 70;

/**
 * A description's first clause - up to its first colon, full stop or line
 * end - kept short for a rack tab.
 */
function firstLine(text) {
  const [first] = (text ?? '').trim().split(/[:.\n]/, 1);
  return first.length > SHORT ? `${first.slice(0, SHORT - 1).trimEnd()}…` : first;
}

/**
 * The rack: each sketch's name and first line, or why it cannot be played.
 * @returns {Promise<{ name: string, title: string|null, description: string, ok: boolean, problem: string|null }[]>}
 */
export async function listSketches(folder) {
  const rack = [];
  for (const name of sketchNames(folder)) {
    try {
      const sketch = await loadSketch(path.join(folder, name));
      rack.push({ name, title: sketch.name, description: firstLine(sketch.description), ok: true, problem: null });
    } catch (error) {
      if (!(error instanceof UsageError)) throw error;
      rack.push({ name, title: null, description: '', ok: false, problem: error.message });
    }
  }
  return rack;
}

/**
 * The factors a weight input drives, wherever `decide:` names it.
 */
function factorsOf(decide, weight) {
  const factors = [];
  const entries = Object.entries(decide ?? {});
  for (const [argument, entry] of entries) {
    const scores = Object.entries(entry.scores ?? {});
    for (const [field, factor] of scores) {
      if (factor.weight === weight) factors.push({ argument, field, ...factor });
    }
  }
  return factors;
}

/**
 * The gate tests a switch input turns on and off.
 */
function gatesOf(decide, name) {
  const found = [];
  const walk = (argument, gates) => {
    const tests = Object.entries(gates ?? {});
    for (const [field, test] of tests) {
      if (field === 'any') for (const group of test) walk(argument, group);
      else if (test?.when === name) found.push({ argument, field });
    }
  };
  const entries = Object.entries(decide ?? {});
  for (const [argument, entry] of entries) walk(argument, entry.gates);
  return found;
}

/**
 * One input as a control.
 */
function controlOf(name, input, sketch) {
  if (input.choose) return { name, kind: 'choose', options: input.choose, default: input.default };
  if (input.switch) return { name, kind: 'switch', default: input.default, gates: gatesOf(sketch.decide, name) };
  if (input.count) return { name, kind: 'count', range: input.count, default: input.default };
  const factors = factorsOf(sketch.decide, name).map((factor) => (factor.ask
    ? { ...factor, question: factor.ask, looks_at: sketch.questions[factor.ask]?.looks_at ?? null }
    : factor));
  return { name, kind: 'weight', range: input.weight, default: input.default, factors };
}

/**
 * The transitions into a state that plays a move - the "decision edge"
 * the power flows along.
 */
function decisionEdges(turn, graph) {
  const playing = new Set(Object.entries(turn.states ?? {}).filter(([, state]) => state?.invoke?.src === 'play').map(([id]) => id));
  return graph.edges.map((edge, index) => (playing.has(edge.to) ? index : -1)).filter((index) => index !== -1);
}

/**
 * What the console draws for one sketch of the rack.
 * @throws {UsageError} a name not in the rack, or a sketch that fails its checks
 */
export async function describeSketch(folder, name) {
  if (!sketchNames(folder).includes(name)) throw new UsageError(`no sketch "${name}" in ${folder}`);
  const directory = path.join(folder, name);
  const sketch = await loadSketch(directory);
  const graph = turnGraph(sketch.turn);
  return {
    name, title: sketch.name, description: sketch.description,
    inputs: Object.entries(sketch.inputs).map(([inputName, input]) => controlOf(inputName, input, sketch)),
    graph, decision: decisionEdges(sketch.turn, graph),
  };
}
