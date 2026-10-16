// Sprint 3 UND-10 AC2, AC8-9 (ARCH §3 "MCP server entry"): the server a
// sketch plays, inline or by reference to an mcpServers file, checked at
// load; `${VAR}` filled only when the run starts.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { resolveServer, expandEntry } from '../src/mcpConfig.mjs';
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
