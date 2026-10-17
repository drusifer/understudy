// Sprint 6 UND-30, sprint 14 UND-41 (docs/design/DASHBOARD.md "State tube"):
// the statechart as a layered flow - initial state first, every state and
// edge laid out and labelled, nothing on top of anything else - and the
// tube's power ring.
import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSketch } from '../src/sketch.mjs';
import { turnGraph } from '../src/watch/turnGraph.mjs';
import { ringOf } from '../src/dashboard/tube.mjs';
import { flowLayout } from '../src/dashboard/flow.mjs';

const isOverlapping = (a, b) => a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;

test('the flow: every state placed, the initial one on top, finals marked, no two boxes overlapping (UND-41 AC1)', async () => {
  const graph = turnGraph((await loadSketch('examples/evening')).turn);
  const flow = await flowLayout(graph, [4]);
  const byName = (a, b) => a.localeCompare(b);
  assert.deepEqual(flow.nodes.map((node) => node.id).toSorted(byName), graph.nodes.map((node) => node.id).toSorted(byName));
  const waiting = flow.nodes.find((node) => node.id === 'waiting');
  assert.ok(waiting.initial);
  assert.equal(Math.min(...flow.nodes.map((node) => node.y)), waiting.y, 'the initial state is at the top');
  assert.deepEqual(flow.nodes.filter((node) => node.final).map((node) => node.id).toSorted(byName), ['booked', 'walked_away']);
  for (const [index, a] of flow.nodes.entries()) {
    const later = flow.nodes.slice(index + 1);
    for (const b of later) assert.ok(!isOverlapping(a, b), `${a.id} and ${b.id} overlap`);
    assert.ok(a.x >= 0 && a.y >= 0 && a.x + a.width <= flow.width && a.y + a.height <= flow.height, `${a.id} inside the drawing`);
  }
  assert.equal(flow.nodes.find((node) => node.id === 'walked_away').name, 'walked away');
});

test('every transition is routed and labelled with its event and guard; the decision edge is marked (UND-41 AC2)', async () => {
  const graph = turnGraph((await loadSketch('examples/evening')).turn);
  const flow = await flowLayout(graph, [4]);
  assert.equal(flow.edges.length, graph.edges.length);
  const toBooked = flow.edges.find((edge) => edge.to === 'booked');
  assert.deepEqual([toBooked.label, toBooked.sub], ['done', 'showing text Ticket issued']);
  for (const edge of flow.edges) {
    assert.ok(edge.points.length >= 2, `${edge.from}->${edge.to} is routed`);
    assert.ok(Number.isFinite(edge.lx) && Number.isFinite(edge.ly));
  }
  assert.deepEqual(flow.edges.filter((edge) => edge.isDecision).map((edge) => edge.index), [4]);
});

test('the ring: one arc per weight in its share of the rim, filled by its value (UND-30 AC3-4)', () => {
  const ring = ringOf([{ name: 'tomato', value: 1.5, range: [0, 3], colour: 'red' }, { name: 'row', value: 0, range: [0, 3], colour: 'cyan' }]);
  assert.equal(ring.length, 2);
  assert.deepEqual(ring.map((arc) => arc.name), ['tomato', 'row']);
  assert.notEqual(ring[0].fill, ring[0].track);
  assert.deepEqual(ringOf([]), []);
});
