// A program started in the sketch directory, for the targets that run
// one: `process` (it IS the app), `http` (it serves the app) and `mcp` (it
// is the server). Starting, noticing it ended, what it last said on
// stderr, and stopping it live here once.

import { spawn } from 'node:child_process';
import path from 'node:path';
import { UsageError } from '../errors.mjs';

const CLOSE_MS = 2000;
const STDERR_LINES = 20;

/**
 * Starts `command` in `directory` with piped stdio; refuses with a
 * `UsageError` when it cannot start at all.
 * @param {{ command: string, args?: string[] }} spec
 * @param {{ directory: string, environment?: object }} options
 * @returns {Promise<{ child: import('node:child_process').ChildProcess, description: string,
 *   exited: () => ({ code: number|null, signal: string|null }|null), ended: Promise<void>,
 *   stderrTail: () => string[], close: () => Promise<void> }>}
 */
export async function startProgram({ command, args: arguments_ = [] }, { directory, environment = process.env }) {
  const description = [command, ...arguments_].join(' ');
  const child = spawn(command, arguments_, { cwd: path.resolve(directory), env: environment, stdio: ['pipe', 'pipe', 'pipe'] });
  const state = { exited: null, stderr: [], partial: '' };
  const closed = new Promise((resolve) => child.once('close', (code, signal) => {
    state.exited = { code, signal };
    resolve();
  }));
  child.stdin.on('error', () => {}); // writing to a program that just ended is reported by `exited`, not thrown
  child.stderr.setEncoding('utf8');
  child.stderr.on('data', (chunk) => {
    const pieces = (state.partial + chunk).split('\n');
    state.partial = pieces.pop();
    state.stderr = [...state.stderr, ...pieces].slice(-STDERR_LINES);
  });
  await new Promise((resolve, reject) => {
    child.once('spawn', resolve);
    child.once('error', (error) => reject(new UsageError(`could not start ${description}: ${error.message}`)));
  });
  return {
    child,
    description,
    exited: () => state.exited,
    ended: closed,
    stderrTail: () => [...state.stderr, ...(state.partial ? [state.partial] : [])].slice(-STDERR_LINES),
    async close() {
      if (state.exited) return;
      child.kill('SIGTERM');
      const timer = setTimeout(() => child.kill('SIGKILL'), CLOSE_MS);
      await closed;
      clearTimeout(timer);
    },
  };
}
