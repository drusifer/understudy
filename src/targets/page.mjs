// Sprint 1 UND-2, reworked in sprint 2 UND-7 (ARCH §4, ADR-0007): a web
// page as a target, played as a person would - with nothing added to it.
//
// The example directory is served on 127.0.0.1 and the page opened in
// headless Chromium. A look reads the page's accessibility snapshot (what a
// screen reader sees: its text and the controls a person could choose,
// `aria.mjs`); a move clicks, ticks or picks a control by its role and
// visible name. Generalized from recard's tests/harness/multiplayer.mjs
// (`startStaticServer`, `launchChromium`). Headless only (recard US-119).

import http from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { UsageError, RunError } from '../errors.mjs';
import { parseSnapshot } from './aria.mjs';

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp',
};
const SYSTEM_CHROMIUM = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome'];
const ACT_MS = 5000;

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
 * A short, stable fingerprint of a snapshot: it changes when the page does.
 */
function fingerprint(text) {
  let hash = 0;
  for (const character of text) hash = (hash * 31 + character.codePointAt(0)) % 2_147_483_647;
  return hash;
}

const VERBS = { button: 'press', link: 'follow', checkbox: 'tick', radio: 'pick', option: 'pick' };

/**
 * Makes one move: `{ role, name, list? }` - a control as the page names it.
 */
async function choose(page, { role, name, list }) {
  const options = { timeout: ACT_MS };
  try {
    if (role === 'option') {
      await page.getByRole('combobox', { name: list, exact: true }).first().selectOption({ label: name }, options);
    } else if (role === 'checkbox' || role === 'radio') {
      await page.getByRole(role, { name, exact: true }).first().check(options);
    } else {
      await page.getByRole(role, { name, exact: true }).first().click(options);
    }
  } catch (error) {
    throw new RunError(`could not ${VERBS[role] ?? 'use'} ${role} "${name}" - it is no longer on the page (${error.message.split('\n', 1)[0]})`, { outcome: 'control-gone', cause: error });
  }
}

/**
 * Headless Chromium as the page target starts it (Playwright's, else a
 * system one) - for the browser tests too.
 */
export async function launchHeadless() {
  return launchChromium(playwrightLaunch, SYSTEM_CHROMIUM);
}

/**
 * Serves the example and opens its page.
 * @param {{ kind: 'page', root?: string, page?: string }} spec
 * @param {{ directory: string, launch?: Function, systemChromium?: string[] }} options
 */
export async function startTarget(spec, { directory, launch = playwrightLaunch, systemChromium = SYSTEM_CHROMIUM }) {
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
    return {
      describe: () => url,
      async view() {
        const snapshot = await page.locator('body').ariaSnapshot();
        return { path: new URL(page.url()).pathname, ...parseSnapshot(snapshot), seq: fingerprint(snapshot) };
      },
      act: (control) => choose(page, control),
      talk: async () => [],
      async say() {},
      exited: () => crash ?? (!isClosed && page.isClosed() ? { code: null, signal: 'page closed' } : null),
      close,
    };
  } catch (error) {
    await close();
    throw error;
  }
}
