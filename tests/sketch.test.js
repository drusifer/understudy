// Sprint 3 UND-9 (ADR-0011), from sprint 1 UND-3: a broken sketch is
// refused at load - before any app starts or Jev is called - naming
// sketch.yaml, the path in it, the bad name and the nearest known one.
// `understudy check` is that load, alone.
import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadSketch, checkSketch, shown } from '../src/sketch.mjs';
import { UsageError } from '../src/errors.mjs';
import { main } from '../src/cli.mjs';

const GOOD = fileURLToPath(new URL('fixtures/sketches/good', import.meta.url));

function scratch() {
  const directory = mkdtempSync(path.join(tmpdir(), 'understudy-sketch-'));
  test.after(() => rmSync(directory, { recursive: true, force: true }));
  return directory;
}

/**
 * A copy of the good fixture with one file's text changed (or removed).
 */
function brokenCopy(file, change) {
  const directory = scratch();
  cpSync(GOOD, directory, { recursive: true });
  const target = path.join(directory, file);
  if (change === null) rmSync(target);
  else writeFileSync(target, change(readFileSync(target, 'utf8')));
  return directory;
}

const sketchChanged = (change) => brokenCopy('sketch.yaml', change);

async function refusal(location) {
  try {
    await loadSketch(location);
  } catch (error) {
    assert.ok(error instanceof UsageError, error.message);
    return error.message;
  }
  assert.fail(`${location} loaded, but should have been refused`);
}

function streams() {
  const io = { out: '', err: '' };
  return { io, stdout: { write: (text) => { io.out += text; } }, stderr: { write: (text) => { io.err += text; } } };
}

test('a good sketch loads: name, target, hooks, questions, a machine, and services to fill at run time', async () => {
  const sketch = await loadSketch(GOOD);
  assert.equal(sketch.name, 'fixture-good');
  assert.equal(sketch.target.kind, 'process');
  assert.equal(sketch.hooks, 'hooks.mjs');
  assert.equal(typeof sketch.app.phase, 'function');
  assert.deepEqual(Object.keys(sketch.questions), ['next']);
  assert.ok(sketch.machine);
  assert.equal(sketch.steps, null);
  assert.equal(typeof sketch.services, 'object');
});

test('check says what it checked, the same for the directory and the file', async () => {
  const line = `${shown(GOOD)}: sketch OK - fixture-good (process, hooks.mjs) - 5 states, 1 question`;
  assert.equal(await checkSketch(GOOD), line);
  assert.equal(await checkSketch(path.join(GOOD, 'sketch.yaml')), line);
});

test('an unknown guard is refused naming sketch.yaml, the turn path, the bad name and the nearest name', async () => {
  const directory = sketchChanged((text) => text.replace('type: phase, params: { is: menu }', 'type: phse, params: { is: menu }'));
  assert.equal(await refusal(directory),
    `${shown(directory)}/sketch.yaml: turn.states.looking.invoke.onDone[0].guard: no guard "phse" - did you mean "phase"?`);
});

test('an unknown actor, or a state that is not there, is refused the same way', async () => {
  const actor = sketchChanged((text) => text.replace('src: look', 'src: lok'));
  assert.equal(await refusal(actor), `${shown(actor)}/sketch.yaml: turn.states.looking.invoke.src: no actor "lok" - did you mean "look"?`);
  const state = sketchChanged((text) => text.replace('STEP: stepping', 'STEP: steping'));
  assert.match(await refusal(state), /sketch\.yaml: turn\.states\.choosing\.on\.STEP: no state "steping" - did you mean "stepping"\?$/);
});

test('the names the hooks add are known to the turn', async () => {
  const directory = sketchChanged((text) => text.replace('- { target: waiting }', '- { target: waiting, guard: sold_out }\n          - { target: waiting }'));
  assert.equal((await loadSketch(directory)).states, 5);
});

test('a question the turn names but the sketch lacks is refused', async () => {
  const directory = sketchChanged((text) => text.replace('question: next', 'question: nxt'));
  assert.match(await refusal(directory), /sketch\.yaml: turn\.states\.stepping\.invoke\.with\.question: no question "nxt" - did you mean "next"\?$/);
});

test('a number in a question\'s prose is refused naming the question', async () => {
  const directory = sketchChanged((text) => text.replace('Pick the next step', 'Pick 2 steps'));
  assert.equal(await refusal(directory),
    `${shown(directory)}/sketch.yaml: questions.next.instructions: carries a number in the question; put the number in state and refer to it by path`);
});

test('a quoted value in a question\'s prose is refused, but a backticked path is fine', async () => {
  const directory = sketchChanged((text) => text.replace('place the order as it stands', 'order when `screen` says "ready"'));
  assert.equal(await refusal(directory),
    `${shown(directory)}/sketch.yaml: questions.next.criteria.order: carries a quoted value in the question; put the value in state and refer to it by path`);
});

test('a question of an unknown type is refused, naming the known types', async () => {
  const directory = sketchChanged((text) => text.replace('type: choice', 'type: choise'));
  assert.equal(await refusal(directory), `${shown(directory)}/sketch.yaml: questions.next.type: no question type "choise" - did you mean "choice"?`);
});

test('bad YAML is refused naming the file and the line', async () => {
  const directory = sketchChanged((text) => text.replace('initial: waiting', 'initial: [waiting'));
  assert.match(await refusal(directory), /sketch\.yaml: not valid YAML - .* at line \d+, column \d+$/);
});

test('an unknown top-level key is refused naming the known ones', async () => {
  const directory = sketchChanged((text) => `${text}adapter: adapter.mjs\n`);
  assert.equal(await refusal(directory),
    `${shown(directory)}/sketch.yaml: adapter: not a sketch key (known: name, description, target, app, player, steps, questions, turn, calls, values, decide, inputs, pick)`);
});

test('a missing name, questions or turn is refused naming the key', async () => {
  assert.match(await refusal(sketchChanged((text) => text.replace('name: fixture-good\n', ''))), /sketch\.yaml: name: must be a non-empty string/);
  assert.match(await refusal(sketchChanged((text) => text.slice(0, text.indexOf('turn:')))), /sketch\.yaml: turn: needs the statechart/);
  assert.match(await refusal(sketchChanged((text) => text.replace('questions:', 'questionz:'))), /sketch\.yaml: questionz: not a sketch key/);
});

test('steps must be a positive whole number', async () => {
  assert.equal((await loadSketch(sketchChanged((text) => `${text}steps: 7\n`))).steps, 7);
  const bad = sketchChanged((text) => `${text}steps: lots\n`);
  assert.equal(await refusal(bad), `${shown(bad)}/sketch.yaml: steps: must be a positive whole number (got "lots")`);
});

test('hooks the sketch names must be there and have every hook', async () => {
  const missing = brokenCopy('hooks.mjs', null);
  assert.equal(await refusal(missing), `${shown(missing)}/sketch.yaml: app: hooks.mjs not found next to sketch.yaml`);
  const partial = brokenCopy('hooks.mjs', (text) => text.replace("  options: () => [{ id: 'order', what: 'place the order' }, { id: 'cancel', what: 'stop' }],\n", ''));
  assert.equal(await refusal(partial), `${shown(partial)}/hooks.mjs: options must be a function - see docs/SKETCHES.md`);
  const undocumented = brokenCopy('hooks.mjs', (text) => text.replace("doc: 'the app says the item is sold out', ", ''));
  assert.equal(await refusal(undocumented), `${shown(undocumented)}/hooks.mjs: library.guards.sold_out needs a one-line doc`);
});

test('a process or http target without hooks is refused, saying what to add', async () => {
  const directory = sketchChanged((text) => text.replace('app: hooks.mjs\n', ''));
  assert.equal(await refusal(directory),
    `${shown(directory)}/sketch.yaml: app: a process target needs hooks that read the app, e.g. app: hooks.mjs - see docs/SKETCHES.md`);
});

test('a target kind that does not exist is refused naming the kinds', async () => {
  const directory = sketchChanged((text) => text.replace('kind: process', 'kind: ftp'));
  assert.equal(await refusal(directory), `${shown(directory)}/sketch.yaml: target.kind: must be "process", "page", "http" or "mcp" (got "ftp")`);
});

test('a target field the kind does not have is refused, naming the known ones', async () => {
  const directory = sketchChanged((text) => text.replace('args: [app.mjs] }', 'args: [app.mjs], hook: __understudy }'));
  assert.equal(await refusal(directory), `${shown(directory)}/sketch.yaml: target.hook: not a process target field (known: command, args)`);
});

test('a target missing a field its kind needs is refused at check, naming it', async () => {
  const directory = sketchChanged((text) => text.replace('command: node, ', ''));
  assert.equal(await refusal(directory), `${shown(directory)}/sketch.yaml: target.command: required for a process target (the program to start, e.g. node)`);
});

test('an http target needs url and state, and a {port} url needs a command', async () => {
  const http = (target) => sketchChanged((text) => text.replace('{ kind: process, command: node, args: [app.mjs] }', () => target));
  const noState = http("{ kind: http, url: 'http://127.0.0.1:8080' }");
  assert.equal(await refusal(noState), `${shown(noState)}/sketch.yaml: target.state: required for an http target (the path a look GETs, e.g. /status)`);
  const noUrl = http('{ kind: http, state: /status }');
  assert.equal(await refusal(noUrl), shown(noUrl) + '/sketch.yaml: target.url: required for an http target (where the API is, e.g. http://127.0.0.1:{port})');
  const portOnly = http("{ kind: http, url: 'http://127.0.0.1:{port}', state: /status }");
  assert.equal(await refusal(portOnly), shown(portOnly) + '/sketch.yaml: target.url: has {port} but no command to start - give the full URL of a running service, or a command');
});

test('the old adapter/part layout is refused, saying it is no longer read', async () => {
  const directory = scratch();
  writeFileSync(path.join(directory, 'adapter.mjs'), 'export default {};\n');
  mkdirSync(path.join(directory, 'part'));
  assert.equal(await refusal(directory), `${shown(directory)}: no sketch.yaml - adapter.mjs and part/ are no longer read; see docs/SKETCHES.md`);
});

test('a directory without a sketch, or a path that does not exist, is named as such', async () => {
  const empty = scratch();
  assert.equal(await refusal(empty), `${shown(empty)}: no sketch.yaml - a sketch is a directory holding sketch.yaml; see docs/SKETCHES.md`);
  assert.equal(await refusal('examples/nope'), 'examples/nope: no such sketch - give a directory holding sketch.yaml, e.g. examples/cli');
});

test('understudy check: good exits 0 without a key; broken exits 2 with one line and no stack', async () => {
  const { io, ...out } = streams();
  assert.equal(await main(['check', GOOD], { environment: {}, ...out }), 0);
  assert.match(io.out, /sketch OK/);
  const directory = sketchChanged((text) => text.replace('src: look', 'src: lok'));
  assert.equal(await main(['check', directory], { environment: {}, ...out }), 2);
  assert.match(io.err, /^understudy: .*sketch\.yaml: turn\..*no actor "lok" - did you mean "look"\?\n$/);
});

test('understudy library <sketch> lists the names its hooks add', async () => {
  const { io, ...out } = streams();
  assert.equal(await main(['library', GOOD], { environment: {}, ...out }), 0);
  assert.match(io.out, /^fixture-good guards:\n {2}sold_out - the app says the item is sold out$/m);
});

/**
 * A sketch directory holding an MCP sketch with these target and extra
 * top-level lines (and these other files).
 */
function mcpSketch(target, extra = '', files = {}) {
  const directory = scratch();
  const good = readFileSync(path.join(GOOD, 'sketch.yaml'), 'utf8');
  const text = good.replace('target: { kind: process, command: node, args: [app.mjs] }\napp: hooks.mjs\n', () => `target: ${target}\n${extra}`);
  writeFileSync(path.join(directory, 'sketch.yaml'), text);
  for (const [name, content] of Object.entries(files)) writeFileSync(path.join(directory, name), content);
  return directory;
}

test('an MCP sketch needs no code: the generic MCP app plays it, and check says so', async () => {
  const directory = mcpSketch('{ kind: mcp, server: { command: node, args: [server.mjs] } }');
  const sketch = await loadSketch(directory);
  assert.deepEqual(sketch.target, { kind: 'mcp', servers: [{ name: null, entry: { command: 'node', args: ['server.mjs'] }, from: `${shown(directory)}/sketch.yaml` }] });
  assert.equal(typeof sketch.app.idle, 'function');
  assert.equal(await checkSketch(directory), `${shown(directory)}: sketch OK - fixture-good (mcp, generic app) - 5 states, 1 question`);
});

test('an MCP sketch can name several servers; each is checked and named (UND-20)', async () => {
  const directory = mcpSketch('{ kind: mcp, servers: { boxoffice: { command: node, args: [b.mjs] }, ratings: { command: node, args: [r.mjs] } } }');
  const sketch = await loadSketch(directory);
  assert.deepEqual(sketch.target.servers.map((server) => server.name), ['boxoffice', 'ratings']);
  const bad = mcpSketch('{ kind: mcp, servers: { boxoffice: { command: node }, ratings: { type: sse, url: x } } }');
  await assert.rejects(checkSketch(bad), /sketch\.yaml: target\.servers\.ratings\.type: sse servers are not supported/);
});

test('decide: gates are checked at load, naming the file, the gate and the word (UND-21 AC5)', async () => {
  const good = mcpSketch('{ kind: mcp, server: { command: node } }', "decide:\n  seat_map.showing: { join: title, gates: { starts: { at_least: '17:00' } } }\n");
  assert.ok((await loadSketch(good)).app);
  const bad = mcpSketch('{ kind: mcp, server: { command: node } }', 'decide:\n  seat_map.showing: { gates: { row: { among: [E] } } }\n');
  await assert.rejects(checkSketch(bad), { message: `${shown(bad)}/sketch.yaml: decide.seat_map.showing.gates.row: unknown word "among" - use is, in, at_least, at_most, any` });
  const misnamed = mcpSketch('{ kind: mcp, server: { command: node } }', 'decide:\n  seat_map: { gates: {} }\n');
  await assert.rejects(checkSketch(misnamed), /decide\.seat_map: name a tool argument as <tool>\.<argument>/);
  const notMcp = mcpSketch('{ kind: process, command: node }', 'app: hooks.mjs\ndecide: {}\n');
  await assert.rejects(checkSketch(notMcp), /decide: only for an mcp target/);
});

test('inputs, ask factors and pick are checked against what the sketch declares (UND-23 AC5, UND-24 AC6)', async () => {
  const target = '{ kind: mcp, server: { command: node } }';
  const inputs = 'inputs:\n  mood: { choose: [fun, serious], default: fun }\n  centre: { weight: [0, 3], default: 3 }\n';
  const score = 'decide:\n  seat_map.showing: { scores: { audience: { ask: next, weight: 2 }, centre: { range: [0.3, 1], weight: centre } } }\n';
  const asksChoice = mcpSketch(target, inputs + score);
  await assert.rejects(checkSketch(asksChoice), /decide\.seat_map\.showing\.scores\.audience\.ask: names "next" - it must be a type: score question under questions:/);
  const undeclared = mcpSketch(target, 'decide:\n  pick_seats.seat: { scores: { centre: { range: [0.3, 1], weight: centre } } }\n');
  await assert.rejects(checkSketch(undeclared), /decide\.pick_seats\.seat\.scores\.centre\.weight: names input "centre" - declare it under inputs: as \{ weight: \[low, high\], default \}/);
  const pickUnknown = mcpSketch(target, `${inputs}pick: { instructions: Choose one you would enjoy., with: [centre] }\n`);
  await assert.rejects(checkSketch(pickUnknown), /pick\.with: "centre" is not a choice input declared under inputs:/);
  const badDefault = mcpSketch(target, 'inputs:\n  centre: { weight: [0, 3], default: 5 }\n');
  await assert.rejects(checkSketch(badDefault), /inputs\.centre\.default: must be between 0 and 3, got 5/);
  const good = mcpSketch(target, `${inputs}pick: { instructions: Choose one you would enjoy., with: [mood] }\n`);
  assert.deepEqual((await loadSketch(good)).inputs.mood.default, 'fun');
});

test('an MCP sketch by reference reads the mcpServers file; a missing name is refused naming the ones there', async () => {
  const files = { 'servers.json': '{"mcpServers":{"box":{"type":"http","url":"http://127.0.0.1:1/mcp"}}}' };
  const good = mcpSketch('{ kind: mcp, config: servers.json, server: box }', '', files);
  assert.equal((await loadSketch(good)).target.servers[0].entry.type, 'http');
  const wrong = mcpSketch('{ kind: mcp, config: servers.json, server: bx }', '', files);
  assert.equal(await refusal(wrong), `${shown(wrong)}/sketch.yaml: target.server: no server "bx" in servers.json (it has: box)`);
});

test('an MCP sketch takes calls and values, checked; no hooks; other kinds take neither', async () => {
  const server = '{ kind: mcp, server: { command: node } }';
  const fine = mcpSketch(server, 'calls:\n  - { tool: pay, arguments: { method: card } }\nvalues:\n  pick_seats: { count: [2] }\n');
  assert.equal((await loadSketch(fine)).name, 'fixture-good');
  assert.match(await refusal(mcpSketch(server, 'calls:\n  - { tol: pay }\n')), /sketch\.yaml: calls\[0\]: needs tool: <name> \(and arguments: \{ \.\.\. \} to fix some\)$/);
  assert.match(await refusal(mcpSketch(server, 'values:\n  pick_seats: { count: [] }\n')), /values\.pick_seats\.count: must be a non-empty list/);
  assert.match(await refusal(mcpSketch(server, 'app: hooks.mjs\n')), /app: an mcp target is played by the generic MCP app - remove app:/);
  assert.match(await refusal(sketchChanged((text) => `${text}calls: []\n`)), /sketch\.yaml: calls: only for an mcp target$/);
});
