import { createReadStream, createWriteStream } from 'node:fs';
import { mkdir, rm, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { randomUUID } from 'node:crypto';
import { Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import path from 'node:path';
import { createInterface } from 'node:readline';
import { UsageError } from '../errors.mjs';

const ALIASES = {
  date: ['date', 'transaction date', 'trans date', 'posted date'],
  amount: ['amount', 'transaction amount'],
  merchant: ['merchant', 'description', 'original statement', 'payee', 'name'],
};

function parseHeaderRecord(record) {
  const fields = [];
  let field = '';
  let isInQuotes = false;
  for (let index = 0; index < record.length; index += 1) {
    const char = record[index];
    if (isInQuotes && char === '"' && record[index + 1] === '"') {
      field += '"';
      index += 1;
    } else if (char === '"') {
      isInQuotes = !isInQuotes;
    } else if (char === ',' && !isInQuotes) {
      fields.push(field);
      field = '';
    } else {
      field += char;
    }
  }
  if (isInQuotes) throw new Error('header has an unclosed quoted field');
  fields.push(field);
  return fields.map((name, index) => index === 0 ? name.replace(/^\u{FEFF}/u, '').trim() : name.trim());
}

async function csvHeaders(file, source) {
  let stream;
  try {
    const details = await stat(file);
    if (!details.isFile()) throw new Error('input is not a file');
    stream = createReadStream(file, { encoding: 'utf8' });
    const lines = createInterface({ input: stream, crlfDelay: Infinity });
    const firstLine = await new Promise((resolve, reject) => {
      lines.once('line', resolve);
      lines.once('close', () => reject(new Error('file is empty')));
      stream.once('error', reject);
    });
    lines.close();
    stream.destroy();
    return parseHeaderRecord(firstLine);
  } catch (error) {
    stream?.destroy();
    throw new UsageError(`${source} CSV cannot be read: ${error.message}`);
  }
}

function mapHeaders(headers, source) {
  const normalized = headers.map((header) => header.toLocaleLowerCase().trim());
  const mapping = {};
  for (const [field, aliases] of Object.entries(ALIASES)) {
    const index = aliases.map((alias) => normalized.indexOf(alias)).find((candidate) => candidate >= 0);
    if (index === undefined) {
      throw new UsageError(`${source} CSV is missing a required ${field} column (recognized: ${aliases.join(', ')})`);
    }
    mapping[field] = headers[index];
  }
  return mapping;
}

async function snapshot(source, sourcePath, mapping, destination) {
  let details;
  try {
    details = await stat(sourcePath);
  } catch (error) {
    throw new UsageError(`${source} CSV cannot be read: ${error.message}`);
  }
  if (!details.isFile()) throw new UsageError(`${source} input must be a CSV file`);
  const hash = createHash('sha256');
  const digest = new Transform({ transform(chunk, _encoding, callback) {
    hash.update(chunk);
    callback(null, chunk);
  } });
  await pipeline(createReadStream(sourcePath), digest, createWriteStream(destination, { flags: 'wx' }));
  return { source, file: path.basename(destination), sha256: hash.digest('hex'), bytes: details.size, columns: mapping };
}

/**
 * Validate both source layouts before staging either personal export.
 */
export async function prepareRun({ monarchPath, amexPath, runsDirectory = 'build/runs', runId = `${Date.now()}-${randomUUID()}` }) {
  const resolvedPaths = { monarch: path.resolve(monarchPath), amex: path.resolve(amexPath) };
  const validationStartedAt = Date.now();
  const [monarchHeaders, amexHeaders] = await Promise.all([
    csvHeaders(resolvedPaths.monarch, 'Monarch'),
    csvHeaders(resolvedPaths.amex, 'Amex'),
  ]);
  const mappings = {
    monarch: mapHeaders(monarchHeaders, 'Monarch'),
    amex: mapHeaders(amexHeaders, 'Amex'),
  };
  const validationDurationMs = Date.now() - validationStartedAt;
  const runDirectory = path.resolve(runsDirectory, runId);
  await mkdir(path.dirname(runDirectory), { recursive: true });
  await mkdir(runDirectory, { recursive: false });
  try {
    const inputsDirectory = path.join(runDirectory, 'inputs');
    await mkdir(inputsDirectory);
    const snapshotStartedAt = Date.now();
    const [monarch, amex] = await Promise.all([
      snapshot('monarch', resolvedPaths.monarch, mappings.monarch, path.join(inputsDirectory, 'monarch.csv')),
      snapshot('amex', resolvedPaths.amex, mappings.amex, path.join(inputsDirectory, 'amex.csv')),
    ]);
    const snapshotDurationMs = Date.now() - snapshotStartedAt;
    const manifest = {
      run_id: runId,
      status: 'inputs_ready',
      stages: {
        validation: 'complete',
        snapshot: 'complete',
        csv_to_jsonl: 'pending',
        sqlmesh: 'pending',
        jev_categories: 'pending',
        sqlmesh_final: 'pending',
        review_export: 'pending',
      },
      inputs: [monarch, amex],
    };
    await writeFile(path.join(runDirectory, 'run.json'), `${JSON.stringify(manifest, null, 2)}\n`, { flag: 'wx' });
    return {
      runId,
      runDirectory,
      databasePath: path.join(runDirectory, 'transactions.duckdb'),
      inputs: { monarch, amex },
      stage_timings: { validation: validationDurationMs, snapshot: snapshotDurationMs },
    };
  } catch (error) {
    await rm(runDirectory, { recursive: true, force: true });
    throw error;
  }
}
