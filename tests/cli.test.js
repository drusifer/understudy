// The `understudy` command: a launcher for the Python package. Its arguments, its exit codes (0 done, 1 failed
// after starting, 2 refused before starting) and its messages, which never carry a stack trace.
import test from 'node:test';
import assert from 'node:assert/strict';
import { main } from '../src/cli.mjs';
import { RunError } from '../src/errors.mjs';

const KEY = { TYPESAFE_API_KEY: 'test-key' };
const COFFEE = 'tests/fixtures/coffee/coffee_week.yaml';

function streams() {
  const out = { stdout: '', stderr: '' };
  return { out, stdout: { write: (text) => { out.stdout += text; } }, stderr: { write: (text) => { out.stderr += text; } } };
}

async function cli(argv, { environment = KEY, commands = {} } = {}) {
  const io = streams();
  const code = await main(argv, { environment, stdout: io.stdout, stderr: io.stderr, commands });
  return { code, ...io.out };
}

test('run passes the sketch, each --source and --out to the Python package', async () => {
  const seen = [];
  const commands = { run: async (options) => { seen.push(options); options.stdout.write('stage a\n'); return 0; } };
  const result = await cli(['run', 'coffee_week.yaml', '--source', 'sales.path=a.jsonl', '--source=news=b.jsonl', '--out', 'build/runs'], { commands, environment: {} });
  assert.equal(result.code, 0);
  assert.equal(result.stdout, 'stage a\n');
  assert.equal(seen[0].sketch, 'coffee_week.yaml');
  assert.deepEqual(seen[0].source, ['sales.path=a.jsonl', 'news=b.jsonl']);
  assert.equal(seen[0].out, 'build/runs');
});

test('run needs no key here: whether Jev is needed is the sketch\'s business, decided in Python', async () => {
  const result = await cli(['run', 'coffee_week.yaml'], { environment: {}, commands: { run: async () => 0 } });
  assert.equal(result.code, 0);
});

test('check passes the sketch and the exit code through', async () => {
  const seen = [];
  const result = await cli(['check', 'coffee_week.yaml'], { environment: {}, commands: { check: async (options) => { seen.push(options.sketch); return 2; } } });
  assert.equal(result.code, 2);
  assert.deepEqual(seen, ['coffee_week.yaml']);
});

test('the real command checks a sketch through Python', async () => {
  const result = await cli(['check', COFFEE], { environment: process.env });
  assert.equal(result.code, 0);
  assert.equal(result.stdout, 'ok: coffee_week\n');
  assert.equal(result.stderr, '');
});

test('the real command refuses a wrong sketch with one understudy line and no stack trace', async () => {
  const result = await cli(['run', 'tests/fixtures/coffee/missing.yaml'], { environment: process.env });
  assert.equal(result.code, 2);
  assert.match(result.stderr, /understudy: .*missing\.yaml/);
  assert.doesNotMatch(result.stderr, /Traceback|\n {4}at /);
  assert.equal(result.stdout, '');
});

test('mistakes in the command line are refused with what to type instead', async () => {
  const cases = [
    [[], /usage: understudy run <sketch\.yaml>/],
    [['dance'], /no command "dance" - commands: run, check, etl/],
    [['run'], /run needs a sketch, e\.g\. understudy run coffee_week\.yaml/],
    [['run', 'a', 'b'], /run takes one sketch \(got "a", "b"\)/],
    [['run', 'a.yaml', '--headed'], /no option "--headed" for run/],
    [['run', 'a.yaml', '--source'], /--source needs name\.path=file/],
    [['run', 'a.yaml', '--source', 'bare'], /--source needs name\.path=file, e\.g\. --source sales\.path=sales\.jsonl \(got "bare"\)/],
    [['check', 'a.yaml', '--out', 'x'], /no option "--out" for check/],
  ];
  for (const [argv, message] of cases) {
    const result = await cli(argv, { commands: { run: async () => 0, check: async () => 0 } });
    assert.equal(result.code, 2, argv.join(' '));
    assert.match(result.stderr, message);
    assert.doesNotMatch(result.stderr, /\n {4}at /, 'no stack trace');
  }
});

test('the old commands say they are being rebuilt instead of failing', async () => {
  for (const command of ['library', 'watch', 'dashboard']) {
    const result = await cli([command, 'examples']);
    assert.equal(result.code, 2);
    assert.equal(result.stderr, `understudy: ${command} is being rebuilt for the new sketch model (see docs/sprints/EPIC_PYTHON_PORT.md)\n`);
  }
});

test('--help prints the usage on stdout and exits 0', async () => {
  const result = await cli(['--help']);
  assert.equal(result.code, 0);
  assert.match(result.stdout, /usage: understudy run <sketch\.yaml> \[--source name\.path=file\]\.\.\./);
  assert.match(result.stdout, /understudy check <sketch\.yaml>/);
  assert.match(result.stdout, /understudy etl run --monarch <csv> --amex <csv>/);
});

test('etl run requires both named CSV inputs and passes them to the stage runner', async () => {
  const seen = [];
  const commands = { etl: async (options) => { seen.push(options); options.stdout.write('etl complete\n'); } };
  const result = await cli(['etl', 'run', '--monarch', 'monarch.csv', '--amex=amex.csv', '--out', 'build/results', '--since', '2026-01-01', '--amex-account', 'Platinum'], { commands });
  assert.equal(result.code, 0);
  assert.equal(result.stdout, 'etl complete\n');
  assert.equal(seen[0].monarchPath, 'monarch.csv');
  assert.equal(seen[0].amexPath, 'amex.csv');
  assert.equal(seen[0].out, 'build/results');
  assert.equal(seen[0].since, '2026-01-01');
  assert.equal(seen[0].amexAccount, 'Platinum');
  const missing = await cli(['etl', 'run', '--monarch', 'monarch.csv'], { commands, environment: {} });
  assert.equal(missing.code, 2);
  assert.equal(missing.stderr, 'understudy: understudy etl run needs --amex <csv>\n');
  const noKey = await cli(['etl', 'run', '--monarch', 'monarch.csv', '--amex', 'amex.csv'], { commands, environment: {} });
  assert.equal(noKey.code, 2);
  assert.equal(noKey.stderr, 'understudy: understudy etl run needs a TypeSafe key: set TYPESAFE_API_KEY\n');
});

test('the Python ETL bridge preserves a missing-input refusal without calling Jev', async () => {
  const result = await cli(['etl', 'run', '--monarch', '/missing-monarch.csv', '--amex', '/missing-amex.csv'],
    { environment: { ...process.env, TYPESAFE_API_KEY: 'test-key' } });
  assert.equal(result.code, 2);
  assert.match(result.stderr, /understudy: .*missing-monarch/);
  assert.doesNotMatch(result.stderr, /Traceback|unexpected error/);
  assert.equal(result.stdout, '');
});

test('a run that fails after starting exits 1 with its message; anything unexpected exits 1 too', async () => {
  const failed = await cli(['run', 'a.yaml'], { commands: { run: async () => { throw new RunError('python stopped by SIGKILL'); } } });
  assert.equal(failed.code, 1);
  assert.equal(failed.stderr, 'understudy: python stopped by SIGKILL\n');
  const broken = await cli(['run', 'a.yaml'], { commands: { run: async () => { throw new TypeError('x is undefined'); } } });
  assert.equal(broken.code, 1);
  assert.equal(broken.stderr, 'understudy: unexpected error: x is undefined\n');
});
