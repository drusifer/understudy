// The console page: draws what the server returns (src/dashboard/server.py). The server decides what is shown;
// this script lists the runs, draws one, follows a live one, and keeps the theme and mode.
'use strict';

const THEMES = ['steampunk', 'professional', 'starship'];
const MODES = ['auto', 'light', 'dark'];
const $ = (id) => document.getElementById(id);
const make = (tag, attributes = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  node.append(...children);
  return node;
};
const remembered = (key) => { try { return localStorage.getItem(`understudy.${key}`); } catch { return null; } };
const remember = (key, value) => { try { localStorage.setItem(`understudy.${key}`, value); } catch { /* private mode */ } };
const known = (list, ...candidates) => candidates.find((each) => list.includes(each)) ?? list[0];

const state = { view: 'run', runs: [], chosen: null, chosenState: null, follow: null, openGroups: new Set(), theme: 'steampunk', mode: 'auto' };
const query = new URLSearchParams(location.search);
const device = matchMedia('(prefers-color-scheme: dark)');

function look() {
  const root = document.documentElement;
  root.dataset.theme = state.theme;
  root.dataset.mode = state.mode === 'auto' ? (device.matches ? 'dark' : 'light') : state.mode;
  for (const button of document.querySelectorAll('.theme-choice')) button.setAttribute('aria-pressed', String(button.dataset.theme === state.theme));
  for (const button of document.querySelectorAll('.mode-choice')) button.setAttribute('aria-pressed', String(button.dataset.mode === state.mode));
}

// The printer holds every line of the chosen run in state.lines; the finder decides which of them are on the paper.
state.lines = [];
state.failures = [];
state.jev = null;
state.jevGauges = [];
const finder = () => ({ text: $('find-text').value.trim().toLowerCase(), failures: $('find-failures').checked, stage: $('find-stage').value });

function shown(entry, find) {
  if (find.failures && entry.tone !== 'held') return false;
  if (find.stage && !(entry.stage === find.stage || entry.stage.startsWith(`${find.stage}.`) || entry.stage.startsWith(`${find.stage}[`))) return false;
  return !find.text || entry.text.toLowerCase().includes(find.text);
}

function line(each, index) {
  return make('div', { class: `line ${each.tone ?? ''}${each.event === 'decision' ? ' decision' : ''}`, 'data-index': String(index) }, each.text);
}

function noMatch() {
  const clear = make('button', { type: 'button', class: 'find-button' }, 'CLEAR FILTERS');
  clear.addEventListener('click', clearFinder);
  return make('div', { class: 'no-match', role: 'status' }, 'no lines match ', clear);
}

function renderPaper() {
  const find = finder();
  const nodes = state.lines.flatMap((each, index) => (shown(each, find) ? [line(each, index)] : []));
  $('paper').replaceChildren(...(nodes.length || !state.lines.length ? nodes : [noMatch()]));
  $('paper-window').scrollTop = $('paper-window').scrollHeight;
}

function clearFinder() {
  $('find-text').value = '';
  $('find-failures').checked = false;
  $('find-stage').value = '';
  renderPaper();
}

function setFailures(indices) {
  state.failures = indices;
  $('jump-failure').disabled = indices.length === 0;
  $('jump-failure').title = indices.length ? 'Show the first failed line' : 'no failure in this run';
}

// A new line from a run that is going: kept, and put on the paper only if the finder lets it through.
function append(each) {
  state.lines.push(each);
  const index = state.lines.length - 1;
  if (each.tone === 'held') setFailures([...state.failures, index]);
  if (!shown(each, finder())) return;
  const window = $('paper-window');
  const atEnd = window.scrollTop + window.clientHeight >= window.scrollHeight - 8;
  $('paper').querySelector('.no-match')?.remove();
  $('paper').append(line(each, index));
  if (atEnd) window.scrollTop = window.scrollHeight;
}

function gauge(each) {
  const ticks = Array.from({ length: 11 }, (_, index) => {
    const angle = ((-60 + index * 12) * Math.PI) / 180;
    const [inner, outer] = index % 5 === 0 ? [36, 46] : [40, 46];
    const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    for (const [name, value] of Object.entries({ x1: 50 + inner * Math.sin(angle), y1: 56 - inner * Math.cos(angle), x2: 50 + outer * Math.sin(angle), y2: 56 - outer * Math.cos(angle), class: 'tick' })) tick.setAttribute(name, value);
    return tick;
  });
  const dial = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  dial.setAttribute('viewBox', '0 0 100 62');
  dial.setAttribute('class', 'dial');
  dial.setAttribute('aria-hidden', 'true');
  dial.innerHTML = '<path d="M 10 56 A 46 46 0 0 1 90 56" class="arc" fill="none"/><line x1="50" y1="56" x2="50" y2="14" class="needle"/><circle cx="50" cy="56" r="4" class="hub"/>';
  dial.prepend(...ticks);
  // A needle only where the run knows a full scale (level is a fraction); otherwise just the figure.
  const attributes = each.level === null
    ? { class: 'gauge no-needle', role: 'group' }
    : { class: 'gauge', role: 'meter', 'aria-valuemin': '0', 'aria-valuemax': '1', 'aria-valuenow': String(each.level) };
  const node = make('div', { ...attributes, 'aria-valuetext': `${each.name.toLowerCase()} ${each.text}`, 'aria-label': each.about, title: each.about },
    dial, make('div', { class: 'figure' }, each.text), make('div', { class: 'gauge-name' }, each.name));
  node.style.setProperty('--level', String(each.level ?? 0));
  return node;
}

const WORDS = { running: 'RUNNING', paused: 'PAUSED', done: 'DONE', failed: 'FAILED', stopped: 'STOPPED', stalled: 'STALLED', unreadable: 'NO DETAILS' };
const LAMPS = { running: 'on-air', paused: 'standby', done: 'done', failed: 'failed', stopped: 'standby', stalled: 'stalled', unreadable: 'dark' };

// The banner above the printer: why a run failed (it jumps to that line), or that a run looks dead.
function drawBanner(run) {
  if (run.failure) {
    const banner = make('button', { type: 'button', class: 'banner', title: 'Show this line in the printer' }, `FAILED at ${run.failure.stage}: ${run.failure.reason}`);
    banner.addEventListener('click', () => jumpTo(run.failure.line));
    $('banner-slot').replaceChildren(banner);
  } else if (run.state === 'stalled') {
    $('banner-slot').replaceChildren(make('div', { class: 'banner warn' }, run.ended));
  } else {
    $('banner-slot').replaceChildren();
  }
}

// Bring one line (by its place in the whole log) into view; if the finder is hiding it, clear the finder first.
function jumpTo(index) {
  if (index === null || index === undefined) return;
  let node = $('paper').querySelector(`[data-index="${index}"]`);
  if (!node) {
    clearFinder();
    node = $('paper').querySelector(`[data-index="${index}"]`);
  }
  node?.scrollIntoView({ block: 'center' });
}

function drawSummary(run) {
  const { summary } = run;
  const pairs = Object.entries(summary.with);
  const outputs = Object.entries(summary.outputs);
  const rows = [
    ['outcome', summary.outcome ?? '-'], ['mode', summary.mode || '-'], ['stale', summary.stale === null ? '-' : String(summary.stale)],
    ['took', `${summary.seconds}s`], ['with', pairs.length ? pairs.map(([name, value]) => `${name}=${value}`).join(' ') : '-'],
    ['wrote', outputs.length ? outputs.map(([file, count]) => `${file} (${count} ${count === 1 ? 'row' : 'rows'})`).join(', ') : '-'],
  ];
  $('summary').replaceChildren(...rows.flatMap(([name, value]) => [make('dt', {}, name), make('dd', {}, value)]));
}

const SVG_NS = 'http://www.w3.org/2000/svg';

// An SVG element with its attributes; text is only ever set through textContent, never as markup.
function svgEl(name, attributes = {}, ...children) {
  const element = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  for (const child of children) element.append(child);
  return element;
}

function arrowMarker(id, className) {
  return svgEl('marker', { id, viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 8, markerHeight: 8, orient: 'auto' },
    svgEl('path', { d: 'M0 0L10 5L0 10z', class: className }));
}

// What a node is, in words: a piece of the stage (read or written) or a beat (in the flow, or waiting until it is read).
function nodeWords(node) {
  if (node.kind === 'piece') return node.write ? 'file written' : 'file read';
  return `${node.final ? 'final beat' : node.waits ? 'beat performed when read' : 'beat'}${node.action ? `, ${node.action}` : ''}`;
}

// `options.pick(node)` makes the nodes `options.can(node)` accepts clickable (`options.picked` names the one chosen), for a
// diagram the person chooses a beat on: `options.mode` is 'hold' (hold the next run before it) or 'show' (show its step).
function stateGroup(node, options = {}) {
  const detail = node.action ?? node.path ?? '';
  const name = svgEl('text', { class: 'state-name', x: node.x + node.w / 2, y: node.y + node.h / 2 + (detail ? -1 : 5), 'text-anchor': 'middle' });
  name.textContent = node.id;
  const under = detail ? [svgEl('text', { class: 'state-detail', x: node.x + node.w / 2, y: node.y + node.h / 2 + 14, 'text-anchor': 'middle' })] : [];
  if (detail) under[0].textContent = detail;
  // what the run did here, once the beat has completed: the rows it made (or wrote), in a small tag on the corner of its box
  const said = options.steps?.[node.id];
  const rows = said?.made?.rows ?? Object.values(said?.wrote ?? {})[0]?.rows;
  if (rows !== undefined) {
    const tag = svgEl('text', { class: 'row-badge', x: node.x + node.w - 2, y: node.y - 5, 'text-anchor': 'end' });
    tag.textContent = `${rows} ${rows === 1 ? 'row' : 'rows'}`;
    under.push(tag);
  }
  if (node.initial) {
    const start = svgEl('text', { class: 'start-tag', x: node.x + 2, y: node.y - 5 });
    start.textContent = 'START';
    under.push(start);
  }
  const extra = node.kind === 'piece' ? `, ${nodeWords(node)}` : node.waits ? ', performed when read' : '';
  const label = `${node.id}${node.final ? ', final beat' : ''}${node.current ? ', current beat' : ''}${extra}${detail ? `, ${detail}` : ''}${rows !== undefined ? `, ${rows} rows` : ''}`;
  const piece = node.kind === 'piece';
  const box = svgEl('rect', { class: 'state-box', x: node.x, y: node.y, width: node.w, height: node.h, rx: piece ? node.h / 2 : 6 });
  const ring = node.final ? [svgEl('rect', { class: 'final-ring', x: node.x + 4, y: node.y + 4, width: node.w - 8, height: node.h - 8, rx: 4 })] : [];
  const pickable = Boolean(options.pick) && Boolean(options.can?.(node));
  const picked = pickable && options.picked === node.id;
  const holding = options.mode === 'hold';
  const classes = ['state', piece ? 'piece' : '', piece && node.write ? 'write' : '', node.waits ? 'waits' : '', node.final ? 'final' : '',
    node.current ? 'current' : '', node.initial ? 'initial' : '', pickable ? 'pickable' : '',
    picked ? (holding ? 'hold-here' : 'chosen') : ''].filter(Boolean).join(' ');
  const attributes = pickable ? { role: 'button', tabindex: 0, 'aria-pressed': String(picked),
    'aria-label': holding ? `hold before ${node.id}` : label } : { role: 'img', 'aria-label': label };
  const group = svgEl('g', { class: classes, ...attributes, 'data-state': node.id }, svgEl('title', {}), box, ...ring, name, ...under);
  group.querySelector('title').textContent = pickable
    ? `${nodeWords(node)}: click to ${holding ? 'hold the run before this beat' : 'see what this beat read and made'}` : nodeWords(node);
  if (pickable) {
    group.addEventListener('click', () => options.pick(node));
    group.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); options.pick(node); } });
  }
  return group;
}

function edgeGroup(edge) {
  const line = svgEl('polyline', { class: `edge ${edge.kind}${edge.back ? ' back' : ''}${edge.taken ? ' taken' : ''}`, points: edge.points.map((point) => point.join(',')).join(' '),
    'marker-end': `url(#${edge.taken ? 'arrow-taken' : 'arrow'})`, 'data-from': edge.from, 'data-to': edge.to });
  if (!edge.label) return [line];
  const box = edge.label_box;
  const text = svgEl('text', { class: 'edge-label-text', x: box.x + 5, y: box.y + box.h - 5 });
  text.textContent = edge.label;
  return [line, svgEl('rect', { class: 'edge-label-box', x: box.x, y: box.y, width: box.w, height: box.h, rx: 3 }), text];
}

// A play's plan as boxes, tags and arrows from the server's layout (src/dashboard/chart.py); the page only draws it.
function drawDiagram(wrap, chart, options = {}) {
  wrap.hidden = !chart;
  if (!chart) { wrap.replaceChildren(); return; }
  wrap.replaceChildren(svgEl('svg', { class: 'chart-svg', width: chart.width, height: chart.height, viewBox: `0 0 ${chart.width} ${chart.height}`, 'aria-hidden': 'false' },
    svgEl('defs', {}, arrowMarker('arrow', 'arrowhead'), arrowMarker('arrow-taken', 'arrowhead taken')),
    ...chart.edges.flatMap(edgeGroup), ...chart.nodes.map((node) => stateGroup(node, options))));
}

// The chosen run's diagram, with the beat it is in lit; a beat clicked on it is the one the step view describes.
function drawChart(run) {
  const chart = run.chart;
  state.shownRun = run;
  if (state.view === 'plan') return; // the picked play's plan is on screen (controls.js); a run tab or a start brings the run back
  $('chart-title').textContent = `DIAGRAM OF RUN ${stamp(run.id)}`;
  drawViewButton(chart);
  drawDiagram($('chart-wrap'), chart, { pick: pickStep, picked: state.stepBeat, mode: 'show', can: (node) => node.kind === 'beat', steps: run.steps });
  drawBox(run);
  if (!chart) {
    $('chart-note').textContent = 'this run\'s log has no plan, so there is no diagram to draw';
    return;
  }
  const current = chart.nodes.find((node) => node.current);
  $('chart-note').textContent = chart.ended ? `ended${current ? ` in ${current.id}` : ''}: ${chart.ended}`
    : current ? `in beat ${current.id}` : 'waiting for the first beat';
}

function pickStep(node) {
  state.stepBeat = state.stepBeat === node.id ? null : node.id;
  drawChart(state.shownRun);
  $('chart-wrap').querySelector(`[data-state="${CSS.escape(node.id)}"]`)?.focus(); // the diagram was drawn again
}

const dollars = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

// What the money went on: the run's ten largest categories with amount and share; nothing is drawn for a run without the file.
function drawSpending(spending) {
  const box = $('spending');
  box.hidden = !spending;
  if (!spending) { $('spending-list').replaceChildren(); $('spending-more').textContent = ''; return; }
  $('spending-list').replaceChildren(...spending.top.map((each) => make('li', {},
    make('span', { class: 'spend-name' }, each.category),
    make('span', { class: 'spend-amount' }, `${dollars.format(each.amount)} · ${(each.share * 100).toFixed(1)}%`))));
  $('spending-more').textContent = spending.problem ?? (spending.top.length === 0 ? 'no spending in this run'
    : spending.more > 0 ? `and ${spending.more} more` : '');
}

// Everything but the printer's lines, so it can be refreshed while a run goes without losing the reader's place.
function drawStatus(run) {
  $('gauges').replaceChildren(...[...run.gauges, ...state.jevGauges].map(gauge));
  $('tube-caption').textContent = `${run.sketch} · ${WORDS[run.state]} · ${run.mode}`;
  $('ended').textContent = run.ended;
  $('printer-state').textContent = run.state === 'running' ? 'PRINTING' : WORDS[run.state];
  $('status-lamp').className = `lamp ${LAMPS[run.state]}`;
  $('status-text').textContent = WORDS[run.state];
  drawBanner(run);
  drawSummary(run);
  drawSpending(run.spending);
  drawChart(run);
  state.chosenState = run.state;
  if (typeof afterStatus === 'function') afterStatus(run); // controls.js: the controls follow the chosen run
  if (typeof afterReplayStatus === 'function') afterReplayStatus(run); // replay.js: REPLAY follows the chosen run
}

// The stages the stage filter offers: each top-level stage and each group of nested stages.
function fillStageFilter(run) {
  const names = run.tube.flatMap((stage) => [stage.name, ...stage.groups.map((group) => group.name)]);
  $('find-stage').replaceChildren(make('option', { value: '' }, 'all stages'), ...names.map((name) => make('option', { value: name }, name)));
}

// The Jev list: what Jev was asked in this run and how sure it was, from the run's captured answers.
function drawJev() {
  const jev = state.jev;
  const unsure = $('jev-unsure').checked;
  if (!jev) { $('jev-summary').textContent = 'JEV READS'; $('jev-list').replaceChildren(); return; }
  const flagged = jev.reads.filter((each) => each.flagged).length;
  $('jev-summary').textContent = jev.kept ? `JEV READS · ${jev.reads.length} read, ${flagged} unsure` : `JEV READS · ${jev.note}`;
  const items = jev.reads.filter((each) => !unsure || each.flagged).map((each) => make('details', { class: `jev-read ${each.flagged ? 'unsure' : ''}` },
    make('summary', {}, `${each.source} · ${each.top} ${each.probability.toFixed(2)}${each.flagged ? ' · UNSURE' : ''}`),
    ...(each.instructions ? [make('div', { class: 'jev-question' }, each.instructions)] : []),
    ...each.levels.map(([level, probability]) => make('div', { class: 'jev-level' }, `${level} ${probability.toFixed(2)}`))));
  const notes = [];
  if (!jev.kept) notes.push(make('div', { class: 'about' }, jev.note));
  if (jev.missing.length) notes.push(make('div', { class: 'about' }, `missing capture halves: ${jev.missing.join(', ')}`));
  if (jev.kept && !items.length) notes.push(make('div', { class: 'about' }, unsure ? 'no unsure reads' : 'no reads'));
  $('jev-list').replaceChildren(...notes, ...items);
}

async function loadJev(id) {
  const jev = await getJson(`api/runs/${id}/jev`);
  if (state.chosen !== id) return;
  state.jev = jev;
  state.jevGauges = [];
  if (jev?.kept && jev.reads.length) {
    const total = jev.asked + jev.reused;
    state.jevGauges = [
      { name: 'SURE', level: jev.confidence, text: jev.confidence.toFixed(2), about: "how sure Jev was of its last read" },
      { name: 'ASKED', level: total ? jev.asked / total : null, text: `${jev.asked}·${jev.reused}`, about: 'answers asked live · answers reused from a capture' },
    ];
  }
  drawJev();
  const run = await getJson(runUrl(id));
  if (run && state.chosen === id) drawStatus(run);
}

$('jev-unsure').addEventListener('input', drawJev);

function draw(run) {
  state.jev = null;
  state.jevGauges = [];
  state.lines = run.lines;
  setFailures(run.failures);
  fillStageFilter(run);
  clearFinder();
  drawStatus(run);
}

for (const id of ['find-text', 'find-failures', 'find-stage']) $(id).addEventListener('input', renderPaper);
$('jump-start').addEventListener('click', () => { $('paper-window').scrollTop = 0; });
$('jump-end').addEventListener('click', () => { $('paper-window').scrollTop = $('paper-window').scrollHeight; });
$('jump-failure').addEventListener('click', () => jumpTo(state.failures[0]));

// The address of a run's description (or one of its parts), with the diagram view the person chose (the server picks when none).
function runUrl(id, more = '', query = '') {
  const parts = [query, state.diagramView ? `view=${state.diagramView}` : ''].filter(Boolean);
  return `api/runs/${id}${more}${parts.length ? `?${parts.join('&')}` : ''}`;
}

// The button that shows a big play whole or as its flow only (it is there when the flow view hides anything).
function drawViewButton(chart) {
  const button = $('diagram-view');
  button.hidden = !chart || chart.hidden === 0;
  if (!chart || chart.hidden === 0) return;
  const flow = chart.view === 'flow';
  button.textContent = flow ? `SHOW ALL ${chart.total} NODES` : 'SHOW ONLY THE FLOW';
  button.title = flow ? `${chart.hidden} beats that wait to be read are hidden; their reads are drawn from the files to the flow beats`
    : 'Hide the beats that wait to be read';
  button.dataset.next = flow ? 'all' : 'flow';
}

async function switchView() {
  state.diagramView = $('diagram-view').dataset.next;
  if (state.view === 'plan') { showPlan(); return; }
  if (typeof replay !== 'undefined' && replay.open) { replayTo(replay.at); return; }
  const run = state.chosen ? await getJson(runUrl(state.chosen)) : null;
  if (run) drawStatus(run);
}

// A fetch that says so when the server cannot be reached, and recovers by itself on the next one that works.
async function getJson(url) {
  try {
    const value = await (await fetch(url)).json();
    setOffline(false);
    return value;
  } catch {
    setOffline(true);
    return null;
  }
}

function setOffline(offline) {
  $('offline').hidden = !offline;
  $('console').classList.toggle('stale', offline);
}

async function choose(id) {
  if (typeof endReplay === 'function') endReplay(false); // replay.js: choosing a run closes a replay
  state.follow?.close();
  state.chosen = id;
  state.view = 'run'; // a run tab brings the run's diagram back from a play's plan
  state.stepBeat = null; // the step view follows the new run until a beat is clicked
  rack();
  const run = await getJson(runUrl(id));
  if (!run) return;
  draw(run);
  loadJev(id);
  if (typeof loadDecisions === 'function') loadDecisions(id); // decisions.js: the run's decisions
  if (!['running', 'paused'].includes(run.state)) return;
  const source = new EventSource(`events/${id}`);
  state.follow = source;
  let skip = run.count;
  source.onmessage = (message) => { if (skip > 0) skip -= 1; else { append(JSON.parse(message.data)); refreshSoon(id); } };
  source.addEventListener('end', async () => { source.close(); const done = await getJson(runUrl(id)); if (done) drawStatus(done); loadJev(id); if (typeof loadDecisions === 'function') loadDecisions(id); loadRuns(); });
}

// A new event line while a run goes: refresh what the run says about itself (the lit state, the gauges) soon, but once for a burst.
let refreshTimer = null;
function refreshSoon(id) {
  if (refreshTimer) return;
  refreshTimer = setTimeout(async () => {
    refreshTimer = null;
    const run = await getJson(runUrl(id));
    if (run && state.chosen === id) drawStatus(run);
  }, 250);
}

// run-20261031T012507-46140191 reads "10-31 01:25".
function stamp(id) {
  const [, month, day, hour, minute] = /^run-\d{4}(\d\d)(\d\d)T(\d\d)(\d\d)/.exec(id) ?? [];
  return month ? `${month}-${day} ${hour}:${minute}` : id;
}

const BADGES = { running: 'RUNNING', paused: 'PAUSED', failed: 'FAILED', stalled: 'STALLED', stopped: 'STOPPED' };

// The rack: runs grouped by sketch (the runs arrive newest first, so each group and each tab inside it is newest first),
// each tab carrying a badge in words for a run that is going, failed, stalled or stopped.
const RACK_KEEP = 8; // runs of one play the rack shows before folding the older ones

function runTab(each) {
  const label = make('span', { class: 'name' }, stamp(each.id));
  const tab = make('button', { type: 'button', role: 'tab', class: `sketch-tab ${each.state}`, 'aria-selected': String(each.id === state.chosen), title: `${each.id} · ${each.state}` }, label);
  if (BADGES[each.state]) tab.append(make('span', { class: 'badge' }, BADGES[each.state]));
  tab.addEventListener('click', () => choose(each.id));
  return tab;
}

// One group of the rack: the play's name, its newest runs (and the chosen one, wherever it is), and a button for the rest.
// `folded` groups (the runs this console cannot read) show only the chosen run until opened.
function rackGroup(name, runs, folded) {
  const key = `rack:${name}`;
  const open = state.openGroups.has(key);
  const keep = folded ? 0 : RACK_KEEP;
  const shown = open ? runs : runs.filter((each, index) => index < keep || each.id === state.chosen);
  const hidden = runs.length - shown.length;
  const toggle = (label) => {
    const button = make('button', { type: 'button', class: 'rack-more', 'aria-expanded': String(open) }, label);
    button.addEventListener('click', () => { if (open) state.openGroups.delete(key); else state.openGroups.add(key); rack(); });
    return button;
  };
  return [make('span', { class: 'rack-group' }, name), ...shown.map(runTab),
    ...(hidden > 0 ? [toggle(folded ? `${hidden} unreadable` : `${hidden} older`)] : open && runs.length > keep ? [toggle('fewer')] : [])];
}

function rack() {
  const groups = new Map();
  for (const each of state.runs.filter((run) => run.state !== 'unreadable')) groups.set(each.sketch, [...groups.get(each.sketch) ?? [], each]);
  const unreadable = state.runs.filter((run) => run.state === 'unreadable');
  const nodes = [...[...groups].flatMap(([sketch, runs]) => rackGroup(sketch, runs, false)),
    ...(unreadable.length > 0 ? rackGroup('unreadable', unreadable, true) : [])];
  $('rack').replaceChildren(...(nodes.length ? nodes : [make('span', { class: 'about' }, 'No runs yet - run a sketch with understudy run.')]));
}

async function loadRuns() {
  const runs = await getJson('api/runs');
  if (!runs) return;
  state.runs = runs;
  rack();
  if (!state.chosen && state.runs.length > 0) choose(state.runs[0].id);
  else if (state.chosen && ['running', 'paused', 'stalled'].includes(state.chosenState)) {
    const run = await getJson(runUrl(state.chosen));
    if (run) drawStatus(run);
  }
}

$('looks-toggle').addEventListener('click', () => {
  const open = $('looks').classList.toggle('open');
  $('looks-toggle').setAttribute('aria-expanded', String(open));
});

state.theme = known(THEMES, query.get('theme'), remembered('theme'));
state.mode = known(MODES, query.get('mode'), remembered('mode'));
for (const button of document.querySelectorAll('.theme-choice')) button.addEventListener('click', () => { state.theme = button.dataset.theme; remember('theme', state.theme); look(); });
for (const button of document.querySelectorAll('.mode-choice')) button.addEventListener('click', () => { state.mode = button.dataset.mode; remember('mode', state.mode); look(); });
device.addEventListener('change', look);
look();
loadRuns();
setInterval(loadRuns, window.understudyPollMs ?? 5000); // a test may set understudyPollMs to wait less
