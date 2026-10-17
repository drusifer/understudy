// Sprint 6 UND-27 (ARCH §3, §5, ADR-0023): the dashboard's server - built
// like the watch page's (plain node:http, every file served locally,
// Server-Sent Events) but at the root, with no token in the URL (owner,
// 2026-10-16) - plus a small JSON API: the rack, one sketch's controls and
// its text, and - through `actions` - play, stop, edit, write, power.
// It only ever reads sketches by the names the folder's listing gives.

import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { UsageError } from '../errors.mjs';
import { listenOn, readBody } from '../watch/server.mjs';
import { describeSketch, listSketches, sketchNames } from './rack.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WATCH = path.join(HERE, '..', 'watch');
const FONTS = path.join(HERE, '..', '..', 'node_modules', '@fontsource');
const font = (file) => [path.join(FONTS, file.split('-', 1)[0], 'files', file), 'font/woff2'];
// A whole sketch's text fits (UND-35); the largest example is under 5 KB.
const MAX_BODY = 64 * 1024;
// The page's own files, and the watch page's pure modules it shares.
const FILES = {
  '': [path.join(HERE, 'page.html'), 'text/html; charset=utf-8'],
  'page.mjs': [path.join(HERE, 'page.mjs'), 'text/javascript; charset=utf-8'],
  'page.css': [path.join(HERE, 'page.css'), 'text/css; charset=utf-8'],
  'theme-professional.css': [path.join(HERE, 'theme-professional.css'), 'text/css; charset=utf-8'],
  'theme-starship.css': [path.join(HERE, 'theme-starship.css'), 'text/css; charset=utf-8'],
  'tube.mjs': [path.join(HERE, 'tube.mjs'), 'text/javascript; charset=utf-8'],
  'turnGraph.mjs': [path.join(WATCH, 'turnGraph.mjs'), 'text/javascript; charset=utf-8'],
  'watchPage.mjs': [path.join(WATCH, 'page.mjs'), 'text/javascript; charset=utf-8'],
  // The design's fonts, from the @fontsource packages (OFL), as page.css names them.
  'fonts/cinzel-700.woff2': font('cinzel-latin-700-normal.woff2'),
  'fonts/cinzel-900.woff2': font('cinzel-latin-900-normal.woff2'),
  'fonts/spectral-400.woff2': font('spectral-latin-400-normal.woff2'),
  'fonts/spectral-400-italic.woff2': font('spectral-latin-400-italic.woff2'),
  'fonts/vt323-400.woff2': font('vt323-latin-400-normal.woff2'),
  'fonts/dotgothic16-400.woff2': font('dotgothic16-latin-400-normal.woff2'),
  'fonts/antonio-400.woff2': font('antonio-latin-400-normal.woff2'),
  'fonts/antonio-700.woff2': font('antonio-latin-700-normal.woff2'),
};

const json = (response, status, value) => response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }).end(JSON.stringify(value));
const refuse = (response, status, problem) => json(response, status, { problem });

/**
 * Lines for every open page: the current run's so far, then each new one.
 */
export function createHub() {
  const clients = new Set();
  let history = [];
  return {
    // A new run starts: pages that join later see it from its start.
    reset() {
      history = [];
    },
    send(line) {
      history.push(line);
      for (const response of clients) response.write(`data: ${JSON.stringify(line)}\n\n`);
    },
    join(request, response) {
      response.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
      response.write(`data: ${JSON.stringify({ event: 'hello' })}\n\n`);
      for (const line of history) response.write(`data: ${JSON.stringify(line)}\n\n`);
      clients.add(response);
      request.on('close', () => clients.delete(response));
    },
    close() {
      for (const response of clients) response.end();
    },
  };
}

/**
 * Starts the dashboard for `folder`.
 * @param {{ folder: string, port?: number, host?: string, hub?: ReturnType<typeof createHub>,
 *   actions?: Record<string, (body: object) => Promise<{ status: number, value?: object }>> }} options
 *   `actions`: the POST endpoints (play, stop, edit, write, power), each given the parsed body.
 * @returns {Promise<{ url: string, urls: string[], hub: object, close: () => Promise<void> }>}
 */
export async function startDashboard({ folder, port = 0, host = '127.0.0.1', hub = createHub(), actions = {} }) {
  await listSketches(folder); // refuses a folder with no sketches before anything listens
  const base = '/';

  // The GET endpoints: the rack, one sketch's controls, one sketch's text.
  const read = async (response, rest) => {
    if (rest === 'api/sketches') return json(response, 200, await listSketches(folder));
    // UND-35: a sketch's file as it is, for the bay - even one that fails its checks.
    if (rest.startsWith('api/text/')) {
      const name = decodeURIComponent(rest.slice('api/text/'.length));
      if (!sketchNames(folder).includes(name)) return refuse(response, 404, `no sketch "${name}" in ${folder}`);
      return json(response, 200, { text: await readFile(path.join(folder, name, 'sketch.yaml'), 'utf8') });
    }
    if (!rest.startsWith('api/sketch/')) return refuse(response, 404, 'not found');
    const name = decodeURIComponent(rest.slice('api/sketch/'.length));
    try {
      return json(response, 200, await describeSketch(folder, name));
    } catch (error) {
      if (error instanceof UsageError) return refuse(response, 404, error.message);
      throw error;
    }
  };

  const api = async (request, response, rest) => {
    if (request.method === 'GET') return read(response, rest);
    const verb = rest.slice('api/'.length);
    const action = request.method === 'POST' && Object.hasOwn(actions, verb) ? actions[verb] : undefined;
    if (!action) return refuse(response, 404, 'not found');
    let body;
    try {
      body = JSON.parse((await readBody(request, MAX_BODY)) || '{}');
    } catch {
      return refuse(response, 400, 'the request was not readable JSON (64 KB at most)');
    }
    const { status, value = {} } = await action(body);
    return json(response, status, value);
  };

  const server = http.createServer(async (request, response) => {
    const { pathname } = new URL(request.url, 'http://localhost');
    if (!pathname.startsWith(base)) return response.writeHead(404).end('not found');
    const rest = pathname.slice(base.length);
    try {
      if (rest === 'events' && request.method === 'GET') return hub.join(request, response);
      if (rest.startsWith('api/')) return await api(request, response, rest);
      const file = request.method === 'GET' ? FILES[rest] : undefined;
      if (!file) return response.writeHead(404).end('not found');
      const body = await readFile(file[0]);
      return response.writeHead(200, { 'Content-Type': file[1], 'Cache-Control': 'no-store' }).end(body);
    } catch (error) {
      if (response.headersSent) return response.end();
      return refuse(response, 500, `the dashboard could not do that: ${error.message}`);
    }
  });

  const urls = await listenOn(server, { port, host, base });
  return {
    url: urls[0], urls, hub,
    close: () => new Promise((resolve) => {
      hub.close();
      server.closeAllConnections();
      server.close(() => resolve());
    }),
  };
}
