// Sprint 3 UND-10 AC4 (ARCH §4 "Candidate values", ADR-0013): Jev chooses
// an argument from a finite list - the sketch's values, what the schema
// allows, or what the last result said - and never writes one.
import test from 'node:test';
import assert from 'node:assert/strict';
import { candidatesFor, argumentQuestions, resultValues, MAX_CANDIDATES } from '../src/fill.mjs';

const FILMS = { text: '[{"film":"f1","title":"Up","price":9},{"film":"f2","title":"Orbit","price":11}]', isError: false };

test('the sketch\'s listed values win over everything else', () => {
  assert.deepEqual(candidatesFor({ type: 'integer', minimum: 1, maximum: 4 }, { listed: [2], last: FILMS }), [2]);
});

test('the schema: every enum value, true/false, each whole number of a narrow range', () => {
  assert.deepEqual(candidatesFor({ type: 'string', enum: ['card', 'cash'] }), ['card', 'cash']);
  assert.deepEqual(candidatesFor({ type: 'boolean' }), [true, false]);
  assert.deepEqual(candidatesFor({ type: 'integer', minimum: 1, maximum: 4 }), [1, 2, 3, 4]);
  assert.equal(candidatesFor({ type: 'integer', minimum: 0, maximum: 19 }).length, 20);
});

test('a wide range, or a bare string, takes values of its type from the last result', () => {
  assert.deepEqual(candidatesFor({ type: 'integer', minimum: 0, maximum: 1000 }, { last: FILMS }), [9, 11]);
  assert.deepEqual(candidatesFor({ type: 'string' }, { last: FILMS }), ['f1', 'Up', 'f2', 'Orbit']);
  assert.deepEqual(candidatesFor({ type: 'number' }, { last: { text: '', structured: { total: 18.5 }, isError: false } }), [18.5]);
});

test('nothing to choose from: no result, a plain-text result, or an error result', () => {
  assert.deepEqual(candidatesFor({ type: 'string' }), []);
  assert.deepEqual(candidatesFor({ type: 'string' }, { last: { text: 'Ticket issued', isError: false } }), []);
  assert.deepEqual(resultValues({ text: '["h1"]', isError: true }), []);
});

test('result values are deduplicated and capped', () => {
  const many = { text: JSON.stringify(Array.from({ length: 50 }, (_, index) => `id${index % 30}`)), isError: false };
  const values = candidatesFor({ type: 'string' }, { last: many });
  assert.equal(values.length, MAX_CANDIDATES);
  assert.equal(new Set(values).size, values.length);
});

test('one Choice per open argument; answers read back into values; an unknown answer is off the list', () => {
  const open = [
    { name: 'film', schema: { type: 'string', description: 'the film id' }, candidates: ['f1', 'f2'] },
    { name: 'count', schema: { type: 'integer' }, candidates: [1, 2] },
  ];
  const { questions, read } = argumentQuestions({ instructions: 'Buy tickets.', tool: 'pick_seats', open });
  assert.deepEqual(Object.keys(questions), ['argument_film', 'argument_count']);
  assert.equal(questions.argument_film.instructions, 'Buy tickets. You are calling `pick_seats`: choose the value of its argument `film` (the film id).');
  assert.deepEqual(questions.argument_count.criteria, { v1: '`1`', v2: '`2`' });
  assert.deepEqual(read({ argument_film: { choice: 'v2' }, argument_count: { choice: 'v1' } }), { filled: { film: 'f2', count: 1 } });
  assert.deepEqual(read({ argument_film: { choice: 'v3' }, argument_count: { choice: 'v1' } }), { offList: { name: 'film', answer: 'v3' } });
  assert.deepEqual(read({}), { offList: { name: 'film', answer: null } });
});
