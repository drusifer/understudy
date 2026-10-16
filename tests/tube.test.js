// Sprint 6 UND-30 (docs/design/DASHBOARD.md "State tube"): the tube's
// geometry - states round a loop from the initial one, finals inside beside
// their source, every edge drawn and labelled, the power ring.
import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSketch } from '../src/sketch.mjs';
import { turnGraph } from '../src/watch/turnGraph.mjs';
import { ringOf, tubeLayout } from '../src/dashboard/tube.mjs';

test('every state is placed and named; finals sit inside the loop (UND-30 AC1)', async () => {
  const sketch = await loadSketch('examples/evening');
  const graph = turnGraph(sketch.turn);
  const layout = tubeLayout(graph, [4]);
  const byName = (a, b) => a.localeCompare(b);
  assert.deepEqual(layout.nodes.map((node) => node.id).toSorted(byName), graph.nodes.map((node) => node.id).toSorted(byName));
  const distance = (node) => Math.hypot(node.x - 300, node.y - 300);
  const waiting = layout.nodes.find((node) => node.id === 'waiting');
  assert.deepEqual([waiting.x, waiting.y], [130, 300], 'the initial state at the left');
  for (const node of layout.nodes) assert.ok(node.final ? distance(node) < 120 : Math.abs(distance(node) - 170) < 1, node.id);
});

test('every transition is drawn and labelled with its event and guard (UND-30 AC1)', async () => {
  const graph = turnGraph((await loadSketch('examples/evening')).turn);
  const layout = tubeLayout(graph, []);
  assert.equal(layout.edges.length, graph.edges.length);
  const toBooked = layout.edges.find((edge) => edge.to === 'booked');
  assert.deepEqual([toBooked.label, toBooked.sub], ['done', 'showing text Ticket iss…']);
  const observe = layout.edges.find((edge) => edge.label === 'OBSERVE');
  assert.match(observe.d, / A 170 170 0 0 1 /, 'neighbours run along the loop');
  for (const edge of layout.edges) assert.match(edge.d, /^M [\d.]+ [\d.]+ /);
});

test('the ring: one arc per weight in its share of the rim, filled by its value (UND-30 AC3-4)', () => {
  const ring = ringOf([{ name: 'tomato', value: 1.5, range: [0, 3], colour: 'red' }, { name: 'row', value: 0, range: [0, 3], colour: 'cyan' }]);
  assert.equal(ring.length, 2);
  assert.deepEqual(ring.map((arc) => arc.name), ['tomato', 'row']);
  assert.notEqual(ring[0].fill, ring[0].track);
  assert.deepEqual(ringOf([]), []);
});
