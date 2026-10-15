// Sprint 1 UND-2 (ARCH §5, ADR-U2): a web page as a target - served from
// the example directory, opened headless, driven through its
// `window[hook]`. `make test` never launches Chromium: the browser here
// is a stand-in with the few Playwright calls the target makes.
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { startTarget, startStaticServer } from '../src/targets/page.mjs';
import { UsageError, RunError } from '../src/errors.mjs';

const WEB = fileURLToPath(new URL('../examples/web', import.meta.url));

function get(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (response) => {
      let body = '';
      response.on('data', (chunk) => { body += chunk; });
      response.on('end', () => resolve({ status: response.statusCode, type: response.headers['content-type'], body }));
    }).on('error', reject);
  });
}

test('the static server serves the example, and nothing outside it', async () => {
  const server = await startStaticServer(WEB);
  try {
    const page = await get(`${server.baseUrl}/`);
    assert.equal(page.status, 200);
    assert.equal(page.type, 'text/html');
    assert.equal((await get(`${server.baseUrl}/app.js`)).type, 'text/javascript');
    assert.equal((await get(`${server.baseUrl}/../../package.json`)).status, 404);
    assert.equal((await get(`${server.baseUrl}/%2e%2e/%2e%2e/package.json`)).status, 404);
    assert.equal((await get(`${server.baseUrl}/%E0%A4%A`)).status, 400);
    assert.equal((await get(`${server.baseUrl}/missing.html`)).status, 404);
  } finally {
    await server.close();
  }
});

/**
 * A stand-in for Playwright's `chromium.launch`, recording what was
 * closed. `page` overrides the fake page's behaviour.
 */
function fakeLaunch(page = {}) {
  const record = { browserClosed: false, url: null, evaluated: [] };
  const launch = async () => ({
    newPage: async () => ({
      goto: async (url) => { record.url = url; },
      waitForFunction: async () => {},
      evaluate: async (function_, argument) => {
        record.evaluated.push(argument);
        return page.evaluate ? page.evaluate(argument) : { screen: 'plan', seq: 1 };
      },
      on: () => {},
      isClosed: () => false,
      ...page,
    }),
    close: async () => { record.browserClosed = true; },
  });
  return { launch, record };
}

const spec = { kind: 'page', root: '.', page: 'index.html', hook: '__understudy' };

test('the page is opened from the local server and driven through its hook', async () => {
  const { launch, record } = fakeLaunch();
  const target = await startTarget(spec, { directory: WEB, launch });
  try {
    assert.match(record.url, /^http:\/\/127\.0\.0\.1:\d+\/index\.html$/);
    assert.equal(target.describe(), record.url);
    assert.deepEqual(await target.view(), { screen: 'plan', seq: 1 });
    await target.act({ press: 'pro' });
    assert.deepEqual(record.evaluated.at(-1), { hook: '__understudy', method: 'act', argument: { press: 'pro' } });
    assert.equal(target.exited(), null);
  } finally {
    await target.close();
  }
  assert.equal(record.browserClosed, true);
});

test('no Chromium: refused before the run with the command that installs it, nothing left running', async () => {
  const launch = async () => { throw new Error("browserType.launch: Executable doesn't exist at /nowhere/chrome"); };
  await assert.rejects(startTarget(spec, { directory: WEB, launch, systemChromium: [] }), (error) => {
    assert.ok(error instanceof UsageError);
    assert.equal(error.message, 'Chromium is not installed - run: bobp make install-browser');
    return true;
  });
});

test('a page that never exposes its hook stops the run naming the URL and what it showed; browser closed', async () => {
  const { launch, record } = fakeLaunch({
    waitForFunction: async () => { throw new Error('page.waitForFunction: Timeout 10000ms exceeded.'); },
    evaluate: async () => 'Loading...',
  });
  await assert.rejects(startTarget(spec, { directory: WEB, launch, readyMs: 10_000 }), (error) => {
    assert.ok(error instanceof RunError);
    assert.equal(error.outcome, 'no-first-move');
    assert.match(error.message, /^no first move from http:\/\/127\.0\.0\.1:\d+\/index\.html within 10 s - the page never exposed window\.__understudy \(it showed: "Loading\.\.\."\)$/);
    return true;
  });
  assert.equal(record.browserClosed, true);
});
