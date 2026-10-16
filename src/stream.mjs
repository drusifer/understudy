// Sprint 4 UND-13 (ARCH §3, ADR-0014): a run's lines - `start`, `state`,
// the step lines and the final line - written once, in order, to stdout
// and the log file, and handed to anyone listening (the watch page).

import { appendFileSync } from 'node:fs';

/**
 * @param {{ stdout: { write: Function }, logFile: string }} options
 */
export function createStream({ stdout, logFile }) {
  const history = [];
  const listeners = new Set();
  return {
    /**
     * One line, everywhere it goes.
     * @param {object} line
     */
    emit(line) {
      const text = `${JSON.stringify(line)}\n`;
      stdout.write(text);
      appendFileSync(logFile, text);
      history.push(line);
      for (const listener of listeners) listener(line);
    },
    /**
     * Every line so far, then each new one as it is emitted.
     * @param {(line: object) => void} listener
     * @returns {() => void} stop listening
     */
    listen(listener) {
      for (const line of history) listener(line);
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
