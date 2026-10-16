// Sprint 4 UND-16 (ARCH §4 "Replay", ADR-0014): a finished run's log, read
// and checked before it is served for replay. The log alone is enough: its
// start line carries the sketch's statechart.

import { existsSync, readFileSync, statSync } from 'node:fs';
import { UsageError } from '../errors.mjs';
import { shown } from '../sketch.mjs';

const OLD = 'no start line - replay needs a log written by understudy run (sprint 4 or later)';

/**
 * Every line of a run log, checked: JSON throughout, a start line first.
 * @param {string} file
 * @returns {object[]}
 */
export function readLog(file) {
  if (!existsSync(file) || !statSync(file).isFile()) throw new UsageError(`${shown(file)}: no such log - give a file from build/runs/<sketch>/`);
  const texts = readFileSync(file, 'utf8').split('\n').filter((text) => text.trim() !== '');
  if (texts.length === 0) throw new UsageError(`${shown(file)}: empty - ${OLD}`);
  const lines = texts.map((text, index) => {
    try {
      return JSON.parse(text);
    } catch {
      throw new UsageError(`${shown(file)}: line ${index + 1} is not JSON - this is not a run log`);
    }
  });
  if (lines[0]?.event !== 'start') throw new UsageError(`${shown(file)}: ${OLD}`);
  return lines;
}
