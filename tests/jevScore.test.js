// Sprint 5 UND-23, UND-24 (ARCH §4, ADR-0020): Jev's Score as a factor -
// asked once per row, in one request per look, reused afterwards - and
// the final pick: the sketch's pick instructions, the inputs it is told,
// and a shortlist of one taken without asking.
import test from 'node:test';
import assert from 'node:assert/strict';
import { startTarget } from '../src/targets/mcp.mjs';
import { mcpApp } from '../src/apps/mcp.mjs';
import { fillArguments } from '../src/library.mjs';

const from = 'examples/evening/sketch.yaml';
const SPEC = { kind: 'mcp', servers: [
  { name: 'boxoffice', from, entry: { command: 'node', args: ['boxoffice.mjs'] } },
  { name: 'ratings', from, entry: { command: 'node', args: ['ratings.mjs'] } },
] };
const TITLES = ['Night Shift', 'The Hollow Wood', 'Paper Boats', 'Orbit', 'Crimson Static', 'Sunday Lunch'];
const LEVELS = ['Bored or walked out', 'Mixed - a few good scares', 'Solid fun - would recommend', 'Loved it - best of the year'];
const QUESTIONS = { audience: { type: 'score', looks_at: 'reviews', instructions: 'How much would someone who loves horror enjoy this film?', levels: LEVELS } };
const DECIDE = {
  'boxoffice/seat_map.showing': {
    join: 'title',
    gates: { starts: { at_least: '17:00' }, any: [{ genre: 'horror', tomato: { at_least: 70 } }, { tomato: { at_least: 91 } }] },
    scores: { tomato: { range: [70, 100], weight: 1 }, audience: { ask: 'audience', weight: 'audience' } },
  },
};

/**
 * A Jev double that answers every Score: 3 (loved it) when the reviews
 * scream, else 1; it remembers each request.
 */
function scoringJudge() {
  const requests = [];
  return {
    requests,
    async systemOne(request) {
      requests.push(request);
      const answers = {};
      for (const id of Object.keys(request.questions)) {
        const reviews = request.state.rows[id].reviews.join(' ');
        answers[id] = { type: 'score', score: /scream|best scare/.test(reviews) ? 3 : 1 };
      }
      return { answers };
    },
  };
}

async function evening() {
  const target = await startTarget(SPEC, { directory: 'examples/evening', environment: process.env });
  test.after(() => target.close());
  const app = mcpApp({ decide: DECIDE, questions: QUESTIONS, pick: { instructions: 'Choose for yourself and a friend, in the mood for `inputs.mood`.', with: ['mood'] } });
  app.inputs = { mood: 'fun', audience: 2 };
  const judge = scoringJudge();
  const look = async () => {
    const view = await target.view();
    await app.prepare(view, judge);
    return app.moves(view);
  };
  // As in a run: each call is a step the app makes, then a look.
  const call = async (action) => {
    const [made] = app.act({ call: action, filled: {} }).actions;
    await target.act(made);
    return look();
  };
  return { app, judge, look, call };
}

test('Jev scores the passing rows once, in one request; enthusiastic reviews rank first (UND-23 AC2-4)', async () => {
  const { judge, call } = await evening();
  await call({ server: 'boxoffice', tool: 'list_films', arguments: {} });
  for (const title of TITLES) await call({ server: 'ratings', tool: 'rating', arguments: { title } });
  // Each film that passes its gates is asked about as soon as it is rated; the others never.
  const asked = judge.requests.map((request) => Object.keys(request.questions).length);
  assert.deepEqual(asked, [1, 1, 1]);
  assert.equal(judge.requests[0].questions.r1.type, 'score');
  assert.deepEqual(judge.requests[0].questions.r1.criteria, LEVELS);
  assert.match(judge.requests[0].questions.r1.instructions, /^About `rows\.r1\.reviews`: How much/);

  const moves = await call({ server: 'ratings', tool: 'rating', arguments: { title: 'Night Shift' } });
  assert.equal(judge.requests.length, 3, 'a look with nothing new asks nothing');
  const move = moves.offered.find((each) => each.id === 'tool:boxoffice/seat_map');
  const [{ table, jev }] = move.decided;
  // Night Shift's screaming reviews (audience 1) beat Paper Boats' higher
  // tomato with calm reviews (audience 1/3, squared by its weight 2).
  assert.deepEqual(table.map((each) => each.value), ['s2', 's13', 's4', 's8']);
  assert.deepEqual(table[0].factors, { tomato: 0.4, audience: 1 });
  assert.deepEqual(table[3].factors, { tomato: 0.767, audience: 0.111 });
  assert.deepEqual(jev, { asked: 0, reused: 4 });
});

test('the final pick carries the pick instructions and the inputs it is told (UND-24 AC3)', async () => {
  const { call } = await evening();
  await call({ server: 'boxoffice', tool: 'list_films', arguments: {} });
  let moves;
  for (const title of TITLES) moves = await call({ server: 'ratings', tool: 'rating', arguments: { title } });
  const move = moves.offered.find((each) => each.id === 'tool:boxoffice/seat_map');
  assert.deepEqual(move.told, { mood: 'fun' });
  const requests = [];
  const judge = { async systemOne(request) {
    requests.push(request);
    return { answers: { argument_showing: { choice: 'v2' } } };
  } };
  const filled = await fillArguments({ judge, state: { tools: [] }, question: { instructions: 'Buy tickets.' }, move, phase: 'asking' });
  assert.deepEqual(filled, { showing: 's13' });
  assert.deepEqual(requests[0].state.inputs, { mood: 'fun' });
  assert.match(requests[0].questions.argument_showing.instructions, /^Choose for yourself and a friend, in the mood for `inputs\.mood`\. You are calling/);
});

test('a shortlist of one is taken without asking Jev (UND-24 AC4)', async () => {
  const judge = { async systemOne() {
    throw new Error('Jev was asked');
  } };
  const move = { id: 'tool:pick_seats', call: { tool: 'pick_seats' }, open: [{ name: 'seat', schema: {}, candidates: ['s2-E15'], isDecided: true }] };
  assert.deepEqual(await fillArguments({ judge, state: {}, question: { instructions: 'x' }, move, phase: 'asking' }), { seat: 's2-E15' });
});
