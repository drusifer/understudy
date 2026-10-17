// Sprint 6 UND-28, UND-31 (docs/design/DASHBOARD.md): the console page's
// pure parts - weight colours and their blend, readouts, dial geometry,
// starting values and what the printer prints.
import test from 'node:test';
import assert from 'node:assert/strict';
import { blendOf, dialAngles, FRESH_METERS, gaugesOf, levelOf, metersAfter, modeChoiceOf, modeOf, MODES, printed, readoutOf, rgbOf, scoreText, startingValues, themeOf, THEMES } from '../src/dashboard/page.mjs';

const RED = [255, 72, 56];

test('the blend mixes the weight colours in the ratio of their values; all zero is grey (UND-30 AC3)', () => {
  assert.deepEqual(blendOf([{ value: 1, colour: RED }, { value: 0, colour: [176, 98, 255] }]), RED);
  assert.deepEqual(blendOf([{ value: 1, colour: [200, 0, 0] }, { value: 3, colour: [0, 0, 200] }]), [50, 0, 150]);
  assert.deepEqual(blendOf([{ value: 0, colour: RED }]), [90, 90, 90]);
});

test('a fader reads OFF at 0, 11 at the top, else two places (UND-28 AC2)', () => {
  assert.equal(readoutOf(0, [0, 3]), 'OFF');
  assert.equal(readoutOf(3, [0, 3]), '11');
  assert.equal(readoutOf(1.5, [0, 3]), '1.50');
  assert.equal(scoreText(1), '11');
  assert.equal(scoreText(0.877), '0.877');
});

test('dial options spread over 150 degrees; controls start at the defaults (UND-28 AC1, AC4)', () => {
  assert.deepEqual(dialAngles(4), [-75, -25, 25, 75]);
  assert.deepEqual(dialAngles(2), [-75, 75]);
  assert.deepEqual(startingValues([{ name: 'mood', default: 'fun' }, { name: 'together', default: true }]), { mood: 'fun', together: true });
});

test('the printer prints the start, each step with what the rules did, and the end (UND-31 AC1-2)', () => {
  assert.deepEqual(printed({ event: 'start', sketch: 'evening', inputs: { mood: 'fun', together: false } }),
    [{ text: '=== UNDERSTUDY RUN LOG ===  evening', tone: 'bold' }, { text: 'inputs  mood=fun  together=off' }]);
  const step = printed({ step: 9, move: 'tool:boxoffice/pick_seats', confidence: 0.9, response: { call: { tool: 'pick_seats', arguments: { seat: 's2-E15', count: 2 } } },
    decided: [{ argument: 'boxoffice/pick_seats.seat', table: [{ value: 's2-E15', factors: { row: 1, centre: 0.877 }, total: 0.877 }], removed: [{ value: 'a', why: 'x' }, { value: 'b', why: 'y' }, { value: 'c', why: 'z' }], held: [] }] });
  assert.equal(step[0].text, 'step 9  boxoffice/pick_seats  seat=s2-E15 count=2  (0.90)');
  assert.deepEqual(step[1], { text: '  rules removed 3: a (x), b (y), ...', tone: 'note' });
  assert.equal(step[2].table.argument, 'boxoffice/pick_seats.seat');
  assert.deepEqual(printed({ event: 'dashboard', stderr: 'holding back showing s2 - no "tomato" yet' }), [{ text: '  hold  showing s2 - no "tomato" yet', tone: 'held' }]);
  assert.deepEqual(printed({ final: true, outcome: 'walked-away', steps: 11 }), [{ text: '=== WALKED-AWAY after 11 steps ===', tone: 'bold' }]);
  assert.equal(printed({ event: 'state' }), null);
});

// Sprint 9 UND-36: the themes.
test('the theme: a known ?theme= wins, then the remembered one, else steampunk (UND-36 AC2)', () => {
  assert.deepEqual(THEMES, ['steampunk', 'professional', 'starship']);
  assert.equal(themeOf('starship', 'professional'), 'starship');
  assert.equal(themeOf(null, 'professional'), 'professional');
  assert.equal(themeOf('lcars', 'professional'), 'professional', 'an unknown name is ignored');
  assert.equal(themeOf('lcars', 'tartan'), 'steampunk');
  assert.equal(themeOf(null, null), 'steampunk');
});

// Sprint 11 UND-38: light and dark.
test('the mode: a known ?mode= wins, then the remembered one, else auto; auto follows the device (UND-38 AC1)', () => {
  assert.deepEqual(MODES, ['auto', 'light', 'dark']);
  assert.equal(modeChoiceOf('dark', 'light'), 'dark');
  assert.equal(modeChoiceOf(null, 'light'), 'light');
  assert.equal(modeChoiceOf('dim', 'light'), 'light', 'an unknown value is ignored');
  assert.equal(modeChoiceOf(null, null), 'auto');
  assert.equal(modeOf('auto', true), 'dark');
  assert.equal(modeOf('auto', false), 'light');
  assert.equal(modeOf('light', true), 'light');
  assert.equal(modeOf('dark', false), 'dark');
});

test('theme colours are read as #rrggbb; a weight\'s level is 0-3 whatever its range', () => {
  assert.deepEqual(rgbOf(' #ff4838'), [255, 72, 56]);
  assert.deepEqual(rgbOf('red'), [128, 128, 128]);
  assert.equal(levelOf(10, [0, 10]), 3);
  assert.equal(levelOf(5, [0, 10]), 1.5);
  assert.equal(levelOf(2, [1, 3]), 1.5);
});

// Sprint 15 UND-42: the gauges read the run's own lines.
test('the gauges: steps of the limit, Jev\'s confidence, the shortlist left, Jev asked and reused, idle time (UND-42)', () => {
  const at = (meters, line, now) => metersAfter(meters, line, now);
  let meters = at(FRESH_METERS, { event: 'start', limits: { steps: 30, first_move_ms: 10_000, stall_ms: 8000 } }, 1000);
  assert.deepEqual(gaugesOf(meters, 3000).map((gauge) => [gauge.name, gauge.level, gauge.text]), [
    ['STEPS', 0, '0/30'], ['SURE', 0, '-'], ['SHORTLIST', 0, '-'], ['JEV', 0, '0·0'], ['IDLE', 0.2, '2.0s'],
  ], 'before the first move, idle counts against the first-move limit');
  meters = at(meters, { event: 'state', from: 'a', to: 'b' }, 4000);
  meters = at(meters, { step: 3, confidence: 0.9, decided: [{ table: [{}, {}], removed: [{}, {}, {}], held: [{}], jev: { asked: 2, reused: 1 } }] }, 5000);
  meters = at(meters, { step: 4, confidence: 0.6, decided: [{ table: [{}], removed: [{}], held: [], jev: { asked: 0, reused: 3 } }] }, 6000);
  const [steps, sure, shortlist, jev, idle] = gaugesOf(meters, 10_000);
  assert.deepEqual([steps.level, steps.text], [4 / 30, '4/30']);
  assert.deepEqual([sure.level, sure.text], [0.6, '0.60']);
  assert.deepEqual([shortlist.level, shortlist.text], [0.5, '1/2']);
  assert.deepEqual([jev.level, jev.text], [2 / 6, '2·4']);
  assert.deepEqual([idle.level, idle.text], [0.5, '4.0s'], 'after a move, against the stall limit');
  assert.equal(gaugesOf(meters, 60_000)[4].level, 1, 'capped at the limit');
});
