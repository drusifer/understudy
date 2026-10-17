// Sprint 5 UND-24 (ARCH §5): the person's inputs - declared in the sketch,
// set with --input, refused before anything starts when out of range.
import test from 'node:test';
import assert from 'node:assert/strict';
import { checkInputs, FULL_WEIGHT, resolveInputs, weightInputs, weightsOf } from '../src/inputs.mjs';
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
  assert.equal(check({ mood: { choose: ['fun'], weight: [0, 1], default: 'fun' } }), 'inputs.mood: must be { choose: [...], default }, { weight: [low, high], default }, { count: [low, high], default } or { switch: true, default: true|false }');
  assert.equal(check({ centre: { weight: [3, 0], default: 1 } }), 'inputs.centre.weight: must be [low, high], two numbers, e.g. [0, 3]');
});

test('a switch is on or off; --input takes on/off/true/false (UND-28 AC3-4)', () => {
  const declared = { together: { switch: true, default: true } };
  assert.deepEqual(resolveInputs(declared, []), { together: true });
  assert.deepEqual(resolveInputs(declared, ['together=off']), { together: false });
  assert.deepEqual(resolveInputs(declared, ['together=true']), { together: true });
  assert.equal(refusal(() => resolveInputs(declared, ['together=maybe'])), 'input "together" must be on or off, got "maybe"');
  const check = (inputs) => refusal(() => checkInputs(inputs, (at, message) => { throw new Error(`${at}: ${message}`); }));
  assert.equal(check(declared), null);
  assert.equal(check({ together: { switch: true, default: 'yes' } }), 'inputs.together.default: must be on or off, got "yes"');
  assert.equal(check({ together: { switch: 'on', default: true } }), 'inputs.together.switch: must be true - a switch is { switch: true, default: true|false }');
});

test('a count is a whole number in its range (UND-34 AC1)', () => {
  const declared = { tickets: { count: [1, 4], default: 2 } };
  assert.deepEqual(resolveInputs(declared, ['tickets=3']), { tickets: 3 });
  assert.equal(refusal(() => resolveInputs(declared, ['tickets=9'])), 'input "tickets" must be a whole number from 1 to 4, got 9');
  assert.equal(refusal(() => resolveInputs(declared, ['tickets=2.5'])), 'input "tickets" must be a whole number from 1 to 4, got 2.5');
  const check = (inputs) => refusal(() => checkInputs(inputs, (at, message) => { throw new Error(`${at}: ${message}`); }));
  assert.equal(check(declared), null);
  assert.equal(check({ tickets: { count: [1, 2.5], default: 2 } }), 'inputs.tickets.count: must be [low, high], two whole numbers, e.g. [1, 4]');
});

test('a weight input is a share of the full weighting: 10 of 0-10 weighs 3, 5 weighs 1.5, 0 turns the factor off (owner)', () => {
  const declared = { centre: { weight: [0, 10], default: 10 }, row: { weight: [1, 3], default: 2 }, mood: { choose: ['fun'], default: 'fun' } };
  assert.equal(FULL_WEIGHT, 3);
  assert.deepEqual(weightsOf(declared, { centre: 10, row: 2, mood: 'fun' }), { centre: 3, row: 1.5 });
  assert.deepEqual(weightsOf(declared, { centre: 5, row: 1 }), { centre: 1.5, row: 0 });
  assert.deepEqual(weightsOf({}, {}), {});
});
