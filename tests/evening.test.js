// Sprint 5 UND-18, UND-19 (ARCH §5): the evening example's box office and
// ratings servers, driven through the MCP target as one two-server sketch.
import test from 'node:test';
import assert from 'node:assert/strict';
import { startTarget } from '../src/targets/mcp.mjs';

const from = 'examples/evening/sketch.yaml';
const spec = (environment = {}) => ({
  kind: 'mcp',
  servers: [
    { name: 'boxoffice', from, entry: { command: 'node', args: ['boxoffice.mjs'], env: environment } },
    { name: 'ratings', from, entry: { command: 'node', args: ['ratings.mjs'] } },
  ],
});

async function started(environment) {
  const target = await startTarget(spec(environment), { directory: 'examples/evening', environment: process.env });
  test.after(() => target.close());
  return target;
}

async function call(target, server, tool, arguments_ = {}) {
  const response = await target.act({ server, tool, arguments: arguments_ });
  // The step's text is cut for the log; the view keeps the whole answer.
  const { text } = (await target.view()).last;
  return { ...response, text, value: response.isError ? null : JSON.parse(text) };
}

const seatsOf = async (target, showing) => (await call(target, 'boxoffice', 'seat_map', { showing })).value.seats;

test('films have titles and genres, with afternoon and evening showings in two screen sizes (UND-18 AC1-2)', async () => {
  const target = await started();
  const films = (await call(target, 'boxoffice', 'list_films')).value;
  assert.ok(films.length >= 5);
  assert.ok(films.filter((film) => film.genre === 'horror').length >= 2);
  assert.ok(films.filter((film) => film.genre !== 'horror').length >= 2);
  for (const film of films) {
    assert.ok(film.showings.some((showing) => showing.starts < '17:00'), `${film.title} has an afternoon showing`);
    assert.ok(film.showings.some((showing) => showing.starts >= '17:00'), `${film.title} has an evening showing`);
    for (const showing of film.showings) assert.match(showing.starts, /^\d\d:\d\d$/);
  }
  assert.deepEqual(new Set(films.flatMap((film) => film.showings.map((showing) => showing.screen))), new Set(['small', 'big']));
});

test('a seat map gives each free seat its row, number, run together and centreness scaled to the row (UND-18 AC3)', async () => {
  const target = await started();
  const small = await seatsOf(target, 's4');
  const big = await seatsOf(target, 's2');
  const seat = (seats, row, number) => seats.find((each) => each.row === row && each.number === number);
  assert.deepEqual(seat(small, 'F', 4), { seat: 's4-F4', row: 'F', number: 4, together: 4, centre: 0.67 });
  // 1 at the middle, 0 at the ends, scaled by the row: the 2nd seat of 10
  // scores 0.22; seats 2.5 off the middle score 0.44 of 10 but 0.83 of 30.
  assert.deepEqual([seat(small, 'E', 1).centre, seat(small, 'E', 2).centre], [0, 0.22]);
  assert.deepEqual([seat(small, 'F', 7).centre, seat(big, 'E', 13).centre, seat(big, 'E', 16).centre], [0.67, 0.83, 0.97]);
  assert.equal(seat(big, 'E', 13).together, 6);
});

test('holding two seats from a long enough run holds them side by side; paying issues the ticket (UND-18 AC4)', async () => {
  const target = await started();
  const held = await call(target, 'boxoffice', 'pick_seats', { seat: 's2-E15', count: 2 });
  assert.deepEqual(held.value, { hold: 'h1', title: 'Night Shift', starts: '19:30', seats: 'E15, E16', count: 2, total: 24 });
  const paid = await target.act({ server: 'boxoffice', tool: 'pay', arguments: { hold: 'h1', method: 'card' } });
  assert.equal(paid.text, 'Ticket issued: Night Shift at 19:30, seats E15, E16, 24 paid by card. Enjoy the film!');
  assert.equal((await seatsOf(target, 's2')).some((each) => each.seat === 's2-E15'), false);
});

test('a run too short is refused naming the seat and its run; nothing is held (UND-18 AC5)', async () => {
  const target = await started();
  const refused = await call(target, 'boxoffice', 'pick_seats', { seat: 's4-E2', count: 2 });
  assert.equal(refused.isError, true);
  assert.equal(refused.text, 'E2 has only 1 free seat together');
  assert.ok((await seatsOf(target, 's4')).some((each) => each.seat === 's4-E2'));
});

test('the seat maps hold the three evening horror cases, and BOX_STATE=full takes D-F at every evening showing (UND-18 AC6)', async () => {
  const target = await started();
  const inRows = (seats, rows, at_least = 2) => seats.filter((each) => rows.includes(each.row) && each.together >= at_least);
  assert.ok(inRows(await seatsOf(target, 's2'), ['E']).some((each) => each.centre >= 0.8), 's2: central pair free in E');
  const s4 = await seatsOf(target, 's4');
  assert.ok(inRows(s4, ['E']).every((each) => each.centre < 0.3), 's4: only edge pairs in E');
  assert.ok(inRows(s4, ['F']).some((each) => each.centre >= 0.6), 's4: central pair in F');
  assert.deepEqual(inRows(await seatsOf(target, 's13'), ['D', 'E', 'F']), [], 's13: no pair in D-F');

  const full = await started({ BOX_STATE: 'full' });
  const films = (await call(full, 'boxoffice', 'list_films')).value;
  const evenings = films.flatMap((film) => film.showings.filter((each) => each.starts >= '17:00'));
  for (const showing of evenings) {
    assert.deepEqual(inRows(await seatsOf(full, showing.showing), ['D', 'E', 'F'], 1), [], `${showing.showing} full in D-F`);
  }
});

test('the ratings server answers a score and reviews by title; the same every time (UND-19 AC1-2)', async () => {
  const target = await started();
  const night = (await call(target, 'ratings', 'rating', { title: 'Night Shift' })).value;
  assert.equal(night.tomato, 82);
  assert.ok(night.reviews.length >= 3 && night.reviews.length <= 5);
  assert.deepEqual((await call(target, 'ratings', 'rating', { title: 'Night Shift' })).value, night);
  const films = (await call(target, 'boxoffice', 'list_films')).value;
  const rated = [];
  for (const film of films) rated.push({ ...film, ...(await call(target, 'ratings', 'rating', { title: film.title })).value });
  const horror = rated.filter((film) => film.genre === 'horror');
  const other = rated.filter((film) => film.genre !== 'horror');
  assert.ok(horror.some((film) => film.tomato >= 70) && horror.some((film) => film.tomato < 70));
  assert.ok(other.some((film) => film.tomato > 90) && other.some((film) => film.tomato <= 90));
});

test('an unknown title is a tool error naming it (UND-19 AC3)', async () => {
  const target = await started();
  const unknown = await call(target, 'ratings', 'rating', { title: 'Xyz' });
  assert.equal(unknown.isError, true);
  assert.equal(unknown.text, 'no rating for "Xyz"');
});
