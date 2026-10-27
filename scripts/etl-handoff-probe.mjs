import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { DuckDBInstance } from '@duckdb/node-api';

const root = path.resolve('');
const temporaryRoot = await mkdtemp(path.join(os.tmpdir(), 'understudy-etl-probe-'));
const project = path.join(temporaryRoot, 'sqlmesh');
const database = path.join(temporaryRoot, 'run.duckdb');
const csv = path.join(temporaryRoot, 'transactions.csv');

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { encoding: 'utf8', ...options });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(' ')} failed\n${result.stdout}\n${result.stderr}`);
  }
  return result.stdout;
}

function sqlString(value) {
  return `'${value.replaceAll("'", "''")}'`;
}

try {
  await mkdir(path.join(project, 'models'), { recursive: true });
  await writeFile(csv, 'merchant,amount\nCoffee Shop,4.25\n');
  await writeFile(path.join(project, 'config.yaml'), `gateways:\n  local:\n    connection:\n      type: duckdb\n      database: ${JSON.stringify(database)}\ndefault_gateway: local\nmodel_defaults:\n  dialect: duckdb\n  start: 2026-01-01\n`);
  await writeFile(path.join(project, 'models', 'raw_transactions.sql'), `MODEL (name etl_probe.raw_transactions, kind FULL);\nSELECT * FROM read_csv_auto(${sqlString(csv)});\n`);

  run(path.join(root, '.venv', 'bin', 'sqlmesh'), ['plan', 'dev', '--auto-apply'], { cwd: project });
  assert.ok((await readFile(database)).byteLength > 0, 'SQLMesh should materialize the run database');

  const instance = await DuckDBInstance.create(database);
  const connection = await instance.connect();
  await connection.run('CREATE TABLE category_map (merchant VARCHAR, category VARCHAR)');
  await connection.run("INSERT INTO category_map VALUES ('Coffee Shop', 'Dining')");
  await connection.closeSync();
  await instance.closeSync();

  const verify = `import duckdb, sys; db=duckdb.connect(sys.argv[1], read_only=True); assert db.execute("SELECT category FROM category_map WHERE merchant='Coffee Shop'").fetchone() == ('Dining',); assert db.execute("SELECT count(*) FROM information_schema.tables WHERE table_name LIKE '%raw_transactions%'").fetchone()[0] > 0; db.close()`;
  run(path.join(root, '.venv', 'bin', 'python'), ['-c', verify, database]);
  process.stdout.write('SQLMesh CSV load and sequential Node/Python DuckDB handoff passed.\n');
} finally {
  await rm(temporaryRoot, { recursive: true, force: true });
}
