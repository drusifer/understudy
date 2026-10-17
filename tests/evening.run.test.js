// Sprint 5 UND-25, UND-26 (ARCH §4): the evening example played end to end
// through both real servers by a Jev double - it books the owner's seats,
// or, when the box office is full, walks away and the run succeeds.
import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { runSketch } from '../src/run.mjs';

const ORDER = ['tool:boxoffice/pay', 'tool:boxoffice/pick_seats', 'tool:ratings/rating', 'tool:boxoffice/seat_map', 'tool:boxoffice/list_films'];

/**
 * A Jev double for the evening: moves in ORDER of preference, the first
 * value offered for each argument, and Scores from how the reviews read.
 */
function eveningJudge() {
  const requests = [];
  return {
    requests,
    async systemOne(request) {
      requests.push(request);
      const answers = {};
      for (const [key, question] of Object.entries(request.questions)) {
        if (question.type === 'score') {
          const reviews = request.state.rows[key].reviews.join(' ');
          answers[key] = { type: 'score', score: /scream|best scare/.test(reviews) ? 3 : 1 };
          continue;
        }
        const offered = Object.keys(question.criteria);
        // Pay only right after holding seats, as a person would.
        const order = request.state.last_call?.tool === 'boxoffice/pick_seats' && !request.state.last_call.failed ? ORDER : ORDER.slice(1);
        const choice = key === 'next' ? order.find((id) => offered.some((each) => each.startsWith(id))) : 'v1';
        answers[key] = { type: 'choice', choice: offered.find((each) => each.startsWith(choice)) ?? offered[0], confidence: 0.9 };
      }
      return { answers };
    },
  };
}

async function playEvening({ inputs = [], environment = process.env } = {}) {
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-evening-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  let stdout = '';
  let stderr = '';
  await runSketch('examples/evening', {
    inputs, environment,
    stdout: { write: (text) => { stdout += text; } }, stderr: { write: (text) => { stderr += text; } },
    makeJudge: () => eveningJudge(), logRoot, pollMs: 20, steps: 30,
    signals: new EventEmitter(), // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`
  });
  const lines = stdout.trim().split('\n').map((line) => JSON.parse(line));
  return { lines, steps: lines.filter((line) => line.step), stderr };
}

test('the evening books two central seats in row E for an evening horror film (UND-26 AC1)', async () => {
  const { lines, steps } = await playEvening();
  assert.deepEqual(lines[0].inputs, { mood: 'fun', tomato: 3, audience: 7, row: 7, centre: 10, evenings: true, tickets: 2 });
  const paid = steps.at(-1);
  assert.match(paid.response.text, /^Ticket issued: Night Shift at 19:30, seats E1[5-6], E1[6-7]/);
  const seatStep = steps.find((line) => line.move === 'tool:boxoffice/pick_seats');
  const [decided] = seatStep.decided;
  assert.equal(decided.argument, 'boxoffice/pick_seats.seat');
  assert.deepEqual(Object.keys(decided.table[0].factors), ['row', 'centre']);
  assert.ok(decided.table.every((each, index) => index === 0 || each.total <= decided.table[index - 1].total), 'best first');
  assert.deepEqual(lines.at(-1), { final: true, outcome: 'done', steps: steps.length, state: 'booked' });
});

test('turning the centre knob down changes the score table (UND-26 AC2)', async () => {
  const { steps } = await playEvening({ inputs: ['centre=0'] });
  const [decided] = steps.find((line) => line.move === 'tool:boxoffice/pick_seats').decided;
  assert.ok(decided.table.every((each) => each.factors.centre === 1), 'centre off: every seat scores 1 on it');
});

test('when nothing qualifies the understudy walks away, says why, and the run succeeds (UND-25 AC1-4, UND-26 AC3)', async () => {
  const { lines, steps, stderr } = await playEvening({ environment: { ...process.env, BOX_STATE: 'full' } });
  assert.equal(steps.some((line) => line.move === 'tool:boxoffice/pick_seats'), false, 'nothing held or paid');
  const walked = lines.find((line) => line.event === 'walked-away');
  // Rows D-F are taken: what is left is single seats elsewhere.
  assert.ok(walked.removed['boxoffice/pick_seats.seat'].together > 0);
  assert.deepEqual(walked.removed['boxoffice/seat_map.showing'], { starts: 6, any: 3 });
  assert.match(stderr, /understudy: walked away - nothing qualified: starts removed 6 showings; any removed 3 showings; together removed \d+ seats\n/);
  assert.deepEqual(lines.at(-1), { final: true, outcome: 'walked-away', steps: steps.length, state: 'walked_away' });
});

test('the evenings switch off lets afternoon showings qualify (UND-28 AC3, UND-33 AC3)', async () => {
  const { steps } = await playEvening({ inputs: ['evenings=off'] });
  const showing = steps.find((line) => line.move === 'tool:boxoffice/seat_map');
  const [decided] = showing.decided;
  assert.ok(decided.table.some((each) => each.value === 's1'), 'Night Shift at 14:00 is on the shortlist');
  assert.equal(decided.removed.some((each) => each.why.startsWith('starts')), false);
});

test('three tickets: three side-by-side seats, on the ticket (UND-34 AC3)', async () => {
  const { steps } = await playEvening({ inputs: ['tickets=3'] });
  const hold = steps.find((line) => line.move === 'tool:boxoffice/pick_seats');
  assert.equal(hold.response.call.arguments.count, 3);
  const [decided] = hold.decided;
  assert.ok(decided.removed.some((each) => each.why.startsWith('together 2 < 3')), 'pairs are too short now');
  assert.match(steps.at(-1).response.text, /seats E\d+, E\d+, E\d+/);
});
