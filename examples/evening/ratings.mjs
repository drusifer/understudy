// The evening example's ratings service (docs/sprints/ARCH_SPRINT5.md §5):
// a made-up critics' score and a few made-up audience reviews per film,
// by title. No key, no network, the same answer every time. It knows
// nothing about the box office or understudy.
//
//   node ratings.mjs    stdio

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const RATINGS = {
  'Night Shift': { tomato: 82, reviews: [
    'Jumped out of my seat three times - the best scare of the year.',
    'Genuinely tense from start to finish; the whole room was screaming.',
    'Clever, nasty and fun. Already planning to see it again.',
  ] },
  'The Hollow Wood': { tomato: 64, reviews: [
    'Slow. Nothing happens for an hour and then it just ends.',
    'I checked my phone more than I checked behind the sofa.',
    'A couple of nice shots, but no scares to speak of.',
  ] },
  'Paper Boats': { tomato: 93, reviews: [
    'Quietly devastating - the audience sat through the credits.',
    'Beautifully acted; I laughed and cried within five minutes.',
    'One of those films you keep thinking about for days.',
    'Gentle, warm and completely gripping.',
  ] },
  'Orbit': { tomato: 88, reviews: [
    'Gorgeous to look at, a bit cold at heart.',
    'The space scenes are stunning; the dialogue less so.',
    'Solid sci-fi, worth it for the big screen.',
  ] },
  'Crimson Static': { tomato: 76, reviews: [
    'Some great scares, some silly ones.',
    'Fun with a crowd - people were laughing and screaming in equal measure.',
    'Good premise, wobbly ending.',
    'Not the scariest, but a good night out.',
  ] },
  'Sunday Lunch': { tomato: 71, reviews: [
    'Pleasant enough, a few good laughs.',
    'Fine for a lazy afternoon.',
    'The gran steals every scene.',
  ] },
};

function ratings() {
  const server = new McpServer({ name: 'ratings', version: '1.0.0' });
  server.registerTool('rating', {
    description: 'A film\'s critics\' score (tomato, 0-100) and some audience reviews, by title.',
    inputSchema: { title: z.string().describe('the film\'s title') },
  }, async ({ title }) => {
    const rated = RATINGS[title];
    if (!rated) return { content: [{ type: 'text', text: `no rating for "${title}"` }], isError: true };
    return { content: [{ type: 'text', text: JSON.stringify({ title, ...rated }) }] };
  });
  return server;
}

await ratings().connect(new StdioServerTransport());
