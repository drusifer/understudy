// Sprint 5 UND-21 (ARCH §4, ADR-0018): the decision engine - pure code over
// a value's facts (its answer row, joined). Gates are what the person
// never accepts: a value that fails one is removed, with why; a value
// whose gate needs a fact nobody has answered yet is held back, with
// what is missing - never removed.
//
//   gates:   { <field>: <test>, ..., any: [<gates>, ...] }
//   test:    a bare value (is) | { is, in, at_least, at_most }
//
// `at_least`/`at_most` compare numbers as numbers and HH:MM as times.

export const GATE_WORDS = ['is', 'in', 'at_least', 'at_most'];
const TIME = /^([01]?\d|2[0-3]):([0-5]\d)$/;

const isMapping = (value) => Boolean(value) && typeof value === 'object' && !Array.isArray(value);
const shown = (value) => (typeof value === 'string' ? value : JSON.stringify(value));

/**
 * A number or an HH:MM time as a number to compare (minutes), else null.
 */
export function comparable(value) {
  if (typeof value === 'number') return value;
  const time = typeof value === 'string' ? TIME.exec(value) : null;
  return time ? Number(time[1]) * 60 + Number(time[2]) : null;
}

/**
 * One field's test against its fact: null when it passes, else why not.
 */
function failedTest(field, fact, test) {
  const words = isMapping(test) ? test : { is: test };
  if (Object.hasOwn(words, 'is') && fact !== words.is) return `${field} ${shown(fact)} is not ${shown(words.is)}`;
  if (Object.hasOwn(words, 'in') && !words.in.includes(fact)) return `${field} ${shown(fact)} not in [${words.in.map((each) => shown(each)).join(', ')}]`;
  for (const [word, sign, isFailed] of [['at_least', '<', (a, b) => a < b], ['at_most', '>', (a, b) => a > b]]) {
    if (!Object.hasOwn(words, word)) continue;
    const have = comparable(fact);
    if (have === null || isFailed(have, comparable(words[word]))) return `${field} ${shown(fact)} ${sign} ${shown(words[word])}`;
  }
  return null;
}

/**
 * A value's facts against gates.
 * @returns {{ pass: true }|{ removed: string }|{ missing: string }}
 */
export function gate(facts, gates = {}) {
  let missing = null;
  for (const [field, test] of Object.entries(gates)) {
    if (field === 'any') {
      const results = test.map((group) => gate(facts, group));
      if (results.some((result) => result.pass)) continue;
      const waiting = results.find((result) => result.missing);
      if (waiting) {
        missing ??= waiting.missing;
        continue;
      }
      return { removed: `none of any: ${results.map((result) => result.removed).join('; ')}` };
    }
    if (!Object.hasOwn(facts, field)) {
      missing ??= field;
      continue;
    }
    const why = failedTest(field, facts[field], test);
    if (why) return { removed: why };
  }
  return missing === null ? { pass: true } : { missing };
}

/**
 * One field's test as written.
 */
function checkTest(test, at, fail) {
  if (!isMapping(test)) return;
  for (const [word, value] of Object.entries(test)) {
    if (!GATE_WORDS.includes(word)) fail(at, `unknown word "${word}" - use ${GATE_WORDS.join(', ')}, any`);
    if (word === 'in' && !Array.isArray(value)) fail(`${at}.in`, 'must be a list, e.g. [E, F, D]');
    if ((word === 'at_least' || word === 'at_most') && comparable(value) === null) {
      fail(`${at}.${word}`, `must be a number or an HH:MM time (got ${shown(value)})`);
    }
  }
}

/**
 * Checks a gates mapping as written; `fail(at, message)` names the path.
 */
export function checkGates(gates, at, fail) {
  if (!isMapping(gates)) fail(at, 'must map each field to a test, e.g. { genre: horror, starts: { at_least: \'17:00\' } }');
  for (const [field, test] of Object.entries(gates)) {
    if (field !== 'any') {
      checkTest(test, `${at}.${field}`, fail);
      continue;
    }
    if (!Array.isArray(test) || test.length === 0) fail(`${at}.any`, 'must be a list of gate groups, e.g. [{ genre: horror }, { tomato: { at_least: 91 } }]');
    for (const [index, group] of test.entries()) checkGates(group, `${at}.any[${index}]`, fail);
  }
}
