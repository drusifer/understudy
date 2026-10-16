// Sprint 3 UND-10/11 (ARCH §3 "MCP server entry", ADR-0012): which MCP
// server a sketch plays, in the de facto `mcpServers` shape that Claude
// Desktop and Claude Code read - inline in the sketch, or by reference to
// a file and a server name in it.
//
//   local:  { command, args?, env?, type?: stdio }
//   remote: { type: http, url, headers? }
//
// Checked at load (no server started, no variable read); `${VAR}` and
// `${VAR:-default}` are filled from the environment only when the run
// starts, so `check` needs no secrets.

import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import YAML from 'yaml';
import { UsageError } from './errors.mjs';

const LOCAL_FIELDS = ['type', 'command', 'args', 'env'];
const REMOTE_FIELDS = ['type', 'url', 'headers'];
const VARIABLE = /\$\{([A-Za-z_]\w*)(?::-([^}]*))?\}/g;

const isMapping = (value) => Boolean(value) && typeof value === 'object' && !Array.isArray(value);
const isStrings = (value) => Array.isArray(value) && value.every((each) => typeof each === 'string');
const isStringMap = (value) => isMapping(value) && Object.values(value).every((each) => typeof each === 'string');

/**
 * One `mcpServers` entry's shape; `fail(where, message)` names the path.
 */
export function checkEntry(entry, where, fail) {
  if (!isMapping(entry)) fail(where, 'must be a server entry: { command, args, env } or { type: http, url, headers }');
  const type = entry.type ?? 'stdio';
  if (type === 'sse') fail(`${where}.type`, 'sse servers are not supported - use type: http (streamable HTTP)');
  if (type !== 'stdio' && type !== 'http') fail(`${where}.type`, `must be stdio or http (got ${JSON.stringify(entry.type)})`);
  const known = type === 'http' ? REMOTE_FIELDS : LOCAL_FIELDS;
  const extra = Object.keys(entry).find((field) => !known.includes(field));
  const kind = type === 'http' ? 'a remote (type: http)' : 'a local';
  if (extra) fail(`${where}.${extra}`, `not a field of ${kind} server (known: ${known.join(', ')})`);
  if (type === 'http') checkRemote(entry, where, fail);
  else checkLocal(entry, where, fail);
}

function checkRemote(entry, where, fail) {
  if (typeof entry.url !== 'string' || entry.url === '') fail(`${where}.url`, 'required for a type: http server, e.g. https://example.com/mcp');
  if (entry.headers !== undefined && !isStringMap(entry.headers)) fail(`${where}.headers`, 'must map each header name to text');
}

function checkLocal(entry, where, fail) {
  if (typeof entry.command !== 'string' || entry.command === '') fail(`${where}.command`, 'required for a local server (the program to start, e.g. node)');
  if (entry.args !== undefined && !isStrings(entry.args)) fail(`${where}.args`, 'must be a list of text');
  if (entry.env !== undefined && !isStringMap(entry.env)) fail(`${where}.env`, 'must map each variable name to text');
}

/**
 * The server entry a sketch's `target` names, checked.
 * @param {{ server?: object|string, config?: string }} target
 * @param {{ directory: string, shownFile: string, shown: (file: string) => string }} where
 * @returns {{ entry: object, name: string|null, from: string }} `from` is the file the entry is written in
 */
export function resolveServer(target, { directory, shownFile, shown }) {
  const fail = (at, message) => { throw new UsageError(`${shownFile}: ${at}: ${message}`); };
  if (target.config === undefined) {
    if (!isMapping(target.server)) {
      fail('target.server', 'give the server entry inline ({ command, args } or { type: http, url }), or config: <file> and server: <name>');
    }
    checkEntry(target.server, 'target.server', fail);
    return { entry: target.server, name: null, from: shownFile };
  }
  if (typeof target.config !== 'string' || target.config === '') fail('target.config', 'must name an mcpServers file, e.g. servers.json next to the sketch or /path/to/.mcp.json');
  if (typeof target.server !== 'string' || target.server === '') fail('target.server', `names the server in ${target.config} (with config:, server is a name)`);
  // Relative to the sketch, or absolute - e.g. a project's own .mcp.json.
  const file = path.resolve(directory, target.config);
  if (!existsSync(file)) {
    fail('target.config', path.isAbsolute(target.config) ? `${target.config} not found` : `${target.config} not found next to ${path.basename(shownFile)}`);
  }
  let config;
  try {
    config = YAML.parse(readFileSync(file, 'utf8'));
  } catch (error) {
    throw new UsageError(`${shown(file)}: not valid JSON or YAML - ${error.message.split('\n', 1)[0]}`);
  }
  const fileFail = (at, message) => { throw new UsageError(`${shown(file)}: ${at}: ${message}`); };
  if (!isMapping(config?.mcpServers)) fileFail('mcpServers', 'missing - the file needs { "mcpServers": { "<name>": { ... } } }');
  const names = Object.keys(config.mcpServers);
  if (!Object.hasOwn(config.mcpServers, target.server)) {
    fail('target.server', `no server "${target.server}" in ${target.config} (it has: ${names.join(', ') || 'none'})`);
  }
  checkEntry(config.mcpServers[target.server], `mcpServers.${target.server}`, fileFail);
  return { entry: config.mcpServers[target.server], name: target.server, from: shown(file) };
}

/**
 * The entry with every `${VAR}` filled from `environment`; an unset one
 * with no default refuses the run, naming the variable and the file.
 * @param {object} entry
 * @param {object} environment
 * @param {string} from the file the entry is written in
 */
export function expandEntry(entry, environment, from) {
  const fill = (text) => text.replaceAll(VARIABLE, (_, name, fallback) => {
    const value = environment[name];
    if (value !== undefined && value !== '') return value;
    if (fallback !== undefined) return fallback;
    throw new UsageError(`${from}: \${${name}} is not set - set ${name} in the environment (or give a default: \${${name}:-value})`);
  });
  const fillAll = (value) => {
    if (typeof value === 'string') return fill(value);
    if (Array.isArray(value)) return value.map((each) => fillAll(each));
    if (isMapping(value)) return Object.fromEntries(Object.entries(value).map(([key, each]) => [key, fillAll(each)]));
    return value;
  };
  return fillAll(entry);
}
