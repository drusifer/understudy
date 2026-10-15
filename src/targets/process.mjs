// Sprint 1 UND-1 (ARCH §5, ADR-U1): a command-line program as a target.
//
// The view is what a person would see in a terminal: everything the
// program printed (stdout, by line - an unfinished last line such as a
// prompt included) with each input echoed where it was typed, how many
// inputs have been sent, and how it exited. A move is one line written to
// its stdin. A program has no talk channel.

import { spawn } from 'node:child_process';
import path from 'node:path';
import { UsageError } from '../errors.mjs';

const CLOSE_MS = 2000;

/**
 * Starts `spec.command` in the example directory.
 * @param {{ kind: 'process', command: string, args?: string[] }} spec
 * @param {{ directory: string }} options
 */
export async function startTarget(spec, { directory }) {
  const arguments_ = spec.args ?? [];
  const description = [spec.command, ...arguments_].join(' ');
  const child = spawn(spec.command, arguments_, { cwd: path.resolve(directory), stdio: ['pipe', 'pipe', 'pipe'] });
  const state = { complete: [], partial: '', received: 0, sent: 0, exited: null, errors: '' };
  const closed = new Promise((resolve) => child.once('close', (code, signal) => {
    state.exited = { code, signal };
    resolve();
  }));
  child.stdout.setEncoding('utf8');
  child.stdout.on('data', (chunk) => {
    state.received += chunk.length;
    const pieces = (state.partial + chunk).split('\n');
    state.partial = pieces.pop();
    state.complete.push(...pieces);
  });
  child.stderr.setEncoding('utf8');
  child.stderr.on('data', (chunk) => { state.errors += chunk; });
  child.stdin.on('error', () => {}); // writing to a program that just exited is reported by `exited`, not thrown

  await new Promise((resolve, reject) => {
    child.once('spawn', resolve);
    child.once('error', (error) => reject(new UsageError(`could not start ${description}: ${error.message}`)));
  });

  return {
    describe: () => description,
    async view() {
      const lines = state.partial === '' ? [...state.complete] : [...state.complete, state.partial];
      return { lines, seq: state.received, sent: state.sent, exited: state.exited };
    },
    async talk() {
      return [];
    },
    async say() {},
    async act({ input }) {
      state.sent += 1;
      // A terminal echoes what was typed; a pipe does not, so echo it here.
      state.complete.push(state.partial + input);
      state.partial = '';
      state.received += input.length + 1;
      child.stdin.write(`${input}\n`);
    },
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
