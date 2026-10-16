// Sprint 5 UND-24 (ARCH §5): the person's inputs - what a sketch lets the
// person set when the run starts: a choice (their mood) or a weight within
// a range (how much a preference matters). Declared in sketch.yaml, set
// with `understudy run <sketch> --input name=value`, defaults otherwise.
//
//   inputs:
//     mood:   { choose: [fun, serious, dramatic, romantic], default: fun }
//     centre: { weight: [0, 3], default: 3 }

import { UsageError } from './errors.mjs';

const isMapping = (value) => Boolean(value) && typeof value === 'object' && !Array.isArray(value);
const isBounds = (range) => Array.isArray(range) && range.length === 2 && range.every((each) => typeof each === 'number') && range[0] < range[1];

/**
 * Checks `inputs:` as written; `fail(at, message)` names the path.
 */
export function checkInputs(inputs, fail) {
  if (!isMapping(inputs)) fail('inputs', 'must map each input to { choose: [...], default } or { weight: [low, high], default }');
  for (const [name, input] of Object.entries(inputs)) checkInput(name, input, fail);
}

function checkInput(name, input, fail) {
  const at = `inputs.${name}`;
  const kinds = isMapping(input) ? ['choose', 'weight'].filter((kind) => Object.hasOwn(input, kind)) : [];
  if (kinds.length !== 1) fail(at, 'must be { choose: [...], default } or { weight: [low, high], default }');
  const extra = Object.keys(input).find((key) => key !== kinds[0] && key !== 'default');
  if (extra) fail(`${at}.${extra}`, `not an input field (known: ${kinds[0]}, default)`);
  if (input.choose !== undefined && !(Array.isArray(input.choose) && input.choose.length > 0 && input.choose.every((each) => typeof each === 'string'))) {
    fail(`${at}.choose`, 'must be a list of words, e.g. [fun, serious, dramatic, romantic]');
  }
  if (input.weight !== undefined && !isBounds(input.weight)) fail(`${at}.weight`, 'must be [low, high], two numbers, e.g. [0, 3]');
  const problem = problemWith(name, input, input.default);
  if (problem) fail(`${at}.default`, problem.replace(`input "${name}" `, ''));
}

/**
 * Why `value` cannot be `input`'s value, or null.
 */
function problemWith(name, input, value) {
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
    const value = input.weight && /^-?\d+(\.\d+)?$/.test(text) ? Number(text) : text;
    const problem = problemWith(name, input, value);
    if (problem) throw new UsageError(problem);
    values[name] = value;
  }
  return values;
}

/**
 * The names of the weight inputs, for checking `weight: <name>`.
 */
export function weightInputs(declared = {}) {
  return Object.keys(declared).filter((name) => declared[name].weight);
}
