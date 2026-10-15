// A program started in the example directory, for the targets that run
// one: `process` (it IS the app) and `http` (it serves the app). Starting,
// noticing it ended, and stopping it live here once.

import { spawn } from 'node:child_process';
import path from 'node:path';
import { UsageError } from '../errors.mjs';

const CLOSE_MS = 2000;

/**
 * Starts `command` in `directory` with piped stdio; refuses with a
 * `UsageError` when it cannot start at all.
 * @param {{ command: string, args?: string[] }} spec
 * @param {{ directory: string, environment?: object }} options
 * @returns {Promise<{ child: import('node:child_process').ChildProcess, description: string,
 *   exited: () => ({ code: number|null, signal: string|null }|null), close: () => Promise<void> }>}
 */
export async function startProgram({ command, args: arguments_ = [] }, { directory, environment = process.env }) {
  const description = [command, ...arguments_].join(' ');
  const child = spawn(command, arguments_, { cwd: path.resolve(directory), env: environment, stdio: ['pipe', 'pipe', 'pipe'] });
  const state = { exited: null };
  const closed = new Promise((resolve) => child.once('close', (code, signal) => {
    state.exited = { code, signal };
    resolve();
  }));
  child.stdin.on('error', () => {}); // writing to a program that just ended is reported by `exited`, not thrown
  await new Promise((resolve, reject) => {
    child.once('spawn', resolve);
    child.once('error', (error) => reject(new UsageError(`could not start ${description}: ${error.message}`)));
  });
  return {
    child,
    description,
    exited: () => state.exited,
    async close() {
      if (state.exited) return;
      child.kill('SIGTERM');
      const timer = setTimeout(() => child.kill('SIGKILL'), CLOSE_MS);
      await closed;
      clearTimeout(timer);
    },
  };
}
