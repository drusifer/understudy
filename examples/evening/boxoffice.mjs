// The evening example's box office (docs/sprints/ARCH_SPRINT5.md §5): a
// made-up cinema as an MCP server, with something to have preferences
// about - films of several genres, afternoon and evening showings in a
// small and a big screen, and a seat map that says how many free seats run
// together from each seat and how central it is. It knows nothing about
// understudy or the ratings server.
//
//   node boxoffice.mjs                  stdio
//   BOX_STATE=full node boxoffice.mjs   rows D-F taken at every evening showing
//
// One box office per process: holds made in one call are there for the next.

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const SCREENS = { small: { width: 10, rows: 'ABCDEFGH' }, big: { width: 30, rows: 'ABCDEFGHIJKL' } };

const FILMS = [
  { film: 'f1', title: 'Night Shift', genre: 'horror', price: 12 },
  { film: 'f2', title: 'The Hollow Wood', genre: 'horror', price: 10 },
  { film: 'f3', title: 'Paper Boats', genre: 'drama', price: 9 },
  { film: 'f4', title: 'Orbit', genre: 'sci-fi', price: 11 },
  { film: 'f5', title: 'Crimson Static', genre: 'horror', price: 10 },
  { film: 'f6', title: 'Sunday Lunch', genre: 'comedy', price: 8 },
];

// Rows D-F are spelled out where they matter ('.' free, 'x' taken);
// every other row is mostly taken, a seat in four free. s2: central seats free in E. s4: only
// edge seats in E, central ones in F. s13: nothing two-together in D-F.
const SHOWINGS = [
  { showing: 's1', film: 'f1', starts: '14:00', screen: 'small' },
  { showing: 's2', film: 'f1', starts: '19:30', screen: 'big',
    rows: { D: 'xxxxxxxxxxxxxxx..xxxxxxxxxxxxx', E: 'xxxxxxxxxxxx......xxxxxxxxxxxx', F: 'xxxxxxxx..xxxxxxxxxx..xxxxxxxx' } },
  { showing: 's13', film: 'f1', starts: '22:30', screen: 'small',
    rows: { D: 'x.x.x.x.x.', E: '.x.x.x.x.x', F: 'xxxxxxxxxx' } },
  { showing: 's3', film: 'f5', starts: '15:00', screen: 'small' },
  { showing: 's4', film: 'f5', starts: '20:00', screen: 'small',
    rows: { D: 'xxxxxxxxxx', E: '..xxxxxx..', F: 'xxx....xxx' } },
  { showing: 's5', film: 'f2', starts: '13:30', screen: 'big' },
  { showing: 's6', film: 'f2', starts: '21:00', screen: 'big' },
  { showing: 's7', film: 'f3', starts: '16:00', screen: 'big' },
  { showing: 's8', film: 'f3', starts: '18:00', screen: 'small',
    rows: { D: 'xx..xxxxxx', E: 'xxxx..xxxx', F: 'x..xxxxx..' } },
  { showing: 's9', film: 'f4', starts: '14:30', screen: 'small' },
  { showing: 's10', film: 'f4', starts: '19:00', screen: 'big' },
  { showing: 's11', film: 'f6', starts: '12:00', screen: 'small' },
  { showing: 's12', film: 'f6', starts: '17:00', screen: 'big' },
];

const EVENING = '17:00';
const isFull = process.env.BOX_STATE === 'full';

/**
 * How central seat `number` is in a row `width` seats wide: 1 in the
 * middle, 0 at either end (ARCH §5).
 */
function centreOf(number, width) {
  const middle = (width + 1) / 2;
  return Math.max(0, Math.round((1 - (2 * Math.abs(number - middle)) / (width - 1)) * 100) / 100);
}

/**
 * Which seats of a showing are taken: a row as '.'/'x', one per seat.
 */
function seatingOf(showing, index) {
  const { width, rows } = SCREENS[showing.screen];
  const taken = {};
  for (const [rowIndex, row] of [...rows].entries()) {
    const written = showing.rows?.[row];
    const isBlocked = isFull && showing.starts >= EVENING && 'DEF'.includes(row);
    taken[row] = Array.from({ length: width }, (_, seat) => {
      if (isBlocked) return true;
      if (written) return written[seat] === 'x';
      return (seat * 7 + rowIndex * 3 + index) % 4 !== 0;
    });
  }
  return taken;
}

const office = {
  seating: new Map(SHOWINGS.map((showing, index) => [showing.showing, seatingOf(showing, index)])),
  holds: new Map(),
  next: 1,
};

const filmOf = (showing) => FILMS.find((film) => film.film === showing.film);
const answer = (value) => ({ content: [{ type: 'text', text: typeof value === 'string' ? value : JSON.stringify(value) }] });
const refuse = (text) => ({ content: [{ type: 'text', text }], isError: true });

/**
 * A showing's free seats, each with how many free seats run together
 * from it (to the right) and how central it is.
 */
function freeSeats(showing) {
  const { width } = SCREENS[showing.screen];
  const seats = [];
  const seating = Object.entries(office.seating.get(showing.showing));
  for (const [row, taken] of seating) {
    for (let seat = 0; seat < width; seat++) {
      if (taken.at(seat)) continue;
      let together = 0;
      while (seat + together < width && !taken.at(seat + together)) together++;
      const number = seat + 1;
      seats.push({ seat: `${showing.showing}-${row}${number}`, row, number, together, centre: centreOf(number, width) });
    }
  }
  return seats;
}

function boxOffice() {
  const server = new McpServer({ name: 'boxoffice', version: '1.0.0' });
  server.registerTool('list_films', {
    description: 'Today\'s films with their genre and showings (start time and screen).',
  }, async () => answer(FILMS.map((film) => ({
    film: film.film, title: film.title, genre: film.genre, price: film.price,
    showings: SHOWINGS.filter((showing) => showing.film === film.film).map(({ showing, starts, screen }) => ({ showing, starts, screen })),
  }))));
  server.registerTool('seat_map', {
    description: 'The free seats of one showing: row, number, how many free seats run together from it, how central it is (0 end, 1 middle).',
    inputSchema: { showing: z.string().describe('the showing id from list_films') },
  }, async ({ showing: id }) => {
    const showing = SHOWINGS.find((each) => each.showing === id);
    if (!showing) return refuse(`No showing ${id} today - see list_films.`);
    return answer({ showing: id, title: filmOf(showing).title, starts: showing.starts, screen: showing.screen, seats: freeSeats(showing) });
  });
  server.registerTool('pick_seats', {
    description: 'Hold `count` side-by-side seats starting at `seat` and going right. Returns a hold to pay for.',
    inputSchema: {
      seat: z.string().describe('the seat id from seat_map, e.g. s2-E14'),
      count: z.number().int().min(1).max(4).describe('how many seats'),
    },
  }, async ({ seat: id, count }) => {
    const [showingId, label = ''] = id.split('-', 2);
    const showing = SHOWINGS.find((each) => each.showing === showingId);
    const free = showing ? freeSeats(showing).find((each) => each.seat === id) : null;
    if (!free) return refuse(`No free seat ${id} - see seat_map.`);
    if (free.together < count) return refuse(`${label} has only ${free.together} free seat${free.together === 1 ? '' : 's'} together`);
    const taken = office.seating.get(showingId)[free.row];
    const labels = [];
    for (let seat = free.number - 1; seat < free.number - 1 + count; seat++) {
      taken[seat] = true;
      labels.push(`${free.row}${seat + 1}`);
    }
    const film = filmOf(showing);
    const hold = `h${office.next++}`;
    const held = { hold, title: film.title, starts: showing.starts, seats: labels.join(', '), count, total: film.price * count };
    office.holds.set(hold, held);
    return answer(held);
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
    return answer(`Ticket issued: ${held.title} at ${held.starts}, seats ${held.seats}, ${held.total} paid by card. Enjoy the film!`);
  });
  return server;
}

await boxOffice().connect(new StdioServerTransport());
