// Sprint 1 UND-1 (ARCH §4): `understudy run <dir>` - one understudy
// plays one app until its part reaches the end state.
//
// Generalized from recard's tools/jev/runner.mjs: everything that is not
// the app lives here - the step cap, the first-move timeout, noticing the
// app died, Ctrl-C, the step log - so no part or adapter can be missing
// it. Every step is one JSON line on stdout and in
// build/runs/<adapter>/<timestamp>.jsonl, plus one readable line on
// stderr; every outcome ends with one final line, and the target is
// closed however the run ends.

import { appendFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { MachineSeat } from './seat.mjs';
import { loadPart, shown } from './part.mjs';
import { RunError, UsageError } from './errors.mjs';

const KEY = 'TYPESAFE_API_KEY';

async function typesafeJudge(environment) {
  const { TypeSafeClient } = await import('@typesafe-ai/sdk');
  try {
    return new TypeSafeClient({ apiKey: environment[KEY] });
  } catch (error) {
    throw new UsageError(`Jev could not be set up: ${error.message}`);
  }
}

async function startTarget(spec, { directory }) {
  const { startTarget: start } = await import(`./targets/${spec.kind}.mjs`);
  return start(spec, { directory });
}

/**
 * Jev's failures as the run reports them: the SDK's own message, never
 * the key, and an outcome for the final line.
 */
function reportingFailures(judge) {
  return {
    async systemOne(request) {
      try {
        return await judge.systemOne(request);
      } catch (error) {
        throw new RunError(`Jev request failed: ${error.message}`, { outcome: 'jev-error', cause: error });
      }
    },
  };
}

function summaryLine(entry) {
  const confidence = typeof entry.confidence === 'number' ? ` (${entry.confidence})` : '';
  const offList = entry.offList ? ` - off-list ${JSON.stringify(entry.answer)} first` : '';
  return `understudy: step ${entry.step} ${entry.phase} -> ${entry.move}${confidence}${offList}`;
}

/**
 * Ctrl-C once: stop at the next safe state. Twice: stop now.
 */
function watchInterrupts(signals, onSecond) {
  const state = { count: 0 };
  const handler = () => {
    state.count += 1;
    if (state.count === 2) onSecond();
  };
  signals.on('SIGINT', handler);
  return { isAsked: () => state.count > 0, stop: () => signals.off('SIGINT', handler) };
}

/**
 * Plays `<directory>`'s part against its app.
 * @param {string} directory
 * @param {{ steps?: number, stdout?: { write: Function }, stderr?: { write: Function },
 *   environment?: object, makeJudge?: (environment: object) => object|Promise<object>,
 *   makeTarget?: (spec: object, options: { directory: string }) => Promise<object>,
 *   logRoot?: string, firstMoveMs?: number, pollMs?: number, signals?: import('node:events').EventEmitter,
 *   clock?: () => number }} [options]
 * @throws {UsageError} before anything starts; {RunError} once it has.
 */
export async function runPart(directory, {
  steps = 50, stdout = process.stdout, stderr = process.stderr, environment = process.env,
  makeJudge = typesafeJudge, makeTarget = startTarget, logRoot = path.join('build', 'runs'),
  firstMoveMs = 10_000, pollMs = 250, signals = process, clock = Date.now,
} = {}) {
  const part = await loadPart(directory);
  const { adapter } = part;
  const judge = reportingFailures(await makeJudge(environment));
  const target = await makeTarget(adapter.target, { directory });
  const logDirectory = path.join(logRoot, adapter.name);
  const logFile = path.join(logDirectory, `${new Date(clock()).toISOString().replaceAll(':', '-')}.jsonl`);
  const write = (entry) => {
    const line = `${JSON.stringify(entry)}\n`;
    stdout.write(line);
    appendFileSync(logFile, line);
  };
  const run = { taken: 0, seat: null };
  const interrupts = watchInterrupts(signals, () => target.close());
  try {
    mkdirSync(logDirectory, { recursive: true });
    stderr.write(`understudy: playing ${adapter.name} (${target.describe()}) - log ${shown(logFile)}\n`);
    Object.assign(part.services, { target, judge, name: 'understudy', player: adapter.player ?? {}, app: adapter.app });
    run.seat = new MachineSeat({ machine: part.machine, services: part.services, pollMs, clock });
    await playUntilDone({ run, target, steps, firstMoveMs, clock, interrupts, write, stderr });
  } catch (error) {
    write({ final: true, outcome: interrupts.isAsked() ? 'interrupted' : error.outcome ?? 'error', steps: run.taken, state: run.seat?.state ?? null });
    throw error;
  } finally {
    interrupts.stop();
    await target.close();
  }
  const outcome = interrupts.isAsked() ? 'interrupted' : 'done';
  write({ final: true, outcome, steps: run.taken, state: run.seat.state });
  if (outcome === 'interrupted') {
    throw new RunError(`stopped by Ctrl-C after ${run.taken} step${run.taken === 1 ? '' : 's'}, at a safe state`, { outcome });
  }
}

/**
 * The loop: "is it my move?", then one step, until the seat is done -
 * stopping on the step cap, a dead app or no first move.
 */
async function playUntilDone({ run, target, steps, firstMoveMs, clock, interrupts, write, stderr }) {
  const started = clock();
  for (;;) {
    const next = await run.seat.nextMove({ shouldStop: interrupts.isAsked });
    if (next === 'done') return;
    const exited = target.exited?.();
    if (exited) {
      // Its last output can land between the look and the exit: one more
      // look decides whether it ended where the part ends.
      if (await run.seat.nextMove({ shouldStop: interrupts.isAsked }) === 'done') return;
      throw new RunError(`${target.describe()} exited with code ${exited.code} before the end state`, { outcome: 'app-exited' });
    }
    if (next === 'move') {
      if (run.taken === steps) {
        throw new RunError(`stopped after ${steps} steps without reaching the end state (last state: ${run.seat.state})`, { outcome: 'step-cap' });
      }
      run.taken += 1;
      const record = await stepped(run.seat, run.taken);
      const entry = { step: run.taken, ...record, state: run.seat.state };
      write(entry);
      stderr.write(`${summaryLine(entry)}\n`);
    } else if (run.taken === 0 && clock() - started >= firstMoveMs) {
      const view = await target.view();
      throw new RunError(`no first move from ${target.describe()} within ${firstMoveMs / 1000} s - last view: ${JSON.stringify(view)}`, { outcome: 'no-first-move' });
    }
  }
}

/**
 * One step; a failure inside it is named by its step number.
 */
async function stepped(seat, number) {
  try {
    return await seat.step();
  } catch (error) {
    if (error instanceof RunError) throw new RunError(`step ${number}: ${error.message}`, { outcome: error.outcome, cause: error });
    throw error;
  }
}
