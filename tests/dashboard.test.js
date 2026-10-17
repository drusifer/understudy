// Sprint 6 UND-27 (ARCH §3, §5, ADR-0023): the dashboard's rack and server -
// a folder's sketches over a token path, one sketch's controls, refusals.
import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { UsageError } from '../src/errors.mjs';
import { describeSketch, listSketches, sketchNames } from '../src/dashboard/rack.mjs';
import { startDashboard } from '../src/dashboard/server.mjs';

/**
 * A folder holding two real examples and one broken sketch.
 */
function folder() {
  const root = mkdtempSync(path.join(tmpdir(), 'understudy-rack-'));
  test.after(() => rmSync(root, { recursive: true, force: true }));
  cpSync('examples/cli', path.join(root, 'cli'), { recursive: true });
  mkdirSync(path.join(root, 'broken'));
  writeFileSync(path.join(root, 'broken', 'sketch.yaml'), 'name: broken\n');
  mkdirSync(path.join(root, 'notes'));
  return root;
}

test('the rack lists every sketch directory; a broken one says why (UND-27 AC1-2)', async () => {
  const root = folder();
  assert.deepEqual(sketchNames(root), ['broken', 'cli']);
  const rack = await listSketches(root);
  assert.equal(rack[1].name, 'cli');
  assert.equal(rack[1].ok, true);
  assert.match(rack[1].description, /^An understudy/);
  assert.equal(rack[0].ok, false);
  assert.match(rack[0].problem, /broken\/sketch\.yaml: questions: needs a mapping/);
});

test('a path that is not a folder of sketches is refused (UND-27 AC4)', () => {
  assert.throws(() => sketchNames('examples/cli/app.mjs'), new UsageError('examples/cli/app.mjs is not a folder of sketches - give a folder holding sketch directories, e.g. examples'));
  assert.throws(() => sketchNames('docs'), /docs holds no sketches/);
});

test('the evening sketch is described as controls: a mood dial, weights with their factors, its statechart', async () => {
  const evening = await describeSketch('examples', 'evening');
  const mood = evening.inputs.find((input) => input.name === 'mood');
  assert.deepEqual(mood, { name: 'mood', kind: 'choose', options: ['fun', 'serious', 'dramatic', 'romantic'], default: 'fun' });
  const centre = evening.inputs.find((input) => input.name === 'centre');
  assert.deepEqual(centre.range, [0, 10]);
  assert.deepEqual(centre.factors, [{ argument: 'boxoffice/pick_seats.seat', field: 'centre', range: [0.3, 1], weight: 'centre' }]);
  const audience = evening.inputs.find((input) => input.name === 'audience');
  assert.equal(audience.factors[0].looks_at, 'reviews');
  assert.ok(evening.graph.nodes.some((node) => node.id === 'walked_away' && node.final));
  assert.deepEqual(evening.decision.map((index) => evening.graph.edges[index].to), ['acting']);
  await assert.rejects(describeSketch('examples', '../src'), /no sketch "\.\.\/src" in examples/);
});

test('the server: token path, the rack and a sketch as JSON, 404 elsewhere (UND-27 AC1, AC5)', async () => {
  const dashboard = await startDashboard({ folder: 'examples', port: 0 });
  test.after(() => dashboard.close());
  assert.match(dashboard.url, /^http:\/\/127\.0\.0\.1:\d+\/d\/[\w-]{16}\/$/);
  const page = await fetch(dashboard.url);
  assert.equal(page.status, 200);
  assert.match(await page.text(), /Understudy operations console/);
  const rack = await (await fetch(`${dashboard.url}api/sketches`)).json();
  assert.ok(rack.some((each) => each.name === 'evening'));
  const evening = await (await fetch(`${dashboard.url}api/sketch/evening`)).json();
  assert.equal(evening.title, 'evening');
  const missing = await fetch(`${dashboard.url}api/sketch/nope`);
  assert.equal(missing.status, 404);
  assert.deepEqual(await missing.json(), { problem: 'no sketch "nope" in examples' });
  assert.equal((await fetch(dashboard.url.replace(/\/d\/[^/]+\//, '/d/wrong/'))).status, 404);
  assert.equal((await fetch(`${dashboard.url}api/play`, { method: 'POST', body: '{}' })).status, 404, 'no actions wired');
});

test('a folder without sketches is refused before anything listens', async () => {
  await assert.rejects(startDashboard({ folder: 'docs', port: 0 }), UsageError);
});
