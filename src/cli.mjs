// Sprint 1 (UND-4, UND-5 AC3, ADR-U5): the `understudy` command.
//
//   understudy run <dir> [--steps N]   play <dir>'s part against its app (needs TYPESAFE_API_KEY)
//   understudy check <dir>             load and check <dir>'s adapter and part, start nothing
//   understudy library [<dir>]         every name a part may use, with its meaning
//
// Exit codes are the same for every command: 0 done, 1 the run failed
// after starting, 2 refused before starting. Every failure is one
// `understudy: <message>` line on stderr - never a stack trace.

import { UsageError, RunError } from './errors.mjs';
import { genericLibrary } from './library.mjs';

export const DEFAULT_STEPS = 50;
const KEY = 'TYPESAFE_API_KEY';

const USAGE = `usage: understudy run <dir> [--steps N]   play <dir>'s part against its app (needs ${KEY})
       understudy check <dir>             check <dir>'s adapter and part without starting anything
       understudy library [<dir>]         list every name a part may use, with its meaning
`;

/**
 * The listing `understudy library` prints: kinds in order, one
 * `  name - doc` line per name. `extra` is an adapter's own names.
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
  let steps = DEFAULT_STEPS;
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

function oneDirectory(command, positional, { isOptional = false } = {}) {
  const quoted = positional.map((each) => JSON.stringify(each)).join(', ');
  if (positional.length > 1) throw new UsageError(`${command} takes one directory (got ${quoted})`);
  if (!isOptional && positional.length === 0) throw new UsageError(`${command} needs an example directory, e.g. understudy ${command} examples/cli`);
  return positional[0];
}

async function loadModule(name) {
  return import(name);
}

const defaultCommands = {
  async run(directory, options) {
    const { runPart } = await loadModule('./run.mjs');
    return runPart(directory, options);
  },
  async check(directory) {
    const { checkPart } = await loadModule('./part.mjs');
    return checkPart(directory);
  },
  async adapterLibrary(directory) {
    const { adapterLibrary } = await loadModule('./part.mjs');
    return adapterLibrary(directory);
  },
};

const HELP = new Set(['--help', '-h', 'help']);

/**
 * Runs one command line; resolves the exit code. Streams and commands are
 * injectable so tests never start a real app or call Jev.
 * @param {string[]} argv
 * @param {{ environment?: object, stdout?: { write: Function }, stderr?: { write: Function },
 *   commands?: { run?: Function, check?: Function, adapterLibrary?: Function } }} [io]
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
      await use.run(oneDirectory(command, positional), { steps, stdout, stderr, environment });
      return 0;
    }
    if (command === 'check') {
      stdout.write(`${await use.check(oneDirectory(command, positional))}\n`);
      return 0;
    }
    if (command === 'library') {
      const directory = oneDirectory(command, positional, { isOptional: true });
      stdout.write(libraryListing(directory ? await use.adapterLibrary(directory) : null));
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
