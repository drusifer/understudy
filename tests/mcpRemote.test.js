// Sprint 3 UND-11 (ARCH §4 "Connecting to a remote server", §6): a running
// MCP server behind a URL and a token - the box office example in HTTP
// mode - is played by reference to servers.json and left running. A wrong
// token is refused by status, nothing answering is named by URL, and the
// token is never printed or logged.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { EventEmitter } from 'node:events';
import { mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import net from 'node:net';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { startTarget } from '../src/targets/mcp.mjs';
import { runSketch } from '../src/run.mjs';
import { RunError } from '../src/errors.mjs';

const TOKEN = 'tok-1f6d0c7e-never-printed';

function freePort() {
  return new Promise((resolve) => {
    const probe = net.createServer().listen(0, '127.0.0.1', () => {
      const { port } = probe.address();
      probe.close(() => resolve(port));
    });
  });
}

/**
 * The box office in HTTP mode on a free port, stopped after the tests.
 */
async function boxOffice() {
  const port = await freePort();
  const child = spawn(process.execPath, ['examples/mcp/server.mjs', '--http', '--port', String(port), '--token', TOKEN], { stdio: ['ignore', 'ignore', 'pipe'] });
  test.after(() => child.kill());
  await new Promise((resolve) => child.stderr.on('data', (chunk) => { if (String(chunk).includes('listening')) resolve(); }));
  return { port, child };
}

const spec = (port, token = '${MCP_TOKEN}') => ({
  kind: 'mcp', from: 'servers.json',
  entry: { type: 'http', url: `http://127.0.0.1:${port}/mcp`, headers: { Authorization: `Bearer ${token}` } },
});

async function failure(promise) {
  try {
    await promise;
  } catch (error) {
    return error;
  }
  assert.fail('did not fail');
}

test('with the right token the remote server is played, and closing leaves it running', async () => {
  const { port, child } = await boxOffice();
  const target = await startTarget(spec(port), { directory: '.', environment: { MCP_TOKEN: TOKEN } });
  assert.equal(target.describe(), `http://127.0.0.1:${port}/mcp`);
  assert.equal((await target.view()).tools.length, 4);
  const answer = await target.act({ tool: 'pick_seats', arguments: { film: 'f2', count: 2 } });
  assert.equal(answer.isError, false);
  assert.equal(target.exited(), null);
  await target.close();
  assert.equal(child.exitCode, null, 'understudy does not stop a server it did not start');
  const again = await startTarget(spec(port), { directory: '.', environment: { MCP_TOKEN: TOKEN } });
  assert.equal((await again.view()).tools.length, 4);
  await again.close();
});

test('a wrong token is refused with the status and the URL - never the token', async () => {
  const { port } = await boxOffice();
  const error = await failure(startTarget(spec(port), { directory: '.', environment: { MCP_TOKEN: 'wrong-token-xyz' } }));
  assert.ok(error instanceof RunError);
  assert.equal(error.outcome, 'refused');
  assert.equal(error.message, `the MCP server at http://127.0.0.1:${port}/mcp refused the connection (HTTP 401)`);
  assert.ok(!error.message.includes('wrong-token-xyz'));
});

test('nothing answering at the URL is named after the limit', async () => {
  const port = await freePort();
  const started = Date.now();
  const error = await failure(startTarget(spec(port), { directory: '.', environment: { MCP_TOKEN: TOKEN }, handshakeMs: 600, retryMs: 50 }));
  assert.equal(error.outcome, 'no-first-move');
  assert.equal(error.message, `no first move from http://127.0.0.1:${port}/mcp: nothing answered within 0.6 s (ECONNREFUSED)`);
  assert.ok(Date.now() - started < 3000);
});

test('examples/mcp-remote is played end to end by reference; the token is in no output and no log', async () => {
  const { port } = await boxOffice();
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-remote-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  const out = { stdout: '', stderr: '' };
  const moves = ['tool:list_films', 'tool:pick_seats', 'tool:pay(method=card)'];
  let asked = 0;
  const judge = {
    async systemOne({ questions }) {
      const answers = {};
      for (const [key, question] of Object.entries(questions)) {
        // The move first; an argument takes the value naming film f1 or hold h1, else the first.
        const choice = key.startsWith('argument_')
          ? Object.entries(question.criteria).find(([, text]) => /"(f1|h1)"/.test(text))?.[0] ?? 'v1'
          : moves[Math.min(asked++, moves.length - 1)];
        answers[key] = { type: 'choice', choice, confidence: 0.9 };
      }
      return { answers };
    },
  };
  await runSketch('examples/mcp-remote', {
    stdout: { write: (text) => { out.stdout += text; } }, stderr: { write: (text) => { out.stderr += text; } },
    environment: { MCP_TOKEN: TOKEN, BOX_PORT: String(port) }, makeJudge: () => judge, logRoot, pollMs: 20,
    signals: new EventEmitter(), // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`
  });
  const lines = out.stdout.trim().split('\n').map((line) => JSON.parse(line));
  assert.deepEqual(lines.filter((line) => !line.final).map((line) => line.response.call), [
    { tool: 'list_films', arguments: {} },
    { tool: 'pick_seats', arguments: { film: 'f1', count: 2 } },
    { tool: 'pay', arguments: { method: 'card', hold: 'h1' } },
  ]);
  assert.equal(lines.at(-1).outcome, 'done');
  const folder = path.join(logRoot, 'boxoffice-remote');
  const log = readFileSync(path.join(folder, readdirSync(folder)[0]), 'utf8');
  const outputs = Object.entries({ stdout: out.stdout, stderr: out.stderr, log });
  for (const [where, text] of outputs) {
    assert.ok(!text.includes(TOKEN), `the token is in ${where}`);
  }
  assert.ok(out.stderr.includes(`playing boxoffice-remote (http://127.0.0.1:${port}/mcp)`));
});
