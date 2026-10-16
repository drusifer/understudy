// Sprint 1 UND-4, UND-5 AC3, ADR-U5: the `understudy` command - its
// arguments, its exit codes (0 done, 1 failed after starting, 2 refused
// before starting) and its messages, which never carry a stack trace.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { main } from '../src/cli.mjs';
import { RunError } from '../src/errors.mjs';

const BIN = fileURLToPath(new URL('../bin/understudy.mjs', import.meta.url));
const KEY = { TYPESAFE_API_KEY: 'test-key' };

function streams() {
  const out = { stdout: '', stderr: '' };
  return { out, stdout: { write: (text) => { out.stdout += text; } }, stderr: { write: (text) => { out.stderr += text; } } };
}

async function cli(argv, { environment = KEY, commands = {} } = {}) {
  const io = streams();
  const code = await main(argv, { environment, stdout: io.stdout, stderr: io.stderr, commands });
  return { code, ...io.out };
}

test('run without a TypeSafe key is refused before anything starts, naming the variable', async () => {
  let isStarted = false;
  for (const environment of [{}, { TYPESAFE_API_KEY: '  ' }]) {
    const result = await cli(['run', 'examples/cli'], { environment, commands: { run: async () => { isStarted = true; } } });
    assert.equal(result.code, 2);
    assert.equal(result.stderr, 'understudy: understudy run needs a TypeSafe key: set TYPESAFE_API_KEY\n');
  }
  assert.equal(isStarted, false);
});

test('the real command refuses a keyless run the same way, with no stack trace', () => {
  const environment = { ...process.environment };
  delete environment.TYPESAFE_API_KEY;
  const result = spawnSync(process.execPath, [BIN, "run", "examples/cli"], { env: environment, encoding: 'utf8' });
  assert.equal(result.status, 2);
  assert.equal(result.stderr, 'understudy: understudy run needs a TypeSafe key: set TYPESAFE_API_KEY\n');
});

test('check does not need the key', async () => {
  const seen = [];
  const result = await cli(['check', 'examples/cli'], { environment: {}, commands: { check: async (directory) => { seen.push(directory); return 'examples/cli: sketch OK'; } } });
  assert.equal(result.code, 0);
  assert.deepEqual(seen, ['examples/cli']);
  assert.equal(result.stdout, 'examples/cli: sketch OK\n');
});

test('run passes the sketch and --steps N / --steps=N; without it the sketch or the default decides', async () => {
  const calls = [];
  const commands = { run: async (directory, options) => { calls.push([directory, options.steps]); } };
  assert.equal((await cli(['run', 'examples/cli'], { commands })).code, 0);
  assert.equal((await cli(['run', 'examples/cli', '--steps', '7'], { commands })).code, 0);
  assert.equal((await cli(['run', '--steps=3', 'examples/web'], { commands })).code, 0);
  assert.deepEqual(calls, [['examples/cli', undefined], ['examples/cli', 7], ['examples/web', 3]]);
});

test('--steps with no number says so', async () => {
  const result = await cli(['run', 'examples/cli', '--steps'], { commands: { run: async () => {} } });
  assert.equal(result.code, 2);
  assert.equal(result.stderr, 'understudy: --steps needs a number, e.g. --steps 20\n');
});

test('a bad --steps is refused naming the flag and the value', async () => {
  for (const value of ['0', '-2', '1.5', 'many']) {
    const result = await cli(['run', 'examples/cli', '--steps', value], { commands: { run: async () => {} } });
    assert.equal(result.code, 2, value);
    assert.equal(result.stderr, `understudy: --steps must be a positive whole number (got "${value}")\n`);
  }
});

test('mistakes in the command line are refused with what to type instead', async () => {
  const cases = [
    [[], /usage: understudy run <sketch>/],
    [['dance'], /no command "dance" - commands: run, check, library/],
    [['run'], /run needs a sketch, e.g. understudy run examples\/cli/],
    [['run', 'a', 'b'], /run takes one sketch \(got "a", "b"\)/],
    [['run', 'examples/cli', '--headed'], /no option "--headed" for run/],
  ];
  for (const [argv, message] of cases) {
    const result = await cli(argv, { commands: { run: async () => {} } });
    assert.equal(result.code, 2, argv.join(' '));
    assert.match(result.stderr, message);
    assert.doesNotMatch(result.stderr, /\n {4}at /, 'no stack trace');
  }
});

test('--help prints the usage on stdout and exits 0', async () => {
  const result = await cli(['--help']);
  assert.equal(result.code, 0);
  assert.match(result.stdout, /usage: understudy run <sketch> \[--steps N\]/);
  assert.match(result.stdout, /understudy check <sketch>/);
  assert.match(result.stdout, /understudy library \[<sketch>\]/);
  assert.match(result.stdout, /<sketch> is a directory holding sketch\.yaml/);
});

test('a run that fails after starting exits 1 with its message; anything unexpected exits 1 too', async () => {
  const failed = await cli(['run', 'examples/cli'], { commands: { run: async () => { throw new RunError('node app.mjs exited with code 3 before the end state'); } } });
  assert.equal(failed.code, 1);
  assert.equal(failed.stderr, 'understudy: node app.mjs exited with code 3 before the end state\n');
  const broken = await cli(['run', 'examples/cli'], { commands: { run: async () => { throw new TypeError('x is undefined'); } } });
  assert.equal(broken.code, 1);
  assert.equal(broken.stderr, 'understudy: unexpected error: x is undefined\n');
});

test('library lists every generic name grouped by kind, one line each with its meaning', async () => {
  const result = await cli(['library'], { environment: {} });
  assert.equal(result.code, 0);
  const lines = result.stdout.split('\n');
  assert.equal(lines[0], 'guards:');
  assert.ok(lines.includes('actions:'));
  assert.ok(lines.includes('actors:'));
  assert.ok(lines.some((line) => /^ {2}changed - the app's view/.test(line)));
  assert.ok(lines.some((line) => /^ {2}look - /.test(line)));
  assert.ok(lines.some((line) => /^ {2}play - /.test(line)));
});

test('--watch and --port reach the run; --port without --watch, or a bad port, is refused', async () => {
  const calls = [];
  const commands = { run: async (location, options) => { calls.push(options.watch); } };
  assert.equal((await cli(['run', 'examples/cli', '--watch'], { commands })).code, 0);
  assert.equal((await cli(['run', 'examples/cli', '--watch', '--port', '4180'], { commands })).code, 0);
  assert.equal((await cli(['run', 'examples/cli', '--port=4181', '--watch'], { commands })).code, 0);
  assert.equal((await cli(['run', 'examples/cli'], { commands })).code, 0);
  assert.deepEqual(calls, [{ port: undefined }, { port: 4180 }, { port: 4181 }, null]);
  const lonely = await cli(['run', 'examples/cli', '--port', '4180'], { commands });
  assert.equal(lonely.code, 2);
  assert.equal(lonely.stderr, 'understudy: --port needs --watch (it is the watch page\'s port)\n');
  const bad = await cli(['run', 'examples/cli', '--watch', '--port', '99999'], { commands });
  assert.equal(bad.stderr, 'understudy: --port must be a port number from 1 to 65535 (got "99999")\n');
  assert.match((await cli(['check', 'examples/cli', '--watch'], { commands })).stderr, /no option "--watch" for check/);
});
