// Sprint 4 UND-14/15/16 in a real browser (`make test-browser`): the watch
// page driven in headless Chromium against real runs of the examples, with
// a Jev double - no key, no cost. These replace the sprint 4 UAT scratch
// scripts. `make test` stays browser-free (ADR-0006).
import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runSketch } from '../../src/run.mjs';
import { launchHeadless } from '../../src/targets/page.mjs';
import { startWatch, logSource } from '../../src/watch/server.mjs';
import { readLog } from '../../src/watch/replay.mjs';

const GOOD = fileURLToPath(new URL('../fixtures/sketches/good', import.meta.url));
const browser = await launchHeadless();
test.after(() => browser.close());

/**
 * Jev at the box office: the moves in order; each argument from `values`
 * (a list is used in order, one per call).
 */
function judgeAtTheBoxOffice(moves, values) {
  let move = 0;
  const used = {};
  return {
    async systemOne({ questions }) {
      const answers = {};
      for (const [key, question] of Object.entries(questions)) {
        if (!key.startsWith('argument_')) {
          answers[key] = { type: 'choice', choice: moves[Math.min(move++, moves.length - 1)], confidence: 0.9 };
          continue;
        }
        const name = key.slice('argument_'.length);
        const wanted = [values[name]].flat();
        const value = wanted[Math.min(used[name] ?? 0, wanted.length - 1)];
        used[name] = (used[name] ?? 0) + 1;
        const choice = Object.entries(question.criteria).find(([, text]) => text === `\`${JSON.stringify(value)}\``)?.[0] ?? 'v99';
        answers[key] = { type: 'choice', choice, confidence: 0.9 };
      }
      return { answers };
    },
  };
}

const BOX_OFFICE = () => judgeAtTheBoxOffice(['tool:list_films', 'tool:pick_seats', 'tool:pay'], { film: 'f2', count: 2, hold: 'h1', method: 'card' });

/**
 * A watched run, started in the background: resolves its page address as
 * soon as it is printed; `finished` settles when the run ends.
 */
async function watchedRun(sketch, { judge, paused = false, signals = new EventEmitter(), ...options }) { // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-browser-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  const { promise: address, resolve: found } = Promise.withResolvers();
  const finished = (async () => {
    try {
      await runSketch(sketch, {
        stdout: { write: () => {} },
        stderr: { write: (text) => { const url = /watch at (\S+)/.exec(text)?.[1]; if (url) found(url); } },
        makeJudge: () => judge, logRoot, pollMs: 20, steps: 20, watch: { port: 0, paused }, signals, ...options,
      });
      return null;
    } catch (error) {
      return error;
    }
  })();
  return { url: await address, finished, logRoot, signals };
}

async function open(url) {
  const page = await browser.newPage({ viewport: { width: 1400, height: 700 } });
  test.after(() => page.close());
  await page.goto(url);
  return page;
}

/**
 * What a person sees on the page.
 */
const seen = (page) => page.evaluate(() => {
  const text = (selector) => document.querySelector(selector)?.textContent ?? null;
  return {
    status: text('#status'), current: text('.node.current text'), taken: text('.edge.taken text'),
    // Each decision as one line: its heading's parts, then each row, separated by ' | '.
    steps: [...document.querySelectorAll('#steps li')].map((item) => [...item.children]
      .map((row) => (row.classList.contains('step-head') ? [...row.children].map((part) => part.textContent).join(' | ') : row.textContent))
      .join(' | ')),
    future: document.querySelectorAll('#steps li.future').length,
    buttons: Object.fromEntries([...document.querySelectorAll('#controls button')].map((button) => [button.dataset.action, !button.disabled])),
    ending: document.querySelector('#ending').hidden ? null : text('#ending'),
  };
});

const until = (page, predicate, argument) => page.waitForFunction(predicate, argument, { timeout: 10_000 });
const statusStarts = (page, prefix) => until(page, (start) => document.querySelector('#status').textContent.startsWith(start), prefix);

test('live: paused at the start, stepped, reloaded, resumed - the diagram and decisions follow (UND-14, UND-15)', async () => {
  const run = await watchedRun('examples/mcp', { judge: BOX_OFFICE(), paused: true });
  const page = await open(run.url);
  await statusStarts(page, 'paused before step 1');
  let now = await seen(page);
  assert.equal(now.current, 'choosing', 'paused in the move state, before Jev is asked');
  assert.deepEqual(now.buttons, { pause: false, step: true, resume: true });

  await page.click('button[data-action=step]');
  await statusStarts(page, 'paused before step 2');
  now = await seen(page);
  assert.equal(now.steps.length, 1, 'Step made exactly one move');
  assert.match(now.steps[0], /^step 1 \| asking \| -> tool:list_films \(0\.9\) \| offered: tool:list_films \| answer: \[\{"film":"f1"/);

  await page.reload();
  await statusStarts(page, 'paused before step 2');
  assert.equal((await seen(page)).steps.length, 1, 'a reload rebuilds everything so far');

  await page.click('button[data-action=resume]');
  await until(page, () => document.querySelector('#ending').hidden === false);
  now = await seen(page);
  assert.equal(now.status, 'done');
  assert.equal(now.ending, 'done after 3 steps');
  assert.equal(now.current, 'finished');
  assert.equal(now.taken, 'done: showing text Ticket issued');
  assert.match(now.steps[1], /arguments: film=f2, count=2 \| answer: \{"hold":"h1"/);
  assert.match(now.steps[2], /-> tool:pay \(0\.9\) .*arguments: hold=h1, method=card \| answer: Ticket issued/);
  assert.deepEqual(now.buttons, { pause: false, step: false, resume: false }, 'no control after the end');
  assert.equal(await run.finished, null);
});

test('live: Pause on a running run holds it while the app is idle, past the limit; Resume lets it stall (UND-15 AC4)', async () => {
  // The fixture app goes quiet after the first move (`brewing` is not a move phase).
  const app = { screen: 'menu', seq: 0 };
  const target = {
    describe: () => 'node app.mjs', view: async () => ({ screen: app.screen, seq: app.seq }), talk: async () => [], say: async () => {},
    act: async () => { app.seq += 1; app.screen = 'brewing'; }, exited: () => null, close: async () => {},
  };
  const judge = { systemOne: async () => ({ answers: { next: { type: 'choice', choice: 'cancel', confidence: 0.8 } } }) };
  const run = await watchedRun(GOOD, { judge, makeTarget: async () => target, firstMoveMs: 600, stallMs: 600 });
  const page = await open(run.url);
  await until(page, () => document.querySelectorAll('#steps li').length === 1);
  await page.click('button[data-action=pause]');
  await statusStarts(page, 'paused before step 2');
  // Nothing should happen for a while: there is no event to wait for, only time to let pass.
  await page.waitForTimeout(1500); // eslint-disable-line sonarjs/no-fixed-wait-in-tests -- more than twice the 600 ms stall limit
  assert.equal((await seen(page)).status, 'paused before step 2', 'not stalled while paused');
  await page.click('button[data-action=resume]');
  await until(page, () => document.querySelector('#ending').hidden === false);
  const now = await seen(page);
  assert.equal(now.status, 'ended: stalled');
  assert.match(now.ending, /^stalled: nothing to do for 0\.6 s after step 1/, 'the outcome is said once (DEF-12)');
  assert.equal((await run.finished)?.outcome, 'stalled');
});

test('live: Ctrl-C while paused stops at once - no move, and the page says why (UND-15 AC5)', async () => {
  let asked = 0;
  const judge = { systemOne: async () => { asked += 1; return { answers: {} }; } };
  const run = await watchedRun('examples/mcp', { judge, paused: true });
  const page = await open(run.url);
  await statusStarts(page, 'paused before step 1');
  run.signals.emit('SIGINT');
  await until(page, () => document.querySelector('#ending').hidden === false);
  const now = await seen(page);
  assert.equal(now.status, 'ended: interrupted');
  assert.equal(now.ending, 'interrupted: stopped by Ctrl-C while paused, after 0 steps');
  assert.equal(asked, 0, 'Jev was never asked');
  assert.equal((await run.finished)?.outcome, 'interrupted');
});

test('replay: a finished run\'s log, stepped through each state change, a step clicked, played to the end (UND-16)', async () => {
  const run = await watchedRun('examples/mcp', { judge: BOX_OFFICE() });
  assert.equal(await run.finished, null);
  const folder = path.join(run.logRoot, 'boxoffice-mcp');
  const lines = readLog(path.join(folder, readdirSync(folder)[0]));
  const server = await startWatch({ mode: 'replay', source: logSource(lines) });
  test.after(() => server.close());
  const page = await open(server.url);
  await statusStarts(page, 'replay - step 0 of 3');
  let now = await seen(page);
  assert.deepEqual(now.buttons, { play: true, back: false, forward: true });
  assert.equal(now.future, 3, 'every decision listed, those to come faded');

  await page.click('button[data-action=forward]');
  now = await seen(page);
  assert.deepEqual([now.current, now.taken], ['looking', 'OBSERVE'], 'Step forward walks one state change');

  await page.click('#steps li[data-step="2"]');
  now = await seen(page);
  assert.equal(now.status, 'replay - step 2 of 3');
  assert.equal(now.future, 1);

  await page.click('button[data-action=play]');
  await until(page, () => document.querySelector('#ending').hidden === false);
  now = await seen(page);
  assert.equal(now.ending, 'done after 3 steps');
  assert.deepEqual(now.buttons, { play: false, back: true, forward: false });
});
