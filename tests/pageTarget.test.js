// Sprint 2 UND-7 (ARCH §4, ADR-0007): a web page as a target - served from
// the example directory, opened headless, read through its accessibility
// snapshot and moved by role and name, with nothing added to the page.
// `make test` never launches Chromium: the browser here is a stand-in
// with the few Playwright calls the target makes.
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

const SNAPSHOT = `- heading "Sign up" [level=1]
- paragraph: Which plan would you like?
- button "Free"
- button "Pro (paid monthly)"
- combobox "Size":
  - option "Small" [selected]
  - option "Large"
- checkbox "Agree"`;

/**
 * A stand-in for Playwright's `chromium.launch`. `calls` records each
 * move as `[method, role, name]`; `failing` makes moves time out.
 */
function fakeLaunch({ snapshot = SNAPSHOT, failing = false } = {}) {
  const record = { browserClosed: false, url: null, calls: [] };
  const control = (role, { name }) => {
    const move = (method) => async (...parameters) => {
      if (failing) throw new Error('locator.click: Timeout 5000ms exceeded.\nCall log: ...');
      record.calls.push([method, role, name, ...parameters.slice(0, -1)]);
    };
    return { first: () => ({ click: move('click'), check: move('check'), selectOption: move('selectOption') }) };
  };
  const launch = async () => ({
    newPage: async () => ({
      goto: async (url) => { record.url = url; },
      url: () => record.url,
      locator: () => ({ ariaSnapshot: async () => snapshot }),
      getByRole: control,
      on: () => {},
      isClosed: () => false,
    }),
    close: async () => { record.browserClosed = true; },
  });
  return { launch, record };
}

const spec = { kind: 'page', root: '.', page: 'index.html' };

test('the page is opened from the local server and its view is what a person sees', async () => {
  const { launch, record } = fakeLaunch();
  const target = await startTarget(spec, { directory: WEB, launch });
  try {
    assert.match(record.url, /^http:\/\/127\.0\.0\.1:\d+\/index\.html$/);
    assert.equal(target.describe(), record.url);
    const view = await target.view();
    assert.equal(view.path, '/index.html');
    assert.equal(view.title, 'Sign up');
    assert.deepEqual(view.text, ['Sign up', 'Which plan would you like?']);
    assert.deepEqual(view.controls.map((each) => `${each.role}:${each.name}`),
      ['button:Free', 'button:Pro (paid monthly)', 'option:Small', 'option:Large', 'checkbox:Agree']);
    assert.equal(typeof view.seq, 'number');
    assert.deepEqual(await target.talk(), []);
    assert.equal(target.exited(), null);
  } finally {
    await target.close();
  }
  assert.equal(record.browserClosed, true);
});

test('a move uses the control by role and name: press, pick from a list, tick', async () => {
  const { launch, record } = fakeLaunch();
  const target = await startTarget(spec, { directory: WEB, launch });
  try {
    await target.act({ role: 'button', name: 'Pro (paid monthly)' });
    await target.act({ role: 'option', name: 'Large', list: 'Size' });
    await target.act({ role: 'checkbox', name: 'Agree' });
    assert.deepEqual(record.calls, [
      ['click', 'button', 'Pro (paid monthly)'],
      ['selectOption', 'combobox', 'Size', { label: 'Large' }],
      ['check', 'checkbox', 'Agree'],
    ]);
  } finally {
    await target.close();
  }
});

test('a control that is gone by the time of the move stops the run, naming it', async () => {
  const { launch } = fakeLaunch({ failing: true });
  const target = await startTarget(spec, { directory: WEB, launch });
  try {
    await assert.rejects(target.act({ role: 'button', name: 'Free' }), (error) => {
      assert.ok(error instanceof RunError);
      assert.equal(error.outcome, 'control-gone');
      assert.equal(error.message, 'could not press button "Free" - it is no longer on the page (locator.click: Timeout 5000ms exceeded.)');
      return true;
    });
  } finally {
    await target.close();
  }
});

test('no Chromium: refused before the run with the command that installs it, nothing left running', async () => {
  const launch = async () => { throw new Error("browserType.launch: Executable doesn't exist at /nowhere/chrome"); };
  await assert.rejects(startTarget(spec, { directory: WEB, launch, systemChromium: [] }), (error) => {
    assert.ok(error instanceof UsageError);
    assert.equal(error.message, 'Chromium is not installed - run: bobp make install-browser');
    return true;
  });
});
