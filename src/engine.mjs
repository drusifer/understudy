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
//
// Scores rank what passes (UND-22, ADR-0018). Each factor puts one field
// at a position 0..1 - `range: [from, to]` (straight, either way, clamped)
// or `order: [best, ..., worst]` (item i of n at (n - i) / n, unlisted 0) -
// and its weight bends it: score = position ^ weight, weight 0 = off. A
// value's total is the product of its scores, so the factor weighted most
// counts most and a zero anywhere removes the value. The shortlist is
// every total above zero, best first, bounded by `at_most` and/or
// `total: { at_least }`.

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

export const FACTOR_WORDS = ['range', 'order', 'weight'];
const round = (value) => Math.round(value * 1000) / 1000;

/**
 * Where a fact sits along a factor, 0..1 (null when it cannot be placed).
 */
function positionOf(fact, factor) {
  if (factor.order) {
    const index = factor.order.indexOf(fact);
    return index === -1 ? 0 : (factor.order.length - index) / factor.order.length;
  }
  const [from, to] = factor.range.map((each) => comparable(each));
  const have = comparable(fact);
  if (have === null) return null;
  return Math.min(1, Math.max(0, (have - from) / (to - from)));
}

/**
 * A value's factor scores and their product.
 * @param {object} facts
 * @param {Record<string, { range?: unknown[], order?: unknown[], weight?: number }>} factors
 * @returns {{ factors: Record<string, number>, total: number }|{ missing: string }|{ removed: string, factors: object, total: 0 }}
 */
export function score(facts, factors = {}) {
  const scores = {};
  let total = 1;
  let zero = null;
  for (const [field, factor] of Object.entries(factors)) {
    const weight = factor.weight ?? 1;
    if (weight === 0) {
      scores[field] = 1;
      continue;
    }
    if (!Object.hasOwn(facts, field)) return { missing: field };
    const raw = (positionOf(facts[field], factor) ?? 0) ** weight;
    scores[field] = round(raw);
    total *= raw;
    zero ??= raw === 0 ? field : null;
  }
  if (zero) return { removed: `${zero} ${shown(facts[zero])} scores 0`, factors: scores, total: 0 };
  return { factors: scores, total: round(total) };
}

/**
 * The scored values worth Jev's pick: best first (ties keep their order),
 * bounded by `at_most` and `total.at_least`.
 * @param {{ value: unknown, total: number }[]} scored
 * @param {{ at_most?: number, total?: { at_least?: number } }} [bounds]
 */
export function shortlist(scored, bounds = {}) {
  const floor = bounds.total?.at_least ?? 0;
  const ranked = scored.filter((each) => each.total > 0 && each.total >= floor).toSorted((a, b) => b.total - a.total);
  return bounds.at_most === undefined ? ranked : ranked.slice(0, bounds.at_most);
}

const isRange = (range) => Array.isArray(range) && range.length === 2
  && range.every((each) => comparable(each) !== null) && comparable(range[0]) !== comparable(range[1]);

function checkFactor(factor, where, fail) {
  if (!isMapping(factor)) fail(where, 'must be { range: [from, to] } or { order: [best, ...] }, with a weight');
  const extra = Object.keys(factor).find((word) => !FACTOR_WORDS.includes(word));
  if (extra) fail(where, `unknown word "${extra}" - use ${FACTOR_WORDS.join(', ')}`);
  if (Object.hasOwn(factor, 'range') === Object.hasOwn(factor, 'order')) fail(where, 'needs one of range: [from, to] or order: [best, ...]');
  if (factor.range !== undefined && !isRange(factor.range)) fail(`${where}.range`, 'must be two different numbers or HH:MM times, e.g. [0.3, 1]');
  if (factor.order !== undefined && (!Array.isArray(factor.order) || factor.order.length === 0)) fail(`${where}.order`, 'must be a list, best first, e.g. [E, F, D]');
  if (factor.weight !== undefined && !(typeof factor.weight === 'number' && factor.weight >= 0)) fail(`${where}.weight`, `must be a number of 0 or more (got ${shown(factor.weight)})`);
}

/**
 * Checks a scores mapping as written.
 */
export function checkScores(factors, at, fail) {
  if (!isMapping(factors)) fail(at, 'must map each field to a factor, e.g. { centre: { range: [0.3, 1], weight: 3 } }');
  for (const [field, factor] of Object.entries(factors)) checkFactor(factor, `${at}.${field}`, fail);
}

/**
 * Checks a shortlist bound as written.
 */
export function checkShortlist(bounds, at, fail) {
  const isGood = isMapping(bounds)
    && Object.keys(bounds).every((word) => word === 'at_most' || word === 'total')
    && (bounds.at_most === undefined || (Number.isSafeInteger(bounds.at_most) && bounds.at_most > 0))
    && (bounds.total === undefined || (isMapping(bounds.total) && typeof bounds.total.at_least === 'number'));
  if (!isGood) fail(at, 'must be { at_most: N } and/or { total: { at_least: X } }');
}
