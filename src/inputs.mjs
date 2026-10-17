// Sprint 5 UND-24 (ARCH §5): the person's inputs - what a sketch lets the
// person set when the run starts: a choice (their mood) or a weight within
// a range (how much a preference matters). Declared in sketch.yaml, set
// with `understudy run <sketch> --input name=value`, defaults otherwise.
//
//   inputs:
//     mood:   { choose: [fun, serious, dramatic, romantic], default: fun }
//     centre: { weight: [0, 3], default: 3 }
//     together: { switch: true, default: true }      (sprint 6: turns a gate on or off, `when:`)
//     tickets: { count: [1, 4], default: 2 }         (sprint 7: a whole number; `{ input: tickets }`)

import { UsageError } from './errors.mjs';

const KINDS = ['choose', 'weight', 'switch', 'count'];
const SHAPES = '{ choose: [...], default }, { weight: [low, high], default }, { count: [low, high], default } or { switch: true, default: true|false }';
const SWITCH_WORDS = new Map([['on', true], ['true', true], ['off', false], ['false', false]]);
const isMapping = (value) => Boolean(value) && typeof value === 'object' && !Array.isArray(value);
const isBounds = (range) => Array.isArray(range) && range.length === 2 && range.every((each) => typeof each === 'number') && range[0] < range[1];

/**
 * Checks `inputs:` as written; `fail(at, message)` names the path.
 */
export function checkInputs(inputs, fail) {
  if (!isMapping(inputs)) fail('inputs', `must map each input to ${SHAPES}`);
  for (const [name, input] of Object.entries(inputs)) checkInput(name, input, fail);
}

function checkInput(name, input, fail) {
  const at = `inputs.${name}`;
  const kinds = isMapping(input) ? KINDS.filter((kind) => Object.hasOwn(input, kind)) : [];
  if (kinds.length !== 1) fail(at, `must be ${SHAPES}`);
  const extra = Object.keys(input).find((key) => key !== kinds[0] && key !== 'default');
  if (extra) fail(`${at}.${extra}`, `not an input field (known: ${kinds[0]}, default)`);
  if (input.choose !== undefined && !(Array.isArray(input.choose) && input.choose.length > 0 && input.choose.every((each) => typeof each === 'string'))) {
    fail(`${at}.choose`, 'must be a list of words, e.g. [fun, serious, dramatic, romantic]');
  }
  if (input.weight !== undefined && !isBounds(input.weight)) fail(`${at}.weight`, 'must be [low, high], two numbers, e.g. [0, 3]');
  if (input.count !== undefined && !(isBounds(input.count) && input.count.every((each) => Number.isSafeInteger(each)))) fail(`${at}.count`, 'must be [low, high], two whole numbers, e.g. [1, 4]');
  if (input.switch !== undefined && input.switch !== true) fail(`${at}.switch`, 'must be true - a switch is { switch: true, default: true|false }');
  const problem = problemWith(name, input, input.default);
  if (problem) fail(`${at}.default`, problem.replace(`input "${name}" `, ''));
}

/**
 * Why `value` cannot be `input`'s value, or null.
 */
function problemWith(name, input, value) {
  if (input.switch) return typeof value === 'boolean' ? null : `input "${name}" must be on or off, got ${JSON.stringify(value)}`;
  if (input.count) {
    const [low, high] = input.count;
    return Number.isSafeInteger(value) && value >= low && value <= high ? null : `input "${name}" must be a whole number from ${low} to ${high}, got ${value}`;
  }
  if (input.choose) {
    return input.choose.includes(value) ? null : `input "${name}" must be one of ${input.choose.join(', ')}, got ${JSON.stringify(value)}`;
  }
  const [low, high] = input.weight;
  return typeof value === 'number' && value >= low && value <= high ? null : `input "${name}" must be between ${low} and ${high}, got ${value}`;
}

/**
 * The inputs' values for a run: each `name=value` given, else its default.
 * @param {Record<string, object>} declared the sketch's `inputs:`
 * @param {string[]} given `name=value` pairs from `--input`
 * @throws {UsageError} an unknown name or a value out of its range or list
 */
export function resolveInputs(declared = {}, given = []) {
  const values = Object.fromEntries(Object.entries(declared).map(([name, input]) => [name, input.default]));
  for (const pair of given) {
    const [name, text] = pair.split(/=(.*)/s, 2);
    if (!Object.hasOwn(declared, name)) {
      const names = Object.keys(declared);
      throw new UsageError(`no input "${name}" in sketch.yaml - it declares ${names.length > 0 ? names.join(', ') : 'none'}`);
    }
    const input = declared[name];
    const value = valueOf(input, text);
    const problem = problemWith(name, input, value);
    if (problem) throw new UsageError(problem);
    values[name] = value;
  }
  return values;
}

/**
 * A `--input` text as the input's kind of value: a number for a weight,
 * a boolean for a switch (on/off, true/false), else the text.
 */
function valueOf(input, text) {
  if ((input.weight || input.count) && /^-?\d+(\.\d+)?$/.test(text)) return Number(text);
  if (input.switch && SWITCH_WORDS.has(text)) return SWITCH_WORDS.get(text);
  return text;
}

/**
 * The names of the inputs that hold a number (weights and counts), for
 * checking `{ input: <name> }` where a number is needed.
 */
export function numberInputs(declared = {}) {
  return Object.keys(declared).filter((name) => declared[name].weight || declared[name].count);
}

/**
 * `{ input: <name> }` - a value the run's inputs fill in (sprint 7).
 */
export const isInputReference = (value) => Boolean(value) && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === 1 && typeof value.input === 'string';

/**
 * The names of the switch inputs, for checking `when: <name>`.
 */
export function switchInputs(declared = {}) {
  return Object.keys(declared).filter((name) => declared[name].switch);
}

// A weight input is a share of the full weighting (owner, 2026-10-16): at
// the top of its range a factor's weight is FULL_WEIGHT, half way 1.5, at
// the bottom 0 (the factor is off).
export const FULL_WEIGHT = 3;

/**
 * The weight each weight input gives the factors that name it, from the
 * run's values: FULL_WEIGHT times its share of its range.
 * @param {Record<string, object>} declared the sketch's `inputs:`
 * @param {Record<string, unknown>} values the run's inputs
 */
export function weightsOf(declared = {}, values = {}) {
  return Object.fromEntries(Object.entries(declared).filter(([, input]) => input.weight).map(([name, input]) => {
    const [low, high] = input.weight;
    return [name, (FULL_WEIGHT * (values[name] - low)) / (high - low)];
  }));
}

/**
 * The names of the weight inputs, for checking `weight: <name>`.
 */
export function weightInputs(declared = {}) {
  return Object.keys(declared).filter((name) => declared[name].weight);
}
