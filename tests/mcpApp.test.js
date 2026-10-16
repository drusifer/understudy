// Sprint 3 UND-10 AC3-5 (ARCH §5): the generic MCP app - tools are the
// moves, fixed calls and listed values shape them, a tool with nothing to
// choose for a required argument is left out (said once) until a result
// supplies values.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mcpApp } from '../src/apps/mcp.mjs';

const TOOLS = [
  { name: 'list_films', description: 'What is on.', inputSchema: { type: 'object', properties: {} } },
  {
    name: 'pick_seats', description: 'Hold seats.',
    inputSchema: { type: 'object', properties: { film: { type: 'string' }, count: { type: 'integer', minimum: 1, maximum: 4 } }, required: ['film', 'count'] },
  },
  {
    name: 'pay', description: 'Pay for a hold.',
    inputSchema: { type: 'object', properties: { hold: { type: 'string' }, method: { type: 'string', enum: ['card', 'cash'] } }, required: ['hold', 'method'] },
  },
];
const FIRST = { tools: TOOLS, last: null, seq: 1 };
const AFTER_LIST = { tools: TOOLS, last: { tool: 'list_films', arguments: {}, isError: false, text: '[{"film":"f1"}]' }, seq: 2 };

function played(app, view) {
  const state = app.project(view);
  return { state, options: app.options(state) };
}

test('at first only the tool with nothing to fill is offered; the others are said once each', () => {
  const app = mcpApp();
  const said = [];
  app.notify = (line) => { said.push(line); };
  assert.equal(app.phase(FIRST), 'asking');
  const { options } = played(app, FIRST);
  assert.deepEqual(options.map((option) => option.id), ['tool:list_films']);
  played(app, FIRST);
  assert.deepEqual(said, [
    'not offering tool:pick_seats yet - argument "film" (string) has nothing to choose from; list values for it in sketch.yaml',
    'not offering tool:pay yet - argument "hold" (string) has nothing to choose from; list values for it in sketch.yaml',
  ]);
});

test('a result supplies values: the tool is offered with each open argument and its candidates', () => {
  const app = mcpApp();
  const pick = played(app, AFTER_LIST).options.find((option) => option.id === 'tool:pick_seats');
  assert.deepEqual(pick.open.map(({ name, candidates }) => [name, candidates]), [['film', ['f1']], ['count', [1, 2, 3, 4]]]);
  assert.deepEqual(app.act({ ...pick, filled: { film: 'f1', count: 2 } }), { actions: [{ tool: 'pick_seats', arguments: { film: 'f1', count: 2 } }] });
});

test('fixed calls replace the tool\'s own move; their open arguments are still chosen', () => {
  const app = mcpApp({ calls: [{ tool: 'pay', arguments: { method: 'card' } }] });
  const pay = played(app, AFTER_LIST).options.find((option) => option.id.startsWith('tool:pay'));
  assert.equal(pay.id, 'tool:pay(method=card)');
  assert.deepEqual(pay.open.map(({ name }) => name), ['hold']);
  assert.deepEqual(app.act({ ...pay, filled: { hold: 'f1' } }), { actions: [{ tool: 'pay', arguments: { method: 'card', hold: 'f1' } }] });
});

test('listed values make a tool playable from the start', () => {
  const app = mcpApp({ values: { pick_seats: { film: ['f2'] } } });
  const pick = played(app, FIRST).options.find((option) => option.id === 'tool:pick_seats');
  assert.deepEqual(pick.open[0].candidates, ['f2']);
});

test('what Jev reads: each tool, what it does and its arguments; the last call and what it said', () => {
  const { state } = played(mcpApp(), AFTER_LIST);
  assert.deepEqual(state.tools[1], { name: 'pick_seats', does: 'Hold seats.', arguments: { film: 'string', count: 'integer' } });
  assert.deepEqual(state.last_call, { tool: 'list_films', arguments: {}, failed: false, said: '[{"film":"f1"}]' });
});

test('nothing offerable: waiting, and idle names each tool and why', () => {
  const app = mcpApp();
  const view = { tools: TOOLS.slice(1), last: null, seq: 1 };
  assert.equal(app.phase(view), 'waiting');
  assert.match(app.idle(view), /^nothing can be offered: tool:pick_seats - argument "film" \(string\) has nothing to choose from; .*; tool:pay - argument "hold"/);
  assert.equal(app.idle({ tools: [], last: null }), 'the server lists no tools');
});

test('a refused call does not take away the values the answer before it offered', () => {
  const app = mcpApp();
  played(app, AFTER_LIST);
  const refused = { tools: TOOLS, last: { tool: 'pay', arguments: { hold: 'f1', method: 'cash' }, isError: true, text: 'Cards only.' }, seq: 3 };
  const pay = played(app, refused).options.find((option) => option.id === 'tool:pay');
  assert.deepEqual(pay.open[0].candidates, ['f1']);
});
