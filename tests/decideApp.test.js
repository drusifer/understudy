// Sprint 5 UND-21 AC2-4 (ARCH §4): the owner's film gate over the evening
// servers - only evening showings of horror at 70+ or anything above 90
// are offered; films without a score are held back and said once; what
// was removed is in the move for the step line; a used showing is spent.
import test from 'node:test';
import assert from 'node:assert/strict';
import { startTarget } from '../src/targets/mcp.mjs';
import { mcpApp } from '../src/apps/mcp.mjs';

const from = 'examples/evening/sketch.yaml';
const SPEC = {
  kind: 'mcp',
  servers: [
    { name: 'boxoffice', from, entry: { command: 'node', args: ['boxoffice.mjs'] } },
    { name: 'ratings', from, entry: { command: 'node', args: ['ratings.mjs'] } },
  ],
};
const DECIDE = {
  'boxoffice/seat_map.showing': {
    join: 'title',
    gates: { starts: { at_least: '17:00' }, any: [{ genre: 'horror', tomato: { at_least: 70 } }, { tomato: { at_least: 91 } }] },
  },
};

async function setUp() {
  const target = await startTarget(SPEC, { directory: 'examples/evening', environment: process.env });
  test.after(() => target.close());
  const notes = [];
  const app = mcpApp({ decide: DECIDE });
  app.notify = (line) => {
    notes.push(line);
  };
  const moveFor = async (id) => app.moves(await target.view()).offered.find((move) => move.id === id);
  // As in a run: every answer is looked at before the next call.
  const call = async (action) => {
    await target.act(action);
    return app.moves(await target.view());
  };
  return { target, app, notes, moveFor, call };
}

test('showings wait for their film\'s score, then only those passing the gate are offered', async () => {
  const { notes, moveFor, call } = await setUp();
  const waiting = (await call({ server: 'boxoffice', tool: 'list_films', arguments: {} })).blocked.find((move) => move.id === 'tool:boxoffice/seat_map');
  assert.match(waiting.why, /^argument "showing" is waiting for tomato for Night Shift/);
  assert.ok(notes.includes('holding back showing s2 - no "tomato" for "Night Shift" yet'));
  assert.ok(notes.every((line) => !line.includes('showing s1 ')), 'an afternoon showing is removed, not held');

  for (const title of ['Night Shift', 'The Hollow Wood', 'Paper Boats', 'Orbit', 'Crimson Static', 'Sunday Lunch']) {
    await call({ server: 'ratings', tool: 'rating', arguments: { title } });
  }
  const move = await moveFor('tool:boxoffice/seat_map');
  assert.deepEqual(move.open[0].candidates, ['s2', 's13', 's8', 's4']);
  const [decision] = move.decided;
  assert.equal(decision.argument, 'boxoffice/seat_map.showing');
  assert.deepEqual(decision.held, []);
  assert.deepEqual(decision.removed.find((each) => each.value === 's1'), { value: 's1', why: 'starts 14:00 < 17:00' });
  assert.deepEqual(decision.removed.find((each) => each.value === 's6'), { value: 's6', why: 'none of any: tomato 64 < 70; tomato 64 < 91' });
  assert.equal(notes.filter((line) => line.startsWith('holding back showing s2')).length, 1, 'said once');
});

test('a showing used in a call that answered is spent', async () => {
  const { app, moveFor, call } = await setUp();
  await call({ server: 'boxoffice', tool: 'list_films', arguments: {} });
  await call({ server: 'ratings', tool: 'rating', arguments: { title: 'Night Shift' } });
  let move = await moveFor('tool:boxoffice/seat_map');
  assert.deepEqual(move.open[0].candidates, ['s2', 's13']);
  const { actions } = app.act({ ...move, filled: { showing: 's2' } });
  for (const action of actions) await call(action);
  move = await moveFor('tool:boxoffice/seat_map');
  assert.deepEqual(move.open[0].candidates, ['s13']);
});
