// Sprint 2 UND-7 (ARCH §4, ADR-0007): a page's accessibility snapshot, as
// Playwright prints it, read into what a person sees - its text - and what
// a person could choose - its controls. The snapshot below was recorded
// from Playwright 1.62.1 (hidden button already absent, as in the browser).
import test from 'node:test';
import assert from 'node:assert/strict';
import { parseSnapshot } from '../src/targets/aria.mjs';

const RECORDED = `- heading "Sign up" [level=1]
- paragraph: Which plan?
- button "Free"
- button "Gold" [disabled]
- link "Terms":
  - /url: "#x"
- checkbox "Agree" [checked]
- text: Agree Size
- combobox "Size":
  - option "Small" [selected]
  - option "Large"
- radio "Tea"
- text: Tea
- textbox "Name"
- text: Name`;

test('the title is the first heading, and the text is what a person reads', () => {
  const view = parseSnapshot(RECORDED);
  assert.equal(view.title, 'Sign up');
  assert.deepEqual(view.text, ['Sign up', 'Which plan?', 'Agree Size', 'Tea', 'Name']);
});

test('the controls are the ones a person could choose: enabled buttons, links, boxes and options', () => {
  assert.deepEqual(parseSnapshot(RECORDED).controls, [
    { role: 'button', name: 'Free' },
    { role: 'link', name: 'Terms' },
    { role: 'checkbox', name: 'Agree', checked: true },
    { role: 'option', name: 'Small', list: 'Size', selected: true },
    { role: 'option', name: 'Large', list: 'Size' },
    { role: 'radio', name: 'Tea' },
  ]);
});

test('names with quotes and colons survive, and quoted text is unquoted', () => {
  const view = parseSnapshot(String.raw`- button "Say \"hi\": now"
- paragraph: "Total: 3"`);
  assert.deepEqual(view.controls, [{ role: 'button', name: 'Say "hi": now' }]);
  assert.deepEqual(view.text, ['Total: 3']);
});

test('nested content counts, and an empty page has nothing', () => {
  const view = parseSnapshot(`- main:
  - heading "Welcome aboard!" [level=2]
  - list:
    - listitem: one
    - listitem:
      - link "Help"`);
  assert.equal(view.title, 'Welcome aboard!');
  assert.deepEqual(view.text, ['Welcome aboard!', 'one']);
  assert.deepEqual(view.controls, [{ role: 'link', name: 'Help' }]);
  assert.deepEqual(parseSnapshot(''), { title: null, text: [], controls: [] });
});
