import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runEtl } from '../../src/etl/run.mjs';

const monarchPath = fileURLToPath(new URL('../fixtures/etl/monarch.csv', import.meta.url));
const amexPath = fileURLToPath(new URL('../fixtures/etl/amex.csv', import.meta.url));

function categoryJudge() {
  const calls = [];
  return {
    calls,
    async systemOne(request) {
      calls.push(request);
      const answers = {};
      for (const [id, merchant] of Object.entries(request.state.merchants)) {
        let choice;
        switch (merchant.descriptor) {
          case 'Cafe, Local': {
            choice = 'Food & Dining::Coffee';
            break;
          }
          case 'Monarch Only': {
            choice = 'Transportation::Transit';
            break;
          }
          default: {
            choice = 'off-list';
          }
        }
        answers[id] = { choice, confidence: 0.9 };
      }
      return { model: 'scripted', answers };
    },
  };
}

test('runs CSV-to-JSONL, reconciliation, batched Jev mapping, final SQL, and review export', async () => {
  const runsDirectory = await mkdtemp(path.join(os.tmpdir(), 'understudy-etl-run-test-'));
  const judge = categoryJudge();
  try {
    let summary;
    try {
      summary = await runEtl({
        monarchPath,
        amexPath,
        runsDirectory,
        makeJudge: async () => judge,
        stdout: { write() {} },
      });
    } catch (error) {
      const [runId] = await readdir(runsDirectory);
      let log = 'No SQLMesh log was written.';
      try {
        log = await readFile(path.join(runsDirectory, runId, 'sqlmesh.log'), 'utf8');
      } catch {
        // The SQLMesh process can fail before it creates its log file.
      }
      throw new Error(`${error.message}\n${log}`, { cause: error });
    }
    const runDirectory = path.join(runsDirectory, summary.run_id);
    const manifest = JSON.parse(await readFile(path.join(runDirectory, 'run.json'), 'utf8'));
    const review = await readFile(path.join(runDirectory, 'review.csv'), 'utf8');
    const walkthrough = await readFile(path.join(runDirectory, 'walkthrough.md'), 'utf8');
    const events = (await readFile(path.join(runDirectory, 'events.jsonl'), 'utf8'))
      .trim().split('\n').map((line) => JSON.parse(line));

    assert.equal(summary.status, 'complete');
    assert.deepEqual(summary.input_rows.map(({ source, rows }) => [source, rows]), [['monarch', 2], ['amex', 3]]);
    assert.deepEqual(summary.reconciliation_rows.map(({ match_status, rows }) => [match_status, rows]), [['matched', 1], ['unmatched', 3]]);
    assert.equal(summary.opposite_sign_candidate_pairs, 1);
    assert.equal(summary.transactions, 4);
    assert.equal(summary.classified_transactions, 2);
    assert.equal(summary.misc_transactions, 2);
    assert.equal(summary.review_required_transactions, 2);
    assert.equal(judge.calls.length, 1, 'the four distinct merchants are sent in one bounded request');
    assert.equal(Object.keys(judge.calls[0].questions).length, 4);
    assert.ok(Object.values(judge.calls[0].state.merchants).some(({ descriptor }) => descriptor === 'Cafe, Local'));
    assert.equal(judge.calls[0].questions.merchant_1.criteria['Food & Dining::Coffee'], 'Food & Dining / Coffee: Coffee shops, cafes, and coffee purchases.');
    assert.deepEqual(Object.values(manifest.stages), ['complete', 'complete', 'complete', 'complete', 'complete', 'complete', 'complete']);
    assert.equal(manifest.category_decisions.distinct_merchants, 4);
    assert.match(walkthrough, /Jev category decisions/);
    assert.match(walkthrough, /Requests: 1/);
    assert.match(walkthrough, /Unique same-date, opposite-sign candidate pairs kept separate: 1/);
    assert.doesNotMatch(walkthrough, /Cafe, Local/);
    assert.ok(events.some(({ event, merchant_count }) => event === 'batch_complete' && merchant_count === 4));
    assert.deepEqual(
      [...new Set(events.filter(({ event }) => event === 'stage_complete').map(({ stage }) => stage))],
      ['validation', 'snapshot', 'csv_to_jsonl', 'sqlmesh', 'jev_categories', 'sqlmesh_final', 'review_export'],
    );
    assert.match(review, /Food & Dining,Coffee,classified/);
    assert.match(review, /Misc,Other or not yet classified,fallback_misc/);
    assert.match(review, /"Cafe, Local"/);
  } finally {
    await rm(runsDirectory, { recursive: true, force: true });
  }
});

test('a failed Jev request marks the category stage failed and does not export a completed review', async () => {
  const runsDirectory = await mkdtemp(path.join(os.tmpdir(), 'understudy-etl-failure-test-'));
  try {
    await assert.rejects(runEtl({
      monarchPath,
      amexPath,
      runsDirectory,
      makeJudge: async () => ({ async systemOne() { throw new Error('synthetic unavailable'); } }),
      stdout: { write() {} },
    }), /Jev category request failed/);
    const [runId] = await readdir(runsDirectory);
    const runDirectory = path.join(runsDirectory, runId);
    const manifest = JSON.parse(await readFile(path.join(runDirectory, 'run.json'), 'utf8'));
    assert.equal(manifest.status, 'failed');
    assert.equal(manifest.failure, 'jev_categories');
    await assert.rejects(readFile(path.join(runDirectory, 'summary.json')));
    await assert.rejects(readFile(path.join(runDirectory, 'review.csv')));
  } finally {
    await rm(runsDirectory, { recursive: true, force: true });
  }
});

test('reconciles and categorizes a synthetic 4,700-transaction workload locally', async (context) => {
  const runsDirectory = await mkdtemp(path.join(os.tmpdir(), 'understudy-etl-scale-test-'));
  const sourceDirectory = path.join(runsDirectory, 'sources');
  await mkdir(sourceDirectory);
  const largeMonarchPath = path.join(sourceDirectory, 'monarch.csv');
  const largeAmexPath = path.join(sourceDirectory, 'amex.csv');
  const transactionCount = 4700;
  const rows = ['Date,Amount,Merchant'];
  for (let index = 0; index < transactionCount; index += 1) {
    rows.push(`2026-01-01,${(index + 1).toFixed(2)},Merchant ${index % 5 + 1}`);
  }
  const csv = `${rows.join('\n')}\n`;
  await Promise.all([writeFile(largeMonarchPath, csv), writeFile(largeAmexPath, csv)]);
  const calls = [];
  const startedAt = Date.now();
  try {
    const summary = await runEtl({
      monarchPath: largeMonarchPath,
      amexPath: largeAmexPath,
      runsDirectory,
      makeJudge: async () => ({
        async systemOne(request) {
          calls.push(request);
          return {
            model: 'synthetic-scale',
            answers: Object.fromEntries(Object.keys(request.questions).map((id) => [id, {
              choice: 'Food & Dining::Restaurants',
              confidence: 0.9,
            }])),
          };
        },
      }),
      stdout: { write() {} },
    });
    const runDirectory = path.join(runsDirectory, summary.run_id);
    const review = await readFile(path.join(runDirectory, 'review.csv'), 'utf8');

    assert.deepEqual(summary.input_rows.map(({ source, rows: count }) => [source, count]), [
      ['monarch', transactionCount],
      ['amex', transactionCount],
    ]);
    assert.deepEqual(summary.reconciliation_rows.map(({ match_status, rows: count }) => [match_status, count]), [
      ['matched', transactionCount],
    ]);
    assert.equal(summary.transactions, transactionCount);
    assert.equal(summary.classified_transactions, transactionCount);
    assert.equal(summary.misc_transactions, 0);
    assert.equal(calls.length, 1, 'five repeated merchant keys should fit in one Jev batch');
    assert.equal(Object.keys(calls[0].questions).length, 5);
    assert.equal(review.trim().split('\n').length, transactionCount + 1, 'review export includes its header and every reconciled row');
    context.diagnostic(`4,700 matched transactions completed through CSV->JSONL, SQLMesh, Jev double, and review export in ${Date.now() - startedAt} ms.`);
  } finally {
    await rm(runsDirectory, { recursive: true, force: true });
  }
});
