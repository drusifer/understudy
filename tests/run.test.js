// Sprint 1 UND-1 AC2-5 (ARCH §4, §6): the run loop, proven with a fake
// target and a Jev double - no process, no browser, no network. Every
// outcome writes a final line, and the target is closed however it ends.
import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runPart } from '../src/run.mjs';
import { RunError } from '../src/errors.mjs';
import { shown } from '../src/part.mjs';

const GOOD = fileURLToPath(new URL('fixtures/parts/good', import.meta.url));

/**
 * The fixture's app, in memory: on `menu` until a move is sent; `order`
 * ends it (`done`), `cancel` leaves it on the menu.
 */
function fakeApp({ screen = 'menu', exitAfterMove = null, staleLooks = 0 } = {}) {
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
      if (exitAfterMove !== null) app.exit = { code: exitAfterMove };
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

async function play({ app = fakeApp(), judge = judgeAnswering('order'), steps = 50, firstMoveMs = 2000, signals = new EventEmitter() } = {}) { // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`, an EventEmitter
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-runs-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  const io = streams();
  let error = null;
  try {
    await runPart(GOOD, {
      steps, stdout: io.stdout, stderr: io.stderr, environment: { TYPESAFE_API_KEY: 'test' },
      makeJudge: () => judge, makeTarget: async () => app.target, logRoot, firstMoveMs, pollMs: 1, signals,
    });
  } catch (error_) {
    error = error_;
  }
  const folder = path.join(logRoot, 'fixture-good');
  const [file] = readdirSync(folder);
  const lines = io.out.stdout.trim().split('\n').map((line) => JSON.parse(line));
  return { app, judge, error, lines, final: lines.at(-1), log: readFileSync(path.join(folder, file), 'utf8'), file: path.join(folder, file), ...io.out };
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
