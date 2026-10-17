// Sprint 6 UND-29 (ARCH §3, §4 "Play", ADR-0023): the console's runs - one at
// a time, through the same `runSketch` the command line uses. The run's
// stdout lines (start, state, steps, final) go to every open page as they
// are written, with its stderr lines and `dashboard` notes beside them;
// STOP is Ctrl-C to that run.

import { EventEmitter } from 'node:events';
import path from 'node:path';
import { runSketch } from '../run.mjs';
import { createGate } from '../watch/gate.mjs';
import { sketchNames } from './rack.mjs';

const STDERR = 'understudy: ';

/**
 * Whole lines out of written chunks.
 */
function lineWriter(onLine) {
  let pending = '';
  return {
    write(chunk) {
      pending += chunk;
      const lines = pending.split('\n');
      pending = lines.pop();
      for (const line of lines) if (line !== '') onLine(line);
    },
  };
}

/**
 * A control's value as `--input` text: a switch as on/off.
 */
function wordOf(value) {
  if (typeof value !== 'boolean') return value;
  return value ? 'on' : 'off';
}

/**
 * The control values as `--input` pairs: switches as on/off.
 */
function pairsOf(inputs = {}) {
  return Object.entries(inputs).map(([name, value]) => `${name}=${wordOf(value)}`);
}

/**
 * @param {{ folder: string, hub: { reset: Function, send: Function }, environment?: object,
 *   run?: typeof runSketch, runOptions?: object }} options
 *   `runOptions` go to every run as they are (tests: a Jev double, a log root).
 */
export function createRunner({ folder, hub, environment = process.env, run = runSketch, runOptions = {} }) {
  let current = null;

  async function playing(sketch, inputs, signals, state, gate) {
    let outcome = null;
    let isStarted = false;
    const stdout = lineWriter((text) => {
      const line = JSON.parse(text);
      if (line.event === 'start') {
        isStarted = true;
        // A STOP pressed while the servers were starting is delivered now:
        // the run only listens for Ctrl-C once it has started.
        if (state.isStopAsked) signals.emit('SIGINT');
      }
      if (line.final) outcome = line.outcome;
      hub.send(line);
    });
    const stderr = lineWriter((text) => hub.send({ event: 'dashboard', stderr: text.startsWith(STDERR) ? text.slice(STDERR.length) : text }));
    try {
      await run(path.join(folder, sketch), { ...runOptions, inputs: pairsOf(inputs), environment, stdout, stderr, signals, gate });
    } catch (error) {
      // UND-29 AC4: refused before it started - say why; nothing is running.
      if (!isStarted) return { refused: error.message };
    }
    return { outcome };
  }

  return {
    isRunning: () => current !== null,

    /**
     * Starts `sketch` with the controls' values - `paused`: before its first
     * move (STEP, UND-39); refused while one runs.
     * @returns {Promise<{ status: number, value?: object }>}
     */
    async play({ sketch, inputs, paused = false } = {}) {
      if (current) return { status: 409, value: { problem: 'a run is going - press STOP first' } };
      if (typeof sketch !== 'string' || !sketchNames(folder).includes(sketch)) return { status: 404, value: { problem: `no sketch "${sketch}" in ${folder}` } };
      // Stands in for `process` in runSketch, which listens for 'SIGINT' on it.
      const signals = new EventEmitter(); // eslint-disable-line unicorn/prefer-event-target -- runSketch takes an EventEmitter
      // UND-39: every pause, step and resume is shown on the open pages.
      const gate = createGate({ isPaused: paused === true, onChange: (change) => hub.send({ event: 'dashboard', ...change }) });
      hub.reset();
      hub.send({ event: 'dashboard', running: true, sketch, inputs: inputs ?? {}, paused: paused === true });
      const playingNow = { sketch, signals, gate, isStopAsked: false, finished: null };
      playingNow.finished = (async () => {
        const ended = await playing(sketch, inputs, signals, playingNow, gate);
        current = null;
        hub.send({ event: 'dashboard', running: false, sketch, ...ended });
        return ended;
      })();
      current = playingNow;
      return { status: 202, value: { running: true } };
    },

    /**
     * Stops the run as Ctrl-C would (UND-29 AC2).
     */
    async stop() {
      if (!current) return { status: 409, value: { problem: 'nothing is running' } };
      current.isStopAsked = true;
      current.signals.emit('SIGINT');
      return { status: 202, value: { stopping: true } };
    },

    /**
     * PAUSE, STEP and RESUME (UND-39): the run's gate, refused when nothing
     * runs or the gate cannot (pause while paused, step or resume while running).
     */
    control(action) {
      if (!current) return { status: 409, value: { problem: 'nothing is running' } };
      if (!current.gate[action]()) return { status: 409, value: { problem: `cannot ${action} now` } };
      return { status: 202, value: { [action]: true } };
    },

    /**
     * The run in progress, ended (for the console closing).
     */
    async close() {
      if (!current) return;
      current.isStopAsked = true;
      current.signals.emit('SIGINT');
      await current.finished;
    },

    // Resolves when the run in progress ends (tests).
    finished: () => current?.finished ?? Promise.resolve(null),
  };
}
