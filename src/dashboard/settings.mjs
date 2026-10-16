// Sprint 6 UND-32 (ARCH §4 "Save an edit", ADR-0024/0025): the access panels'
// edits, saved to the sketch. Only the settings a panel shows can change
// (allow-listed paths); only the edited value's text in the file is
// replaced (found through the YAML parser), so comments and layout stay; the result is checked with loadSketch on a copy
// before anything is written. The first edit of a sketch keeps a factory
// copy in <folder>/.factory/; POWER on puts every copy back.

import { cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import YAML from 'yaml';
import { UsageError } from '../errors.mjs';
import { loadSketch } from '../sketch.mjs';
import { sketchNames } from './rack.mjs';

const SKETCH = 'sketch.yaml';
const FACTORY = '.factory';
const ANY = Symbol('any name');
// What a panel may change - nothing else in a sketch.
const ALLOWED = [
  ['inputs', ANY, 'default'],
  ['inputs', ANY, 'choose'],
  ['decide', ANY, 'scores', ANY, 'range'],
  ['decide', ANY, 'scores', ANY, 'order'],
  ['decide', ANY, 'scores', ANY, 'ask'],
  ['questions', ANY, 'looks_at'],
];

const PLAIN = /^[A-Za-z_][\w ./-]*$/;
const RESERVED = /^(?:true|false|null|yes|no|on|off|~)$/i;

/**
 * A value as YAML flow text: lists in brackets, plain words unquoted.
 */
export function flowText(value) {
  if (Array.isArray(value)) return `[${value.map((each) => flowText(each)).join(', ')}]`;
  if (typeof value === 'string') return PLAIN.test(value) && !RESERVED.test(value) && value.trim() === value ? value : JSON.stringify(value);
  return JSON.stringify(value);
}

/**
 * `text` with the value at `keys` replaced in place; a key the file does
 * not have yet is added through the document (its layout may then change).
 */
function patched(text, keys, value) {
  const document = YAML.parseDocument(text);
  const node = document.getIn(keys, true);
  if (node?.range) return text.slice(0, node.range[0]) + flowText(value) + text.slice(node.range[1]);
  document.setIn(keys, value);
  return document.toString({ lineWidth: 0 });
}

const isAllowed = (keys) => Array.isArray(keys) && ALLOWED.some((pattern) => pattern.length === keys.length
  && pattern.every((part, index) => typeof keys[index] === 'string' && (part === ANY || part === keys[index])));

/**
 * @param {{ folder: string }} options
 */
export function createSettings({ folder }) {
  const factoryOf = (sketch) => path.join(folder, FACTORY, `${sketch}.yaml`);

  /**
   * The edited text, checked as a whole sketch on a copy of its directory.
   * @returns {string|null} why it was refused, or null
   */
  async function refusalOf(sketch, text) {
    const scratch = mkdtempSync(path.join(tmpdir(), 'understudy-edit-'));
    const copy = path.join(scratch, sketch);
    try {
      cpSync(path.join(folder, sketch), copy, { recursive: true });
      writeFileSync(path.join(copy, SKETCH), text);
      await loadSketch(copy);
      return null;
    } catch (error) {
      if (!(error instanceof UsageError)) throw error;
      // Name the real file, and only what is wrong in it.
      return error.message.replace(/^.*?sketch\.yaml: /, '');
    } finally {
      rmSync(scratch, { recursive: true, force: true });
    }
  }

  return {
    /**
     * Saves changes - `[{ path: [...keys], value }]` - to one sketch, all or nothing.
     * @returns {Promise<{ status: number, value: object }>}
     */
    async edit({ sketch, changes } = {}) {
      if (typeof sketch !== 'string' || !sketchNames(folder).includes(sketch)) return { status: 404, value: { problem: `no sketch "${sketch}" in ${folder}` } };
      if (!Array.isArray(changes) || changes.length === 0 || changes.some((change) => !isAllowed(change?.path))) {
        return { status: 400, value: { problem: 'only the settings the panels show can be changed' } };
      }
      const file = path.join(folder, sketch, SKETCH);
      const original = readFileSync(file, 'utf8');
      let text = original;
      for (const { path: keys, value } of changes) text = patched(text, keys, value);
      const problem = await refusalOf(sketch, text);
      if (problem) return { status: 422, value: { problem } };
      if (!existsSync(factoryOf(sketch))) {
        mkdirSync(path.dirname(factoryOf(sketch)), { recursive: true });
        writeFileSync(factoryOf(sketch), original);
      }
      writeFileSync(file, text);
      return { status: 200, value: { ok: true } };
    },

    /**
     * Puts every edited sketch back as it was before its first edit
     * (POWER on, UND-32 AC4), and forgets the copies.
     * @returns {string[]} the sketches restored
     */
    restore() {
      const directory = path.join(folder, FACTORY);
      if (!existsSync(directory)) return [];
      const restored = [];
      for (const entry of readdirSync(directory)) {
        const sketch = entry.replace(/\.yaml$/, '');
        if (!sketchNames(folder).includes(sketch)) continue;
        writeFileSync(path.join(folder, sketch, SKETCH), readFileSync(path.join(directory, entry)));
        rmSync(path.join(directory, entry));
        restored.push(sketch);
      }
      rmSync(directory, { recursive: true, force: true });
      return restored;
    },
  };
}
