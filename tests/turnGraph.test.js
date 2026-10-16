// Sprint 4 (ARCH §5): the one way a transition is named, in the log and on
// the diagram.
import test from 'node:test';
import assert from 'node:assert/strict';
import { guardLabel, transitionLabel } from '../src/watch/turnGraph.mjs';

test('guards read as words: type, then each parameter as name value', () => {
  assert.equal(guardLabel({ type: 'phase', params: { is: 'asking' } }), 'phase is asking');
  assert.equal(guardLabel({ type: 'showing', params: { text: 'Ticket issued' } }), 'showing text Ticket issued');
  assert.equal(guardLabel({ type: 'counted', params: { field: 'tries', at_least: 3 } }), 'counted field tries at_least 3');
  assert.equal(guardLabel('sold_out'), 'sold_out');
  assert.equal(guardLabel(), '');
});

test('transitions: the event (done for a finished invoke, always for eventless), then the guard', () => {
  assert.equal(transitionLabel('OBSERVE'), 'OBSERVE');
  assert.equal(transitionLabel('STEP'), 'STEP');
  assert.equal(transitionLabel('xstate.done.actor.0.(machine).looking', { type: 'phase', params: { is: 'asking' } }), 'done: phase is asking');
  assert.equal(transitionLabel('xstate.done.actor.0.(machine).acting'), 'done');
  assert.equal(transitionLabel('', 'asked_to_leave'), 'always: asked_to_leave');
});

import { readFileSync } from 'node:fs';
import YAML from 'yaml';
import { turnGraph } from '../src/watch/turnGraph.mjs';
import { layout } from '../src/watch/layout.mjs';

const turnOf = (example) => YAML.parse(readFileSync(`examples/${example}/sketch.yaml`, 'utf8')).turn;

test('every example\'s turn becomes every state and every transition, labelled', () => {
  const graph = turnGraph(turnOf('web'));
  assert.deepEqual(graph.nodes.map((node) => node.id), ['waiting', 'looking', 'answering', 'replying', 'finished']);
  assert.deepEqual(graph.edges.map(({ from, to, label }) => `${from} -${label}-> ${to}`), [
    'waiting -OBSERVE-> looking',
    'looking -done: showing text Welcome aboard-> finished',
    'looking -done: phase is asking-> answering',
    'looking -done-> waiting',
    'answering -STEP-> replying',
    'replying -done-> waiting',
  ]);
  assert.equal(graph.nodes.at(-1).final, true);
  for (const example of ['cli', 'http', 'mcp', 'mcp-remote']) assert.equal(turnGraph(turnOf(example)).edges.length, 6, example);
});

test('the layout puts states in columns by distance from the start, every edge drawn, nothing overlapping', () => {
  const drawn = layout(turnGraph(turnOf('cli')));
  const column = Object.fromEntries(drawn.nodes.map((node) => [node.id, node.column]));
  assert.deepEqual(column, { waiting: 0, looking: 1, answering: 2, finished: 2, replying: 3 });
  assert.equal(drawn.edges.length, 6);
  for (const edge of drawn.edges) assert.match(edge.path, /^M -?\d+,-?\d+ C /);
  const boxes = drawn.nodes;
  for (const [index, a] of boxes.entries()) {
    const later = boxes.slice(index + 1);
    for (const b of later) {
      const isApart = a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y;
      assert.ok(isApart, `${a.id} and ${b.id} overlap`);
    }
  }
  assert.ok(drawn.width > 0 && drawn.height > 0);
});

test('a state nothing reaches still gets a place, after the rest', () => {
  const drawn = layout(turnGraph({ initial: 'a', states: { a: { on: { GO: 'b' } }, b: {}, orphan: {} } }));
  assert.deepEqual(drawn.nodes.map((node) => [node.id, node.column]), [['a', 0], ['b', 1], ['orphan', 2]]);
});
