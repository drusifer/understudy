// Sprint 2 UND-7 (ARCH §4 "Generic page app"): what a page sketch gets when
// it names no hooks - the controls a person could choose are the moves.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pageApp } from '../src/apps/page.mjs';
import { loadSketch, checkSketch } from '../src/sketch.mjs';

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
 * A sketch directory: a page sketch with these extra top-level lines, and
 * `hooks.mjs` when its source is given.
 */
function sketchWith(extra, hooksSource = null) {
  const directory = mkdtempSync(path.join(tmpdir(), 'understudy-page-app-'));
  test.after(() => rmSync(directory, { recursive: true, force: true }));
  if (hooksSource) writeFileSync(path.join(directory, 'hooks.mjs'), hooksSource);
  writeFileSync(path.join(directory, 'sketch.yaml'), `${extra}
questions:
  answer: { type: choice, instructions: Pick what to press on \`page\`. }
turn:
  initial: waiting
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

test('a page sketch with no hooks gets the generic page app, and check says so', async () => {
  const directory = sketchWith('name: plain\ntarget: { kind: page, page: index.html }');
  const sketch = await loadSketch(directory);
  assert.equal(sketch.app, pageApp);
  assert.match(await checkSketch(directory), /: sketch OK - plain \(page, generic app\) - 5 states, 1 question$/);
});

test('a page sketch that names its own hooks uses them whole', async () => {
  const directory = sketchWith('name: own\ntarget: { kind: page }\napp: hooks.mjs',
    "export default { phase: () => 'asking', project: () => ({}), options: () => [], act: () => ({ actions: [] }) };\n");
  const sketch = await loadSketch(directory);
  assert.notEqual(sketch.app, pageApp);
  assert.match(await checkSketch(directory), /: sketch OK - own \(page, hooks\.mjs\)/);
});
