// Sprint 5 UND-21 (ARCH §4, ADR-0018): gates over a value's facts - pass,
// removed with why, or held back with the missing fact.
import test from 'node:test';
import assert from 'node:assert/strict';
import { gate, checkGates, comparable } from '../src/engine.mjs';

const OWNER = {
  starts: { at_least: '17:00' },
  any: [{ genre: 'horror', tomato: { at_least: 70 } }, { tomato: { at_least: 91 } }],
};

test('numbers compare as numbers and HH:MM as times', () => {
  assert.equal(comparable(70), 70);
  assert.equal(comparable('19:30'), 1170);
  assert.equal(comparable('9:05'), 545);
  assert.equal(comparable('evening'), null);
});

test('the owner\'s film gate: evening horror at 70+, or anything above 90', () => {
  const film = (genre, tomato, starts) => gate({ genre, tomato, starts }, OWNER);
  assert.deepEqual(film('horror', 82, '19:30'), { pass: true });
  assert.deepEqual(film('drama', 93, '18:00'), { pass: true });
  assert.deepEqual(film('horror', 82, '14:00'), { removed: 'starts 14:00 < 17:00' });
  assert.deepEqual(film('horror', 64, '21:00'), { removed: 'none of any: tomato 64 < 70; tomato 64 < 91' });
  assert.deepEqual(film('sci-fi', 88, '19:00'), { removed: 'none of any: genre sci-fi is not horror; tomato 88 < 91' });
});

test('a missing fact holds a value back; a known failure still removes it', () => {
  assert.deepEqual(gate({ genre: 'horror', starts: '19:30' }, OWNER), { missing: 'tomato' });
  assert.deepEqual(gate({ genre: 'drama', starts: '19:30' }, OWNER), { missing: 'tomato' });
  assert.deepEqual(gate({ genre: 'horror', starts: '14:00' }, OWNER), { removed: 'starts 14:00 < 17:00' });
});

test('is, in, at_most, and a bare value', () => {
  const seat = { row: 'G', together: 2, centre: 0.4 };
  assert.deepEqual(gate(seat, { row: { in: ['E', 'F', 'D'] } }), { removed: 'row G not in [E, F, D]' });
  assert.deepEqual(gate(seat, { together: { at_least: 2 }, centre: { at_most: 0.5 } }), { pass: true });
  assert.deepEqual(gate(seat, { row: 'G' }), { pass: true });
  assert.deepEqual(gate(seat, { row: { is: 'E' } }), { removed: 'row G is not E' });
});

test('check refuses unknown words, a non-list in or any, and an incomparable bound - naming the path', () => {
  const refusal = (gates) => {
    try {
      checkGates(gates, 'decide.x.y.gates', (at, message) => { throw new Error(`${at}: ${message}`); });
    } catch (error) {
      return error.message;
    }
    return null;
  };
  assert.equal(refusal(OWNER), null);
  assert.equal(refusal({ row: { among: ['E'] } }), 'decide.x.y.gates.row: unknown word "among" - use is, in, at_least, at_most, when, any');
  assert.equal(refusal({ row: { in: 'E' } }), 'decide.x.y.gates.row.in: must be a list, e.g. [E, F, D]');
  assert.equal(refusal({ any: { genre: 'horror' } }), 'decide.x.y.gates.any: must be a list of gate groups, e.g. [{ genre: horror }, { tomato: { at_least: 91 } }]');
  assert.equal(refusal({ starts: { at_least: 'evening' } }), 'decide.x.y.gates.starts.at_least: must be a number or an HH:MM time (got evening)');
});

import { score, shortlist, checkScores, checkShortlist } from '../src/engine.mjs';

const ROWS = { order: ['E', 'F', 'D'] };

test('an order\'s weight bends its curve: E/F/D at weight 1 and 2 (UND-22 AC1)', () => {
  const rowScore = (row, weight) => score({ row }, { row: { ...ROWS, weight } }).factors.row;
  assert.deepEqual(['E', 'F', 'D'].map((row) => rowScore(row, 1)), [1, 0.667, 0.333]);
  assert.deepEqual(['E', 'F', 'D'].map((row) => rowScore(row, 2)), [1, 0.444, 0.111]);
});

test('a range is straight between its ends, either way, clamped; HH:MM works', () => {
  const at = (fact, range) => score({ x: fact }, { x: { range } }).factors?.x;
  assert.equal(at(0.65, [0.3, 1]), 0.5);
  assert.equal(at(2, [0.3, 1]), 1);
  assert.equal(at(14, [20, 10]), 0.6);
  assert.equal(at('19:00', ['17:00', '21:00']), 0.5);
});

test('weight 0 turns a factor off - it scores 1 even at the bottom of its range (Smith, Gate 1)', () => {
  assert.deepEqual(score({ centre: 0.1 }, { centre: { range: [0.3, 1], weight: 0 } }), { factors: { centre: 1 }, total: 1 });
});

test('the total is the product; a zero anywhere removes the value with why (UND-22 AC2)', () => {
  const factors = { row: { ...ROWS, weight: 2 }, centre: { range: [0.3, 1], weight: 3 } };
  const edgeE = score({ row: 'E', centre: 0.4 }, factors);
  const centreF = score({ row: 'F', centre: 1 }, factors);
  assert.ok(edgeE.total > 0 && edgeE.total < 0.01);
  assert.equal(centreF.total, 0.444);
  assert.ok(edgeE.total < centreF.total, 'an edge seat in E ranks below a central one in F (UND-22 AC4)');
  assert.deepEqual(score({ row: 'E', centre: 0.3 }, factors), { removed: 'centre 0.3 scores 0', factors: { row: 1, centre: 0 }, total: 0 });
  assert.deepEqual(score({ row: 'E' }, factors), { missing: 'centre' });
});

test('the shortlist is every total above zero, best first, bounded by at_most and total.at_least (UND-22 AC3)', () => {
  const scored = [{ value: 'a', total: 0.2 }, { value: 'b', total: 0.9 }, { value: 'c', total: 0 }, { value: 'd', total: 0.5 }, { value: 'e', total: 0.5 }];
  assert.deepEqual(shortlist(scored).map((each) => each.value), ['b', 'd', 'e', 'a']);
  assert.deepEqual(shortlist(scored, { at_most: 2 }).map((each) => each.value), ['b', 'd']);
  assert.deepEqual(shortlist(scored, { total: { at_least: 0.5 } }).map((each) => each.value), ['b', 'd', 'e']);
});

test('check refuses a bad range, order, weight or shortlist - naming the factor (UND-22 AC6)', () => {
  const refusal = (check, value) => {
    try {
      check(value, 'decide.x.y.scores', (at, message) => { throw new Error(`${at}: ${message}`); });
    } catch (error) {
      return error.message;
    }
    return null;
  };
  assert.equal(refusal(checkScores, { centre: { range: [0.3, 1], weight: 3 }, row: { order: ['E'] } }), null);
  assert.equal(refusal(checkScores, { centre: { range: [0.3] } }), 'decide.x.y.scores.centre.range: must be two different numbers or HH:MM times, e.g. [0.3, 1]');
  assert.equal(refusal(checkScores, { row: { order: 'E' } }), 'decide.x.y.scores.row.order: must be a list, best first, e.g. [E, F, D]');
  assert.equal(refusal(checkScores, { row: { order: ['E'], weight: -1 } }), 'decide.x.y.scores.row.weight: must be a number of 0 or more, or an input\'s name (got -1)');
  assert.equal(refusal(checkScores, { row: { weight: 2 } }), 'decide.x.y.scores.row: needs one of range: [from, to], order: [best, ...] or ask: <score question>');
  assert.equal(refusal(checkScores, { row: { order: ['E'], curve: 2 } }), 'decide.x.y.scores.row: unknown word "curve" - use range, order, ask, weight');
  assert.equal(refusal(checkShortlist, { at_most: 0 }), 'decide.x.y.scores: must be { at_most: N } and/or { total: { at_least: X } }');
});

test('a weight may name an input; an ask factor uses Jev\'s answer for the value (UND-23, UND-24)', () => {
  const factors = { centre: { range: [0.3, 1], weight: 'centre' }, audience: { ask: 'audience', weight: 2 } };
  assert.deepEqual(score({ centre: 0.65 }, factors, { inputs: { centre: 1 } }), { missing: 'audience', ask: 'audience' });
  assert.deepEqual(score({ centre: 0.65 }, factors, { inputs: { centre: 1 }, answers: { audience: 0.5 } }), { factors: { centre: 0.5, audience: 0.25 }, total: 0.125 });
  assert.deepEqual(score({ centre: 0.65 }, factors, { inputs: { centre: 0 }, answers: { audience: 1 } }), { factors: { centre: 1, audience: 1 }, total: 1 });
  assert.deepEqual(score({ centre: 0.65 }, factors, { inputs: { centre: 1 }, answers: { audience: 0 } }).removed, 'audience 0 scores 0');
});

test('a test with when: applies only while its switch is on (UND-28 AC3)', () => {
  const gates = { together: { at_least: 2, when: 'together' }, row: { in: ['E', 'F', 'D'] } };
  const single = { together: 1, row: 'E' };
  assert.deepEqual(gate(single, gates, { inputs: { together: true } }), { removed: 'together 1 < 2' });
  assert.deepEqual(gate(single, gates, { inputs: { together: false } }), { pass: true });
  assert.deepEqual(gate({ row: 'E' }, gates, { inputs: { together: false } }), { pass: true }, 'an off test needs no fact');
  const refusal = (switches) => {
    try {
      checkGates(gates, 'decide.x.y.gates', (at, message) => { throw new Error(`${at}: ${message}`); }, switches);
    } catch (error) {
      return error.message;
    }
    return null;
  };
  assert.equal(refusal(['together']), null);
  assert.equal(refusal([]), 'decide.x.y.gates.together.when: names "together" - declare it under inputs: as { switch: true, default: true }');
});

test('a gate bound may be one of the run\'s inputs (UND-34 AC2)', () => {
  const gates = { together: { at_least: { input: 'tickets' } } };
  assert.deepEqual(gate({ together: 2 }, gates, { inputs: { tickets: 2 } }), { pass: true });
  assert.deepEqual(gate({ together: 2 }, gates, { inputs: { tickets: 3 } }), { removed: 'together 2 < 3' });
  const refusal = (numbers) => {
    try {
      checkGates(gates, 'decide.x.y.gates', (at, message) => { throw new Error(`${at}: ${message}`); }, [], numbers);
    } catch (error) {
      return error.message;
    }
    return null;
  };
  assert.equal(refusal(['tickets']), null);
  assert.equal(refusal(['mood']), 'decide.x.y.gates.together.at_least: names input "tickets" - declare it under inputs: as a count or a weight');
});
