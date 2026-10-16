// Sprint 1 (UND-4, UND-5 AC3, ADR-U5): the `understudy` command.
//
//   understudy run <sketch> [--steps N] [--watch [--port N] [--pause]]
//                                         play the sketch against its app (needs TYPESAFE_API_KEY)
//   understudy check <sketch>             load and check the sketch, start nothing
//   understudy library [<sketch>]         every name a sketch may use, with its meaning
//   understudy watch <log> [--port N]     replay a finished run on the watch page (sprint 4)
//
// <sketch> is a directory holding sketch.yaml, or the file itself (ADR-0011).
//
// Exit codes are the same for every command: 0 done, 1 the run failed
// after starting, 2 refused before starting. Every failure is one
// `understudy: <message>` line on stderr - never a stack trace.

import { UsageError, RunError } from './errors.mjs';
import { genericLibrary } from './library.mjs';

const KEY = 'TYPESAFE_API_KEY';

const USAGE = `usage: understudy run <sketch> [--steps N] [--watch [--port N] [--pause]]
           play the sketch against its app (needs ${KEY});
           --watch serves a live view of the run on 127.0.0.1; --pause starts it paused
       understudy check <sketch>
           check the sketch without starting anything
       understudy library [<sketch>]
           list every name a sketch may use, with its meaning
       understudy watch <log.jsonl> [--port N]
           replay a finished run's log on the watch page
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

// Each option: the commands that take it, and how its value is read
// (`null` for a flag).
const OPTIONS = {
  steps: { commands: ['run'], read: (value) => {
    if (!/^[1-9]\d*$/.test(value)) throw new UsageError(`--steps must be a positive whole number (got "${value}")`);
    return Number(value);
  }, needs: 'a number', example: '--steps 20' },
  port: { commands: ['run', 'watch'], read: (value) => {
    const port = Number(value);
    if (!/^\d+$/.test(value) || port < 1 || port > 65_535) throw new UsageError(`--port must be a port number from 1 to 65535 (got "${value}")`);
    return port;
  }, needs: 'a port number', example: '--port 4173' },
  watch: { commands: ['run'], read: null },
  pause: { commands: ['run'], read: null },
};

/**
 * One `--name` or `--name=value` (or `--name value`): its name and value.
 */
function option(command, rest, index) {
  const [flag, inline] = rest[index].slice(2).split(/=(.*)/s, 2);
  const known = OPTIONS[flag];
  if (!known?.commands.includes(command)) throw new UsageError(`no option "--${flag}" for ${command} - see understudy --help`);
  if (known.read === null) return { name: flag, value: true, used: 0 };
  const value = inline ?? rest[index + 1];
  if (!value) throw new UsageError(`--${flag} needs ${known.needs}, e.g. ${known.example}`);
  return { name: flag, value: known.read(value), used: inline === undefined ? 1 : 0 };
}

function parse(argv) {
  const [command, ...rest] = argv;
  const positional = [];
  const options = {};
  for (let index = 0; index < rest.length; index++) {
    if (!rest[index].startsWith('-')) {
      positional.push(rest[index]);
      continue;
    }
    const { name, value, used } = option(command, rest, index);
    options[name] = value;
    index += used;
  }
  if (command === 'run' && options.port !== undefined && !options.watch) throw new UsageError('--port needs --watch (it is the watch page\'s port)');
  if (command === 'run' && options.pause && !options.watch) throw new UsageError('--pause needs --watch (the page is where you step it)');
  return { command, positional, ...options };
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
  async watch(file, { port, stderr }) {
    const { readLog } = await loadModule('./watch/replay.mjs');
    const { startWatch, logSource } = await loadModule('./watch/server.mjs');
    const lines = readLog(file);
    const server = await startWatch({ port, mode: 'replay', source: logSource(lines) });
    stderr.write(`understudy: replaying ${file} at ${server.url} - Ctrl-C to stop\n`);
    // UND-16 AC5: serve until Ctrl-C, then stop cleanly (exit 0).
    await new Promise((resolve) => process.once('SIGINT', resolve));
    await server.close();
  },
};

const HELP = new Set(['--help', '-h', 'help']);

/**
 * Each command: what it does with the parsed command line. Writes to
 * stdout; failures are thrown.
 */
const COMMANDS = {
  async run({ positional, steps, watch, port, pause }, { use, environment, stdout, stderr }) {
    // UND-4: Jev is required, so a run without its key never starts.
    if (!environment[KEY]?.trim()) throw new UsageError(`understudy run needs a TypeSafe key: set ${KEY}`);
    await use.run(oneSketch('run', positional), { steps, stdout, stderr, environment, watch: watch ? { port, paused: pause === true } : null });
  },
  async check({ positional }, { use, stdout }) {
    stdout.write(`${await use.check(oneSketch('check', positional))}\n`);
  },
  async library({ positional }, { use, stdout }) {
    const location = oneSketch('library', positional, { isOptional: true });
    stdout.write(libraryListing(location ? await use.sketchLibrary(location) : null));
  },
  async watch({ positional, port }, { use, stderr }) {
    const quoted = positional.map((each) => JSON.stringify(each)).join(', ');
    if (positional.length !== 1) throw new UsageError(positional.length === 0 ? 'watch needs a run log, e.g. understudy watch build/runs/coffee-cli/<time>.jsonl' : `watch takes one log (got ${quoted})`);
    await use.watch(positional[0], { port, stderr });
  },
};

/**
 * Runs one command line; resolves the exit code. Streams and commands are
 * injectable so tests never start a real app or call Jev.
 * @param {string[]} argv
 * @param {{ environment?: object, stdout?: { write: Function }, stderr?: { write: Function },
 *   commands?: { run?: Function, check?: Function, sketchLibrary?: Function, watch?: Function } }} [io]
 */
export async function main(argv, { environment = process.env, stdout = process.stdout, stderr = process.stderr, commands = {} } = {}) {
  try {
    if (HELP.has(argv[0])) {
      stdout.write(USAGE);
      return 0;
    }
    if (argv.length === 0) throw new UsageError(USAGE.trimEnd());
    const parsed = parse(argv);
    const command = COMMANDS[parsed.command];
    if (!command) throw new UsageError(`no command "${parsed.command}" - commands: ${Object.keys(COMMANDS).join(', ')} (see understudy --help)`);
    await command(parsed, { use: { ...defaultCommands, ...commands }, environment, stdout, stderr });
    return 0;
  } catch (error) {
    if (error instanceof UsageError) {
      stderr.write(`understudy: ${error.message}\n`);
      return 2;
    }
    stderr.write(error instanceof RunError ? `understudy: ${error.message}\n` : `understudy: unexpected error: ${error.message}\n`);
    return 1;
  }
}
