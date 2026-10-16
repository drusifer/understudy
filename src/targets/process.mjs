// Sprint 1 UND-1 (ARCH §5, ADR-U1): a command-line program as a target.
//
// The view is what a person would see in a terminal: everything the
// program printed (stdout, by line - an unfinished last line such as a
// prompt included) with each input echoed where it was typed, how many
// inputs have been sent, and how it exited. A move is one line written to
// its stdin. A program has no talk channel.

import { startProgram } from './program.mjs';

/**
 * Starts `spec.command` in the example directory.
 * @param {{ kind: 'process', command: string, args?: string[] }} spec
 * @param {{ directory: string }} options
 */
export async function startTarget(spec, { directory }) {
  const program = await startProgram(spec, { directory });
  const state = { complete: [], partial: '', received: 0, sent: 0 };
  program.child.stdout.setEncoding('utf8');
  program.child.stdout.on('data', (chunk) => {
    state.received += chunk.length;
    const pieces = (state.partial + chunk).split('\n');
    state.partial = pieces.pop();
    state.complete.push(...pieces);
  });

  return {
    describe: () => program.description,
    async view() {
      const lines = state.partial === '' ? [...state.complete] : [...state.complete, state.partial];
      return { lines, seq: state.received, sent: state.sent, exited: program.exited() };
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
      program.child.stdin.write(`${input}\n`);
    },
    exited: program.exited,
    close: program.close,
  };
}
