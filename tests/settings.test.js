// Sprint 6 UND-32 (ARCH §4 "Save an edit", ADR-0024/0025): access-panel edits
// saved to the sketch with its comments kept, refused when the checks would
// refuse them, and put back by the factory reset.
import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { checkSketch } from '../src/sketch.mjs';
import { createSettings } from '../src/dashboard/settings.mjs';

function folder() {
  const root = mkdtempSync(path.join(tmpdir(), 'understudy-settings-'));
  test.after(() => rmSync(root, { recursive: true, force: true }));
  cpSync('examples/evening', path.join(root, 'evening'), { recursive: true });
  return root;
}

const CENTRE_RANGE = ['decide', 'boxoffice/pick_seats.seat', 'scores', 'centre', 'range'];

test('an edit is saved; the file keeps its comments and still checks (UND-32 AC1-2)', async () => {
  const root = folder();
  const settings = createSettings({ folder: root });
  const file = path.join(root, 'evening', 'sketch.yaml');
  const before = readFileSync(file, 'utf8');
  const saved = await settings.edit({ sketch: 'evening', changes: [{ path: CENTRE_RANGE, value: [0.4, 1] }, { path: ['inputs', 'centre', 'default'], value: 2 }] });
  assert.deepEqual(saved, { status: 200, value: { ok: true } });
  const after = readFileSync(file, 'utf8');
  assert.ok(after.includes('      centre: { range: [0.4, 1], weight: centre }'));
  assert.ok(after.includes('  centre: { weight: [0, 10], default: 2 }'));
  const changed = after.split('\n').filter((line, index) => line !== before.split('\n')[index]);
  assert.equal(changed.length, 2, 'only the two edited lines change');
  assert.ok(after.includes('# The evening example\'s sketch'), 'comments kept');
  assert.equal(after.split('\n').length, before.split('\n').length, 'layout kept');
  assert.match(await checkSketch(path.join(root, 'evening')), /sketch OK/);
});

test('moods are renamed with their default in one edit; a refused edit writes nothing and says why (UND-32 AC3)', async () => {
  const root = folder();
  const settings = createSettings({ folder: root });
  const file = path.join(root, 'evening', 'sketch.yaml');
  const renamed = await settings.edit({ sketch: 'evening', changes: [
    { path: ['inputs', 'mood', 'choose'], value: ['cheerful', 'serious', 'dramatic'] }, { path: ['inputs', 'mood', 'default'], value: 'cheerful' },
  ] });
  assert.equal(renamed.status, 200);
  const before = readFileSync(file, 'utf8');
  const refused = await settings.edit({ sketch: 'evening', changes: [{ path: CENTRE_RANGE, value: [1, 1] }] });
  assert.deepEqual(refused, { status: 422, value: { problem: 'decide.boxoffice/pick_seats.seat.scores.centre.range: must be two different numbers or HH:MM times, e.g. [0.3, 1]' } });
  const outOfRange = await settings.edit({ sketch: 'evening', changes: [{ path: ['inputs', 'centre', 'default'], value: 12 }] });
  assert.equal(outOfRange.value.problem, 'inputs.centre.default: must be between 0 and 10, got 12');
  assert.equal(readFileSync(file, 'utf8'), before);
});

test('only the panels\' settings can change, only in the folder\'s sketches', async () => {
  const settings = createSettings({ folder: folder() });
  assert.equal((await settings.edit({ sketch: 'evening', changes: [{ path: ['target', 'kind'], value: 'process' }] })).status, 400);
  assert.equal((await settings.edit({ sketch: '../evening', changes: [{ path: CENTRE_RANGE, value: [0.4, 1] }] })).status, 404);
});

test('the factory reset puts every edited sketch back and forgets the copies (UND-32 AC4)', async () => {
  const root = folder();
  const settings = createSettings({ folder: root });
  const file = path.join(root, 'evening', 'sketch.yaml');
  const factory = readFileSync(file, 'utf8');
  await settings.edit({ sketch: 'evening', changes: [{ path: CENTRE_RANGE, value: [0.4, 1] }] });
  await settings.edit({ sketch: 'evening', changes: [{ path: CENTRE_RANGE, value: [0.5, 1] }] });
  assert.equal(readFileSync(path.join(root, '.factory', 'evening.yaml'), 'utf8'), factory, 'the copy is from before the first edit');
  assert.deepEqual(settings.restore(), ['evening']);
  assert.equal(readFileSync(file, 'utf8'), factory);
  assert.equal(existsSync(path.join(root, '.factory')), false);
  assert.deepEqual(settings.restore(), []);
});

// Sprint 8 UND-35 (ADR-0028): the bay behind the printer writes the whole file.
test('the bay writes the whole file as typed, keeping the factory copy (UND-35 AC2)', async () => {
  const root = folder();
  const settings = createSettings({ folder: root });
  const file = path.join(root, 'evening', 'sketch.yaml');
  const factory = readFileSync(file, 'utf8');
  const text = factory.replace('name: evening', 'name: late evening\n# typed in the bay');
  assert.deepEqual(await settings.write({ sketch: 'evening', text }), { status: 200, value: { ok: true } });
  assert.equal(readFileSync(file, 'utf8'), text);
  assert.equal(readFileSync(path.join(root, '.factory', 'evening.yaml'), 'utf8'), factory);
  assert.deepEqual(settings.restore(), ['evening']);
  assert.equal(readFileSync(file, 'utf8'), factory);
});

test('a write that fails the checks writes nothing and says why, without the path (UND-35 AC3)', async () => {
  const root = folder();
  const settings = createSettings({ folder: root });
  const file = path.join(root, 'evening', 'sketch.yaml');
  const before = readFileSync(file, 'utf8');
  const unknownState = await settings.write({ sketch: 'evening', text: before.replace('initial: waiting', 'initial: nowhere') });
  assert.equal(unknownState.status, 422);
  assert.match(unknownState.value.problem, /nowhere/);
  assert.doesNotMatch(unknownState.value.problem, /understudy-edit-|sketch\.yaml/);
  const broken = await settings.write({ sketch: 'evening', text: before.replace('turn:', 'turn: [') });
  assert.equal(broken.status, 422);
  assert.equal(readFileSync(file, 'utf8'), before);
  assert.equal(existsSync(path.join(root, '.factory')), false, 'no factory copy for a refused write');
  assert.equal((await settings.write({ sketch: '../evening', text: before })).status, 404);
  assert.equal((await settings.write({ sketch: 'evening' })).status, 400);
});
