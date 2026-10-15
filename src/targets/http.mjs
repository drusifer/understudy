// Sprint 2 UND-6 (ARCH §4, ADR-0008): a JSON API as a target.
//
// A look is a GET of the app's state (`spec.state`); a move is one request
// `{ method, path, body }`. The view is the state's status and JSON body,
// plus the last answer to a move. An error status is the app's behaviour -
// returned and logged, never thrown; only a lost connection stops the run.
// With `command` the target starts the server on a free port (`{port}` in
// `url`) and stops it at the end; without one it attaches to `url` and
// leaves the service running.

import net from 'node:net';
import { RunError } from '../errors.mjs';
import { startProgram } from './program.mjs';

const READY_MS = 10_000;
const REQUEST_MS = 10_000;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function freePort() {
  return new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', () => {
      const { port } = probe.address();
      probe.close(() => resolve(port));
    });
  });
}

async function parsed(response) {
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return text;
  }
}

/**
 * Starts (or attaches to) the API and waits until it answers.
 * @param {{ kind: 'http', url: string, state: string, command?: string, args?: string[] }} spec
 * @param {{ directory: string, readyMs?: number, requestMs?: number }} options
 */
export async function startTarget(spec, { directory, readyMs = READY_MS, requestMs = REQUEST_MS }) {
  let url = spec.url;
  let program = null;
  if (spec.command) {
    const port = await freePort();
    url = spec.url.split('{port}').join(String(port));
    program = await startProgram(spec, { directory, environment: { ...process.env, PORT: String(port) } });
  }
  const describe = () => (program ? `${program.description} at ${url}` : url);
  const state = { last: null, seq: 0, body: undefined };

  const request = async (method, path, body) => {
    try {
      const response = await fetch(`${url}${path}`, {
        method,
        headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: AbortSignal.timeout(requestMs),
      });
      return { status: response.status, body: await parsed(response) };
    } catch (error) {
      const exited = program?.exited();
      if (exited) throw new RunError(`${program.description} exited with code ${exited.code} before the end state`, { outcome: 'app-exited' });
      throw new RunError(`lost the connection to ${url}: ${error.cause?.code ?? error.message}`, { outcome: 'connection-lost', cause: error });
    }
  };

  await waitUntilAnswering({ url, spec, program, readyMs, describe });

  return {
    describe,
    async view() {
      const answer = await request('GET', spec.state);
      const shown = JSON.stringify(answer.body);
      if (shown !== state.body) {
        state.body = shown;
        state.seq += 1;
      }
      return { status: answer.status, body: answer.body, seq: state.seq, last: state.last, exited: program?.exited() ?? null };
    },
    async act({ method = 'POST', path, body }) {
      const answer = await request(method, path, body);
      state.last = { method, path, status: answer.status, body: answer.body };
      return { status: answer.status };
    },
    async talk() {
      return [];
    },
    async say() {},
    exited: () => program?.exited() ?? null,
    close: async () => program?.close(),
  };
}

/**
 * Any HTTP answer to the state GET means the API is up. A started server
 * that dies or never answers is stopped and named.
 */
async function waitUntilAnswering({ url, spec, program, readyMs, describe }) {
  const deadline = Date.now() + readyMs;
  for (;;) {
    try {
      const left = Math.max(100, deadline - Date.now());
      await fetch(`${url}${spec.state}`, { signal: AbortSignal.timeout(left) });
      return;
    } catch {
      const exited = program?.exited();
      if (exited) throw new RunError(`${program.description} exited with code ${exited.code} before answering`, { outcome: 'app-exited' });
      if (Date.now() >= deadline) {
        await program?.close();
        throw new RunError(`no first move from ${describe().replace(/^.* at /, '')} within ${readyMs / 1000} s - nothing answered GET ${spec.state}`, { outcome: 'no-first-move' });
      }
      await sleep(100);
    }
  }
}
