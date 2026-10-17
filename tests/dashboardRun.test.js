// Sprint 6 UND-29 (ARCH §4 "Play"): the console plays a sketch through
// runSketch with the controls' values, streams its lines, stops it, and
// says why a run could not start.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { serveDashboard } from '../src/dashboard/console.mjs';

const ORDER = ['tool:boxoffice/pay', 'tool:boxoffice/pick_seats', 'tool:ratings/rating', 'tool:boxoffice/seat_map', 'tool:boxoffice/list_films'];

/**
 * The evening's Jev double (as tests/evening.run.test.js).
 */
function eveningJudge(delayMs = 0) {
  return {
    async systemOne(request) {
      if (delayMs > 0) await new Promise((resolve) => setTimeout(resolve, delayMs));
      const answers = {};
      for (const [key, question] of Object.entries(request.questions)) {
        if (question.type === 'score') {
          answers[key] = { type: 'score', score: /scream|best scare/.test(request.state.rows[key].reviews.join(' ')) ? 3 : 1 };
          continue;
        }
        const offered = Object.keys(question.criteria);
        const order = request.state.last_call?.tool === 'boxoffice/pick_seats' && !request.state.last_call.failed ? ORDER : ORDER.slice(1);
        const choice = key === 'next' ? order.find((id) => offered.some((each) => each.startsWith(id))) : 'v1';
        answers[key] = { type: 'choice', choice: offered.find((each) => each.startsWith(choice)) ?? offered[0], confidence: 0.9 };
      }
      return { answers };
    },
  };
}

async function console_({ delayMs = 0, ...options } = {}) {
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-console-'));
  const dashboard = await serveDashboard({
    folder: 'examples', port: 0, environment: { ...process.env, TYPESAFE_API_KEY: 'test' },
    runOptions: { makeJudge: () => eveningJudge(delayMs), logRoot, pollMs: 20, steps: 30 }, ...options,
  });
  test.after(async () => {
    await dashboard.close();
    rmSync(logRoot, { recursive: true, force: true });
  });
  const lines = [];
  dashboard.hub.send = ((send) => (line) => {
    lines.push(line);
    send(line);
  })(dashboard.hub.send);
  const post = (verb, body = {}) => fetch(`${dashboard.url}api/${verb}`, { method: 'POST', body: JSON.stringify(body) });
  return { dashboard, lines, post, logRoot };
}

test('Play runs the sketch with the controls\' values and streams its lines; a second Play waits (UND-29 AC1, AC3, AC5)', async () => {
  const { dashboard, lines, post, logRoot } = await console_();
  const played = await post('play', { sketch: 'evening', inputs: { mood: 'romantic', centre: 1.5 } });
  assert.equal(played.status, 202);
  const again = await post('play', { sketch: 'evening' });
  assert.equal(again.status, 409);
  assert.deepEqual(await again.json(), { problem: 'a run is going - press STOP first' });
  await dashboard.runner.finished();
  const start = lines.find((line) => line.event === 'start');
  assert.equal(start.inputs.mood, 'romantic');
  assert.equal(start.inputs.centre, 1.5);
  assert.ok(lines.some((line) => line.step && line.move === 'tool:boxoffice/pay(method=card)'));
  assert.deepEqual(lines.at(-1), { event: 'dashboard', running: false, sketch: 'evening', outcome: 'done' });
  assert.ok(lines.some((line) => line.event === 'dashboard' && (line.stderr ?? '').startsWith('playing evening')));
  const { readdirSync } = await import('node:fs');
  assert.equal(readdirSync(path.join(logRoot, 'evening')).length, 1, 'the run is logged like any run');
});

test('STOP stops the run as Ctrl-C would (UND-29 AC2)', async () => {
  const { dashboard, lines, post } = await console_({ delayMs: 150 });
  await post('play', { sketch: 'evening' });
  await new Promise((resolve) => setTimeout(resolve, 400));
  assert.equal((await post('stop')).status, 202);
  await dashboard.runner.finished();
  assert.equal(lines.at(-1).outcome, 'interrupted');
  assert.equal((await post('stop')).status, 409);
});

test('a run that cannot start says why and leaves nothing running (UND-29 AC4)', async () => {
  const { dashboard, lines, post } = await console_({ environment: {} });
  await post('play', { sketch: 'evening', inputs: { centre: 12 } });
  await dashboard.runner.finished();
  assert.deepEqual(lines.at(-1), { event: 'dashboard', running: false, sketch: 'evening', refused: 'input "centre" must be between 0 and 10, got 12' });
  assert.equal(dashboard.runner.isRunning(), false);
  assert.equal((await post('play', { sketch: '../src' })).status, 404);
});

test('edits are refused while a run goes; POWER off stops the run (UND-32 AC4-5)', async () => {
  const { dashboard, lines, post } = await console_({ delayMs: 150 });
  await post('play', { sketch: 'evening' });
  const edit = await post('edit', { sketch: 'evening', changes: [{ path: ['inputs', 'centre', 'default'], value: 2 }] });
  assert.equal(edit.status, 409);
  assert.deepEqual(await edit.json(), { problem: 'stop the run before changing the settings' });
  const write = await post('write', { sketch: 'evening', text: 'name: evening\n' });
  assert.equal(write.status, 409, 'nor writes from the bay (UND-35 AC4)');
  const off = await post('power', { on: false });
  assert.deepEqual(await off.json(), { on: false });
  assert.equal(dashboard.runner.isRunning(), false);
  assert.equal(lines.at(-1).outcome, 'interrupted');
  assert.deepEqual(await (await post('power', { on: true })).json(), { on: true, restored: [] });
});

test('the bay reads a sketch\'s file as it is, only by a rack name (UND-35 AC1)', async () => {
  const { dashboard } = await console_();
  const read = await fetch(`${dashboard.url}api/text/evening`);
  assert.equal(read.status, 200);
  assert.deepEqual(await read.json(), { text: readFileSync('examples/evening/sketch.yaml', 'utf8') });
  assert.equal((await fetch(`${dashboard.url}api/text/..%2Fsrc`)).status, 404);
});
