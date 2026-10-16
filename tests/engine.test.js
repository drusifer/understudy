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
  assert.equal(refusal({ row: { among: ['E'] } }), 'decide.x.y.gates.row: unknown word "among" - use is, in, at_least, at_most, any');
  assert.equal(refusal({ row: { in: 'E' } }), 'decide.x.y.gates.row.in: must be a list, e.g. [E, F, D]');
  assert.equal(refusal({ any: { genre: 'horror' } }), 'decide.x.y.gates.any: must be a list of gate groups, e.g. [{ genre: horror }, { tomato: { at_least: 91 } }]');
  assert.equal(refusal({ starts: { at_least: 'evening' } }), 'decide.x.y.gates.starts.at_least: must be a number or an HH:MM time (got evening)');
});
