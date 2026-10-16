// Sprint 1 UND-1/UND-2: the examples, played end to end through their
// real targets by a Jev double - the same path as a live run, without the
// network. (`make test-live` plays them with real Jev.)
import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { runSketch } from '../src/run.mjs';

/**
 * Picks the offered option that `prefer` likes, else the first offered.
 */
function judgePreferring(prefer) {
  return {
    async systemOne({ questions }) {
      const [[key, question]] = Object.entries(questions);
      const offered = Object.keys(question.criteria);
      const choice = offered.find((id) => prefer.includes(id)) ?? offered[0];
      return { answers: { [key]: { type: 'choice', choice, confidence: 0.9 } } };
    },
  };
}

/**
 * Answers with the given ids in order (the last one repeats), offered or not.
 */
function judgeScripted(...ids) {
  let calls = 0;
  return {
    async systemOne({ questions }) {
      const [key] = Object.keys(questions);
      const choice = ids[Math.min(calls, ids.length - 1)];
      calls += 1;
      return { answers: { [key]: { type: 'choice', choice, confidence: 0.9 } } };
    },
  };
}

async function playExample(directory, prefer, judge = judgePreferring(prefer)) {
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-example-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  let stdout = '';
  await runSketch(directory, {
    stdout: { write: (text) => { stdout += text; } }, stderr: { write: () => {} },
    makeJudge: () => judge, logRoot, pollMs: 20, steps: 20,
    signals: new EventEmitter(), // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`
  });
  const all = stdout.trim().split('\n').map((line) => JSON.parse(line));
  // Step and final lines; the `start` and `state` lines (ADR-0014) ride along as `.events`.
  const lines = all.filter((line) => !line.event);
  lines.events = all.filter((line) => line.event);
  return lines;
}

test('the CLI example is played to its end state through the real program', async () => {
  const lines = await playExample('examples/cli', ['size:medium', 'milk:oat', 'confirm:order']);
  assert.deepEqual(lines.filter((line) => !line.final).map((line) => line.move), ['size:medium', 'milk:oat', 'confirm:order']);
  assert.deepEqual(lines.at(-1), { final: true, outcome: 'done', steps: 3, state: 'finished' });
});

test('the HTTP example is played to its end state through the real API; a refused move is logged, not fatal', async () => {
  const lines = await playExample('examples/http', [], judgeScripted('buy:tea', 'coin:2', 'buy:tea'));
  const steps = lines.filter((line) => !line.final);
  assert.deepEqual(steps.map((line) => line.move), ['buy:tea', 'coin:2', 'buy:tea']);
  assert.deepEqual(steps.map((line) => line.response), [{ status: 402 }, { status: 200 }, { status: 200 }]);
  assert.deepEqual(lines.at(-1), { final: true, outcome: 'done', steps: 3, state: 'finished' });
});

/**
 * Plays the box office: the move ids in order, and each argument's value
 * from `values` (a list is used in order, one per call).
 */
function judgeAtTheBoxOffice(moves, values) {
  let move = 0;
  const used = {};
  return {
    async systemOne({ questions }) {
      const answers = {};
      for (const [key, question] of Object.entries(questions)) {
        if (!key.startsWith('argument_')) {
          answers[key] = { type: 'choice', choice: moves[Math.min(move++, moves.length - 1)], confidence: 0.9 };
          continue;
        }
        const name = key.slice('argument_'.length);
        const wanted = [values[name]].flat();
        const value = wanted[Math.min(used[name] ?? 0, wanted.length - 1)];
        used[name] = (used[name] ?? 0) + 1;
        const choice = Object.entries(question.criteria).find(([, text]) => text === `\`${JSON.stringify(value)}\``)?.[0] ?? 'v99';
        answers[key] = { type: 'choice', choice, confidence: 0.9 };
      }
      return { answers };
    },
  };
}

test('the MCP example is played over stdio to a ticket, arguments chosen by Jev; a refused payment is logged, not fatal', async () => {
  const judge = judgeAtTheBoxOffice(['tool:list_films', 'tool:pick_seats', 'tool:pay', 'tool:pay'], { film: 'f2', count: 2, hold: 'h1', method: ['cash', 'card'] });
  const lines = await playExample('examples/mcp', [], judge);
  const steps = lines.filter((line) => !line.final);
  assert.deepEqual(steps.map((line) => line.move), ['tool:list_films', 'tool:pick_seats', 'tool:pay', 'tool:pay']);
  assert.deepEqual(steps.map((line) => line.response.call.arguments), [{}, { film: 'f2', count: 2 }, { hold: 'h1', method: 'cash' }, { hold: 'h1', method: 'card' }]);
  assert.deepEqual(steps.map((line) => line.response.isError), [false, false, true, false]);
  assert.match(steps[3].response.text, /^Ticket issued: 2 for Paper Boats/);
  assert.deepEqual(lines.at(-1), { final: true, outcome: 'done', steps: 4, state: 'finished' });
});

test('an argument Jev answers off the list twice stops the run, naming the argument and what was offered', async () => {
  const judge = judgeAtTheBoxOffice(['tool:list_films', 'tool:pick_seats'], { film: 'nope', count: 2 });
  await assert.rejects(playExample('examples/mcp', [], judge),
    { outcome: 'off-list', message: /^step 2: in phase "asking" Jev answered off the list twice for argument "film" of pick_seats \("v99", then "v99"\) - offered: "f1", "The Long Night"/ });
});

test('the MCP example ends on text only a result says - no tool description contains it (Smith, Gate 2)', async () => {
  const { loadSketch } = await import('../src/sketch.mjs');
  const { startTarget } = await import('../src/targets/mcp.mjs');
  const sketch = await loadSketch('examples/mcp');
  const ending = JSON.stringify(sketch.machine.config.states.looking.invoke.onDone[0].guard.params.text);
  const target = await startTarget(sketch.target, { directory: sketch.directory, environment: process.env });
  try {
    const { tools } = await target.view();
    assert.equal(ending, '"Ticket issued"');
    assert.ok(tools.every((tool) => !JSON.stringify(tool).includes(JSON.parse(ending))));
  } finally {
    await target.close();
  }
});
