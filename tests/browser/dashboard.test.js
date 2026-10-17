// Sprint 6 UND-33 AC2 (docs/design/DASHBOARD.md): the console driven in
// headless Chromium against the real examples with a Jev double - pick the
// evening, move a fader, flip the switch, press Play, watch the tube move
// and the printer print the ticket.
import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { serveDashboard } from '../../src/dashboard/console.mjs';
import { launchHeadless } from '../../src/targets/page.mjs';

const ORDER = ['tool:boxoffice/pay', 'tool:boxoffice/pick_seats', 'tool:ratings/rating', 'tool:boxoffice/seat_map', 'tool:boxoffice/list_films'];

function eveningJudge() {
  return {
    async systemOne(request) {
      await new Promise((resolve) => setTimeout(resolve, 40));
      const answers = {};
      for (const [key, question] of Object.entries(request.questions)) {
        if (question.type === 'score') {
          answers[key] = { type: 'score', score: /scream|best scare/.test(request.state.rows[key].reviews.join(' ')) ? 3 : 1 };
          continue;
        }
        const offered = Object.keys(question.criteria);
        const order = request.state.last_call?.tool === 'boxoffice/pick_seats' && !request.state.last_call.failed ? ORDER : ORDER.slice(1);
        const choice = key === 'next' ? order.find((id) => offered.some((each) => each.startsWith(id))) : 'v1';
        answers[key] = { type: 'choice', choice: offered.find((each) => each.startsWith(choice)) ?? offered[0], confidence: 0.9 };
      }
      return { answers };
    },
  };
}

const browser = await launchHeadless();
test.after(() => browser.close());

async function until(page, check, ms = 15_000) {
  await page.waitForFunction(check, null, { timeout: ms });
}

test('the console plays the evening: controls, Play, the tube follows, the printer prints the ticket', async () => {
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-dash-browser-'));
  const dashboard = await serveDashboard({
    folder: 'examples', port: 0, environment: { ...process.env, TYPESAFE_API_KEY: 'test' },
    runOptions: { makeJudge: () => eveningJudge(), logRoot, pollMs: 20, steps: 30 },
  });
  test.after(async () => {
    await dashboard.close();
    rmSync(logRoot, { recursive: true, force: true });
  });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  const errors = [];
  page.on('pageerror', (error) => {
    errors.push(error.message);
  });
  await page.goto(dashboard.url);
  await page.click('.sketch-tab:has-text("evening")');
  await until(page, () => document.querySelector('#sketch-title').textContent === 'evening');

  // Controls from the sketch's inputs (UND-28).
  assert.deepEqual(await page.$$eval('.dial-option', (options) => options.map((option) => option.textContent)), ['fun', 'serious', 'dramatic', 'romantic']);
  assert.equal(await page.$$eval('.fader', (faders) => faders.length), 4);
  await page.click('.dial-option:has-text("romantic")');
  assert.equal(await page.getAttribute('.dial-option:has-text("romantic")', 'aria-pressed'), 'true');
  await page.fill('#fader-centre', '1.5');
  assert.equal(await page.textContent('#fader-centre >> xpath=../..//div[contains(@class,"nixie")]'), '1.50');
  await page.fill('#fader-row', '10');
  assert.equal(await page.textContent('#fader-row >> xpath=../..//div[contains(@class,"nixie")]'), '11');
  await page.click('button[aria-label="tickets up"]');
  assert.equal(await page.textContent('.stepper-nixie'), '3', 'the brass stepper (UND-34 AC4)');
  const evenings = page.locator('.switch:has-text("evenings")');
  assert.equal(await evenings.getAttribute('aria-pressed'), 'true');

  // The tube draws every state of the turn (UND-30 AC1).
  assert.ok((await page.textContent('#tube .labels')).includes('walked away'));

  // Play (UND-29): the lamp turns, the controls lock, the run streams.
  await page.click('#play');
  await until(page, () => document.querySelector('#play-word').textContent === 'STOP');
  await until(page, () => document.querySelector('#paper').textContent.includes('Ticket issued'));
  await until(page, () => document.querySelector('#play-word').textContent === 'PLAY');
  const paper = await page.textContent('#paper');
  assert.match(paper, /inputs {2}mood=romantic .*centre=1\.5.*tickets=3/);
  assert.match(paper, /seats E\d+, E\d+, E\d+/, 'three seats together');
  assert.match(paper, /=== DONE after \d+ steps ===/);
  assert.ok((await page.$$eval('#paper .eleven', (cells) => cells.length)) > 0, 'a perfect 1.0 prints as 11');
  const tube = await page.getAttribute('#tube svg', 'aria-label');
  assert.ok(tube.endsWith('Now: booked.'), tube);

  // UND-39: STEP plays one move at a time; RESUME runs on; STOP ends it.
  const steps = () => page.$$eval('#paper .line', (nodes) => nodes.filter((node) => /^step \d+/.test(node.textContent.trim())).length);
  assert.equal(await page.isDisabled('#pause'), true, 'PAUSE only while a run plays');
  await page.click('#step');
  await until(page, () => document.querySelector('#tube-caption').textContent.startsWith('paused'));
  await until(page, () => document.querySelector('#ready-hint').textContent.includes('STEP for the next move'));
  const first = await steps();
  await page.click('#step');
  await until(page, () => document.querySelector('#tube-caption').textContent.startsWith('paused') && document.querySelector('#step').disabled === false);
  assert.equal(await page.textContent('#pause'), 'RESUME');
  // Exactly one move per STEP is held to in tests/dashboardRun.test.js; here, no run-away.
  assert.ok((await steps()) <= first + 1, 'one move per STEP');
  await page.click('#pause');
  await until(page, () => document.querySelector('#play-word').textContent === 'PLAY');
  assert.match(await page.textContent('#paper'), /=== DONE after \d+ steps ===/);
  assert.deepEqual(errors, []);
});

// Sprint 8 UND-35: take the printer off, edit the sketch behind it, watch the tube change.
test('behind the printer: the sketch\'s YAML and a sticker; typing saves and the tube redraws; a broken sketch is not saved', async () => {
  const folder = mkdtempSync(path.join(tmpdir(), 'understudy-dash-bay-'));
  cpSync('examples/cli', path.join(folder, 'cli'), { recursive: true });
  const file = path.join(folder, 'cli', 'sketch.yaml');
  const dashboard = await serveDashboard({ folder, port: 0, environment: { ...process.env, TYPESAFE_API_KEY: 'test' } });
  test.after(async () => {
    await dashboard.close();
    rmSync(folder, { recursive: true, force: true });
  });
  const page = await browser.newPage({ viewport: { width: 1600, height: 960 } });
  const errors = [];
  page.on('pageerror', (error) => {
    errors.push(error.message);
  });
  await page.goto(dashboard.url);
  await until(page, () => document.querySelector('#tube .labels')?.textContent.includes('replying'));

  // AC1, AC6: the OPEN latch swaps the printer for the bay; the sticker fits beside the edit box.
  assert.equal(await page.textContent('#open-printer'), 'OPEN');
  await page.focus('#open-printer');
  await page.keyboard.press('Enter');
  assert.equal(await page.isVisible('#printer'), false);
  await until(page, () => document.querySelector('#bay-text').value.includes('initial: waiting'));
  assert.equal(await page.inputValue('#bay-text'), readFileSync(file, 'utf8'));
  const sticker = await page.$eval('.sticker', (node) => ({ text: node.textContent, fits: node.scrollHeight <= node.clientHeight + 1, bottom: node.getBoundingClientRect().bottom }));
  for (const word of ['inputs', 'turn', 'choose', 'weight', 'count', 'switch', 'type: final']) assert.ok(sticker.text.includes(word), word);
  assert.ok(sticker.fits && sticker.bottom <= 960, 'the sticker shows whole on a 1600x960 screen');

  // AC2: typing saves a moment later; the tube shows the renamed state.
  const renamed = readFileSync(file, 'utf8').replaceAll('replying', 'responding');
  await page.fill('#bay-text', renamed);
  await until(page, () => document.querySelector('#tube .labels').textContent.includes('responding'));
  assert.equal(readFileSync(file, 'utf8'), renamed);

  // AC3: a sketch that fails its checks is not saved; the problem shows; the tube keeps the last good one.
  await page.fill('#bay-text', renamed.replace('initial: waiting', 'initial: nowhere'));
  await until(page, () => document.querySelector('#bay-problem').textContent.includes('nowhere'));
  assert.equal(await page.getAttribute('#bay-text', 'aria-invalid'), 'true');
  assert.equal(readFileSync(file, 'utf8'), renamed);
  assert.ok((await page.textContent('#tube .labels')).includes('responding'));

  // On a phone the bay drops down under the tube, one column, nothing wider than the screen (owner).
  await page.setViewportSize({ width: 390, height: 844 });
  for (const theme of ['steampunk', 'professional', 'starship']) {
    await page.click(`.theme-choice[data-theme="${theme}"]`);
    const phone = await page.evaluate(() => {
      const box = (selector) => document.querySelector(selector).getBoundingClientRect();
      return { wide: document.scrollingElement.scrollWidth, tube: box('.tube-panel'), bay: box('#bay'), controls: box('.controls') };
    });
    assert.ok(phone.wide <= 390, `${theme}: nothing scrolls sideways (${phone.wide}px)`);
    assert.ok(phone.bay.top >= phone.tube.bottom && phone.bay.bottom <= phone.controls.top, `${theme}: the bay sits between the tube and the controls`);
  }
  await page.setViewportSize({ width: 1600, height: 960 });

  // AC1, AC7: REFIT PRINTER puts the printer back.
  await page.click('#refit-printer');
  assert.equal(await page.isVisible('#printer'), true);
  assert.equal(await page.isVisible('#bay'), false);
  assert.deepEqual(errors, []);
});

// Sprint 9 UND-36: the themes - the switch restyles at once, is remembered, ?theme= wins,
// the console still plays, and it fits one 1600x960 screen.
test('the THEME switch: each theme restyles the page, is remembered, ?theme= wins, Play still runs, fits 1600x960', async () => {
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-dash-theme-'));
  const dashboard = await serveDashboard({
    folder: 'examples', port: 0, environment: { ...process.env, TYPESAFE_API_KEY: 'test' },
    runOptions: { makeJudge: () => eveningJudge(), logRoot, pollMs: 20, steps: 30 },
  });
  test.after(async () => {
    await dashboard.close();
    rmSync(logRoot, { recursive: true, force: true });
  });
  // A dark device, so AUTO shows each theme's dark look.
  const page = await browser.newPage({ viewport: { width: 1600, height: 960 }, colorScheme: 'dark' });
  const errors = [];
  page.on('pageerror', (error) => {
    errors.push(error.message);
  });
  const theme = () => page.evaluate(() => document.documentElement.dataset.theme);
  const background = () => page.evaluate(() => globalThis.getComputedStyle(document.body).backgroundColor);
  const fits = () => page.evaluate(() => document.scrollingElement.scrollHeight <= globalThis.innerHeight && document.scrollingElement.scrollWidth <= globalThis.innerWidth);
  await page.goto(dashboard.url);
  await until(page, () => document.querySelector('#tube svg'));
  assert.equal(await theme(), 'steampunk');
  assert.ok(await fits(), 'steampunk fits');
  const steampunk = await background();

  const seen = new Set([steampunk]);
  for (const name of ['professional', 'starship']) {
    await page.click(`.theme-choice[data-theme="${name}"]`);
    assert.equal(await theme(), name);
    assert.equal(await page.getAttribute(`.theme-choice[data-theme="${name}"]`, 'aria-pressed'), 'true');
    seen.add(await background());
    assert.ok(await fits(), `${name} fits 1600x960`);
  }
  assert.equal(seen.size, 3, 'each theme has its own background');

  // AC2: remembered across a reload; ?theme= wins; an unknown one is ignored.
  await page.click('.theme-choice[data-theme="professional"]');
  await page.reload();
  await until(page, () => document.querySelector('#tube svg'));
  assert.equal(await theme(), 'professional');
  await page.goto(`${dashboard.url}?theme=starship`);
  assert.equal(await theme(), 'starship');
  await page.goto(`${dashboard.url}?theme=tartan`);
  assert.equal(await theme(), 'professional');

  // AC1, AC5: a run keeps going through a theme change, and the controls work.
  await until(page, () => document.querySelector('.fader'));
  await page.click('#play');
  await until(page, () => document.querySelector('#play-word').textContent === 'STOP');
  await page.click('.theme-choice[data-theme="starship"]');
  await until(page, () => document.querySelector('#paper').textContent.includes('Ticket issued'));
  await until(page, () => document.querySelector('#play-word').textContent === 'PLAY');
  assert.deepEqual(errors, []);
});

// Sprint 11 UND-38: every theme in light and dark; AUTO follows the device.
const MODED = ['steampunk', 'professional', 'starship'];

test('the MODE switch: each theme has a light and a dark look, AUTO follows the device, ?mode= wins, remembered, fits', async () => {
  const dashboard = await serveDashboard({ folder: 'examples', port: 0, environment: { ...process.env, TYPESAFE_API_KEY: 'test' } });
  test.after(() => dashboard.close());
  const page = await browser.newPage({ viewport: { width: 1600, height: 960 }, colorScheme: 'light' });
  const errors = [];
  page.on('pageerror', (error) => {
    errors.push(error.message);
  });
  const mode = () => page.evaluate(() => document.documentElement.dataset.mode);
  const looks = () => page.evaluate(() => {
    const style = globalThis.getComputedStyle;
    return { page: style(document.body).backgroundColor, text: style(document.querySelector('.controls-head h2')).color };
  });
  const fits = () => page.evaluate(() => document.scrollingElement.scrollHeight <= globalThis.innerHeight && document.scrollingElement.scrollWidth <= globalThis.innerWidth);
  const narrow = () => page.evaluate(() => document.scrollingElement.scrollWidth <= globalThis.innerWidth);
  await page.goto(dashboard.url);
  await until(page, () => document.querySelector('#tube svg') && document.querySelector('.controls-head h2').textContent !== '…');

  // AC1: AUTO by default, following the device - and changing with it.
  assert.equal(await page.getAttribute('.mode-choice[data-mode="auto"]', 'aria-pressed'), 'true');
  assert.equal(await mode(), 'light');
  await page.emulateMedia({ colorScheme: 'dark' });
  await until(page, () => document.documentElement.dataset.mode === 'dark');

  // AC2, AC4: each theme, light and dark, looks different, keeps its text readable from its page, and fits.
  for (const name of MODED) {
    await page.click(`.theme-choice[data-theme="${name}"]`);
    const seen = {};
    for (const each of ['light', 'dark']) {
      await page.click(`.mode-choice[data-mode="${each}"]`);
      assert.equal(await mode(), each);
      seen[each] = await looks();
      assert.notEqual(seen[each].page, seen[each].text, `${name} ${each}: text differs from the page`);
      assert.ok(await fits(), `${name} ${each} fits 1600x960`);
      await page.setViewportSize({ width: 390, height: 844 });
      assert.ok(await narrow(), `${name} ${each}: nothing scrolls sideways on a phone`);
      await page.setViewportSize({ width: 1600, height: 960 });
    }
    assert.notEqual(seen.light.page, seen.dark.page, `${name}: light and dark differ`);
  }

  // AC1: remembered across a reload; ?mode= wins; an unknown one is ignored.
  await page.reload();
  await until(page, () => document.querySelector('#tube svg'));
  assert.equal(await mode(), 'dark');
  await page.goto(`${dashboard.url}?mode=light`);
  assert.equal(await mode(), 'light');
  await page.goto(`${dashboard.url}?mode=dim`);
  assert.equal(await mode(), 'dark');
  assert.deepEqual(errors, []);
});
