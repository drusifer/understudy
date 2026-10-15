// Sprint 1 UND-3: a broken part is refused at load - before any app
// starts or Jev is called - naming the file, the path in it, the bad name
// and the nearest known one. `understudy check` is that load, alone.
import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadPart, checkPart, shown } from '../src/part.mjs';
import { UsageError } from '../src/errors.mjs';
import { main } from '../src/cli.mjs';

const GOOD = fileURLToPath(new URL('fixtures/parts/good', import.meta.url));

/**
 * A copy of the good fixture with one file's text changed (or removed).
 */
function brokenCopy(file, change) {
  const directory = mkdtempSync(path.join(tmpdir(), 'understudy-part-'));
  cpSync(GOOD, directory, { recursive: true });
  const target = path.join(directory, file);
  if (change === null) rmSync(target);
  else writeFileSync(target, change(readFileSync(target, 'utf8')));
  test.after(() => rmSync(directory, { recursive: true, force: true }));
  return directory;
}

async function refusal(directory) {
  try {
    await loadPart(directory);
  } catch (error) {
    assert.ok(error instanceof UsageError, error.message);
    return error.message;
  }
  assert.fail(`${directory} loaded, but should have been refused`);
}

test('a good part loads: adapter, questions, a machine, and services to fill at run time', async () => {
  const part = await loadPart(GOOD);
  assert.equal(part.adapter.name, 'fixture-good');
  assert.deepEqual(Object.keys(part.questions), ['next']);
  assert.ok(part.machine);
  assert.equal(typeof part.services, 'object');
});

test('check says what it checked', async () => {
  assert.equal(await checkPart(GOOD), `${shown(GOOD)}: part OK - 5 states, 1 question, adapter fixture-good (process)`);
});

test('an unknown guard is refused naming file, path, bad name and nearest name', async () => {
  const directory = brokenCopy('part/turn.yaml', (text) => text.replace('type: phase, params: { is: menu }', 'type: phse, params: { is: menu }'));
  assert.equal(await refusal(directory),
    `${shown(directory)}/part/turn.yaml: states.looking.invoke.onDone[0].guard: no guard "phse" - did you mean "phase"?`);
});

test('an unknown actor is refused the same way', async () => {
  const directory = brokenCopy('part/turn.yaml', (text) => text.replace('src: look', 'src: lok'));
  assert.equal(await refusal(directory), `${shown(directory)}/part/turn.yaml: states.looking.invoke.src: no actor "lok" - did you mean "look"?`);
});

test('an adapter\'s own names are known to its part', async () => {
  const directory = brokenCopy('part/turn.yaml', (text) => text.replace('- { target: waiting }', '- { target: waiting, guard: sold_out }\n        - { target: waiting }'));
  const part = await loadPart(directory);
  assert.equal(part.states, 5);
});

test('a question the turn names but the questions file lacks is refused', async () => {
  const directory = brokenCopy('part/turn.yaml', (text) => text.replace('question: next', 'question: nxt'));
  assert.match(await refusal(directory), /part\/turn\.yaml: states\.stepping\.invoke\.with\.question: no question "nxt" - did you mean "next"\?$/);
});

test('a number in a question\'s prose is refused naming the question', async () => {
  const directory = brokenCopy('part/questions.yaml', (text) => text.replace('Pick the next step', 'Pick 2 steps'));
  assert.equal(await refusal(directory),
    `${shown(directory)}/part/questions.yaml: next.instructions carries a number in the question; put the number in state and refer to it by path`);
});

test('a quoted value in a question\'s prose is refused, but a backticked path is fine', async () => {
  const directory = brokenCopy('part/questions.yaml', (text) => text.replace('place the order as it stands', 'order when `screen` says "ready"'));
  assert.equal(await refusal(directory),
    `${shown(directory)}/part/questions.yaml: next.criteria.order carries a quoted value in the question; put the value in state and refer to it by path`);
});

test('a question of an unknown type is refused, naming the known types', async () => {
  const directory = brokenCopy('part/questions.yaml', (text) => text.replace('type: choice', 'type: choise'));
  assert.equal(await refusal(directory), `${shown(directory)}/part/questions.yaml: next.type: no question type "choise" - did you mean "choice"?`);
});

test('bad YAML is refused naming the file and the line', async () => {
  const directory = brokenCopy('part/turn.yaml', (text) => text.replace('initial: waiting', 'initial: [waiting'));
  assert.match(await refusal(directory), /part\/turn\.yaml: not valid YAML - .* at line 2, column 1$/);
});

test('a missing adapter or part file is refused saying what an example directory needs', async () => {
  assert.match(await refusal(brokenCopy('adapter.mjs', null)), /: no adapter\.mjs - an example directory needs adapter\.mjs, part\/turn\.yaml and part\/questions\.yaml$/);
  assert.match(await refusal(brokenCopy('part/questions.yaml', null)), /: no part\/questions\.yaml - an example directory needs adapter\.mjs, part\/turn\.yaml and part\/questions\.yaml$/);
});

test('an adapter missing a piece is refused naming the piece', async () => {
  const directory = brokenCopy('adapter.mjs', (text) => text.replace("options: () => [{ id: 'order', what: 'place the order' }, { id: 'cancel', what: 'stop' }],", ''));
  assert.equal(await refusal(directory), `${shown(directory)}/adapter.mjs: app.options must be a function - see docs/ADAPTERS.md`);
  const kindless = brokenCopy('adapter.mjs', (text) => text.replace("kind: 'process'", "kind: 'ftp'"));
  assert.equal(await refusal(kindless), `${shown(kindless)}/adapter.mjs: target.kind must be "process" or "page" (got "ftp")`);
});

test('understudy check: good exits 0 without a key; broken exits 2 with one line and no stack', async () => {
  const io = { out: '', err: '' };
  const streams = { stdout: { write: (text) => { io.out += text; } }, stderr: { write: (text) => { io.err += text; } } };
  assert.equal(await main(['check', GOOD], { environment: {}, ...streams }), 0);
  assert.match(io.out, /part OK/);
  const directory = brokenCopy('part/turn.yaml', (text) => text.replace('src: look', 'src: lok'));
  assert.equal(await main(['check', directory], { environment: {}, ...streams }), 2);
  assert.match(io.err, /^understudy: .*no actor "lok" - did you mean "look"\?\n$/);
});

test('a directory that does not exist, or a file, is named as such - not as a missing adapter', async () => {
  assert.equal(await refusal('examples/nope'), 'examples/nope: no such directory');
  assert.equal(await refusal('package.json'), 'package.json: not a directory - give the example directory, e.g. examples/cli');
});
