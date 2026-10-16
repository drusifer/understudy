// Sprint 4 (ARCH §5): the one way a transition is named, in the log and on
// the diagram.
import test from 'node:test';
import assert from 'node:assert/strict';
import { guardLabel, transitionLabel } from '../src/watch/turnGraph.mjs';

test('guards read as words: type, then each parameter as name value', () => {
  assert.equal(guardLabel({ type: 'phase', params: { is: 'asking' } }), 'phase is asking');
  assert.equal(guardLabel({ type: 'showing', params: { text: 'Ticket issued' } }), 'showing text Ticket issued');
  assert.equal(guardLabel({ type: 'counted', params: { field: 'tries', at_least: 3 } }), 'counted field tries at_least 3');
  assert.equal(guardLabel('sold_out'), 'sold_out');
  assert.equal(guardLabel(), '');
});

test('transitions: the event (done for a finished invoke, always for eventless), then the guard', () => {
  assert.equal(transitionLabel('OBSERVE'), 'OBSERVE');
  assert.equal(transitionLabel('STEP'), 'STEP');
  assert.equal(transitionLabel('xstate.done.actor.0.(machine).looking', { type: 'phase', params: { is: 'asking' } }), 'done: phase is asking');
  assert.equal(transitionLabel('xstate.done.actor.0.(machine).acting'), 'done');
  assert.equal(transitionLabel('', 'asked_to_leave'), 'always: asked_to_leave');
});
