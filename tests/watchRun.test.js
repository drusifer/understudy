// Sprint 4 UND-14 AC1, 4, 6, 7 (ARCH §4): `run --watch` - the server
// starts before anything else, prints its address, streams the run to a
// page that joins mid-run, and changes nothing about the run itself.
import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import net from 'node:net';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runSketch } from '../src/run.mjs';
import { UsageError } from '../src/errors.mjs';

const GOOD = fileURLToPath(new URL('fixtures/sketches/good', import.meta.url));

function fakeTarget() {
  const app = { screen: 'menu', seq: 0, isStarted: true };
  return {
    app,
    target: {
      describe: () => 'node app.mjs',
      view: async () => ({ screen: app.screen, seq: app.seq }),
      talk: async () => [],
      say: async () => {},
      act: async ({ input }) => {
        app.seq += 1;
        if (input === 'order') app.screen = 'done';
      },
      exited: () => null,
      close: async () => {},
    },
  };
}

async function runWith({ watch, judge, makeTarget }) {
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-watch-run-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  const out = { stdout: '', stderr: '' };
  await runSketch(GOOD, {
    stdout: { write: (text) => { out.stdout += text; } }, stderr: { write: (text) => { out.stderr += text; } },
    makeJudge: () => judge, makeTarget, logRoot, pollMs: 5, watch,
    signals: new EventEmitter(), // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`
  });
  return out;
}

const answering = (choice, before = async () => {}) => ({
  async systemOne() {
    await before();
    return { answers: { next: { type: 'choice', choice, confidence: 0.75 } } };
  },
});

test('a page that joins mid-run gets everything so far, then the rest, then end', async () => {
  // The judge holds the first decision until the page has joined, so it joins mid-run.
  const { promise: held, resolve: release } = Promise.withResolvers();
  const { promise: page, resolve: joined } = Promise.withResolvers();
  const readPage = async (url) => {
    const response = await fetch(`${url}events`);
    const decoder = new globalThis.TextDecoder();
    let buffer = '';
    for await (const chunk of response.body) {
      buffer += decoder.decode(chunk, { stream: true });
      if (buffer.includes('"event":"start"')) release();
      if (buffer.includes('event: end')) break;
    }
    return buffer.split('\n\n').filter((block) => block.startsWith('data: ')).map((block) => JSON.parse(block.slice(6)));
  };
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-watch-run-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  const out = { stdout: '', stderr: '' };
  await runSketch(GOOD, {
    stdout: { write: (text) => { out.stdout += text; } },
    stderr: {
      write(text) {
        out.stderr += text;
        const url = /watch at (\S+)\n/.exec(text)?.[1];
        if (url) joined(readPage(url));
      },
    },
    makeJudge: () => answering('order', () => held), makeTarget: async () => fakeTarget().target, logRoot, pollMs: 5, watch: { port: 0 },
    signals: new EventEmitter(), // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`
  });
  const lines = await page;
  assert.match(out.stderr, /^understudy: watch at http:\/\/127\.0\.0\.1:\d+\/w\/[\w-]+\/\n/);
  assert.equal(lines[0].event, 'hello');
  const stdoutLines = out.stdout.trim().split('\n').map((line) => JSON.parse(line));
  assert.deepEqual(lines.slice(1), stdoutLines, 'the page saw exactly the run\'s lines, in order');
  assert.ok(stdoutLines.some((line) => line.step === 1));
});

test('--watch changes nothing about the run: same lines (bar times) as without it', async () => {
  const strip = (text) => text.trim().split('\n').map((line) => JSON.parse(line)).map(({ at, ...rest }) => rest);
  const plain = await runWith({ watch: null, judge: answering('order'), makeTarget: async () => fakeTarget().target });
  const watched = await runWith({ watch: { port: 0 }, judge: answering('order'), makeTarget: async () => fakeTarget().target });
  assert.deepEqual(strip(watched.stdout), strip(plain.stdout));
});

test('a busy --port refuses the run before the judge or the app is started', async () => {
  const blocker = net.createServer();
  await new Promise((resolve) => blocker.listen(0, '127.0.0.1', resolve));
  test.after(() => blocker.close());
  const { port } = blocker.address();
  let isStarted = false;
  await assert.rejects(runWith({
    watch: { port }, judge: answering('order'),
    makeTarget: async () => {
      isStarted = true;
      return fakeTarget().target;
    },
  }), (error) => error instanceof UsageError && error.message === `port ${port} is in use - choose another with --port`);
  assert.equal(isStarted, false);
});
