// Sprint 1 UND-1/UND-2: the examples, played end to end through their
// real targets by a Jev double - the same path as a live run, without the
// network. (`make test-live` plays them with real Jev.)
import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { runPart } from '../src/run.mjs';

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

async function playExample(directory, prefer) {
  const logRoot = mkdtempSync(path.join(tmpdir(), 'understudy-example-'));
  test.after(() => rmSync(logRoot, { recursive: true, force: true }));
  let stdout = '';
  await runPart(directory, {
    stdout: { write: (text) => { stdout += text; } }, stderr: { write: () => {} },
    makeJudge: () => judgePreferring(prefer), logRoot, pollMs: 20, steps: 20,
    signals: new EventEmitter(), // eslint-disable-line unicorn/prefer-event-target -- stands in for `process`
  });
  return stdout.trim().split('\n').map((line) => JSON.parse(line));
}

test('the CLI example is played to its end state through the real program', async () => {
  const lines = await playExample('examples/cli', ['size:medium', 'milk:oat', 'confirm:order']);
  assert.deepEqual(lines.filter((line) => !line.final).map((line) => line.move), ['size:medium', 'milk:oat', 'confirm:order']);
  assert.deepEqual(lines.at(-1), { final: true, outcome: 'done', steps: 3, state: 'finished' });
});
