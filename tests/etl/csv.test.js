import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { prepareRun } from '../../src/etl/csv.mjs';

async function fixture() {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'understudy-csv-test-'));
  const monarchPath = path.join(directory, 'monarch.csv');
  const amexPath = path.join(directory, 'amex.csv');
  await writeFile(monarchPath, '\u{FEFF}Date,Amount,Merchant,Notes\n2026-01-02,12.50,"Cafe, Local",fixture\n');
  await writeFile(amexPath, 'Transaction Date,Transaction Amount,Description\n2026-01-02,12.50,Cafe Local\n');
  return { directory, monarchPath, amexPath };
}

test('validates, snapshots, hashes, and maps source headers without changing input files', async () => {
  const files = await fixture();
  try {
    const run = await prepareRun({
      monarchPath: files.monarchPath,
      amexPath: files.amexPath,
      runsDirectory: path.join(files.directory, 'runs'),
      runId: 'snapshot-test',
    });
    const original = await readFile(files.monarchPath);
    const snapshot = await readFile(path.join(run.runDirectory, 'inputs', 'monarch.csv'));
    const manifest = JSON.parse(await readFile(path.join(run.runDirectory, 'run.json'), 'utf8'));
    assert.deepEqual(snapshot, original);
    assert.equal(manifest.status, 'inputs_ready');
    assert.equal(manifest.inputs[0].sha256, createHash('sha256').update(original).digest('hex'));
    assert.equal(manifest.inputs[0].columns.merchant, 'Merchant');
    assert.equal(manifest.inputs[1].columns.date, 'Transaction Date');
    assert.equal(manifest.inputs[0].bytes, original.length);
  } finally {
    await rm(files.directory, { recursive: true, force: true });
  }
});

test('missing source file is named before any run directory is created', async () => {
  const files = await fixture();
  const runsDirectory = path.join(files.directory, 'runs');
  try {
    await assert.rejects(
      prepareRun({ monarchPath: path.join(files.directory, 'missing.csv'), amexPath: files.amexPath, runsDirectory, runId: 'missing' }),
      /Monarch CSV cannot be read/,
    );
    await assert.rejects(readFile(path.join(runsDirectory, 'missing', 'run.json')));
  } finally {
    await rm(files.directory, { recursive: true, force: true });
  }
});

test('missing required fields names the source and blocks both snapshots', async () => {
  const files = await fixture();
  const runsDirectory = path.join(files.directory, 'runs');
  await writeFile(files.monarchPath, 'Date,Merchant\n2026-01-02,Cafe\n');
  try {
    await assert.rejects(
      prepareRun({ monarchPath: files.monarchPath, amexPath: files.amexPath, runsDirectory, runId: 'bad-header' }),
      /Monarch CSV is missing a required amount column/,
    );
    await assert.rejects(readFile(path.join(runsDirectory, 'bad-header', 'run.json')));
  } finally {
    await rm(files.directory, { recursive: true, force: true });
  }
});
