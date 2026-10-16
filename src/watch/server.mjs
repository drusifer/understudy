// Sprint 4 UND-14/16 (ARCH §3, §5, ADR-0015): the watch page's server -
// plain node:http on 127.0.0.1, every path under an unguessable per-run
// token. It serves the page's own files (nothing from the internet) and
// streams the run's lines as Server-Sent Events: everything so far, then
// each new line, then `end` after the final line. In a live run it also
// takes the page's pause / step / resume.

import http from 'node:http';
import { randomBytes } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { UsageError } from '../errors.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FILES = {
  '': ['page.html', 'text/html; charset=utf-8'],
  'page.mjs': ['page.mjs', 'text/javascript; charset=utf-8'],
  'turnGraph.mjs': ['turnGraph.mjs', 'text/javascript; charset=utf-8'],
  'layout.mjs': ['layout.mjs', 'text/javascript; charset=utf-8'],
  'page.css': ['page.css', 'text/css; charset=utf-8'],
};
const ACTIONS = new Set(['pause', 'step', 'resume']);
const END = 'event: end\ndata: {}\n\n';

function sendTo(response, line) {
  response.write(`data: ${JSON.stringify(line)}\n\n`);
  if (line.final) response.write(END);
}
const MAX_BODY = 1024;

function readBody(request) {
  return new Promise((resolve, reject) => {
    let body = '';
    request.setEncoding('utf8');
    request.on('data', (chunk) => {
      body += chunk;
      if (body.length > MAX_BODY) reject(new Error('too large'));
    });
    request.on('end', () => resolve(body));
    request.on('error', reject);
  });
}

/**
 * Starts the server.
 * @param {{ port?: number, mode: 'live'|'replay', source: { listen: (fn: (line: object) => void) => () => void },
 *   control?: (action: string) => boolean }} options
 *   `source` is the run's stream (or a log, for replay); `control` applies a
 *   page action and says whether it applied.
 * @returns {Promise<{ url: string, send: (line: object) => void, close: () => Promise<void> }>}
 */
export async function startWatch({ port = 0, mode, source, control = null }) {
  const token = randomBytes(12).toString('base64url');
  const base = `/w/${token}/`;
  const clients = new Set();
  let latest = null; // the newest live-only line (pause state), for pages that join later

  const events = (request, response) => {
    response.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
    response.write(`data: ${JSON.stringify({ event: 'hello', mode })}\n\n`);
    let isEnded = false;
    const stop = source.listen((line) => {
      isEnded ||= line.final === true;
      sendTo(response, line);
    });
    // A replayed log is all there is, even one that stops without a final line.
    if (mode === 'replay' && !isEnded) response.write(END);
    if (latest) sendTo(response, latest);
    clients.add(response);
    request.on('close', () => {
      stop();
      clients.delete(response);
    });
  };

  const act = async (request, response) => {
    let action;
    try {
      ({ action } = JSON.parse(await readBody(request)));
    } catch {
      return response.writeHead(400).end('bad request');
    }
    if (mode !== 'live' || !ACTIONS.has(action) || !control?.(action)) return response.writeHead(409).end('not now');
    return response.writeHead(204).end();
  };

  const server = http.createServer(async (request, response) => {
    const { pathname } = new URL(request.url, 'http://localhost');
    if (!pathname.startsWith(base)) return response.writeHead(404).end('not found');
    const rest = pathname.slice(base.length);
    if (rest === 'events' && request.method === 'GET') return events(request, response);
    if (rest === 'control' && request.method === 'POST') return act(request, response);
    const file = request.method === 'GET' ? FILES[rest] : undefined;
    if (!file) return response.writeHead(404).end('not found');
    try {
      const body = await readFile(path.join(HERE, file[0]));
      return response.writeHead(200, { 'Content-Type': file[1], 'Cache-Control': 'no-store' }).end(body);
    } catch {
      return response.writeHead(404).end('not found');
    }
  });

  await new Promise((resolve, reject) => {
    server.once('error', (error) => {
      reject(error.code === 'EADDRINUSE' ? new UsageError(`port ${port} is in use - choose another with --port`) : error);
    });
    server.listen(port, '127.0.0.1', resolve);
  });

  return {
    url: `http://127.0.0.1:${server.address().port}${base}`,
    /**
     * A live-only line (the pause state) to every open page.
     */
    send(line) {
      latest = line;
      for (const response of clients) sendTo(response, line);
    },
    close: () => new Promise((resolve) => {
      for (const response of clients) response.end();
      server.closeAllConnections();
      server.close(() => resolve());
    }),
  };
}

/**
 * A finished log as a source: every line at once, nothing after.
 * @param {object[]} lines
 */
export function logSource(lines) {
  return {
    listen(listener) {
      for (const line of lines) listener(line);
      return stopNothing;
    },
  };
}

function stopNothing() {}
