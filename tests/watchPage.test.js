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
    retry: 'first answered "v9" (not on offer), asked again', args: 'film=f1, count=2', answer: { text: '{"hold":"h1"}', isBad: false }, decided: [],
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
  assert.deepEqual(endingOf(stalled), { text: 'stalled: nothing to do for 10 s after step 3', isBad: true }, 'the outcome is said once (DEF-12)');
  const stopped = newModel();
  apply(stopped, { event: 'ended', outcome: 'interrupted', message: 'stopped by Ctrl-C while paused, after 0 steps' });
  apply(stopped, { final: true, outcome: 'interrupted', steps: 0, state: 'choosing' });
  assert.equal(endingOf(stopped).text, 'interrupted: stopped by Ctrl-C while paused, after 0 steps');
  assert.equal(endingOf(newModel()), null);
});

import { controlsOf } from '../src/watch/page.mjs';

test('controls: Pause while running, Step and Resume while paused, none after the end or in a replay', () => {
  const model = apply(newModel(), { event: 'start', sketch: 's', plays: 'p', turn: TURN });
  assert.deepEqual(controlsOf(model), { pause: true, step: false, resume: false });
  apply(model, { event: 'control', paused: true, waiting: true, before_step: 2 });
  assert.deepEqual(controlsOf(model), { pause: false, step: true, resume: true });
  apply(model, { final: true, outcome: 'done', steps: 2, state: 'finished' });
  assert.deepEqual(controlsOf(model), { pause: false, step: false, resume: false });
  const replay = apply(apply(newModel(), { event: 'hello', mode: 'replay' }), { event: 'start', sketch: 's', plays: 'p', turn: TURN });
  assert.deepEqual(controlsOf(replay), { pause: false, step: false, resume: false });
});

test('a decided argument shows its score table, what was removed and what is held (UND-22 AC5)', () => {
  const decision = decisionOf({ step: 3, options: [], move: 'tool:boxoffice/pick_seats', decided: [{
    argument: 'boxoffice/pick_seats.seat',
    table: [{ value: 's4-F5', factors: { row: 0.444, centre: 0.599 }, total: 0.266 }, { value: 's4-F4', factors: { row: 0.444, centre: 0.148 }, total: 0.066 }],
    removed: [{ value: 's4-E1', why: 'centre 0 scores 0' }, { value: 's4-A2', why: 'row A not in [E, F, D]' }],
    held: [],
  }] });
  assert.deepEqual(decision.decided, [{
    argument: 'boxoffice/pick_seats.seat',
    columns: ['value', 'row', 'centre', 'total'],
    rows: [['s4-F5', '0.444', '0.599', '0.266'], ['s4-F4', '0.444', '0.148', '0.066']],
    removed: 'removed 2: s4-E1 (centre 0 scores 0), s4-A2 (row A not in [E, F, D])',
    held: null,
  }]);
  assert.deepEqual(decisionOf({ step: 1, options: [], move: 'x' }).decided, []);
});
