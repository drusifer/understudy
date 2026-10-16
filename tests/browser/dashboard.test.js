// Sprint 6 UND-33 AC2 (docs/design/DASHBOARD.md): the console driven in
// headless Chromium against the real examples with a Jev double - pick the
// evening, move a fader, flip the switch, press Play, watch the tube move
// and the printer print the ticket.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
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
  await page.fill('#fader-row', '3');
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
  assert.deepEqual(errors, []);
});
