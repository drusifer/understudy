// Sprint 2 UND-7 (ARCH §4 "Generic page app"): what a web adapter gets when
// it gives no app hooks - the controls a person could choose are the moves.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pageApp } from '../src/apps/page.mjs';
import { loadPart, checkPart } from '../src/part.mjs';

const VIEW = {
  path: '/index.html', title: 'Sign up', seq: 7,
  text: ['Sign up', 'Which plan would you like?'],
  controls: [
    { role: 'button', name: 'Free' },
    { role: 'option', name: 'Large', list: 'Size' },
    { role: 'checkbox', name: 'Agree', checked: true },
  ],
};

test('a page with something to choose is asking; one with nothing is waiting', () => {
  assert.equal(pageApp.phase(VIEW), 'asking');
  assert.equal(pageApp.phase({ ...VIEW, controls: [] }), 'waiting');
});

test('Jev sees the page title, what it says and its controls', () => {
  assert.deepEqual(pageApp.project(VIEW), { page: 'Sign up', says: ['Sign up', 'Which plan would you like?'], controls: VIEW.controls });
});

test('each control is an option named by kind and visible label, and acting uses it by role and name', () => {
  const options = pageApp.options(pageApp.project(VIEW));
  assert.deepEqual(options.map(({ id, what, value }) => ({ id, what, value })), [
    { id: 'button:Free', what: 'press Free', value: 'Free' },
    { id: 'option:Size=Large', what: 'pick Large from Size', value: 'Large' },
    { id: 'checkbox:Agree', what: 'tick Agree', value: 'Agree' },
  ]);
  assert.deepEqual(pageApp.act(options[1]), { actions: [{ role: 'option', name: 'Large', list: 'Size' }] });
  assert.deepEqual(pageApp.act(options[0]), { actions: [{ role: 'button', name: 'Free' }] });
});

/**
 * An example directory with this adapter source and a minimal good part.
 */
function exampleWith(adapterSource) {
  const directory = mkdtempSync(path.join(tmpdir(), 'understudy-page-app-'));
  test.after(() => rmSync(directory, { recursive: true, force: true }));
  mkdirSync(path.join(directory, 'part'));
  writeFileSync(path.join(directory, 'adapter.mjs'), adapterSource);
  writeFileSync(path.join(directory, 'part', 'questions.yaml'), 'answer:\n  type: choice\n  instructions: Pick what to press on `page`.\n');
  writeFileSync(path.join(directory, 'part', 'turn.yaml'), `initial: waiting
states:
  waiting: { tags: [safe], on: { OBSERVE: looking } }
  looking:
    invoke:
      src: look
      onDone:
        - { target: finished, guard: { type: showing, params: { text: Welcome } } }
        - { target: answering, guard: { type: phase, params: { is: asking } } }
        - { target: waiting }
  answering: { tags: [move], on: { STEP: replying } }
  replying: { invoke: { src: play, with: { phase: asking, question: answer }, onDone: waiting } }
  finished: { type: final }
`);
  return directory;
}

test('a page adapter with only a name and a target gets the generic page app, and check says so', async () => {
  const directory = exampleWith("export default { name: 'plain', target: { kind: 'page', page: 'index.html' } };\n");
  const part = await loadPart(directory);
  assert.equal(part.adapter.app, pageApp);
  assert.match(await checkPart(directory), /adapter plain \(page, generic page app\)$/);
});

test('an adapter that gives its own app hooks uses them whole', async () => {
  const directory = exampleWith(`export default {
  name: 'own', target: { kind: 'page' },
  app: { phase: () => 'asking', project: () => ({}), options: () => [], act: () => ({ actions: [] }) },
};\n`);
  const part = await loadPart(directory);
  assert.notEqual(part.adapter.app, pageApp);
  assert.match(await checkPart(directory), /adapter own \(page\)$/);
});
