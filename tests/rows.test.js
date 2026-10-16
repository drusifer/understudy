// Sprint 5 UND-21 (ARCH §4 "Answer rows", ADR-0017): answers as rows -
// nested objects inherit their parents' scalars; a value comes from rows
// that own its field; facts join across answers by a key.
import test from 'node:test';
import assert from 'node:assert/strict';
import { answerRows } from '../src/rows.mjs';

const films = { isError: false, text: JSON.stringify([
  { film: 'f1', title: 'Night Shift', genre: 'horror', showings: [{ showing: 's1', starts: '14:00' }, { showing: 's2', starts: '19:30' }] },
]) };
const rating = { isError: false, text: JSON.stringify({ title: 'Night Shift', tomato: 82, reviews: ['great'] }) };
const seats = { isError: false, structured: { showing: 's2', title: 'Night Shift', seats: [{ seat: 's2-E13', row: 'E', centre: 0.83 }] } };

test('a nested row inherits the scalars around it; values come from rows that own the field', () => {
  const rows = answerRows();
  rows.remember(films);
  rows.remember(seats);
  assert.deepEqual(rows.valuesOf('showing').map(({ value }) => value), ['s1', 's2']);
  const s1 = rows.valuesOf('showing')[0].row;
  assert.deepEqual(s1, { film: 'f1', title: 'Night Shift', genre: 'horror', showing: 's1', starts: '14:00' });
  assert.deepEqual(rows.valuesOf('seat'), [{ value: 's2-E13', row: { showing: 's2', title: 'Night Shift', seat: 's2-E13', row: 'E', centre: 0.83 } }]);
});

test('facts join rows that own the join field; the value\'s own row wins', () => {
  const rows = answerRows();
  rows.remember(films);
  const [s1] = rows.valuesOf('showing');
  assert.equal(rows.factsOf(s1.row, 'title').tomato, undefined);
  rows.remember(rating);
  const facts = rows.factsOf(s1.row, 'title');
  assert.equal(facts.tomato, 82);
  assert.equal(facts.starts, '14:00');
  assert.equal(rows.factsOf(s1.row).tomato, undefined);
});

test('errors and plain text add no rows; the same answer is kept once', () => {
  const rows = answerRows();
  rows.remember({ isError: true, text: '{"showing":"s9"}' });
  rows.remember({ isError: false, text: 'Ticket issued' });
  rows.remember(films);
  rows.remember(films);
  assert.equal(rows.valuesOf('showing').length, 2);
});
