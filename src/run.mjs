// Sprint 1 UND-1 (ARCH §4): `understudy run <sketch>` - one understudy
// plays one app until its sketch's turn reaches the end state.
//
// Generalized from recard's tools/jev/runner.mjs: everything that is not
// the app lives here - the step cap, the first-move timeout, noticing the
// app died, Ctrl-C, the step log - so no sketch can be missing it.
// Every step is one JSON line on stdout and in
// build/runs/<sketch>/<timestamp>.jsonl, plus one readable line on
// stderr; every outcome ends with one final line, and the target is
// closed however the run ends.

import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { MachineSeat } from './seat.mjs';
import { resolveInputs, weightsOf } from './inputs.mjs';
import { loadSketch, shown } from './sketch.mjs';
import { RunError } from './errors.mjs';
import { createStream } from './stream.mjs';
import { startWatch } from './watch/server.mjs';
import { createGate, OPEN_GATE } from './watch/gate.mjs';
import { createJevJudge, reportJevFailures } from './jev.mjs';

export const DEFAULT_STEPS = 50;

async function startTarget(spec, { directory, environment }) {
  const { startTarget: start } = await import(`./targets/${spec.kind}.mjs`);
  return start(spec, { directory, environment });
}

/**
 * Jev's failures as the run reports them: the SDK's own message, never
 * the key, and an outcome for the final line.
 */
const stepCount = (count) => `${count} step${count === 1 ? '' : 's'}`;

function summaryLine(entry) {
  const confidence = typeof entry.confidence === 'number' ? ` (${entry.confidence})` : '';
  const offList = entry.offList ? ` - off-list ${JSON.stringify(entry.answer)} first` : '';
  return `understudy: step ${entry.step} ${entry.phase} -> ${entry.move}${confidence}${offList}`;
}

/**
 * Ctrl-C once: stop at the next safe state. Twice: stop now.
 */
function watchInterrupts(signals, onSecond, onFirst = () => {}) {
  const state = { count: 0 };
  const handler = () => {
    state.count += 1;
    if (state.count === 1) onFirst();
    else if (state.count === 2) onSecond();
  };
  signals.on('SIGINT', handler);
  return { isAsked: () => state.count > 0, stop: () => signals.off('SIGINT', handler) };
}

/**
 * Plays a sketch against its app.
 * @param {string} location a directory holding sketch.yaml, or the file
 * @param {{ steps?: number, stdout?: { write: Function }, stderr?: { write: Function },
 *   environment?: object, makeJudge?: (environment: object) => object|Promise<object>,
 *   makeTarget?: (spec: object, options: { directory: string, environment: object }) => Promise<object>,
 *   logRoot?: string, firstMoveMs?: number, stallMs?: number, pollMs?: number, signals?: import('node:events').EventEmitter,
 *   clock?: () => number, watch?: { port?: number, host?: string, paused?: boolean }|null, makeWatch?: typeof startWatch,
 *   gate?: ReturnType<typeof createGate>|null }} [options]
 *   `watch` serves the live view (`--watch`); the server starts before anything else, so a
 *   busy port refuses the run with nothing started. `paused` starts it paused (`--pause`).
 *   `gate` is a pause gate the caller holds (the dashboard's STEP and PAUSE, UND-39).
 * @throws {UsageError} before anything starts; {RunError} once it has.
 */
export async function runSketch(location, {
  steps, inputs = [], stdout = process.stdout, stderr = process.stderr, environment = process.env,
  makeJudge = createJevJudge, makeTarget = startTarget, logRoot = path.join('build', 'runs'),
  firstMoveMs = 10_000, stallMs = 10_000, pollMs = 250, signals = process, clock = Date.now,
  watch = null, makeWatch = startWatch, gate = null,
} = {}) {
  const sketch = await loadSketch(location);
  // UND-24: inputs out of their range or list refuse the run before it starts.
  const values = resolveInputs(sketch.inputs, inputs);
  const limit = steps ?? sketch.steps ?? DEFAULT_STEPS;
  const logDirectory = path.join(logRoot, sketch.name);
  const logFile = path.join(logDirectory, `${new Date(clock()).toISOString().replaceAll(':', '-')}.jsonl`);
  const stream = createStream({ stdout, logFile });
  // The page's controls reach the run's gate once the run has made it.
  const controls = { gate: OPEN_GATE };
  const watcher = watch ? await makeWatch({ port: watch.port, host: watch.host, mode: 'live', source: stream, control: (action) => controls.gate[action]() }) : null;
  if (watcher) stderr.write(`understudy: watch at ${(watcher.urls ?? [watcher.url]).join(' or ')}\n`);
  try {
    await playSketch({ sketch, inputs: values, limit, stream, logDirectory, logFile, stdout, stderr, environment, makeJudge, makeTarget, firstMoveMs, stallMs, pollMs, signals, clock, watch, watcher, controls, held: gate });
  } finally {
    await watcher?.close();
  }
}

/**
 * The gate a watched run moves through: paused from the start with
 * `--pause`; every change shown on the page, and a pause said on stderr.
 */
function pauseGate({ run, watch, watcher, stderr, clock }) {
  let isSaid = false;
  return createGate({
    isPaused: watch.paused === true, clock,
    onChange({ paused, waiting }) {
      watcher.send({ event: 'control', paused, waiting, before_step: run.taken + 1 });
      if (!paused) isSaid = false;
      if (paused && waiting && !isSaid) {
        isSaid = true;
        stderr.write('understudy: paused - step or resume from the page, or Ctrl-C\n');
      }
    },
  });
}

/**
 * The run itself, once anything that can refuse it has been checked.
 */
async function playSketch({ sketch, inputs, limit, stream, logDirectory, logFile, stderr, environment, makeJudge, makeTarget, firstMoveMs, stallMs, pollMs, signals, clock, watch, watcher, controls, held }) {
    const judge = reportJevFailures(await makeJudge(environment));
  const target = await makeTarget(sketch.target, { directory: sketch.directory, environment });
  const write = (entry) => stream.emit(entry);
  const run = { taken: 0, seat: null, lastMoveAt: null, pausedBefore: 0, app: sketch.app, isStoppedPaused: false };
  const gate = held ?? (watcher ? pauseGate({ run, watch, watcher, stderr, clock }) : OPEN_GATE);
  controls.gate = gate;
  // A generic app may have something to say once (a tool it cannot offer).
  if (Object.hasOwn(sketch.app, 'notify')) sketch.app.notify = (line) => stderr.write(`understudy: ${line}\n`);
  if (Object.hasOwn(sketch.app, 'inputs')) sketch.app.inputs = inputs;
  if (Object.hasOwn(sketch.app, 'weights')) sketch.app.weights = weightsOf(sketch.inputs, inputs);
  const interrupts = watchInterrupts(signals, () => target.close(), () => gate.stop());
  try {
    mkdirSync(logDirectory, { recursive: true });
    const declared = Object.keys(inputs).length > 0 ? { inputs } : {};
    // UND-42: the run's limits, so a gauge can show how near it is to each.
    const limits = { steps: limit, first_move_ms: firstMoveMs, stall_ms: stallMs };
    write({ event: 'start', sketch: sketch.name, plays: target.describe(), ...declared, limits, turn: sketch.turn, at: new Date(clock()).toISOString() });
    stderr.write(`understudy: playing ${sketch.name} (${target.describe()}) - log ${shown(logFile)}\n`);
    // UND-40: every Jev request carries the run's inputs (services.inputs).
    Object.assign(sketch.services, { target, judge, name: 'understudy', player: sketch.player, app: sketch.app, inputs });
    run.seat = new MachineSeat({ machine: sketch.machine, services: sketch.services, pollMs, clock });
    await playUntilDone({ run, target, steps: limit, waits: { firstMoveMs, stallMs }, clock, interrupts, write, stderr, gate });
  } catch (error) {
    flushChanges(run, write);
    const outcome = interrupts.isAsked() ? 'interrupted' : error.outcome ?? 'error';
    write({ event: 'ended', outcome, message: error.message });
    write({ final: true, outcome, steps: run.taken, state: run.seat?.state ?? null });
    throw error;
  } finally {
    gate.end();
    interrupts.stop();
    await target.close();
  }
  flushChanges(run, write);
  if (!interrupts.isAsked() && run.seat.hasTag('walked-away')) {
    // UND-25: leaving empty-handed is a result, not a failure.
    const { removed, sentence } = sketch.app.leaving?.() ?? { removed: {}, sentence: 'walked away' };
    write({ event: 'walked-away', removed });
    stderr.write(`understudy: ${sentence}\n`);
    write({ final: true, outcome: 'walked-away', steps: run.taken, state: run.seat.state });
    return;
  }
  const outcome = interrupts.isAsked() ? 'interrupted' : 'done';
  const stopped = run.isStoppedPaused
    ? `stopped by Ctrl-C while paused, after ${stepCount(run.taken)}`
    : `stopped by Ctrl-C after ${stepCount(run.taken)}, at a safe state`;
  if (outcome === 'interrupted') write({ event: 'ended', outcome, message: stopped });
  write({ final: true, outcome, steps: run.taken, state: run.seat.state });
  if (outcome === 'interrupted') throw new RunError(stopped, { outcome });
}

/**
 * The loop: "is it my move?", then one step, until the seat is done -
 * stopping on the step cap, a dead app, no first move or a stall.
 */
async function playUntilDone({ run, target, steps, waits, clock, interrupts, write, stderr, gate }) {
  const started = clock();
  for (;;) {
    const next = await run.seat.nextMove({ shouldStop: interrupts.isAsked });
    flushChanges(run, write);
    if (next === 'done') return;
    const exited = target.exited?.();
    if (exited) {
      // Its last output can land between the look and the exit: one more
      // look decides whether it ended where the sketch ends.
      if (await run.seat.nextMove({ shouldStop: interrupts.isAsked }) === 'done') return;
      throw new RunError(`${exited.who ?? target.describe()} exited with code ${exited.code} before the end state`, { outcome: 'app-exited' });
    }
    if (next === 'move') {
      // ADR-0016: a paused run waits here, before Jev is asked anything.
      if (await gate.beforeMove() === 'stop') {
        run.isStoppedPaused = true;
        return;
      }
      await takeStep({ run, steps, write, stderr });
      run.lastMoveAt = clock();
      run.pausedBefore = gate.pausedMs();
    } else if (!gate.isPaused()) {
      // Idle limits count running time only.
      const idleFor = clock() - (run.lastMoveAt ?? started) - (gate.pausedMs() - run.pausedBefore);
      await checkIdle({ run, target, waits, idleFor });
    }
  }
}

/**
 * Nothing to do yet: fine for a while, then no first move (before step 1)
 * or a stall (after it) - one rule for every target (ADR-0010).
 */
async function checkIdle({ run, target, waits, idleFor }) {
  const limit = run.taken === 0 ? waits.firstMoveMs : waits.stallMs;
  if (idleFor < limit) return;
  const view = await target.view();
  // The app can say why nothing is offered; else the view speaks for itself.
  const why = run.app.idle?.(view);
  const shownView = JSON.stringify(view);
  if (run.taken === 0) {
    const seen = why ?? 'last view: ' + shownView;
    throw new RunError(`no first move from ${target.describe()} within ${limit / 1000} s - ${seen}`, { outcome: 'no-first-move' });
  }
  const seen = why ?? 'the app showed: ' + shownView.slice(0, 200);
  throw new RunError(`stalled: nothing to do for ${limit / 1000} s after step ${run.taken} (last state: ${run.seat.state})`
    + ` - ${seen} - if this is where the sketch should end, add a showing guard (docs/SKETCHES.md)`, { outcome: 'stalled' });
}

/**
 * The seat's state changes since the last flush, one `state` line each
 * (ADR-0014).
 */
function flushChanges(run, write) {
  const changes = run.seat?.drainChanges() ?? [];
  for (const change of changes) write({ event: 'state', ...change });
}

/**
 * One step within the cap, logged as it is taken.
 */
async function takeStep({ run, steps, write, stderr }) {
  if (run.taken === steps) {
    throw new RunError(`stopped after ${stepCount(steps)} without reaching the end state (last state: ${run.seat.state})`, { outcome: 'step-cap' });
  }
  run.taken += 1;
  const record = await stepped(run.seat, run.taken);
  flushChanges(run, write);
  const entry = { step: run.taken, ...record, state: run.seat.state };
  write(entry);
  stderr.write(`${summaryLine(entry)}\n`);
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
