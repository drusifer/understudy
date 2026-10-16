// Sprint 4 UND-14 (ARCH §3): the watch page's model and the words it
// shows - tested without a browser. (The page itself is driven in
// Chromium during UAT; `make test` launches no browser, ADR-0006.)
import test from 'node:test';
import assert from 'node:assert/strict';
import { newModel, apply, decisionOf, answerOf, endingOf } from '../src/watch/page.mjs';

const TURN = { initial: 'waiting', states: { waiting: { on: { OBSERVE: 'looking' } }, looking: { invoke: { src: 'look', onDone: 'waiting' } } } };

test('a start line draws the turn and puts the run in its initial state; state lines move it', () => {
  const model = newModel();
  apply(model, { event: 'start', sketch: 'coffee-cli', plays: 'node app.mjs', turn: TURN });
  assert.equal(model.sketch, 'coffee-cli');
  assert.equal(model.current, 'waiting');
  assert.deepEqual(model.drawing.nodes.map((node) => node.id), ['waiting', 'looking']);
  apply(model, { event: 'state', from: 'waiting', to: 'looking', on: 'OBSERVE' });
  assert.equal(model.current, 'looking');
  assert.deepEqual(model.taken, { event: 'state', from: 'waiting', to: 'looking', on: 'OBSERVE' });
});

test('a step becomes a decision: options, pick with confidence, off-list retry, arguments, answer', () => {
  const decision = decisionOf({
    step: 2, phase: 'asking', options: ['tool:list_films', 'tool:pick_seats'], move: 'tool:pick_seats', confidence: 1, offList: true, answer: 'v9',
    response: { call: { tool: 'pick_seats', arguments: { film: 'f1', count: 2 } }, isError: false, text: '{"hold":"h1"}\nmore' },
  });
  assert.deepEqual(decision, {
    step: 2, phase: 'asking', options: ['tool:list_films', 'tool:pick_seats'], move: 'tool:pick_seats', picked: 'tool:pick_seats (1)',
    retry: 'first answered "v9" (not on offer), asked again', args: 'film=f1, count=2', answer: { text: '{"hold":"h1"}', isBad: false },
  });
  assert.equal(decisionOf({ step: 1, options: [], move: 'size:medium', confidence: 0.95 }).picked, 'size:medium (0.95)');
});

test('the app\'s answer in one line: an HTTP status, or a tool result (an error says so)', () => {
  assert.deepEqual(answerOf({ status: 402 }), { text: 'status 402', isBad: true });
  assert.deepEqual(answerOf({ status: 200 }), { text: 'status 200', isBad: false });
  assert.deepEqual(answerOf({ call: { tool: 'pay' }, isError: true, text: 'This box office takes cards only.' }), { text: 'error: This box office takes cards only.', isBad: true });
  assert.equal(answerOf({ call: { tool: 'x' }, isError: false, text: 'y'.repeat(200) }).text.length, 123);
  assert.equal(answerOf(), null);
});

test('how it ended: done after N steps, or the outcome and why', () => {
  const done = apply(newModel(), { final: true, outcome: 'done', steps: 3, state: 'finished' });
  assert.deepEqual(endingOf(done), { text: 'done after 3 steps', isBad: false });
  const stalled = newModel();
  apply(stalled, { event: 'ended', outcome: 'stalled', message: 'stalled: nothing to do for 10 s after step 3' });
  apply(stalled, { final: true, outcome: 'stalled', steps: 3, state: 'waiting' });
  assert.deepEqual(endingOf(stalled), { text: 'stalled: stalled: nothing to do for 10 s after step 3', isBad: true });
  assert.equal(endingOf(newModel()), null);
});
