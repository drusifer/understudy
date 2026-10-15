// Sprint 2 UND-6 (ARCH §4, ADR-0008): a JSON API as a target - a look is
// a GET of its state, a move is a request, an error status is the app's
// answer (not a crash), and a lost connection stops the run. Driven
// against in-process servers and the example's own server, never Jev.
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { startTarget } from '../src/targets/http.mjs';
import { RunError } from '../src/errors.mjs';

const EXAMPLE = fileURLToPath(new URL('../examples/http', import.meta.url));

/**
 * A tiny API: GET /state shows a counter; POST /add adds to it; POST /nope is refused.
 */
async function counterServer() {
  const state = { count: 0 };
  const server = http.createServer((request, response) => {
    let text = '';
    request.on('data', (chunk) => { text += chunk; });
    request.on('end', () => {
      const send = (status, body) => {
        response.writeHead(status, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify(body));
      };
      if (request.method === 'GET' && request.url === '/state') return send(200, state);
      if (request.method === 'POST' && request.url === '/add') {
        state.count += JSON.parse(text).by;
        return send(200, state);
      }
      send(402, { error: 'not today' });
    });
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}`;
  return { url, close: () => new Promise((resolve) => { server.closeAllConnections(); server.close(resolve); }) };
}

test('attached to a running API: the view is its state, a move is a request, and both are recorded', async () => {
  const api = await counterServer();
  const target = await startTarget({ kind: 'http', url: api.url, state: '/state' }, { directory: EXAMPLE });
  try {
    const first = await target.view();
    assert.equal(first.status, 200);
    assert.deepEqual(first.body, { count: 0 });
    assert.equal(first.last, null);
    assert.deepEqual(await target.act({ method: 'POST', path: '/add', body: { by: 2 } }), { status: 200 });
    const second = await target.view();
    assert.deepEqual(second.body, { count: 2 });
    assert.notEqual(second.seq, first.seq, 'seq moves when the state changes');
    assert.equal((await target.view()).seq, second.seq, 'and not when it does not');
    assert.deepEqual(second.last, { method: 'POST', path: '/add', status: 200, body: { count: 2 } });
    assert.equal(target.describe(), api.url);
    assert.deepEqual(await target.talk(), []);
  } finally {
    await target.close();
  }
  assert.equal((await fetch(`${api.url}/state`)).status, 200, 'an attached API is left running');
  await api.close();
});

test('an error status is the app\'s answer: returned and kept as the last answer, never thrown', async () => {
  const api = await counterServer();
  const target = await startTarget({ kind: 'http', url: api.url, state: '/state' }, { directory: EXAMPLE });
  try {
    assert.deepEqual(await target.act({ method: 'POST', path: '/nope' }), { status: 402 });
    assert.deepEqual((await target.view()).last, { method: 'POST', path: '/nope', status: 402, body: { error: 'not today' } });
  } finally {
    await target.close();
    await api.close();
  }
});

test('a lost connection stops the run, naming the URL', async () => {
  const api = await counterServer();
  const target = await startTarget({ kind: 'http', url: api.url, state: '/state' }, { directory: EXAMPLE });
  await api.close();
  await assert.rejects(target.view(), (error) => {
    assert.ok(error instanceof RunError);
    assert.equal(error.outcome, 'connection-lost');
    assert.match(error.message, new RegExp(`^lost the connection to ${api.url}: `));
    return true;
  });
  await target.close();
});

test('started: the example server runs on a free port and is stopped at the end', async () => {
  const spec = { kind: 'http', command: 'node', args: ['server.mjs'], url: 'http://127.0.0.1:{port}', state: '/machine' };
  const target = await startTarget(spec, { directory: EXAMPLE });
  try {
    assert.match(target.describe(), /^node server\.mjs at http:\/\/127\.0\.0\.1:\d+$/);
    assert.equal((await target.view()).body.credit, 0);
    assert.equal(target.exited(), null);
  } finally {
    await target.close();
  }
  assert.notEqual(target.exited(), null, 'the server it started is stopped');
});

test('a started server that never answers stops the run after the wait, and is stopped', async () => {
  const spec = { kind: 'http', command: process.execPath, args: ['-e', 'setInterval(() => {}, 1000)'], url: 'http://127.0.0.1:{port}', state: '/state' };
  await assert.rejects(startTarget(spec, { directory: EXAMPLE, readyMs: 300 }), (error) => {
    assert.ok(error instanceof RunError);
    assert.equal(error.outcome, 'no-first-move');
    assert.match(error.message, /^no first move from http:\/\/127\.0\.0\.1:\d+ within 0\.3 s - nothing answered GET \/state$/);
    return true;
  });
});

test('a started server that exits before answering is named with its exit code', async () => {
  const spec = { kind: 'http', command: process.execPath, args: ['-e', 'process.exit(4)'], url: 'http://127.0.0.1:{port}', state: '/state' };
  await assert.rejects(startTarget(spec, { directory: EXAMPLE }), (error) => {
    assert.ok(error instanceof RunError);
    assert.equal(error.outcome, 'app-exited');
    assert.match(error.message, /-e process\.exit\(4\) exited with code 4 before answering/);
    return true;
  });
});
