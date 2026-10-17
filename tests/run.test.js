// Sprint 1 UND-1 AC2-5 (ARCH §4, §6): the run loop, proven with a fake
// target and a Jev double - no process, no browser, no network. Every
// outcome writes a final line, and the target is closed however it ends.
import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { appendFileSync, cpSync, mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runSketch, DEFAULT_STEPS } from '../src/run.mjs';
import { RunError } from '../src/errors.mjs';
import { shown } from '../src/sketch.mjs';

const GOOD = fileURLToPath(new URL('fixtures/sketches/good', import.meta.url));

/**
 * The fixture's app, in memory: on `menu` until a move is sent; `order`
 * ends it (`done`), `cancel` leaves it on the menu.
 */
function fakeApp({ screen = 'menu', exitAfterMove = null, staleLooks = 0, afterMove = null, answer } = {}) {
  const app = { screen, seq: 0, acted: [], closed: false, exit: null, stale: null };
  app.target = {
    describe: () => 'node app.mjs',
    async view() {
      if (app.stale && app.stale.looks > 0) {
        app.stale.looks -= 1;
        return app.stale.view;
      }
      return { screen: app.screen, seq: app.seq };
    },
    talk: async () => [],
    say: async () => {},
    act: async (action) => {
      // `staleLooks`: the app is still busy (not yet showing the move's
      // result) for that many looks - the seat's own after-step look is one.
      app.stale = { looks: staleLooks, view: { screen: 'brewing', seq: app.seq } };
      app.acted.push(action);
      app.seq += 1;
      if (action.input === 'order') app.screen = 'done';
      if (afterMove) app.screen = afterMove;
      if (exitAfterMove !== null) app.exit = { code: exitAfterMove };
      return answer;
    },
    exited: () => app.exit,
    close: async () => { app.closed = true; },
  };
  return app;
}

function judgeAnswering(...choices) {
  const asked = [];
  return {
    asked,
    async systemOne(request) {
      asked.push(request);
      const choice = choices[Math.min(asked.length - 1, choices.length - 1)];
      if (choice instanceof Error) throw choice;
      return { answers: { next: { type: 'choice', choice, confidence: 0.75 } } };
    },
  };
}

function streams() {
  const out = { stdout: '', stderr: '' };
  return { out, stdout: { write: (text) => { out.stdout += text; } }, stderr: { write: (text) => { out.stderr += text; } } };
}

async function play({ sketch = GOOD, app = fakeApp(), judge = judgeAnswering('order'), steps, firstMoveMs = 2000, stallMs = 2000, signals = new EventEmitter() } = {}) { // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`, an EventEmitter
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-runs-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  const io = streams();
  let error = null;
  try {
    await runSketch(sketch, {
      steps, stdout: io.stdout, stderr: io.stderr, environment: { TYPESAFE_API_KEY: 'test' },
      makeJudge: () => judge, makeTarget: async () => app.target, logRoot, firstMoveMs, stallMs, pollMs: 1, signals,
    });
  } catch (error_) {
    error = error_;
  }
  const folder = path.join(logRoot, 'fixture-good');
  const [file] = readdirSync(folder);
  const all = io.out.stdout.trim().split('\n').map((line) => JSON.parse(line));
  const lines = all.filter((line) => !line.event);
  return { app, judge, error, lines, events: all.filter((line) => line.event), final: lines.at(-1), log: readFileSync(path.join(folder, file), 'utf8'), file: path.join(folder, file), ...io.out };
}

test('a run plays to the end state: one JSON line per step, a final line, the same lines in the log', async () => {
  const run = await play();
  assert.equal(run.error, null);
  assert.deepEqual(run.app.acted, [{ input: 'order' }]);
  assert.equal(run.lines.length, 2);
  const [step] = run.lines;
  assert.equal(step.step, 1);
  assert.equal(step.phase, 'menu');
  assert.equal(step.state, 'waiting', 'the machine state after the step');
  assert.deepEqual(step.options, ['order', 'cancel']);
  assert.equal(step.picked, 'order');
  assert.equal(step.confidence, 0.75);
  assert.deepEqual(run.final, { final: true, outcome: 'done', steps: 1, state: 'finished' });
  assert.equal(run.log, run.stdout, 'the log holds exactly the stdout lines');
  assert.equal(run.app.closed, true);
});

test('the sketch\'s steps: sets the cap; --steps wins over it; neither means 50', async () => {
  const directory = mkdtempSync(path.join(tmpdir(), 'understudy-steps-'));
  test.after(() => rmSync(directory, { recursive: true, force: true }));
  cpSync(GOOD, directory, { recursive: true });
  appendFileSync(path.join(directory, 'sketch.yaml'), 'steps: 2\n');
  const fromSketch = await play({ sketch: directory, judge: judgeAnswering('cancel') });
  assert.deepEqual(fromSketch.final, { final: true, outcome: 'step-cap', steps: 2, state: 'choosing' });
  const fromFlag = await play({ sketch: directory, judge: judgeAnswering('cancel'), steps: 4 });
  assert.equal(fromFlag.final.steps, 4);
  const byDefault = await play({ judge: judgeAnswering('cancel', 'cancel', 'order') });
  assert.equal(byDefault.final.outcome, 'done', 'the fixture has no steps:, so the default cap of 50 applies');
  assert.equal(DEFAULT_STEPS, 50);
});

test('stderr starts with what is played and where the log goes, then one readable line per step', async () => {
  const run = await play();
  const [first, second] = run.stderr.trim().split('\n', 2);
  assert.equal(first, `understudy: playing fixture-good (node app.mjs) - log ${shown(run.file)}`);
  assert.equal(second, 'understudy: step 1 menu -> order (0.75)');
});

test('the step cap stops a run that never ends, naming the cap and the last state', async () => {
  const run = await play({ judge: judgeAnswering('cancel'), steps: 3 });
  assert.ok(run.error instanceof RunError);
  assert.equal(run.error.message, 'stopped after 3 steps without reaching the end state (last state: choosing)');
  assert.equal(run.app.acted.length, 3);
  assert.deepEqual(run.final, { final: true, outcome: 'step-cap', steps: 3, state: 'choosing' });
  assert.equal(run.app.closed, true);
});

test('two off-list answers stop the run; nothing reaches the app', async () => {
  const run = await play({ judge: judgeAnswering('refund', 'teleport') });
  assert.ok(run.error instanceof RunError);
  assert.match(run.error.message, /^step 1: in phase "menu" Jev answered off the list twice \("refund", then "teleport"\)/);
  assert.deepEqual(run.app.acted, []);
  assert.equal(run.final.outcome, 'off-list');
  assert.equal(run.app.closed, true);
});

test('one off-list answer is logged and the second, offered answer is played', async () => {
  const run = await play({ judge: judgeAnswering('refund', 'order') });
  assert.equal(run.error, null);
  assert.equal(run.lines[0].offList, true);
  assert.equal(run.lines[0].answer, 'refund');
  assert.match(run.stderr, /step 1 menu -> order \(0\.75\) - off-list "refund" first/);
});

test('an app that exits before the end state stops the run, naming the program and its exit code', async () => {
  const run = await play({ app: fakeApp({ exitAfterMove: 3 }), judge: judgeAnswering('cancel') });
  assert.ok(run.error instanceof RunError);
  assert.equal(run.error.message, 'node app.mjs exited with code 3 before the end state');
  assert.equal(run.final.outcome, 'app-exited');
  assert.equal(run.app.closed, true);
});

test('an app that prints its end and exits between two looks has finished, not failed', async () => {
  const run = await play({ app: fakeApp({ exitAfterMove: 0, staleLooks: 2 }), judge: judgeAnswering('order') });
  assert.equal(run.error, null);
  assert.equal(run.final.outcome, 'done');
});

test('an app that never offers a first move stops the run, naming it and what was seen', async () => {
  const run = await play({ app: fakeApp({ screen: 'loading' }), firstMoveMs: 30 });
  assert.ok(run.error instanceof RunError);
  assert.equal(run.error.message, 'no first move from node app.mjs within 0.03 s - last view: {"screen":"loading","seq":0}');
  assert.equal(run.final.outcome, 'no-first-move');
  assert.equal(run.app.closed, true);
});

test('a failed Jev request stops the run with the SDK\'s message', async () => {
  const run = await play({ judge: judgeAnswering(new Error('401 Unauthorized')) });
  assert.ok(run.error instanceof RunError);
  assert.equal(run.error.message, 'step 1: Jev request failed: 401 Unauthorized');
  assert.equal(run.final.outcome, 'jev-error');
  assert.equal(run.app.closed, true);
});

test('Ctrl-C stops at the next safe state and says so', async () => {
  const signals = new EventEmitter(); // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`
  const judge = judgeAnswering('cancel');
  const original = judge.systemOne.bind(judge);
  judge.systemOne = async (request) => {
    signals.emit('SIGINT');
    return original(request);
  };
  const run = await play({ judge, signals });
  assert.ok(run.error instanceof RunError);
  assert.match(run.error.message, /^stopped by Ctrl-C after 1 step/);
  assert.deepEqual(run.final, { final: true, outcome: 'interrupted', steps: 1, state: 'left' });
  assert.equal(signals.listenerCount('SIGINT'), 0, 'its handler is removed');
  assert.equal(run.app.closed, true);
});

test('a cap of one step reads as one step', async () => {
  const run = await play({ judge: judgeAnswering('cancel'), steps: 1 });
  assert.equal(run.error.message, 'stopped after 1 step without reaching the end state (last state: choosing)');
});

test('a run that stops being offered anything after it started is stalled, with a hint about ending it', async () => {
  const run = await play({ app: fakeApp({ afterMove: 'brewing' }), judge: judgeAnswering('cancel'), stallMs: 30 });
  assert.ok(run.error instanceof RunError);
  assert.equal(run.error.message,
    'stalled: nothing to do for 0.03 s after step 1 (last state: waiting) - the app showed: {"screen":"brewing","seq":1}'
    + ' - if this is where the sketch should end, add a showing guard (docs/SKETCHES.md)');
  assert.deepEqual(run.final, { final: true, outcome: 'stalled', steps: 1, state: 'waiting' });
  assert.equal(run.app.closed, true);
});

test('what the app answered a move with is kept in that step\'s log line', async () => {
  const run = await play({ app: fakeApp({ answer: { status: 402 } }) });
  assert.deepEqual(run.lines[0].response, { status: 402 });
});

test('the log tells the whole story: a start line, then state lines around each step (UND-13)', async () => {
  const run = await play();
  const [start, ...changes] = run.events;
  assert.deepEqual(Object.keys(start), ['event', 'sketch', 'plays', 'limits', 'turn', 'at']);
  assert.deepEqual(Object.keys(start.limits), ['steps', 'first_move_ms', 'stall_ms'], 'the limits a gauge shows (UND-42)');
  assert.equal(start.event, 'start');
  assert.equal(start.sketch, 'fixture-good');
  assert.equal(start.plays, 'node app.mjs');
  assert.equal(start.turn.initial, 'waiting');
  assert.deepEqual(changes.map(({ from, to, on }) => `${from} -${on}-> ${to}`), [
    'waiting -OBSERVE-> looking',
    'looking -done: phase is menu-> choosing',
    'choosing -STEP-> stepping',
    'stepping -done-> waiting',
    'waiting -OBSERVE-> looking',
    'looking -done: phase is done-> finished',
  ]);
  const order = run.stdout.trim().split('\n').map((line) => JSON.parse(line)).map((line) => line.event ?? (line.final ? 'final' : 'step'));
  assert.deepEqual(order, ['start', 'state', 'state', 'state', 'state', 'step', 'state', 'state', 'final']);
});

test('step and final lines keep exactly their sprint 3 fields', async () => {
  const run = await play();
  assert.deepEqual(Object.keys(run.lines[0]), ['step', 'at', 'phase', 'options', 'picked', 'move', 'confidence', 'checks', 'asked', 'state']);
  assert.deepEqual(Object.keys(run.final), ['final', 'outcome', 'steps', 'state']);
});

test('looks that change nothing are counted, not listed: the next state line carries idle_looks', async () => {
  // The app shows `brewing` (not a move phase) for a while, then the menu.
  const app = fakeApp({ screen: 'brewing' });
  setTimeout(() => { app.screen = 'menu'; }, 60);
  const run = await play({ app });
  const changes = run.events.filter((line) => line.event === 'state');
  const idle = changes.find((line) => line.idle_looks !== undefined);
  assert.ok(idle.idle_looks >= 3, `idle looks folded: ${idle.idle_looks}`);
  assert.deepEqual([idle.from, idle.to], ['waiting', 'looking']);
  assert.equal(changes.filter((line) => line.from === 'looking' && line.to === 'waiting').length, 0, 'no idle look is listed');
});
