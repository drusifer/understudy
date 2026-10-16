// Sprint 4 UND-16 (ARCH §4 "Replay"): a finished run's log is read and
// checked before it is replayed - a start line first, JSON throughout - and
// the page steps through it frame by frame.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { readLog } from '../src/watch/replay.mjs';
import { framesOf, frameOfStep, modelAt, endingOf } from '../src/watch/page.mjs';
import { shown } from '../src/sketch.mjs';
import { UsageError } from '../src/errors.mjs';

const TURN = { initial: 'waiting', states: { waiting: { on: { OBSERVE: 'looking' } }, looking: { invoke: { src: 'look', onDone: 'waiting' } } } };
const START = { event: 'start', sketch: 'coffee-cli', plays: 'node app.mjs', turn: TURN };
const step = (number) => ({ step: number, phase: 'asking', options: ['a', 'b'], picked: 'a', move: 'a', confidence: 0.9, state: 'waiting' });
const state = (from, to) => ({ event: 'state', from, to, on: 'OBSERVE' });
const LOG = [START, state('waiting', 'looking'), step(1), state('looking', 'waiting'), step(2), { final: true, outcome: 'done', steps: 2, state: 'waiting' }];

function logFile(lines) {
  const directory = mkdtempSync(path.join(tmpdir(), 'understudy-replay-'));
  test.after(() => rmSync(directory, { recursive: true, force: true }));
  const file = path.join(directory, 'run.jsonl');
  writeFileSync(file, lines.map((line) => (typeof line === 'string' ? line : JSON.stringify(line))).join('\n') + '\n');
  return file;
}

function refusal(file) {
  try {
    readLog(file);
  } catch (error) {
    assert.ok(error instanceof UsageError);
    return error.message;
  }
  assert.fail('was not refused');
}

test('a run log is read whole', () => {
  assert.deepEqual(readLog(logFile(LOG)), LOG);
});

test('a log from before sprint 4, a file that is not a log, or no file at all, is refused naming why', () => {
  const old = logFile([step(1), { final: true, outcome: 'done', steps: 1, state: 'finished' }]);
  assert.equal(refusal(old), `${shown(old)}: no start line - replay needs a log written by understudy run (sprint 4 or later)`);
  const notLog = logFile([START, 'hello world']);
  assert.equal(refusal(notLog), `${shown(notLog)}: line 2 is not JSON - this is not a run log`);
  assert.match(refusal('build/runs/nope.jsonl'), /^build\/runs\/nope\.jsonl: no such log/);
});

test('frames: one per line - start, each state change, each step - so a replay walks the statechart', () => {
  const frames = framesOf(LOG);
  assert.deepEqual(frames, [0, 1, 2, 3, 4, 5]);
  assert.equal(modelAt(LOG, frames, 1).current, 'looking', 'a state change is its own frame');
  const atStep1 = modelAt(LOG, frames, frameOfStep(LOG, frames, 1));
  assert.equal(atStep1.steps.length, 1);
  assert.equal(endingOf(atStep1), null, 'not ended yet at step 1');
  assert.deepEqual(endingOf(modelAt(LOG, frames, frames.length - 1)), { text: 'done after 2 steps', isBad: false });
});

test('an ended line shares the final line\'s frame', () => {
  const failed = [START, step(1), { event: 'ended', outcome: 'stalled', message: 'stalled: x' }, { final: true, outcome: 'stalled', steps: 1, state: 'waiting' }];
  const frames = framesOf(failed);
  assert.deepEqual(frames, [0, 1, 3]);
  assert.deepEqual(endingOf(modelAt(failed, frames, 2)), { text: 'stalled: x', isBad: true });
});

test('a log cut short (no final line) replays as far as it goes, and says so at the end', () => {
  const cut = LOG.slice(0, 4);
  const frames = framesOf(cut);
  assert.deepEqual(endingOf(modelAt(cut, frames, frames.length - 2)), null);
  assert.deepEqual(endingOf(modelAt(cut, frames, frames.length - 1)), { text: 'log ends without a final line (the run was killed?)', isBad: true });
});
