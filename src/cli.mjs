// The `understudy` command: a launcher. The work is done by the Python package (src/sketch for sketches,
// src/etl for the household ETL); this file reads the command line, starts Python and passes its output and
// exit code through.
//
//   understudy run <sketch.yaml> [--source name.path=file]... [--out folder] [--replay[=run-id|folder]]
//                                         run the sketch and write its outputs; --replay reads the
//                                         captured Jev answers instead of calling Jev
//   understudy check <sketch.yaml> [--source name.path=file]...
//                                         load and check the sketch, run nothing
//   understudy etl run --monarch <csv> --amex <csv> [--out <folder>] [--since YYYY-MM-DD] [--amex-account <name>]
//
// Exit codes are the same for every command: 0 done, 1 the run failed
// after starting, 2 refused before starting. Every failure is one
// `understudy: <message>` line on stderr - never a stack trace.

import { UsageError, RunError } from './errors.mjs';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const KEY = 'TYPESAFE_API_KEY';
const REBUILDING = new Set(['library', 'watch', 'dashboard']);

const USAGE = `usage: understudy run <sketch.yaml> [--source name.path=file]... [--out folder] [--replay[=run-id|folder]]
           run the sketch: its machine, its rules, its sources, and write its outputs under build/runs/;
           --source replaces one file source for this run only;
           --replay reads the last captured Jev answers (no key, no network), or those of a named run or folder
       understudy check <sketch.yaml> [--source name.path=file]...
           check the sketch without running anything
       understudy etl run --monarch <csv> --amex <csv> [--out <folder>] [--since YYYY-MM-DD] [--amex-account <name>]
           merge purchases, pair transfers, link refunds, place merchants with Jev, and write result.jsonl (needs ${KEY})
`;

// Each option: the commands that take it, and how its value is read.
const OPTIONS = {
  source: { commands: ['run', 'check'], read: (value) => {
    if (!/^[\w-]+(\.path)?=./s.test(value)) throw new UsageError(`--source needs name.path=file, e.g. --source sales.path=sales.jsonl (got "${value}")`);
    return value;
  }, needs: 'name.path=file', example: '--source sales.path=sales.jsonl', isRepeated: true },
  replay: { commands: ['run'], read: (value) => value, isOptionalValue: true, needs: 'a run id or folder', example: '--replay=run-20261029T120000-ab12cd34' },
  monarch: { commands: ['etl'], read: (value) => value, needs: 'a CSV path', example: '--monarch transactions.csv' },
  amex: { commands: ['etl'], read: (value) => value, needs: 'a CSV path', example: '--amex transactions.csv' },
  out: { commands: ['run', 'etl'], read: (value) => value, needs: 'a folder', example: '--out build/runs' },
  since: { commands: ['etl'], read: (value) => value, needs: 'a date', example: '--since 2026-01-01' },
  'amex-account': { commands: ['etl'], read: (value) => value, needs: 'an account name', example: '--amex-account "Platinum Card"' },
};

/**
 * One `--name` or `--name=value` (or `--name value`): its name and value.
 */
function option(command, rest, index) {
  const [flag, inline] = rest[index].slice(2).split(/=(.*)/s, 2);
  const known = OPTIONS[flag];
  if (!known?.commands.includes(command)) throw new UsageError(`no option "--${flag}" for ${command} - see understudy --help`);
  if (inline === undefined && known.isOptionalValue) return { name: flag, value: true, used: 0 };
  const value = inline ?? rest[index + 1];
  if (!value) throw new UsageError(`--${flag} needs ${known.needs}, e.g. ${known.example}`);
  return { name: flag, value: known.read(value), used: inline === undefined ? 1 : 0, isRepeated: known.isRepeated === true };
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
    const { name, value, used, isRepeated } = option(command, rest, index);
    options[name] = isRepeated ? [...options[name] ?? [], value] : value;
    index += used;
  }
  return { command, positional, ...options };
}

function oneSketch(command, positional) {
  const quoted = positional.map((each) => JSON.stringify(each)).join(', ');
  if (positional.length > 1) throw new UsageError(`${command} takes one sketch (got ${quoted})`);
  if (positional.length === 0) throw new UsageError(`${command} needs a sketch, e.g. understudy ${command} coffee_week.yaml`);
  return positional[0];
}

/**
 * Starts a Python module of this project and passes its output and exit code through.
 * Resolves the exit code.
 */
function runPython(module, pythonArguments, { environment, stdout, stderr }) {
  const root = fileURLToPath(new URL('../', import.meta.url));
  return new Promise((resolve, reject) => {
    const pythonEnvironment = { ...environment, PYTHONPATH: [root, environment.PYTHONPATH].filter(Boolean).join(path.delimiter) };
    const child = spawn(`${root}.venv/bin/python`, ['-m', module, ...pythonArguments], { env: pythonEnvironment, stdio: ['ignore', 'pipe', 'pipe'] });
    child.stdout.on('data', (chunk) => stdout.write(chunk.toString()));
    child.stderr.on('data', (chunk) => stderr.write(chunk.toString()));
    child.on('error', (error) => reject(new UsageError(`could not start Python: ${error.message}; run bobp make install`)));
    child.on('close', (code, signal) => {
      if (signal) reject(new RunError(`${module} stopped by ${signal}`));
      else resolve(code);
    });
  });
}

const defaultCommands = {
  async run({ sketch, source, out, replay, ...io }) {
    const pythonArguments = ['run', sketch, ...(source ?? []).flatMap((each) => ['--source', each]), ...(out ? ['--out', out] : [])];
    if (replay !== undefined) pythonArguments.push(replay === true ? '--replay' : `--replay=${replay}`);
    return runPython('src.sketch.cli', pythonArguments, io);
  },
  async check({ sketch, source, ...io }) {
    return runPython('src.sketch.cli', ['check', sketch, ...(source ?? []).flatMap((each) => ['--source', each])], io);
  },
  async etl({ monarchPath, amexPath, out, since, amexAccount, ...io }) {
    const pythonArguments = ['--monarch', monarchPath, '--amex', amexPath];
    for (const [name, value] of [['out', out], ['since', since], ['amex-account', amexAccount]]) {
      if (value !== undefined) pythonArguments.push(`--${name}`, value);
    }
    return runPython('src.etl.cli', pythonArguments, io);
  },
};

const HELP = new Set(['--help', '-h', 'help']);

/**
 * Each command: what it does with the parsed command line. Writes to
 * stdout; failures are thrown.
 */
const COMMANDS = {
  async run({ positional, source, out, replay }, { use, environment, stdout, stderr }) {
    return use.run({ sketch: oneSketch('run', positional), source, out, replay, environment, stdout, stderr });
  },
  async check({ positional, source }, { use, environment, stdout, stderr }) {
    return use.check({ sketch: oneSketch('check', positional), source, environment, stdout, stderr });
  },
  async etl({ positional, monarch, amex, out, since, 'amex-account': amexAccount }, { use, environment, stdout, stderr }) {
    if (positional.length !== 1 || positional[0] !== 'run') {
      throw new UsageError('usage: understudy etl run --monarch <csv> --amex <csv>');
    }
    if (!monarch) throw new UsageError('understudy etl run needs --monarch <csv>');
    if (!amex) throw new UsageError('understudy etl run needs --amex <csv>');
    if (!environment[KEY]?.trim()) throw new UsageError(`understudy etl run needs a TypeSafe key: set ${KEY}`);
    return use.etl({ monarchPath: monarch, amexPath: amex, out, since, amexAccount, environment, stdout, stderr });
  },
};

/**
 * Runs one command line; resolves the exit code. Streams and commands are
 * injectable so tests never start Python or call Jev.
 * @param {string[]} argv
 * @param {{ environment?: object, stdout?: { write: Function }, stderr?: { write: Function },
 *   commands?: { run?: Function, check?: Function, etl?: Function } }} [io]
 */
export async function main(argv, { environment = process.env, stdout = process.stdout, stderr = process.stderr, commands = {} } = {}) {
  try {
    if (HELP.has(argv[0])) {
      stdout.write(USAGE);
      return 0;
    }
    if (argv.length === 0) throw new UsageError(USAGE.trimEnd());
    if (REBUILDING.has(argv[0])) {
      throw new UsageError(`${argv[0]} is being rebuilt for the new sketch model (see docs/sprints/EPIC_PYTHON_PORT.md)`);
    }
    const parsed = parse(argv);
    const command = COMMANDS[parsed.command];
    if (!command) throw new UsageError(`no command "${parsed.command}" - commands: ${Object.keys(COMMANDS).join(', ')} (see understudy --help)`);
    const code = await command(parsed, { use: { ...defaultCommands, ...commands }, environment, stdout, stderr });
    return Number.isSafeInteger(code) ? code : 0;
  } catch (error) {
    if (error instanceof UsageError) {
      stderr.write(`understudy: ${error.message}\n`);
      return 2;
    }
    stderr.write(error instanceof RunError ? `understudy: ${error.message}\n` : `understudy: unexpected error: ${error.message}\n`);
    return 1;
  }
}
