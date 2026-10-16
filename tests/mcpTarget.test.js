// Sprint 3 UND-10 AC5-7 (ARCH §4, §6, ADR-0012): the MCP target against
// the real box office example over stdio - started, looked at, called,
// and stopped through program.mjs. A tool error is the server's answer;
// a server that dies or never answers is named with what it printed.
import test from 'node:test';
import assert from 'node:assert/strict';
import { startTarget } from '../src/targets/mcp.mjs';
import { RunError, UsageError } from '../src/errors.mjs';

const BOX = { kind: 'mcp', servers: [{ name: null, entry: { command: 'node', args: ['server.mjs'] }, from: 'examples/mcp/sketch.yaml' }] };
const withEntry = (entry) => ({ kind: 'mcp', servers: [{ ...BOX.servers[0], entry }] });

async function started(spec = BOX, options = {}) {
  const target = await startTarget(spec, { directory: 'examples/mcp', environment: process.env, ...options });
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

test('a look lists the server\'s tools with their schemas; no call yet', async () => {
  const target = await started();
  const view = await target.view();
  assert.deepEqual(view.tools.map((tool) => tool.name), ['list_films', 'pick_seats', 'pay', 'leave_review']);
  assert.deepEqual(view.tools[1].inputSchema.required, ['film', 'count']);
  assert.equal(view.last, null);
  assert.equal(target.describe(), 'node server.mjs');
});

test('a call is one move: the answer is logged with the call, and the next look carries it', async () => {
  const target = await started();
  const first = await target.view();
  const response = await target.act({ tool: 'pick_seats', arguments: { film: 'f2', count: 2 } });
  assert.deepEqual(response, { call: { tool: 'pick_seats', arguments: { film: 'f2', count: 2 } }, isError: false, text: '{"hold":"h1","film":"Paper Boats","count":2,"total":14}' });
  const after = await target.view();
  assert.equal(after.last.tool, 'pick_seats');
  assert.notEqual(after.seq, first.seq, 'a new answer is a change');
});

test('a tool error and an unknown tool are the server\'s answers, not failures', async () => {
  const target = await started();
  const refused = await target.act({ tool: 'pay', arguments: { hold: 'h9', method: 'card' } });
  assert.deepEqual(refused, { call: { tool: 'pay', arguments: { hold: 'h9', method: 'card' } }, isError: true, text: 'No hold h9 - pick seats first.' });
  const unknown = await target.act({ tool: 'dance', arguments: {} });
  assert.equal(unknown.isError, true);
  assert.match(unknown.text, /Tool dance not found/);
});

test('a server that exits before the handshake is named with its exit code and what it printed', async () => {
  const spec = withEntry({ command: 'node', args: ['-e', 'console.error("no database"); process.exit(3)'] });
  const error = await failure(startTarget(spec, { directory: 'examples/mcp', environment: process.env }));
  assert.ok(error instanceof RunError);
  assert.equal(error.outcome, 'app-exited');
  assert.match(error.message, /exited with code 3 before the MCP handshake - it printed: no database$/);
});

test('a server that never answers the handshake is stopped and named after the limit', async () => {
  const spec = withEntry({ command: 'node', args: ['-e', 'setInterval(() => {}, 1000)'] });
  const error = await failure(startTarget(spec, { directory: 'examples/mcp', environment: process.env, handshakeMs: 300 }));
  assert.equal(error.outcome, 'no-first-move');
  assert.match(error.message, /did not answer the MCP handshake within 0\.3 s - it printed nothing on stderr$/);
});

test('a server that dies mid-run stops the run, naming its exit code', async () => {
  const target = await started();
  await target.view();
  process.kill(Number(await pidOf()), 'SIGKILL');
  const error = await failure((async () => {
    for (let tries = 0; tries < 50; tries++) {
      await target.view();
      await new Promise((resolve) => setTimeout(resolve, 20));
    }
  })());
  assert.ok(error instanceof RunError);
  assert.equal(error.outcome, 'app-exited');
  assert.ok(target.exited());
});

test('an unset ${VAR} refuses before anything starts', async () => {
  const spec = withEntry({ command: 'node', args: ['${NO_SUCH_SERVER}'] });
  const error = await failure(startTarget(spec, { directory: 'examples/mcp', environment: {} }));
  assert.ok(error instanceof UsageError);
  assert.match(error.message, /^examples\/mcp\/sketch\.yaml: \$\{NO_SUCH_SERVER\} is not set/);
});

/**
 * The started server's process id, from the operating system's view of
 * the test's children (the target does not expose its program).
 */
async function pidOf() {
  const { execFileSync } = await import('node:child_process');
  const children = execFileSync('pgrep', ['-P', String(process.pid), '-f', 'server.mjs'], { encoding: 'utf8' }).trim().split('\n');
  return children.at(-1);
}
