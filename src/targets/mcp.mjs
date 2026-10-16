// Sprint 3 UND-10/11 (ARCH §4, ADR-0012): an MCP server as a target, with
// understudy as its client (`@modelcontextprotocol/sdk`'s `Client`).
//
// A look lists the server's tools and carries the last call's result; a
// move is one tool call. A tool that answers with an error - a result
// with `isError`, or a JSON-RPC error - is the app's answer: returned and
// logged, never thrown. Only losing the server stops the run. A local
// server (stdio) is started in the sketch directory through
// `program.mjs`; a remote one (`type: http`) is contacted at its URL and
// left running.

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport, StreamableHTTPError } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { ErrorCode, McpError } from '@modelcontextprotocol/sdk/types.js';
import { RunError } from '../errors.mjs';
import { expandEntry } from '../mcpConfig.mjs';
import { startProgram } from './program.mjs';
import { ProgramTransport } from './mcpTransport.mjs';

const HANDSHAKE_MS = 10_000;
const RETRY_MS = 250;
const RESULT_CHARS = 2000;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const newClient = () => new Client({ name: 'understudy', version: '0.1.0' });

async function closeQuietly(client) {
  try {
    await client.close();
  } catch { /* already gone */ }
}

/**
 * A result's text content, joined.
 */
function textOf(result) {
  return (result.content ?? []).filter((part) => part.type === 'text').map((part) => part.text).join('\n');
}

const stderrOf = (program) => {
  const tail = program.stderrTail().filter((line) => line.trim() !== '').slice(-5);
  return tail.length > 0 ? ` - it printed: ${tail.join(' | ')}` : ' - it printed nothing on stderr';
};

/**
 * Starts the server and completes the MCP handshake within `handshakeMs`.
 */
async function startLocal(entry, { directory, environment, handshakeMs }) {
  const program = await startProgram(entry, { directory, environment: { ...environment, ...entry.env } });
  const client = newClient();
  let timer;
  const exited = (async () => {
    await program.ended;
    return 'exited';
  })();
  const timedOut = new Promise((resolve) => { timer = setTimeout(() => resolve('timeout'), handshakeMs); });
  const connected = (async () => {
    try {
      await client.connect(new ProgramTransport(program), { timeout: handshakeMs });
      return 'connected';
    } catch {
      return 'failed';
    }
  })();
  const how = await Promise.race([connected, exited, timedOut]);
  clearTimeout(timer);
  if (how === 'connected') return { client, program, describe: () => program.description };
  await program.close();
  const ended = program.exited();
  if (how === 'exited' || (how === 'failed' && ended)) {
    throw new RunError(`${program.description} exited with code ${ended?.code ?? ended?.signal} before the MCP handshake${stderrOf(program)}`, { outcome: 'app-exited' });
  }
  throw new RunError(`no first move from ${program.description}: it did not answer the MCP handshake within ${handshakeMs / 1000} s${stderrOf(program)}`, { outcome: 'no-first-move' });
}

/**
 * Connects to a running server at `entry.url` with its headers, trying
 * again while nothing answers, for up to `handshakeMs`. A server that
 * answers with an HTTP error has refused: that is final. The URL is
 * shown filled in; header values (tokens) are never shown.
 */
async function startRemote(entry, { shownUrl, handshakeMs, retryMs }) {
  let url;
  try {
    url = new URL(entry.url);
  } catch {
    throw new RunError(`${shownUrl} is not a URL`, { outcome: 'no-first-move' });
  }
  const deadline = Date.now() + handshakeMs;
  for (;;) {
    const client = newClient();
    const transport = new StreamableHTTPClientTransport(url, { requestInit: { headers: entry.headers ?? {} } });
    try {
      await client.connect(transport, { timeout: Math.max(100, deadline - Date.now()) });
      return { client, describe: () => shownUrl };
    } catch (error) {
      await closeQuietly(client);
      if (error instanceof StreamableHTTPError && error.code >= 400) {
        throw new RunError(`the MCP server at ${shownUrl} refused the connection (HTTP ${error.code})`, { outcome: 'refused' });
      }
      if (Date.now() >= deadline) {
        const why = error.cause?.code ?? error.message;
        throw new RunError(`no first move from ${shownUrl}: nothing answered within ${handshakeMs / 1000} s (${why})`, { outcome: 'no-first-move' });
      }
      await sleep(retryMs);
    }
  }
}

/**
 * Connects to the server named by `spec.entry` (`${VAR}` filled first):
 * starts a local one, or reaches a remote one (`type: http`).
 * @param {{ kind: 'mcp', entry: object, from: string }} spec
 * @param {{ directory: string, environment?: object, handshakeMs?: number, retryMs?: number }} options
 */
export async function startTarget(spec, { directory, environment = process.env, handshakeMs = HANDSHAKE_MS, retryMs = RETRY_MS }) {
  const entry = expandEntry(spec.entry, environment, spec.from);
  const { client, program = null, describe } = entry.type === 'http'
    ? await startRemote(entry, { shownUrl: entry.url, handshakeMs, retryMs })
    : await startLocal(entry, { directory, environment, handshakeMs });
  const state = { last: null, seq: 0, shown: undefined };

  /**
   * A failure that is not the server's answer: the server is gone.
   */
  const lost = (error) => {
    const ended = program?.exited();
    if (ended) return new RunError(`${describe()} exited with code ${ended.code ?? ended.signal} before the end state${stderrOf(program)}`, { outcome: 'app-exited', cause: error });
    return new RunError(`lost the connection to ${describe()}: ${error.message}`, { outcome: 'connection-lost', cause: error });
  };
  const isAnswer = (error) => error instanceof McpError && error.code !== ErrorCode.ConnectionClosed && error.code !== ErrorCode.RequestTimeout && !program?.exited();

  return {
    describe,
    async view() {
      const tools = [];
      try {
        let cursor;
        do {
          const page = await client.listTools(cursor ? { cursor } : undefined);
          tools.push(...page.tools.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })));
          cursor = page.nextCursor;
        } while (cursor);
      } catch (error) {
        throw lost(error);
      }
      const shown = JSON.stringify([tools, state.last]);
      if (shown !== state.shown) {
        state.shown = shown;
        state.seq += 1;
      }
      return { tools, last: state.last, seq: state.seq, exited: program?.exited() ?? null };
    },
    async act({ tool, arguments: arguments_ = {} }) {
      let answer;
      try {
        const result = await client.callTool({ name: tool, arguments: arguments_ });
        answer = { isError: result.isError === true, text: textOf(result), ...(result.structuredContent && { structured: result.structuredContent }) };
      } catch (error) {
        if (!isAnswer(error)) throw lost(error);
        answer = { isError: true, text: error.message };
      }
      state.last = { tool, arguments: arguments_, ...answer };
      return { call: { tool, arguments: arguments_ }, isError: answer.isError, text: answer.text.slice(0, RESULT_CHARS) };
    },
    talk: async () => [],
    async say() {},
    exited: () => program?.exited() ?? null,
    async close() {
      await closeQuietly(client);
      await program?.close();
    },
  };
}
