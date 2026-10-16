// Sprint 5 UND-20 (ARCH §3, ADR-0022): one MCP target over several
// servers - every server's tools in one look, each named by its server;
// a call goes to its own server; a server that will not start stops the
// ones already started and is named.
import test from 'node:test';
import assert from 'node:assert/strict';
import { startTarget } from '../src/targets/mcp.mjs';
import { mcpApp } from '../src/apps/mcp.mjs';
import { RunError } from '../src/errors.mjs';

const from = 'examples/mcp/sketch.yaml';
const box = (name) => ({ name, entry: { command: 'node', args: ['server.mjs'] }, from });
const TWO = { kind: 'mcp', servers: [box('a'), box('b')] };
const options = { directory: 'examples/mcp', environment: process.env };

async function started(spec = TWO) {
  const target = await startTarget(spec, options);
  test.after(() => target.close());
  return target;
}

async function failure(promise) {
  try {
    await promise;
  } catch (error) {
    return error;
  }
  assert.fail('did not fail');
}

test('a look lists every server\'s tools, each with its server', async () => {
  const target = await started();
  const { tools } = await target.view();
  assert.deepEqual(tools.map((tool) => `${tool.server}/${tool.name}`), [
    'a/list_films', 'a/pick_seats', 'a/pay', 'a/leave_review', 'b/list_films', 'b/pick_seats', 'b/pay', 'b/leave_review',
  ]);
  assert.equal(target.describe(), 'a (node server.mjs), b (node server.mjs)');
});

test('a call goes to the server it names, and the answer says which', async () => {
  const target = await started();
  const held = await target.act({ server: 'b', tool: 'pick_seats', arguments: { film: 'f1', count: 3 } });
  assert.deepEqual(held.call, { server: 'b', tool: 'pick_seats', arguments: { film: 'f1', count: 3 } });
  assert.equal(held.isError, false);
  // a's box office still has every seat; b's has none left for f1.
  assert.equal((await target.act({ server: 'a', tool: 'pick_seats', arguments: { film: 'f1', count: 3 } })).isError, false);
  assert.equal((await target.act({ server: 'b', tool: 'pick_seats', arguments: { film: 'f1', count: 1 } })).isError, true);
  assert.equal((await target.view()).last.server, 'b');
});

test('a server that does not start is named, and the ones started before it are stopped', async () => {
  const first = box('boxoffice');
  const broken = { name: 'ratings', from, entry: { command: 'node', args: ['-e', 'console.error("no scores"); process.exit(3)'] } };
  const error = await failure(startTarget({ kind: 'mcp', servers: [first, broken] }, options));
  assert.ok(error instanceof RunError);
  assert.equal(error.outcome, 'app-exited');
  assert.match(error.message, /^server "ratings" did not start: node -e .* exited with code 3 before the MCP handshake - it printed: no scores$/);
});

test('closing stops every server', async () => {
  const target = await startTarget(TWO, options);
  await target.view();
  await target.close();
  await assert.rejects(target.view());
});

test('with several servers, moves are named <server>/<tool> and call their own server', () => {
  const app = mcpApp({ calls: [{ tool: 'b/pay', arguments: { method: 'card' } }], values: { 'a/pick_seats': { count: [2] } } });
  const tool = (server, name, inputSchema) => ({ server, name, description: '', inputSchema });
  const view = {
    tools: [
      tool('a', 'list_films', { type: 'object' }),
      tool('a', 'pick_seats', { type: 'object', properties: { count: { type: 'integer' } }, required: ['count'] }),
      tool('b', 'pay', { type: 'object', properties: { method: { type: 'string' } }, required: ['method'] }),
    ],
    last: null,
  };
  const { offered } = app.moves(view);
  assert.deepEqual(offered.map((move) => move.id), ['tool:a/list_films', 'tool:a/pick_seats', 'tool:b/pay(method=card)']);
  assert.deepEqual(app.act({ ...offered[1], filled: { count: 2 } }).actions, [{ server: 'a', tool: 'pick_seats', arguments: { count: 2 } }]);
  assert.equal(app.project(view).tools[2].name, 'b/pay');
});

test('with one server, ids and calls are as before (no server named)', () => {
  const app = mcpApp();
  const { offered } = app.moves({ tools: [{ server: null, name: 'list_films', inputSchema: { type: 'object' } }], last: null });
  assert.equal(offered[0].id, 'tool:list_films');
  assert.deepEqual(app.act(offered[0]).actions, [{ tool: 'list_films', arguments: {} }]);
});
