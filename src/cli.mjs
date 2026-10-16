// Sprint 1 (UND-4, UND-5 AC3, ADR-U5): the `understudy` command.
//
//   understudy run <sketch> [--steps N]   play the sketch against its app (needs TYPESAFE_API_KEY)
//   understudy check <sketch>             load and check the sketch, start nothing
//   understudy library [<sketch>]         every name a sketch may use, with its meaning
//
// <sketch> is a directory holding sketch.yaml, or the file itself (ADR-0011).
//
// Exit codes are the same for every command: 0 done, 1 the run failed
// after starting, 2 refused before starting. Every failure is one
// `understudy: <message>` line on stderr - never a stack trace.

import { UsageError, RunError } from './errors.mjs';
import { genericLibrary } from './library.mjs';

const KEY = 'TYPESAFE_API_KEY';

const USAGE = `usage: understudy run <sketch> [--steps N]   play the sketch against its app (needs ${KEY})
       understudy check <sketch>             check the sketch without starting anything
       understudy library [<sketch>]         list every name a sketch may use, with its meaning
<sketch> is a directory holding sketch.yaml (e.g. examples/cli) or the file itself.
`;

/**
 * The listing `understudy library` prints: kinds in order, one
 * `  name - doc` line per name. `extra` is the names a sketch's hooks add.
 */
export function libraryListing(extra = null) {
  const lines = [];
  const sections = [['', genericLibrary({})], ...(extra ? [[`${extra.name} `, extra.library]] : [])];
  for (const [prefix, library] of sections) {
    for (const kind of ['guards', 'actions', 'actors']) {
      const entries = Object.entries(library[kind] ?? {});
      if (entries.length === 0) continue;
      lines.push(`${prefix}${kind}:`, ...entries.map(([name, entry]) => `  ${name} - ${entry.doc}`));
    }
  }
  return `${lines.join('\n')}\n`;
}

function parse(argv) {
  const [command, ...rest] = argv;
  const positional = [];
  let steps;
  for (let index = 0; index < rest.length; index++) {
    const argument = rest[index];
    if (command === 'run' && (argument === '--steps' || argument.startsWith('--steps='))) {
      const value = argument === '--steps' ? rest[++index] : argument.slice('--steps='.length);
      if (!value) throw new UsageError('--steps needs a number, e.g. --steps 20');
      if (!/^[1-9]\d*$/.test(value ?? '')) throw new UsageError(`--steps must be a positive whole number (got "${value ?? ''}")`);
      steps = Number(value);
    } else if (argument.startsWith('-')) {
      throw new UsageError(`no option "${argument}" for ${command} - see understudy --help`);
    } else {
      positional.push(argument);
    }
  }
  return { command, positional, steps };
}

function oneSketch(command, positional, { isOptional = false } = {}) {
  const quoted = positional.map((each) => JSON.stringify(each)).join(', ');
  if (positional.length > 1) throw new UsageError(`${command} takes one sketch (got ${quoted})`);
  if (!isOptional && positional.length === 0) throw new UsageError(`${command} needs a sketch, e.g. understudy ${command} examples/cli`);
  return positional[0];
}

async function loadModule(name) {
  return import(name);
}

const defaultCommands = {
  async run(location, options) {
    const { runSketch } = await loadModule('./run.mjs');
    return runSketch(location, options);
  },
  async check(location) {
    const { checkSketch } = await loadModule('./sketch.mjs');
    return checkSketch(location);
  },
  async sketchLibrary(location) {
    const { sketchLibrary } = await loadModule('./sketch.mjs');
    return sketchLibrary(location);
  },
};

const HELP = new Set(['--help', '-h', 'help']);

/**
 * Runs one command line; resolves the exit code. Streams and commands are
 * injectable so tests never start a real app or call Jev.
 * @param {string[]} argv
 * @param {{ environment?: object, stdout?: { write: Function }, stderr?: { write: Function },
 *   commands?: { run?: Function, check?: Function, sketchLibrary?: Function } }} [io]
 */
export async function main(argv, { environment = process.env, stdout = process.stdout, stderr = process.stderr, commands = {} } = {}) {
  try {
    if (HELP.has(argv[0])) {
      stdout.write(USAGE);
      return 0;
    }
    if (argv.length === 0) throw new UsageError(USAGE.trimEnd());
    const { command, positional, steps } = parse(argv);
    const use = { ...defaultCommands, ...commands };
    if (command === 'run') {
      // UND-4: Jev is required, so a run without its key never starts.
      if (!environment[KEY]?.trim()) throw new UsageError(`understudy run needs a TypeSafe key: set ${KEY}`);
      await use.run(oneSketch(command, positional), { steps, stdout, stderr, environment });
      return 0;
    }
    if (command === 'check') {
      stdout.write(`${await use.check(oneSketch(command, positional))}\n`);
      return 0;
    }
    if (command === 'library') {
      const location = oneSketch(command, positional, { isOptional: true });
      stdout.write(libraryListing(location ? await use.sketchLibrary(location) : null));
      return 0;
    }
    throw new UsageError(`no command "${command}" - commands: run, check, library (see understudy --help)`);
  } catch (error) {
    if (error instanceof UsageError) {
      stderr.write(`understudy: ${error.message}\n`);
      return 2;
    }
    stderr.write(error instanceof RunError ? `understudy: ${error.message}\n` : `understudy: unexpected error: ${error.message}\n`);
    return 1;
  }
}
