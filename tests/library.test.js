// Sprint 1 (ARCH §5, ADR-U3/U4): the generic vocabulary - `look` and
// `phase` read the app's phase through the adapter, and `play` never
// sends a move Jev picked off the offered list.
import test from 'node:test';
import assert from 'node:assert/strict';
import { genericLibrary } from '../src/library.mjs';
import { RunError } from '../src/errors.mjs';

const QUESTIONS = {
  next: { type: 'choice', instructions: 'What next?', criteria: { order: 'place the order', cancel: 'stop' } },
};

const APP = {
  phase: (view) => view.screen,
  project: (view) => ({ screen: view.screen }),
  options: () => [{ id: 'order', what: 'place the order' }, { id: 'cancel', what: 'stop' }],
  act: (move) => ({ actions: [{ input: move.id }] }),
};

function fakeTarget(screen = 'menu') {
  const target = { acted: [], said: [] };
  Object.assign(target, {
    view: async () => ({ screen, seq: 1 }),
    talk: async () => [],
    act: async (action) => { target.acted.push(action); },
    say: async (text) => { target.said.push(text); },
  });
  return target;
}

function judgeAnswering(...choices) {
  const asked = [];
  return {
    asked,
    async systemOne(request) {
      asked.push(request);
      const choice = choices[Math.min(asked.length - 1, choices.length - 1)];
      return { answers: { next: { type: 'choice', choice, confidence: 0.8 } } };
    },
  };
}

const servicesWith = (judge, target = fakeTarget()) => ({ target, judge, name: 'understudy', questions: QUESTIONS, player: {}, app: APP });
const play = (library, context = {}) => library.actors.play.fn({ input: { context, phase: 'menu', question: 'next' } });

test('the vocabulary uses app words, not card-table words', () => {
  const library = genericLibrary({});
  assert.deepEqual(Object.keys(library.guards).toSorted((a, b) => a.localeCompare(b)), ['changed', 'counted', 'phase', 'played', 'quiet', 'showing', 'verdict']);
  assert.deepEqual(Object.keys(library.actors).toSorted((a, b) => a.localeCompare(b)), ['ask', 'judge', 'look', 'play']);
  for (const kind of ['guards', 'actions', 'actors']) {
    const entries = Object.entries(library[kind]);
    for (const [name, entry] of entries) {
      assert.ok(entry.doc && !/\btable\b|\bgame\b|\bbot\b/.test(entry.doc), `${kind}.${name} doc: "${entry.doc}"`);
    }
  }
});

test('look reports the phase the adapter reads off the view, and the phase guard tests it', async () => {
  const library = genericLibrary(servicesWith(judgeAnswering('order'), fakeTarget('checkout')));
  const output = await library.actors.look.fn({ input: { context: {}, event: {} } });
  assert.equal(output.phase, 'checkout');
  assert.equal(library.guards.phase.fn({ event: { output } }, { is: 'checkout' }), true);
  assert.equal(library.guards.phase.fn({ event: { output } }, { is: 'menu' }), false);
});

test('look also hands on the view it read, and showing finds text anywhere in it', async () => {
  const library = genericLibrary(servicesWith(judgeAnswering('order'), fakeTarget('Welcome aboard!')));
  const output = await library.actors.look.fn({ input: { context: {}, event: {} } });
  assert.deepEqual(output.view, { screen: 'Welcome aboard!', seq: 1 });
  assert.equal(library.guards.showing.fn({ event: { output } }, { text: 'Welcome aboard' }), true);
  assert.equal(library.guards.showing.fn({ event: { output } }, { text: 'Goodbye' }), false);
  const nested = { output: { view: { body: { items: [{ name: 'tea', state: 'dispensed' }] } } } };
  assert.equal(library.guards.showing.fn({ event: nested }, { text: 'dispensed' }), true, 'nested strings count');
});

test('an offered pick is sent to the app and recorded', async () => {
  const target = fakeTarget();
  const library = genericLibrary(servicesWith(judgeAnswering('order'), target));
  const { record } = await play(library);
  assert.deepEqual(target.acted, [{ input: 'order' }]);
  assert.equal(record.move, 'order');
  assert.equal(record.offList, undefined);
});

test('an off-list pick is never sent: Jev is asked once more and the record says so', async () => {
  const target = fakeTarget();
  const judge = judgeAnswering('refund', 'cancel');
  const library = genericLibrary(servicesWith(judge, target));
  const { record } = await play(library);
  assert.equal(judge.asked.length, 2);
  assert.deepEqual(target.acted, [{ input: 'cancel' }], 'only the second, offered answer reaches the app');
  assert.equal(record.offList, true);
  assert.equal(record.answer, 'refund');
  assert.equal(record.move, 'cancel');
});

test('two off-list picks stop the run, naming both answers, and nothing is sent', async () => {
  const target = fakeTarget();
  const library = genericLibrary(servicesWith(judgeAnswering('refund', 'teleport'), target));
  await assert.rejects(play(library), (error) => {
    assert.ok(error instanceof RunError);
    assert.match(error.message, /"refund".*"teleport"/);
    assert.match(error.message, /offered: order, cancel/);
    return true;
  });
  assert.deepEqual(target.acted, []);
});
