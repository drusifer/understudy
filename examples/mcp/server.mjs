// The MCP example's app (docs/SKETCHES.md): a tiny cinema box office as
// an MCP server. List today's films, hold seats for one, pay for the hold;
// paying issues the ticket. It knows nothing about understudy.
//
//   node server.mjs                                   stdio (examples/mcp starts it)
//   node server.mjs --http --port 8765 --token T      streamable HTTP at /mcp, `Authorization: Bearer T`
//
// One box office per process: holds made in one call are there for the next.

import http from 'node:http';
import { parseArgs } from 'node:util';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { z } from 'zod';

const FILMS = [
  { film: 'f1', title: 'The Long Night', price: 9, seats_left: 3 },
  { film: 'f2', title: 'Paper Boats', price: 7, seats_left: 40 },
  { film: 'f3', title: 'Orbit', price: 11, seats_left: 0 },
];

const office = { films: structuredClone(FILMS), holds: new Map(), next: 1 };

const answer = (value) => ({ content: [{ type: 'text', text: typeof value === 'string' ? value : JSON.stringify(value) }] });
const refuse = (text) => ({ content: [{ type: 'text', text }], isError: true });

function boxOffice() {
  const server = new McpServer({ name: 'boxoffice', version: '1.0.0' });
  server.registerTool('list_films', {
    description: 'Today\'s films with their price per seat and how many seats are left.',
  }, async () => answer(office.films));
  server.registerTool('pick_seats', {
    description: 'Hold seats for one film. Returns a hold to pay for.',
    inputSchema: {
      film: z.string().describe('the film id from list_films'),
      count: z.number().int().min(1).max(4).describe('how many seats'),
    },
  }, async ({ film, count }) => {
    const showing = office.films.find((each) => each.film === film);
    if (!showing) return refuse(`No film ${film} today - see list_films.`);
    if (showing.seats_left < count) return refuse(`Only ${showing.seats_left} seats left for ${showing.title}.`);
    showing.seats_left -= count;
    const hold = `h${office.next++}`;
    office.holds.set(hold, { film: showing.title, count, total: showing.price * count });
    return answer({ hold, film: showing.title, count, total: showing.price * count });
  });
  server.registerTool('pay', {
    description: 'Pay for a hold from pick_seats.',
    inputSchema: {
      hold: z.string().describe('the hold from pick_seats'),
      method: z.enum(['card', 'cash']).describe('how to pay'),
    },
  }, async ({ hold, method }) => {
    const held = office.holds.get(hold);
    if (!held) return refuse(`No hold ${hold} - pick seats first.`);
    if (method === 'cash') return refuse('This box office takes cards only.');
    office.holds.delete(hold);
    return answer(`Ticket issued: ${held.count} for ${held.film}, ${held.total} paid by card. Enjoy the film!`);
  });
  server.registerTool('leave_review', {
    description: 'Write a review of a film.',
    inputSchema: { text: z.string().describe('what you thought of it') },
  }, async () => answer('Thanks for the review.'));
  return server;
}

async function serveHttp({ port, token }) {
  const site = http.createServer(async (request, response) => {
    if (request.headers.authorization !== `Bearer ${token}`) {
      response.writeHead(401).end('unauthorized');
      return;
    }
    if (request.url !== '/mcp' || request.method !== 'POST') {
      response.writeHead(405).end('POST /mcp only');
      return;
    }
    // Stateless: a server per request, one box office for all of them.
    const server = boxOffice();
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    response.on('close', () => {
      transport.close();
      server.close();
    });
    await server.connect(transport);
    await transport.handleRequest(request, response);
  });
  site.listen(port, '127.0.0.1', () => console.error(`boxoffice: listening on http://127.0.0.1:${port}/mcp`));
}

const { values } = parseArgs({ options: { http: { type: 'boolean' }, port: { type: 'string', default: '8765' }, token: { type: 'string' } } });
if (values.http && !values.token) {
  console.error('boxoffice: --http needs --token');
  process.exitCode = 2;
} else if (values.http) {
  await serveHttp({ port: Number(values.port), token: values.token });
} else {
  await boxOffice().connect(new StdioServerTransport());
}
