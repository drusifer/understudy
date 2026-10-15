// Sprint 1 UND-1 (ARCH §5 target interface): a command-line program as a
// target - its output is the view, a line on stdin is a move, and its
// exit is noticed. Driven against tiny inline programs, never Jev.
import test from 'node:test';
import assert from 'node:assert/strict';
import { startTarget } from '../src/targets/process.mjs';
import { UsageError } from '../src/errors.mjs';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function until(check, ms = 3000) {
  const deadline = Date.now() + ms;
  while (!(await check())) {
    if (Date.now() > deadline) throw new Error('timed out');
    await sleep(10);
  }
}

const ECHO = String.raw`
const readline = require('node:readline');
process.stdout.write('ready\n? name [ann|bob]\nprompt> ');
readline.createInterface({ input: process.stdin }).on('line', (line) => {
  if (line === 'quit') process.exit(3);
  process.stdout.write('hello ' + line + '\n');
});
`;

const start = (source) => startTarget({ kind: 'process', command: process.execPath, args: ['-e', source] }, { directory: process.cwd() });

test('the view is the output so far - an unfinished prompt line included - and grows with it', async () => {
  const target = await start(ECHO);
  try {
    await until(async () => (await target.view()).lines.at(-1) === 'prompt> ');
    const first = await target.view();
    assert.deepEqual(first.lines, ['ready', '? name [ann|bob]', 'prompt> ']);
    assert.equal(first.sent, 0);
    assert.equal(first.exited, null);
    await target.act({ input: 'ann' });
    await until(async () => (await target.view()).lines.includes('hello ann'));
    const second = await target.view();
    assert.deepEqual(second.lines, ['ready', '? name [ann|bob]', 'prompt> ann', 'hello ann'], 'the input is echoed where it was typed');
    assert.ok(second.seq > first.seq, 'seq moves when output arrives');
    assert.equal(second.sent, 1);
    assert.deepEqual(await target.talk(), [], 'a program has no talk channel');
  } finally {
    await target.close();
  }
});

test('an exit is noticed with its code, after all its output', async () => {
  const target = await start(ECHO);
  try {
    await target.act({ input: 'quit' });
    await until(() => target.exited() !== null);
    assert.deepEqual(target.exited(), { code: 3, signal: null });
    assert.equal((await target.view()).exited.code, 3);
  } finally {
    await target.close();
  }
});

test('describe names the program as it was started', async () => {
  const target = await startTarget({ kind: 'process', command: process.execPath, args: ['-e', 'setInterval(() => {}, 1000)'] }, { directory: process.cwd() });
  try {
    assert.equal(target.describe(), `${process.execPath} -e setInterval(() => {}, 1000)`);
  } finally {
    await target.close();
  }
});

test('close stops a program that would run forever, and is safe to call twice', async () => {
  const target = await start('setInterval(() => {}, 1000)');
  await target.close();
  assert.notEqual(target.exited(), null);
  await target.close();
});

test('a program that cannot be started is refused before the run, naming it', async () => {
  await assert.rejects(
    startTarget({ kind: 'process', command: 'no-such-program-understudy', args: [] }, { directory: process.cwd() }),
    (error) => error instanceof UsageError && /could not start no-such-program-understudy: .*ENOENT/.test(error.message),
  );
});
