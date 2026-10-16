// Sprint 4 UND-14/16 (ARCH §5): the watch server over real HTTP on a free
// port - token-guarded paths, the page's own files, SSE with history then
// live lines then `end`, control in live mode only, a busy port refused.
import test from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import { startWatch, logSource } from '../src/watch/server.mjs';
import { createStream } from '../src/stream.mjs';
import { UsageError } from '../src/errors.mjs';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

function liveStream() {
  const directory = mkdtempSync(path.join(tmpdir(), 'understudy-watch-'));
  test.after(() => rmSync(directory, { recursive: true, force: true }));
  return createStream({ stdout: { write: () => {} }, logFile: path.join(directory, 'run.jsonl') });
}

async function started(options) {
  const watch = await startWatch(options);
  test.after(() => watch.close());
  return watch;
}

/**
 * Reads SSE messages until `count` arrived (or `end`), as { event, data }.
 */
async function messages(url, count) {
  const response = await fetch(`${url}events`);
  const reader = response.body.getReader();
  const decoder = new globalThis.TextDecoder();
  let buffer = '';
  const found = [];
  while (found.length < count) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let cut;
    while ((cut = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      const event = /^event: (.*)$/m.exec(block)?.[1] ?? 'message';
      found.push({ event, data: JSON.parse(/^data: (.*)$/m.exec(block)[1]) });
    }
  }
  await reader.cancel();
  return found;
}

test('serves the page files under the token only; anything else is 404', async () => {
  const watch = await started({ mode: 'live', source: liveStream() });
  assert.match(watch.url, /^http:\/\/127\.0\.0\.1:\d+\/w\/[\w-]{16}\/$/);
  const layout = await fetch(`${watch.url}layout.mjs`);
  assert.equal(layout.status, 200);
  assert.match(layout.headers.get('content-type'), /javascript/);
  const origin = new URL(watch.url).origin;
  assert.equal((await fetch(`${origin}/w/wrong-token/layout.mjs`)).status, 404);
  assert.equal((await fetch(`${watch.url}server.mjs`)).status, 404, 'only the page files are served');
  assert.equal((await fetch(`${watch.url}../../etc/passwd`)).status, 404);
});

test('a page that joins late gets the history, then live lines, then end after the final line', async () => {
  const stream = liveStream();
  const watch = await started({ mode: 'live', source: stream });
  stream.emit({ event: 'start', sketch: 'x' });
  stream.emit({ event: 'state', from: 'a', to: 'b', on: 'OBSERVE' });
  const reading = messages(watch.url, 5);
  setTimeout(() => stream.emit({ final: true, outcome: 'done', steps: 0, state: 'b' }), 50);
  const got = await reading;
  const kindOf = ({ event, data }) => {
    if (event === 'end') return 'end';
    return data.event ?? (data.final ? 'final' : '?');
  };
  assert.deepEqual(got.map((message) => kindOf(message)), ['hello', 'start', 'state', 'final', 'end']);
});

test('replay: the whole log at once, then end - even without a final line', async () => {
  const watch = await started({ mode: 'replay', source: logSource([{ event: 'start', sketch: 'x' }, { step: 1 }]) });
  const got = await messages(watch.url, 4);
  assert.deepEqual(got.map(({ event }) => event), ['message', 'message', 'message', 'end']);
  assert.equal(got[0].data.mode, 'replay');
});

test('control: live runs take pause / step / resume; replay and unknown actions are 409', async () => {
  const asked = [];
  const live = await started({ mode: 'live', source: liveStream(), control: (action) => {
    asked.push(action);
    return true;
  } });
  const post = (url, body) => fetch(`${url}control`, { method: 'POST', body: JSON.stringify(body) });
  assert.equal((await post(live.url, { action: 'pause' })).status, 204);
  assert.equal((await post(live.url, { action: 'dance' })).status, 409);
  assert.equal((await post(live.url, 'nonsense')).status, 409);
  assert.deepEqual(asked, ['pause']);
  const replay = await started({ mode: 'replay', source: logSource([]) });
  assert.equal((await post(replay.url, { action: 'pause' })).status, 409);
});

test('a busy port is refused before anything starts', async () => {
  const blocker = net.createServer();
  await new Promise((resolve) => blocker.listen(0, '127.0.0.1', resolve));
  test.after(() => blocker.close());
  const { port } = blocker.address();
  await assert.rejects(startWatch({ port, mode: 'live', source: liveStream() }),
    (error) => error instanceof UsageError && error.message === `port ${port} is in use - choose another with --port`);
});

test('--host 0.0.0.0 listens on every interface and names an address per interface, loopback last', async () => {
  const watch = await started({ mode: 'live', source: liveStream(), host: '0.0.0.0' });
  assert.ok(watch.urls.length > 0);
  assert.match(watch.urls.at(-1), /^http:\/\/127\.0\.0\.1:\d+\/w\//);
  for (const url of watch.urls) assert.equal((await fetch(`${url}layout.mjs`)).status, 200, url);
});

test('an address this machine does not have is refused, saying what to give', async () => {
  await assert.rejects(startWatch({ mode: 'live', source: liveStream(), host: '203.0.113.7' }),
    (error) => error instanceof UsageError && error.message === 'cannot listen on 203.0.113.7 - give an address this machine has (e.g. 0.0.0.0 for every interface)');
});
