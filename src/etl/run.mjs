import { appendFile, cp, copyFile, readFile, rename, writeFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DuckDBInstance } from '@duckdb/node-api';
import { createJevJudge, reportJevFailures } from '../jev.mjs';
import { RunError } from '../errors.mjs';
import { classifyMerchants, loadTaxonomy, TAXONOMY_PATH } from './categories.mjs';
import { prepareRun } from './csv.mjs';

const ROOT = fileURLToPath(new URL('../..', import.meta.url));
const SQLMESH = path.join(ROOT, 'sqlmesh');
const PYTHON = path.join(ROOT, '.venv', 'bin', 'python');
const CSV_TO_JSONL = path.join(ROOT, 'src', 'etl', 'csv_to_jsonl.py');
const MAP_TABLE = 'etl__dev.category_map';
const CATEGORIZED_TABLE = 'etl__dev.categorized_transactions';

async function readManifest(runDirectory) {
  return JSON.parse(await readFile(path.join(runDirectory, 'run.json'), 'utf8'));
}

async function saveManifest(runDirectory, manifest) {
  const file = path.join(runDirectory, 'run.json');
  const temporary = `${file}.tmp`;
  await writeFile(temporary, `${JSON.stringify(manifest, null, 2)}\n`);
  await rename(temporary, file);
}

function convertCsvToJsonl(source, input, runDirectory) {
  const destination = path.join(runDirectory, 'inputs', `${source}.jsonl`);
  const result = spawnSync(PYTHON, [
    CSV_TO_JSONL,
    path.join(runDirectory, 'inputs', input.file),
    destination,
    source,
    input.columns.date,
    input.columns.amount,
    input.columns.merchant,
  ], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  if (result.error || result.status !== 0) {
    throw new RunError(`${source} CSV could not be converted to staged JSONL.`, { cause: result.error });
  }
  return destination;
}

async function prepareSqlMeshProject(runDirectory) {
  await cp(SQLMESH, path.join(runDirectory, 'sqlmesh'), { recursive: true });
  await copyFile(TAXONOMY_PATH, path.join(runDirectory, 'taxonomy.yaml'));
}

async function runSqlMesh(runDirectory, databasePath, jsonlFiles, { restateCategorized = false } = {}) {
  const project = path.join(runDirectory, 'sqlmesh');
  const environment = {
    ...process.env,
    UNDERSTUDY_ETL_DATABASE: databasePath,
    UNDERSTUDY_ETL_MONARCH_JSONL: jsonlFiles.monarch,
    UNDERSTUDY_ETL_AMEX_JSONL: jsonlFiles.amex,
  };
  const arguments_ = ['plan', 'dev', '--auto-apply'];
  if (restateCategorized) arguments_.push('--restate-model', 'etl.categorized_transactions');
  const result = spawnSync(path.join(ROOT, '.venv', 'bin', 'sqlmesh'), arguments_, {
    cwd: project,
    env: environment,
    encoding: 'utf8',
    maxBuffer: 8 * 1024 * 1024,
  });
  const log = `${result.stdout ?? ''}\n${result.stderr ?? ''}`;
  await appendFile(path.join(runDirectory, 'sqlmesh.log'), `${restateCategorized ? '=== Final category materialization ===' : '=== Initial reconciliation materialization ==='}\n${log}\n`);
  if (result.error || result.status !== 0) {
    const stage = restateCategorized ? 'final category materialization' : 'SQLMesh reconciliation';
    throw new RunError(`${stage} failed; this run is incomplete.`, { cause: result.error });
  }
}

function sqlLiteral(value) {
  if (value === null || value === undefined) return 'NULL';
  if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE';
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'NULL';
  return `'${String(value).replaceAll("'", "''")}'`;
}

async function withDatabase(databasePath, action) {
  const instance = await DuckDBInstance.create(databasePath);
  const connection = await instance.connect();
  try {
    return await action(connection);
  } finally {
    await connection.closeSync();
    await instance.closeSync();
  }
}

async function createCategoryMap(databasePath) {
  await withDatabase(databasePath, async (connection) => {
    await connection.run(`CREATE SCHEMA IF NOT EXISTS etl__dev`);
    await connection.run(`CREATE TABLE ${MAP_TABLE} (
      merchant_key VARCHAR,
      merchant VARCHAR,
      category VARCHAR,
      subcategory VARCHAR,
      classification_status VARCHAR,
      confidence DOUBLE,
      taxonomy_version VARCHAR,
      decision_model VARCHAR,
      review_required BOOLEAN
    )`);
    // Sprint 17's refund model reads this table; this runner never fills it (it goes with the
    // Python controller), but SQLMesh plans every model in the project, so it must exist.
    await connection.run(`CREATE TABLE etl__dev.transfer_judgment (
      payee_key VARCHAR,
      payee VARCHAR,
      decision VARCHAR,
      probability DOUBLE
    )`);
  });
}

async function merchantCandidates(databasePath) {
  return withDatabase(databasePath, async (connection) => {
    const result = await connection.runAndReadAll(`
      SELECT lower(trim(merchant)) AS merchant_key,
        min(trim(merchant)) AS merchant,
        count(*) AS transaction_count
      FROM etl__dev.reconciled_transactions
      WHERE nullif(trim(merchant), '') IS NOT NULL
      GROUP BY lower(trim(merchant))
      ORDER BY lower(trim(merchant))
    `);
    return result.getRowObjects().map((row) => ({ ...row, transaction_count: Number(row.transaction_count) }));
  });
}

async function writeCategoryMap(databasePath, mappings) {
  await withDatabase(databasePath, async (connection) => {
    for (let offset = 0; offset < mappings.length; offset += 100) {
      const rows = mappings.slice(offset, offset + 100).map((mapping) => `(${[
        mapping.merchant_key,
        mapping.merchant,
        mapping.category,
        mapping.subcategory,
        mapping.classification_status,
        mapping.confidence,
        mapping.taxonomy_version,
        mapping.decision_model,
        mapping.review_required,
      ].map((value) => sqlLiteral(value)).join(', ')})`);
      if (rows.length > 0) {
        await connection.run(`INSERT INTO ${MAP_TABLE} VALUES ${rows.join(', ')}`);
      }
    }
  });
}

async function readFinalCounts(databasePath) {
  return withDatabase(databasePath, async (connection) => {
    const raw = await connection.runAndReadAll(`
      SELECT 'monarch' AS source, count(*) AS rows FROM etl__dev.raw_monarch
      UNION ALL
      SELECT 'amex' AS source, count(*) AS rows FROM etl__dev.raw_amex
    `);
    const reconciliation = await connection.runAndReadAll(`
      SELECT match_status, count(*) AS rows
      FROM etl__dev.reconciled_transactions
      GROUP BY match_status
      ORDER BY match_status
    `);
    const oppositeSignCandidates = await connection.runAndReadAll(`
      WITH monarch_keys AS (
        SELECT transaction_date, abs(amount) AS magnitude, min(amount) AS amount, count(*) AS row_count
        FROM etl__dev.raw_monarch
        WHERE transaction_date IS NOT NULL AND amount IS NOT NULL
        GROUP BY transaction_date, abs(amount)
      ), amex_keys AS (
        SELECT transaction_date, abs(amount) AS magnitude, min(amount) AS amount, count(*) AS row_count
        FROM etl__dev.raw_amex
        WHERE transaction_date IS NOT NULL AND amount IS NOT NULL
        GROUP BY transaction_date, abs(amount)
      )
      SELECT count(*) AS pairs
      FROM monarch_keys AS monarch
      JOIN amex_keys AS amex USING (transaction_date, magnitude)
      WHERE monarch.row_count = 1
        AND amex.row_count = 1
        AND monarch.amount <> 0
        AND monarch.amount = -amex.amount
    `);
    const categories = await connection.runAndReadAll(`
      SELECT category, subcategory, classification_status, count(*) AS rows
      FROM ${CATEGORIZED_TABLE}
      GROUP BY category, subcategory, classification_status
      ORDER BY category, subcategory, classification_status
    `);
    const totals = await connection.runAndReadAll(`
      SELECT count(*) AS transactions,
        count(*) FILTER (WHERE classification_status = 'classified') AS classified,
        count(*) FILTER (WHERE category = 'Misc') AS misc,
        count(*) FILTER (WHERE review_required) AS review_required
      FROM ${CATEGORIZED_TABLE}
    `);
    const total = totals.getRowObjects()[0];
    return {
      input_rows: raw.getRowObjects().map((row) => ({ ...row, rows: Number(row.rows) })),
      reconciliation_rows: reconciliation.getRowObjects().map((row) => ({ ...row, rows: Number(row.rows) })),
      opposite_sign_candidate_pairs: Number(oppositeSignCandidates.getRowObjects()[0].pairs),
      category_rows: categories.getRowObjects().map((row) => ({ ...row, rows: Number(row.rows) })),
      transactions: Number(total.transactions),
      classified_transactions: Number(total.classified),
      misc_transactions: Number(total.misc),
      review_required_transactions: Number(total.review_required),
    };
  });
}

async function exportReviewCsv(databasePath, outputPath) {
  await withDatabase(databasePath, async (connection) => {
    await connection.run(`COPY (
      SELECT * FROM ${CATEGORIZED_TABLE}
      ORDER BY transaction_date NULLS LAST, amount NULLS LAST,
        CASE WHEN monarch_source_row IS NULL THEN 1 ELSE 0 END,
        coalesce(monarch_source_row, amex_source_row)
    ) TO ${sqlLiteral(outputPath)} (HEADER, DELIMITER ',')`);
  });
}

const FAILED_STAGE_MESSAGES = {
  csv_to_jsonl: 'CSV-to-JSONL hydration failed; this run is incomplete.',
  sqlmesh: 'SQLMesh reconciliation failed; this run is incomplete.',
  jev_categories: 'Jev category classification failed; this run is incomplete.',
  sqlmesh_final: 'Final category materialization failed; this run is incomplete.',
  review_export: 'Review export failed; this run is incomplete.',
};

function durationText(milliseconds) {
  return `${(milliseconds / 1000).toFixed(2)} s`;
}

function walkthroughMarkdown({ runId, status, events, summary, failedStage }) {
  const completedStages = events.filter((event) => event.event === 'stage_complete');
  const batches = events.filter((event) => event.event === 'batch_complete');
  const stoppedAt = failedStage ? ` (stopped at ${failedStage})` : '';
  const lines = [
    `# ETL run walkthrough: ${runId}`,
    '',
    `Status: **${status}**${stoppedAt}`,
    '',
    '| Step | Duration | Details |',
    '| --- | ---: | --- |',
    ...completedStages.map((event) => `| ${event.stage} | ${durationText(event.duration_ms ?? 0)} | ${event.details?.summary ?? 'Completed'} |`),
  ];

  const categoryEvent = completedStages.find((event) => event.stage === 'jev_categories');
  if (categoryEvent) {
    const { details = {} } = categoryEvent;
    lines.push(
      '',
      '## Jev category decisions',
      '',
      `- Distinct merchants: ${details.distinct_merchants}`,
      `- Requests: ${details.requests}`,
      `- Classified: ${details.classified}`,
      `- Fallback to Misc: ${details.fallback_misc}`,
      `- Request batches recorded: ${batches.length}`,
    );
  }

  if (summary) {
    lines.push(
      '',
      '## Reconciliation',
      '',
      ...summary.input_rows.map((item) => `- ${item.source} input rows: ${item.rows}`),
      ...summary.reconciliation_rows.map((item) => `- ${item.match_status}: ${item.rows}`),
      `- Unique same-date, opposite-sign candidate pairs kept separate: ${summary.opposite_sign_candidate_pairs}`,
      `- Rows requiring review: ${summary.review_required_transactions}`,
      '',
      '## Outputs',
      '',
      `- Review CSV: \`${path.basename(summary.review_csv)}\``,
      '- Summary: `summary.json`',
      '- Structured event log: `events.jsonl`',
      '- This walkthrough: `walkthrough.md`',
    );
  }
  lines.push('');
  return lines.join('\n');
}

/**
 * Snapshot CSVs, stage flat JSONL, reconcile, classify merchants, and export review rows.
 */
export async function runEtl({
  monarchPath,
  amexPath,
  stdout = process.stdout,
  environment = process.env,
  makeJudge = createJevJudge,
  runsDirectory = path.join(ROOT, 'build', 'runs'),
}) {
  const judge = reportJevFailures(await makeJudge(environment));
  const run = await prepareRun({ monarchPath, amexPath, runsDirectory });
  const manifest = await readManifest(run.runDirectory);
  manifest.status = 'running';
  manifest.stages.csv_to_jsonl = 'running';
  await saveManifest(run.runDirectory, manifest);

  let failedStage = 'csv_to_jsonl';
  const eventsPath = path.join(run.runDirectory, 'events.jsonl');
  const events = [];
  const recordEvent = async (event) => {
    const record = { timestamp: new Date().toISOString(), ...event };
    events.push(record);
    await appendFile(eventsPath, `${JSON.stringify(record)}\n`);
  };
  const stageStartedAt = new Map();
  const startStage = async (stage, details = {}) => {
    stageStartedAt.set(stage, Date.now());
    await recordEvent({ event: 'stage_started', stage, details });
  };
  const completeStage = async (stage, details = {}) => {
    await recordEvent({
      event: 'stage_complete',
      stage,
      duration_ms: stageStartedAt.has(stage) ? Date.now() - stageStartedAt.get(stage) : run.stage_timings[stage],
      details,
    });
  };

  try {
    await writeFile(eventsPath, '');
    await recordEvent({ event: 'stage_complete', stage: 'validation', duration_ms: run.stage_timings.validation, details: { summary: 'Both CSV headers and required columns verified' } });
    await recordEvent({ event: 'stage_complete', stage: 'snapshot', duration_ms: run.stage_timings.snapshot, details: { summary: `Two input snapshots saved (${run.inputs.monarch.bytes + run.inputs.amex.bytes} bytes)` } });
    await startStage('csv_to_jsonl');
    const jsonlFiles = {
      monarch: convertCsvToJsonl('monarch', run.inputs.monarch, run.runDirectory),
      amex: convertCsvToJsonl('amex', run.inputs.amex, run.runDirectory),
    };
    manifest.stages.csv_to_jsonl = 'complete';
    manifest.staged_inputs = Object.fromEntries(Object.entries(jsonlFiles).map(([source, file]) => [source, path.basename(file)]));
    manifest.stages.sqlmesh = 'running';
    await saveManifest(run.runDirectory, manifest);
    await completeStage('csv_to_jsonl', { summary: 'Flat JSONL snapshots staged for SQLMesh' });

    await startStage('sqlmesh');
    await prepareSqlMeshProject(run.runDirectory);
    await createCategoryMap(run.databasePath);
    failedStage = 'sqlmesh';
    await runSqlMesh(run.runDirectory, run.databasePath, jsonlFiles);
    manifest.stages.sqlmesh = 'complete';
    manifest.stages.jev_categories = 'running';
    await saveManifest(run.runDirectory, manifest);
    await completeStage('sqlmesh', { summary: 'Initial reconciliation models materialized' });

    failedStage = 'jev_categories';
    await startStage('jev_categories');
    const taxonomy = await loadTaxonomy();
    manifest.taxonomy_version = taxonomy.version;
    const candidates = await merchantCandidates(run.databasePath);
    const distinctMerchants = candidates.length;
    await recordEvent({
      event: 'classification_started',
      stage: 'jev_categories',
      details: { distinct_merchants: distinctMerchants, requests: Math.ceil(distinctMerchants / 5) },
    });
    const mappings = await classifyMerchants({
      candidates,
      taxonomy,
      judge,
      onBatchComplete: (batch) => recordEvent({ event: 'batch_complete', stage: 'jev_categories', ...batch }),
    });
    await writeCategoryMap(run.databasePath, mappings);
    manifest.category_decisions = {
      distinct_merchants: mappings.length,
      classified: mappings.filter((mapping) => mapping.classification_status === 'classified').length,
      fallback_misc: mappings.filter((mapping) => mapping.review_required).length,
    };
    manifest.stages.jev_categories = 'complete';
    manifest.stages.sqlmesh_final = 'running';
    await saveManifest(run.runDirectory, manifest);
    await completeStage('jev_categories', {
      summary: `${mappings.length} merchants classified in ${events.filter((event) => event.event === 'batch_complete').length} requests`,
      distinct_merchants: mappings.length,
      requests: events.filter((event) => event.event === 'batch_complete').length,
      classified: manifest.category_decisions.classified,
      fallback_misc: manifest.category_decisions.fallback_misc,
    });

    failedStage = 'sqlmesh_final';
    await startStage('sqlmesh_final');
    await runSqlMesh(run.runDirectory, run.databasePath, jsonlFiles, { restateCategorized: true });
    manifest.stages.sqlmesh_final = 'complete';
    manifest.stages.review_export = 'running';
    await saveManifest(run.runDirectory, manifest);
    await completeStage('sqlmesh_final', { summary: 'Final category and review models materialized' });

    failedStage = 'review_export';
    await startStage('review_export');
    const reviewPath = path.join(run.runDirectory, 'review.csv');
    await exportReviewCsv(run.databasePath, reviewPath);
    const counts = await readFinalCounts(run.databasePath);
    const summary = {
      run_id: run.runId,
      status: 'complete',
      ...counts,
      database: path.relative(ROOT, run.databasePath),
      review_csv: path.relative(ROOT, reviewPath),
      walkthrough: path.relative(ROOT, path.join(run.runDirectory, 'walkthrough.md')),
    };
    await completeStage('review_export', { summary: `${summary.transactions} review rows exported` });
    await writeFile(path.join(run.runDirectory, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
    manifest.status = 'complete';
    manifest.stages.review_export = 'complete';
    manifest.outputs = { summary: 'summary.json', review: 'review.csv', taxonomy: 'taxonomy.yaml', events: 'events.jsonl', walkthrough: 'walkthrough.md' };
    await saveManifest(run.runDirectory, manifest);
    await writeFile(path.join(run.runDirectory, 'walkthrough.md'), walkthroughMarkdown({ runId: run.runId, status: 'complete', events, summary }));
    stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
    return summary;
  } catch (error) {
    manifest.status = 'failed';
    manifest.stages[failedStage] = 'failed';
    manifest.failure = failedStage;
    await saveManifest(run.runDirectory, manifest);
    await recordEvent({ event: 'stage_failed', stage: failedStage });
    await writeFile(path.join(run.runDirectory, 'walkthrough.md'), walkthroughMarkdown({ runId: run.runId, status: 'failed', events, failedStage }));
    if (error instanceof RunError) throw error;
    throw new RunError(FAILED_STAGE_MESSAGES[failedStage], { cause: error });
  }
}
