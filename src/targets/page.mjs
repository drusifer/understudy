// Sprint 1 UND-2 (ARCH §5, ADR-U2): a web page as a target.
//
// The example directory is served on 127.0.0.1, the page is opened in
// headless Chromium, and everything goes through the page's own hook,
// `window[hook]` (default `__understudy`): `view()` is the view (it
// carries its own `seq`), `act(action)` makes a move, and `talk()` /
// `say(text)` are the talk channel when the page has one. Generalized
// from recard's tests/harness/multiplayer.mjs (`startStaticServer`,
// `launchChromium`, `HarnessPeer`). Headless only (recard US-119).

import http from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { UsageError, RunError } from '../errors.mjs';

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp',
};
const SYSTEM_CHROMIUM = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome'];
const READY_MS = 10_000;

/**
 * Serves `root` on 127.0.0.1 (any free port); resolves `{ baseUrl, close() }`.
 * A path that resolves outside the root is a 404, a malformed `%` a 400
 * (recard US-152).
 * @param {string} root
 */
export async function startStaticServer(root) {
  const base = path.resolve(root);
  const server = http.createServer(async (request, response) => {
    const answer = (status, body) => {
      response.writeHead(status);
      response.end(body);
    };
    let pathname;
    try {
      pathname = decodeURIComponent(request.url.split('?', 1)[0]);
    } catch {
      return answer(400, 'bad request');
    }
    const filePath = path.resolve(base, `.${pathname === '/' ? '/index.html' : pathname}`);
    const inside = path.relative(base, filePath);
    if (inside === '..' || inside.startsWith(`..${path.sep}`) || path.isAbsolute(inside)) return answer(404, 'not found');
    try {
      const body = await readFile(filePath);
      response.writeHead(200, { 'Content-Type': MIME[path.extname(filePath)] ?? 'application/octet-stream' });
      response.end(body);
    } catch {
      answer(404, 'not found');
    }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  return {
    baseUrl: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise((resolve) => {
      server.closeAllConnections();
      server.close(resolve);
    }),
  };
}

async function playwrightLaunch(options) {
  const { chromium } = await import('playwright');
  return chromium.launch(options);
}

/**
 * Playwright's own Chromium, else a system install; neither is a
 * `UsageError` saying how to get one.
 */
async function launchChromium(launch, systemChromium) {
  // understudy owns Ctrl-C (it stops at a safe state), so Playwright must not.
  const options = { headless: true, args: ['--no-sandbox'], handleSIGINT: false, handleSIGTERM: false };
  try {
    return await launch(options);
  } catch (error) {
    for (const executablePath of systemChromium) {
      try {
        return await launch({ ...options, executablePath });
      } catch { /* try the next one */ }
    }
    if (/Executable doesn't exist|install/i.test(error.message)) throw new UsageError('Chromium is not installed - run: bobp make install-browser');
    throw new UsageError(`Chromium could not be started: ${error.message.split('\n', 1)[0]}`);
  }
}

/**
 * Calls `window[hook][method](argument)` in the page; `undefined` when the
 * hook has no such method (an optional one, like `talk`).
 */
function callHook({ hook, method, argument }) {
  const object = globalThis[hook];
  return typeof object?.[method] === 'function' ? object[method](argument) : undefined;
}

/**
 * What the page shows, for a message - empty when even that fails.
 */
async function pageText(page) {
  try {
    return await page.evaluate(() => globalThis.document.body?.textContent ?? '');
  } catch {
    return '';
  }
}

/**
 * Serves the example, opens its page and waits for its hook.
 * @param {{ kind: 'page', root?: string, page?: string, hook?: string }} spec
 * @param {{ directory: string, launch?: Function, systemChromium?: string[], readyMs?: number }} options
 */
export async function startTarget(spec, { directory, launch = playwrightLaunch, systemChromium = SYSTEM_CHROMIUM, readyMs = READY_MS }) {
  const hook = spec.hook ?? '__understudy';
  const server = await startStaticServer(path.resolve(directory, spec.root ?? '.'));
  const url = `${server.baseUrl}/${spec.page ?? 'index.html'}`;
  let browser = null;
  let isClosed = false;
  const close = async () => {
    if (isClosed) return;
    isClosed = true;
    await browser?.close();
    await server.close();
  };
  try {
    browser = await launchChromium(launch, systemChromium);
    const page = await browser.newPage();
    let crash = null;
    page.on('crash', () => { crash = { code: null, signal: 'page crashed' }; });
    await page.goto(url);
    try {
      await page.waitForFunction((name) => typeof globalThis[name]?.view === 'function', hook, { timeout: readyMs });
    } catch {
      const shown = await pageText(page);
      throw new RunError(`no first move from ${url} within ${readyMs / 1000} s - the page never exposed window.${hook} (it showed: ${JSON.stringify(String(shown).trim().slice(0, 120))})`, { outcome: 'no-first-move' });
    }
    const call = (method, argument) => page.evaluate(callHook, { hook, method, argument });
    return {
      describe: () => url,
      view: () => call('view'),
      act: (action) => call('act', action),
      talk: async () => (await call('talk')) ?? [],
      say: (text) => call('say', text),
      exited: () => crash ?? (!isClosed && page.isClosed() ? { code: null, signal: 'page closed' } : null),
      close,
    };
  } catch (error) {
    await close();
    throw error;
  }
}
