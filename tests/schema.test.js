// Sprint 10 UND-37 (ADR-0031): schema/sketch.schema.json - the editor's
// structural check of sketch.yaml - accepts every example, rejects the common
// mistakes at their path, and knows exactly the keys and kinds check knows.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import Ajv from 'ajv';
import YAML from 'yaml';
import { KEYS, QUESTION_TYPES, TARGET_FIELDS } from '../src/sketch.mjs';
import { KINDS } from '../src/inputs.mjs';

const schema = JSON.parse(readFileSync('schema/sketch.schema.json', 'utf8'));
const validate = new Ajv({ allErrors: true, strict: false }).compile(schema);
const examples = readdirSync('examples').map((name) => path.join('examples', name, 'sketch.yaml')).filter((file) => existsSync(file));
const sorted = (list) => list.toSorted((a, b) => a.localeCompare(b));
const evening = () => YAML.parse(readFileSync('examples/evening/sketch.yaml', 'utf8'));

// Where the schema says a sketch is wrong: the paths of its complaints.
function complaints(sketch) {
  return validate(sketch) ? [] : validate.errors.map((error) => error.instancePath);
}

test('every example passes the schema (UND-37 AC3)', () => {
  assert.ok(examples.length >= 6);
  for (const file of examples) {
    const sketch = YAML.parse(readFileSync(file, 'utf8'));
    assert.deepEqual(complaints(sketch), [], file);
  }
});

test('the common mistakes are flagged at their path (UND-37 AC3)', () => {
  const at = (change) => {
    const sketch = evening();
    change(sketch);
    return complaints(sketch);
  };
  assert.ok(at((sketch) => { sketch.tunr = sketch.turn; }).includes(''), 'an unknown top-level key');
  assert.ok(at((sketch) => { sketch.target = { kind: 'ftp', command: 'x' }; }).includes('/target/kind'), 'an unknown target kind');
  assert.ok(at((sketch) => { sketch.target = { kind: 'process', command: 'node', page: 'index.html' }; }).includes('/target'), 'a field of another kind');
  assert.ok(at((sketch) => { sketch.inputs.centre = { weight: [0, 10], switch: true, default: 3 }; }).includes('/inputs/centre'), 'an input with two kinds');
  assert.ok(at((sketch) => { sketch.questions.next.type = 'essay'; }).includes('/questions/next/type'), 'an unknown question type');
  assert.ok(at((sketch) => { sketch.turn.states.acting.invok = sketch.turn.states.acting.invoke; }).includes('/turn/states/acting'), 'a misspelt state key');
  assert.ok(at((sketch) => { sketch.decide['boxoffice/pick_seats.seat'].scores.row.curve = 2; }).includes('/decide/boxoffice~1pick_seats.seat/scores/row'), 'an unknown score word');
});

test('the schema knows exactly what check knows (UND-37 AC4)', () => {
  assert.deepEqual(sorted(Object.keys(schema.properties)), sorted(KEYS), 'top-level keys');
  const kinds = schema.definitions.target.oneOf.map((branch) => branch.properties.kind.const);
  assert.deepEqual(sorted(kinds), sorted(Object.keys(TARGET_FIELDS)), 'target kinds');
  for (const branch of schema.definitions.target.oneOf) {
    const kind = branch.properties.kind.const;
    const fields = Object.keys(branch.properties).filter((field) => field !== 'kind');
    assert.deepEqual(sorted(fields), sorted(TARGET_FIELDS[kind]), `${kind} fields`);
  }
  const inputKinds = schema.definitions.input.oneOf.map((branch) => branch.required[0]);
  assert.deepEqual(sorted(inputKinds), sorted(KINDS), 'input kinds');
  assert.deepEqual(sorted(schema.definitions.question.properties.type.enum), sorted(QUESTION_TYPES), 'question types');
});
