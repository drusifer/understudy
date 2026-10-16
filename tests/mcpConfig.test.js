// Sprint 3 UND-10 AC2, AC8-9 (ARCH §3 "MCP server entry"): the server a
// sketch plays, inline or by reference to an mcpServers file, checked at
// load; `${VAR}` filled only when the run starts.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { resolveServer, resolveServers, expandEntry } from '../src/mcpConfig.mjs';
import { shown } from '../src/sketch.mjs';
import { UsageError } from '../src/errors.mjs';

function directoryWith(files) {
  const directory = mkdtempSync(path.join(tmpdir(), 'understudy-mcp-config-'));
  test.after(() => rmSync(directory, { recursive: true, force: true }));
  for (const [name, text] of Object.entries(files)) writeFileSync(path.join(directory, name), text);
  return directory;
}

const resolve = (target, directory = directoryWith({})) => resolveServer(target, { directory, shownFile: 'sketch.yaml', shown });

function refusal(run) {
  try {
    run();
  } catch (error) {
    assert.ok(error instanceof UsageError, error.message);
    return error.message;
  }
  assert.fail('was not refused');
}

test('an inline local entry is taken as written', () => {
  const server = { command: 'node', args: ['server.mjs'], env: { MODE: 'test' } };
  assert.deepEqual(resolve({ kind: 'mcp', server }), { entry: server, name: null, from: 'sketch.yaml' });
});

test('a file reference picks the named entry from mcpServers (JSON, Claude\'s shape)', () => {
  const directory = directoryWith({ 'servers.json': JSON.stringify({ mcpServers: { box: { type: 'http', url: 'http://127.0.0.1:1/mcp', headers: { Authorization: 'Bearer ${T}' } } } }) });
  const { entry, name, from } = resolve({ kind: 'mcp', config: 'servers.json', server: 'box' }, directory);
  assert.equal(entry.type, 'http');
  assert.equal(name, 'box');
  assert.equal(from, shown(path.join(directory, 'servers.json')));
});

test('a missing file, or a name the file does not have, is refused naming what it has', () => {
  assert.equal(refusal(() => resolve({ kind: 'mcp', config: 'nope.json', server: 'box' })), 'sketch.yaml: target.config: nope.json not found next to sketch.yaml');
  const directory = directoryWith({ 'servers.json': '{"mcpServers":{"via":{"command":"via"},"box":{"command":"node"}}}' });
  assert.equal(refusal(() => resolve({ kind: 'mcp', config: 'servers.json', server: 'bx' }, directory)),
    'sketch.yaml: target.server: no server "bx" in servers.json (it has: via, box)');
  const empty = directoryWith({ 'servers.json': '{}' });
  assert.match(refusal(() => resolve({ kind: 'mcp', config: 'servers.json', server: 'box' }, empty)), /servers\.json: mcpServers: missing/);
});

test('entry shapes: sse, unknown fields, missing command or url are refused', () => {
  assert.equal(refusal(() => resolve({ kind: 'mcp', server: { type: 'sse', url: 'x' } })),
    'sketch.yaml: target.server.type: sse servers are not supported - use type: http (streamable HTTP)');
  assert.equal(refusal(() => resolve({ kind: 'mcp', server: { command: 'node', cwd: '/' } })),
    'sketch.yaml: target.server.cwd: not a field of a local server (known: type, command, args, env)');
  assert.match(refusal(() => resolve({ kind: 'mcp', server: { args: [] } })), /target\.server\.command: required for a local server/);
  assert.match(refusal(() => resolve({ kind: 'mcp', server: { type: 'http' } })), /target\.server\.url: required for a type: http server/);
  assert.match(refusal(() => resolve({ kind: 'mcp', server: 'box' })), /target\.server: give the server entry inline/);
});

test('${VAR} and ${VAR:-default} are filled from the environment, everywhere in the entry', () => {
  const entry = { type: 'http', url: '${BASE:-http://127.0.0.1:8765}/mcp', headers: { Authorization: 'Bearer ${TOKEN}' } };
  assert.deepEqual(expandEntry(entry, { TOKEN: 's3cret' }, 'servers.json'),
    { type: 'http', url: 'http://127.0.0.1:8765/mcp', headers: { Authorization: 'Bearer s3cret' } });
  assert.deepEqual(expandEntry({ command: 'node', args: ['${APP}'] }, { APP: 'a.mjs' }, 'x'), { command: 'node', args: ['a.mjs'] });
});

test('an unset ${VAR} with no default refuses, naming the variable and the file', () => {
  assert.equal(refusal(() => expandEntry({ type: 'http', url: 'u', headers: { Authorization: 'Bearer ${MCP_TOKEN}' } }, {}, 'examples/mcp-remote/servers.json')),
    'examples/mcp-remote/servers.json: ${MCP_TOKEN} is not set - set MCP_TOKEN in the environment (or give a default: ${MCP_TOKEN:-value})');
});

test('a config path may be absolute - a project\'s own .mcp.json, say (DEF-09)', () => {
  const elsewhere = directoryWith({ '.mcp.json': '{"mcpServers":{"via":{"command":"via","args":["mcp"]}}}' });
  const config = path.join(elsewhere, '.mcp.json');
  const { entry, from } = resolve({ kind: 'mcp', config, server: 'via' });
  assert.deepEqual(entry, { command: 'via', args: ['mcp'] });
  assert.equal(from, shown(config));
  assert.equal(refusal(() => resolve({ kind: 'mcp', config: '/no/such/.mcp.json', server: 'via' })), 'sketch.yaml: target.config: /no/such/.mcp.json not found');
});

test('servers: several inline entries, each named and checked (UND-20)', () => {
  const servers = resolveServers({ kind: 'mcp', servers: { boxoffice: { command: 'node', args: ['b.mjs'] }, ratings: { command: 'node', args: ['r.mjs'] } } },
    { directory: directoryWith({}), shownFile: 'sketch.yaml', shown });
  assert.deepEqual(servers.map((server) => server.name), ['boxoffice', 'ratings']);
  assert.equal(refusal(() => resolveServers({ kind: 'mcp', servers: { ratings: { args: [] } } }, { directory: directoryWith({}), shownFile: 'sketch.yaml', shown })),
    'sketch.yaml: target.servers.ratings.command: required for a local server (the program to start, e.g. node)');
});

test('servers: names in a config file; both server and servers, or a missing name, are refused', () => {
  const directory = directoryWith({ 'servers.json': '{"mcpServers":{"box":{"command":"node"},"rate":{"command":"node"}}}' });
  const where = { directory, shownFile: 'sketch.yaml', shown };
  assert.deepEqual(resolveServers({ kind: 'mcp', config: 'servers.json', servers: ['box', 'rate'] }, where).map((server) => server.name), ['box', 'rate']);
  assert.equal(refusal(() => resolveServers({ kind: 'mcp', config: 'servers.json', servers: ['box', 'nope'] }, where)),
    'sketch.yaml: target.server: no server "nope" in servers.json (it has: box, rate)');
  assert.equal(refusal(() => resolveServers({ kind: 'mcp', server: { command: 'node' }, servers: {} }, where)),
    'sketch.yaml: target.servers: give server: (one) or servers: (several), not both');
});
