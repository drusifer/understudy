// The beat box: for the beat the run is on (or the one clicked on the diagram), what goes in and what comes out, as small
// charts: a gauge for a number column, a donut or bars for a text column, bars for a Jev answer or a blend decision. A beat
// that runs once per row shows one pass at a time, with a stepper. It draws what the server's `steps` say (src/dashboard/
// view.py, from the run's log), so a live run and a replay use the same code. It shares page.js's helpers ($, make, svgEl,
// state); text is only ever set through textContent.
'use strict';

const boxView = { pass: {}, run: null }; // the pass the person stepped to, by beat; the run last drawn (to draw it again)
const BAR_W = 120;
const UNSURE_BELOW = 0.7;

function number(value) {
  return Number.isInteger(value) ? String(value) : String(Number(Number(value).toPrecision(3)));
}

function rowsText(count) {
  return `${count} ${count === 1 ? 'row' : 'rows'}`;
}

function cut(text, length) {
  const value = String(text);
  return value.length > length ? `${value.slice(0, length - 1)}...` : value;
}

function labelText(x, y, text, className, anchor = 'start') {
  const element = svgEl('text', { class: className, x, y, 'text-anchor': anchor });
  element.textContent = text;
  return element;
}

// A chart is one SVG with a text equivalent: the name a screen reader gets and the tooltip.
function chartFrame(width, height, said, ...parts) {
  const title = svgEl('title', {});
  title.textContent = said;
  return svgEl('svg', { class: 'box-chart', width, height, viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': said }, title, ...parts);
}

// A number column: its range as a track, the mean as a tick.
function gaugeChart(column) {
  const span = column.max - column.min;
  const at = span > 0 ? 8 + ((column.mean - column.min) / span) * (BAR_W + 40 - 16) : 8;
  const said = `${column.name}: from ${number(column.min)} to ${number(column.max)}, mean ${number(column.mean)}, over ${rowsText(column.rows)}`;
  return chartFrame(BAR_W + 40, 44, said,
    labelText(0, 9, column.name, 'box-axis'),
    svgEl('rect', { class: 'gauge-track', x: 8, y: 16, width: BAR_W + 40 - 16, height: 8, rx: 4 }),
    svgEl('rect', { class: 'gauge-fill', x: 8, y: 16, width: Math.max(1, at - 8), height: 8, rx: 4 }),
    svgEl('line', { class: 'gauge-tick', x1: at, x2: at, y1: 12, y2: 28 }),
    labelText(8, 40, number(column.min), 'box-axis'),
    labelText(at, 40, `mean ${number(column.mean)}`, 'box-axis', 'middle'),
    labelText(BAR_W + 40 - 8, 40, number(column.max), 'box-axis', 'end'));
}

// A text column with few values: a donut and its legend.
function donutChart(column) {
  const total = column.top.reduce((sum, [, count]) => sum + count, 0);
  const radius = 15;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  const slices = column.top.map(([, count], index) => {
    const length = (count / total) * circumference;
    const slice = svgEl('circle', { class: `slice-${index}`, cx: 22, cy: 22, r: radius, fill: 'none', 'stroke-width': 9,
      'stroke-dasharray': `${length} ${circumference - length}`, 'stroke-dashoffset': -offset, transform: 'rotate(-90 22 22)' });
    offset += length;
    return slice;
  });
  const legend = column.top.map(([value, count], index) => [
    svgEl('rect', { class: `swatch-${index}`, x: 52, y: 6 + index * 14, width: 8, height: 8 }),
    labelText(64, 14 + index * 14, `${cut(value, 16)} ${count}`, 'box-axis')]).flat();
  const said = `${column.name}: ${column.top.map(([value, count]) => `${value} ${count}`).join(', ')}`;
  return chartFrame(BAR_W + 40, Math.max(44, 12 + column.top.length * 14), said, labelText(0, 9, column.name, 'box-axis'), ...slices, ...legend);
}

// Bars: a label, a bar and a number for each row. `value` is 0 to `most`.
const LABEL_W = 150; // room for a bar's label (about 24 characters of the small font)

function barsChart(title, rows, most, said, className = '') {
  const parts = rows.flatMap(([label, value, text, top], index) => [
    labelText(0, 22 + index * 16, cut(label, 24), `box-axis${top ? ' box-top' : ''}`),
    svgEl('rect', { class: `bar${top ? ' bar-top' : ''}${className ? ` ${className}` : ''}`, x: LABEL_W, y: 14 + index * 16, width: Math.max(1, (value / most) * BAR_W), height: 9, rx: 2 }),
    labelText(LABEL_W + BAR_W + 6, 22 + index * 16, text, `box-axis${top ? ' box-top' : ''}`)]);
  return chartFrame(LABEL_W + BAR_W + 56, 20 + rows.length * 16, said, labelText(0, 9, title, 'box-axis'), ...parts);
}

// A text column with many values: its commonest values as bars.
function topBars(column) {
  const most = Math.max(...column.top.map(([, count]) => count));
  const said = `${column.name}: ${column.distinct} different values, commonest ${column.top.map(([value, count]) => `${value} ${count}`).join(', ')}`;
  return barsChart(`${column.name} (${column.distinct} values)`, column.top.map(([value, count]) => [value, count, String(count), false]), most, said);
}

function columnChart(column) {
  if (column.rows === 1 && column.kind !== 'other') { // one value is not a spread: say it
    return make('div', { class: 'box-item' }, make('span', { class: 'box-item-name' }, column.name),
      make('span', { class: 'box-item-value' }, column.kind === 'number' ? number(column.min) : column.top[0][0]));
  }
  if (column.kind === 'number') return gaugeChart(column);
  if (column.kind === 'text') return column.distinct <= 4 ? donutChart(column) : topBars(column);
  return null;
}

// Jev's answer: each level as a bar from 0 to 1, the top one marked, UNSURE when it is below 0.7.
function jevChart(answer) {
  const levels = answer.levels ?? [[answer.top, answer.probability]];
  const unsure = answer.probability < UNSURE_BELOW || answer.top === 'none_of_these';
  const said = `Jev on ${answer.source}: ${levels.map(([name, probability]) => `${name} ${probability.toFixed(2)}`).join(', ')}${unsure ? ', unsure' : ''}`;
  return barsChart(`${answer.source}${unsure ? ' - UNSURE' : ''}`, levels.map(([name, probability], index) => [name, probability, probability.toFixed(2), index === 0]), 1, said, unsure ? 'bar-unsure' : '');
}

// A blend decision: each option's weight as a bar, the pick marked, an option something removed struck out in the text.
function decisionChart(decision) {
  const options = decision.options ?? [];
  const most = Math.max(0.0001, ...options.map((option) => option.weight ?? 0));
  const rows = options.map((option) => [option.name ?? '?', option.weight ?? 0,
    `${number(option.weight ?? 0)}${option.removed_by ? ' (removed)' : ''}`, option.name === decision.pick]);
  const said = `${decision.row} ${decision.dimension}: picked ${decision.pick}; ${options.map((option) => `${option.name} ${number(option.weight ?? 0)}`).join(', ')}`;
  return barsChart(`${decision.row} · ${decision.dimension}`, rows, most, said);
}

// One piece as a card: its name, how many rows, and up to three charts of its columns.
function pieceCard(name, piece, note = '') {
  const card = make('div', { class: 'box-card' }, make('div', { class: 'box-card-head' }, `${name} · ${rowsText(piece.rows ?? 0)}${note}`));
  const charts = (piece.columns ?? []).map(columnChart).filter(Boolean).slice(0, 3);
  if (charts.length > 0) card.append(...charts);
  else card.append(make('div', { class: 'box-quiet' }, (piece.keys ?? []).length > 0 ? `columns: ${piece.keys.join(', ')}` : 'no columns to chart'));
  return card;
}

// The row one pass of a repeated beat was for, as labeled values.
function itemCard(pass) {
  const lines = Object.entries(pass.item ?? {}).map(([name, value]) => make('div', { class: 'box-item' },
    make('span', { class: 'box-item-name' }, name), make('span', { class: 'box-item-value' }, String(value))));
  return make('div', { class: 'box-card' }, make('div', { class: 'box-card-head' }, `this pass's row (${(pass.index ?? 0) + 1} of ${pass.of ?? '?'})`), ...lines);
}

function statusOf(run, beat, said) {
  if (run.state === 'plan') return 'plan only';
  if (run.failure?.stage === beat.id) return 'failed';
  if (said?.jev && !said.action && !said.iterations) return 'answered by Jev';
  if (said?.decisions && !said.action) return 'decided';
  if (said?.iterations && !said.action) return `ran ${said.iterations.count} ${said.iterations.count === 1 ? 'pass' : 'passes'}`;
  if (said?.action || (said && 'read' in said)) return 'done';
  if (beat.current) return run.state === 'paused' ? 'held before it runs' : run.state === 'running' ? 'running' : 'ended here';
  return 'not run yet';
}

function chosenPass(beat, passes) {
  const latest = passes.latest;
  const stored = boxView.pass[beat];
  const at = stored !== undefined && stored >= 0 && stored < latest.length ? stored : latest.length - 1;
  return { at, pass: latest[at] };
}

function passStepper(beat, passes, at) {
  const first = passes.count - passes.latest.length;
  const label = make('span', { class: 'box-pass', role: 'status' }, `pass ${first + at + 1} of ${passes.count}`);
  const move = (by, text, name) => {
    const button = make('button', { type: 'button', class: 'find-button', 'aria-label': name }, text);
    button.disabled = at + by < 0 || at + by >= passes.latest.length;
    button.addEventListener('click', () => { boxView.pass[beat] = at + by; drawBox(boxView.run); $('beat-box').querySelector(`[aria-label="${name}"]`)?.focus(); });
    return button;
  };
  return make('div', { class: 'box-stepper' }, move(-1, '<', 'previous pass'), label, move(1, '>', 'next pass'),
    make('span', { class: 'box-quiet' }, 'looks back over the passes; it does not hold the run'));
}

// The beat the box follows when none was clicked: the one the run is on, or, when the run is on its final beat (which does
// nothing to show) or over, the last beat that did something.
function followedBeat(run, beats) {
  const current = beats.find((node) => node.current);
  if (current && !current.final) return current;
  const done = Object.keys(run.steps ?? {}).map((id) => beats.find((node) => node.id === id && !node.final)).filter(Boolean);
  return done.at(-1) ?? current ?? beats.find((node) => node.initial) ?? beats[0];
}

function plannedReads(chart, beat) {
  return chart.edges.filter((edge) => edge.kind === 'reads' && edge.to === beat.id).map((edge) => edge.from);
}

// Draw the box for `run` ({ chart, steps, state, failure }): the beat the run is on, or the one clicked on the diagram.
function drawBox(run) {
  boxView.run = run;
  const chart = run.chart;
  const beats = chart ? chart.nodes.filter((node) => node.kind === 'beat') : [];
  const root = $('beat-box');
  if (beats.length === 0) {
    root.replaceChildren(make('div', { class: 'box-quiet' }, 'no beat to show: this run\'s log has no plan'));
    return;
  }
  const beat = beats.find((node) => node.id === state.stepBeat) ?? followedBeat(run, beats);
  const said = run.steps?.[beat.id];
  const passes = said?.iterations;
  const status = statusOf(run, beat, said);
  const pick = passes ? chosenPass(beat.id, passes) : null;
  const inside = [];
  const outside = [];
  if (pick) {
    inside.push(itemCard(pick.pass));
    outside.push(pieceCard('made by this pass', pick.pass.made ?? { rows: 0 }));
  } else if (said) {
    inside.push(...Object.entries(said.read ?? {}).map(([name, piece]) => pieceCard(name, piece)));
    outside.push(...Object.entries(said.wrote ?? {}).map(([name, piece]) => pieceCard(name, piece, ' written')));
    if (said.made) outside.push(pieceCard('result', said.made));
  } else {
    inside.push(...plannedReads(chart, beat).map((name) => make('div', { class: 'box-card' }, make('div', { class: 'box-card-head' }, name),
      make('div', { class: 'box-quiet' }, run.state === 'plan' ? 'read by this beat' : 'not read yet'))));
  }
  if (inside.length === 0) inside.push(make('div', { class: 'box-quiet' }, 'reads nothing'));
  if (outside.length === 0) outside.push(make('div', { class: 'box-quiet' }, said ? 'makes nothing to draw' : 'nothing yet'));
  const answers = (said?.jev ?? []).filter((answer) => !pick || String(answer.source).includes(`[${pick.pass.index}]`));
  const extras = [...answers.map(jevChart), ...(said?.decisions ?? []).slice(-3).map(decisionChart)];
  root.replaceChildren(
    make('div', { class: 'box-title' }, beat.id, make('span', { class: 'box-status' }, ` · ${said?.action ?? beat.action ?? 'no action'} · ${status}`)),
    make('div', { class: 'box-flow' },
      make('div', { class: 'box-zone' }, make('div', { class: 'box-zone-name' }, 'IN'), ...inside),
      make('div', { class: 'box-arrow', 'aria-hidden': 'true' }, '>'),
      make('div', { class: 'box-zone' }, make('div', { class: 'box-zone-name' }, 'OUT'), ...outside)),
    ...(pick ? [passStepper(beat.id, passes, pick.at)] : []),
    ...(extras.length > 0 ? [make('div', { class: 'box-zone-name' }, 'WHAT JEV AND THE BLENDS DECIDED'), make('div', { class: 'box-extras' }, ...extras)] : []),
    make('div', { class: 'box-quiet' }, state.stepBeat ? 'click the beat again on the diagram to follow the run' : 'follows the beat the run is on; click a beat on the diagram to look at another'));
}
