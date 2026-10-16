// Sprint 4 UND-15 (ARCH §4 "Pause gate", ADR-0016): the gate before each
// move - pause holds it, step lets one move through, resume opens it,
// Ctrl-C lets a paused run go to stop; paused time is kept.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createGate, OPEN_GATE } from '../src/watch/gate.mjs';

const settled = async (promise) => {
  const marker = Symbol('pending');
  const value = await Promise.race([promise, new Promise((resolve) => setTimeout(() => resolve(marker), 20))]);
  return value === marker ? 'pending' : value;
};

test('running: every move goes at once; paused: it waits until step or resume', async () => {
  const gate = createGate();
  assert.equal(await gate.beforeMove(), 'go');
  assert.equal(gate.pause(), true);
  const waiting = gate.beforeMove();
  assert.equal(await settled(waiting), 'pending');
  assert.equal(gate.step(), true);
  assert.equal(await waiting, 'go');
  assert.equal(await settled(gate.beforeMove()), 'pending', 'after one step it is paused again');
  gate.resume();
  assert.equal(await gate.beforeMove(), 'go');
});

test('a step pressed before the run reaches its move lets that one move through', async () => {
  const gate = createGate({ isPaused: true });
  gate.step();
  assert.equal(await gate.beforeMove(), 'go');
  assert.equal(await settled(gate.beforeMove()), 'pending');
});

test('only the action that applies is taken; none after the end', () => {
  const gate = createGate();
  assert.equal(gate.step(), false);
  assert.equal(gate.resume(), false);
  assert.equal(gate.pause(), true);
  assert.equal(gate.pause(), false);
  gate.end();
  assert.equal(gate.resume(), false);
});

test('Ctrl-C lets a paused run go to stop; a running one is left to stop as usual', async () => {
  const running = createGate();
  running.stop();
  assert.equal(await running.beforeMove(), 'go');
  const paused = createGate({ isPaused: true });
  const waiting = paused.beforeMove();
  paused.stop();
  assert.equal(await waiting, 'stop');
});

test('paused time is kept, so idle limits can leave it out', () => {
  let now = 1000;
  const gate = createGate({ clock: () => now });
  gate.pause();
  now += 15_000;
  assert.equal(gate.pausedMs(), 15_000);
  gate.resume();
  now += 5000;
  assert.equal(gate.pausedMs(), 15_000);
});

test('every change is told, with whether the run is waiting at the gate', async () => {
  const told = [];
  const gate = createGate({ onChange: (state) => { told.push(state); } });
  gate.pause();
  const waiting = gate.beforeMove();
  gate.resume();
  await waiting;
  assert.deepEqual(told, [{ paused: true, waiting: false }, { paused: true, waiting: true }, { paused: false, waiting: false }]);
  assert.equal(await OPEN_GATE.beforeMove(), 'go');
});
