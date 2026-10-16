// Sprint 5 UND-24 (ARCH §5): the person's inputs - declared in the sketch,
// set with --input, refused before anything starts when out of range.
import test from 'node:test';
import assert from 'node:assert/strict';
import { checkInputs, resolveInputs, weightInputs } from '../src/inputs.mjs';
import { UsageError } from '../src/errors.mjs';

const DECLARED = {
  mood: { choose: ['fun', 'serious', 'dramatic', 'romantic'], default: 'fun' },
  row: { weight: [0, 3], default: 2 },
  centre: { weight: [0, 3], default: 3 },
};

const refusal = (run) => {
  try {
    run();
  } catch (error) {
    assert.ok(error instanceof UsageError || error.message.startsWith('inputs'), error.message);
    return error.message;
  }
  return null;
};

test('defaults, then each --input given (UND-24 AC2)', () => {
  assert.deepEqual(resolveInputs(DECLARED, []), { mood: 'fun', row: 2, centre: 3 });
  assert.deepEqual(resolveInputs(DECLARED, ['mood=romantic', 'centre=1']), { mood: 'romantic', row: 2, centre: 1 });
  assert.deepEqual(resolveInputs(DECLARED, ['centre=0.5']).centre, 0.5);
  assert.deepEqual(weightInputs(DECLARED), ['row', 'centre']);
});

test('an unknown input, a choice not listed or a weight out of range refuses the run (UND-24 AC5)', () => {
  assert.equal(refusal(() => resolveInputs(DECLARED, ['volume=11'])), 'no input "volume" in sketch.yaml - it declares mood, row, centre');
  assert.equal(refusal(() => resolveInputs({}, ['mood=fun'])), 'no input "mood" in sketch.yaml - it declares none');
  assert.equal(refusal(() => resolveInputs(DECLARED, ['centre=5'])), 'input "centre" must be between 0 and 3, got 5');
  assert.equal(refusal(() => resolveInputs(DECLARED, ['centre=lots'])), 'input "centre" must be between 0 and 3, got lots');
  assert.equal(refusal(() => resolveInputs(DECLARED, ['mood=sad'])), 'input "mood" must be one of fun, serious, dramatic, romantic, got "sad"');
});

test('check refuses a bad declaration or a default outside its own range (UND-24 AC6)', () => {
  const check = (inputs) => refusal(() => checkInputs(inputs, (at, message) => { throw new Error(`${at}: ${message}`); }));
  assert.equal(check(DECLARED), null);
  assert.equal(check({ centre: { weight: [0, 3], default: 5 } }), 'inputs.centre.default: must be between 0 and 3, got 5');
  assert.equal(check({ mood: { choose: ['fun'], default: 'sad' } }), 'inputs.mood.default: must be one of fun, got "sad"');
  assert.equal(check({ mood: { choose: ['fun'], weight: [0, 1], default: 'fun' } }), 'inputs.mood: must be { choose: [...], default } or { weight: [low, high], default }');
  assert.equal(check({ centre: { weight: [3, 0], default: 1 } }), 'inputs.centre.weight: must be [low, high], two numbers, e.g. [0, 3]');
});
