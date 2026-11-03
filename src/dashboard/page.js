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

const state = { runs: [], chosen: null, chosenState: null, follow: null, openGroups: new Set(), theme: 'steampunk', mode: 'auto' };
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
  return make('div', { class: `line ${each.tone ?? ''}`, 'data-index': String(index) }, each.text);
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

const WORDS = { running: 'RUNNING', done: 'DONE', failed: 'FAILED', stopped: 'STOPPED', stalled: 'STALLED', unreadable: 'NO DETAILS' };
const LAMPS = { running: 'on-air', done: 'done', failed: 'failed', stopped: 'standby', stalled: 'stalled', unreadable: 'dark' };

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

function stateGroup(node) {
  const name = svgEl('text', { class: 'state-name', x: node.x + node.w / 2, y: node.y + node.h / 2 + 5, 'text-anchor': 'middle' });
  name.textContent = node.id;
  const label = `${node.id}${node.final ? ', final state' : ''}${node.current ? ', current state' : ''}`;
  const box = svgEl('rect', { class: 'state-box', x: node.x, y: node.y, width: node.w, height: node.h, rx: 6 });
  const ring = node.final ? [svgEl('rect', { class: 'final-ring', x: node.x + 4, y: node.y + 4, width: node.w - 8, height: node.h - 8, rx: 4 })] : [];
  const group = svgEl('g', { class: `state${node.final ? ' final' : ''}${node.current ? ' current' : ''}${node.initial ? ' initial' : ''}`,
    role: 'img', 'aria-label': label, 'data-state': node.id }, box, ...ring, name);
  return group;
}

function edgeGroup(edge) {
  const line = svgEl('polyline', { class: `edge${edge.back ? ' back' : ''}${edge.taken ? ' taken' : ''}`, points: edge.points.map((point) => point.join(',')).join(' '),
    'marker-end': `url(#${edge.taken ? 'arrow-taken' : 'arrow'})`, 'data-from': edge.from, 'data-to': edge.to });
  if (!edge.label) return [line];
  const box = edge.label_box;
  const text = svgEl('text', { class: 'edge-label-text', x: box.x + 5, y: box.y + box.h - 5 });
  text.textContent = edge.label;
  return [line, svgEl('rect', { class: 'edge-label-box', x: box.x, y: box.y, width: box.w, height: box.h, rx: 3 }), text];
}

// The machine as boxes and arrows from the server's layout (src/dashboard/chart.py); the page only draws it.
function drawChart(run) {
  const chart = run.chart;
  const wrap = $('chart-wrap');
  wrap.hidden = !chart;
  if (!chart) {
    wrap.replaceChildren();
    $('chart-note').textContent = 'this run\'s log has no story, so there is no diagram to draw';
    return;
  }
  const current = chart.nodes.find((node) => node.current);
  $('chart-note').textContent = chart.ended ? `ended${current ? ` in ${current.id}` : ''}: ${chart.ended}`
    : current ? `in state ${current.id}` : 'waiting for the first state';
  wrap.replaceChildren(svgEl('svg', { class: 'chart-svg', width: chart.width, height: chart.height, viewBox: `0 0 ${chart.width} ${chart.height}`, 'aria-hidden': 'false' },
    svgEl('defs', {}, arrowMarker('arrow', 'arrowhead'), arrowMarker('arrow-taken', 'arrowhead taken')),
    ...chart.edges.flatMap(edgeGroup), ...chart.nodes.map(stateGroup)));
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

// One top-level stage: its lamp, and under it each group of nested stages (open or closed as the reader left it).
function stageBlock(stage) {
  const block = make('div', { class: 'stage-block' }, make('div', { class: `stage-lamp ${stage.state}` }, make('i'), stage.name));
  for (const group of stage.groups) {
    const key = `${stage.name}/${group.name}`;
    const progress = group.seen > 0 ? `${group.done} of ${group.seen} done` : group.state;
    const details = make('details', { class: `group ${group.state}` },
      make('summary', {}, `${group.name} · ${progress}${group.seen > 0 && group.state === 'running' ? ' · running' : ''}`),
      ...group.stages.map((child) => make('div', { class: 'group-stage' }, `${child.name} · ${child.completed} of ${child.started} done`)));
    details.open = state.openGroups.has(key);
    details.addEventListener('toggle', () => { if (details.open) state.openGroups.add(key); else state.openGroups.delete(key); });
    block.append(details);
  }
  return block;
}

// Everything but the printer's lines, so it can be refreshed while a run goes without losing the reader's place.
function drawStatus(run) {
  $('tube').replaceChildren(...run.tube.map(stageBlock));
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
  if (jev.hidden) {
    notes.push(make('div', { class: 'about' }, `${jev.hidden} of these reads have level names from your own data, shown as "option N"; `
      + 'unlock with the access secret (START A RUN panel above) to see the names'));
  }
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
  const run = await getJson(`api/runs/${id}`);
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

// A fetch that says so when the server cannot be reached, and recovers by itself on the next one that works.
// The access secret lives in this tab only (sessionStorage), and goes out only in a header, never in an address.
function secretHeaders() {
  try {
    const secret = sessionStorage.getItem('understudy.secret');
    return secret ? { 'X-Understudy-Secret': secret } : {};
  } catch { return {}; }
}

async function getJson(url) {
  try {
    const value = await (await fetch(url, { headers: secretHeaders() })).json();
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
  state.follow?.close();
  state.chosen = id;
  rack();
  const run = await getJson(`api/runs/${id}`);
  if (!run) return;
  draw(run);
  loadJev(id);
  if (run.state !== 'running') return;
  const source = new EventSource(`events/${id}`);
  state.follow = source;
  let skip = run.count;
  source.onmessage = (message) => { if (skip > 0) skip -= 1; else { append(JSON.parse(message.data)); refreshSoon(id); } };
  source.addEventListener('end', async () => { source.close(); const done = await getJson(`api/runs/${id}`); if (done) drawStatus(done); loadJev(id); loadRuns(); });
}

// A new event line while a run goes: refresh what the run says about itself (the lit state, the gauges) soon, but once for a burst.
let refreshTimer = null;
function refreshSoon(id) {
  if (refreshTimer) return;
  refreshTimer = setTimeout(async () => {
    refreshTimer = null;
    const run = await getJson(`api/runs/${id}`);
    if (run && state.chosen === id) drawStatus(run);
  }, 250);
}

// run-20261031T012507-46140191 reads "10-31 01:25".
function stamp(id) {
  const [, month, day, hour, minute] = /^run-\d{4}(\d\d)(\d\d)T(\d\d)(\d\d)/.exec(id) ?? [];
  return month ? `${month}-${day} ${hour}:${minute}` : id;
}

const BADGES = { running: 'RUNNING', failed: 'FAILED', stalled: 'STALLED', stopped: 'STOPPED' };

// The rack: runs grouped by sketch (the runs arrive newest first, so each group and each tab inside it is newest first),
// each tab carrying a badge in words for a run that is going, failed, stalled or stopped.
function rack() {
  const groups = new Map();
  for (const each of state.runs) groups.set(each.sketch, [...groups.get(each.sketch) ?? [], each]);
  const nodes = [...groups].flatMap(([sketch, runs]) => [
    make('span', { class: 'rack-group' }, sketch),
    ...runs.map((each) => {
      const label = make('span', { class: 'name' }, stamp(each.id));
      const tab = make('button', { type: 'button', role: 'tab', class: `sketch-tab ${each.state}`, 'aria-selected': String(each.id === state.chosen), title: `${each.id} · ${each.state}` }, label);
      if (BADGES[each.state]) tab.append(make('span', { class: 'badge' }, BADGES[each.state]));
      tab.addEventListener('click', () => choose(each.id));
      return tab;
    }),
  ]);
  $('rack').replaceChildren(...(nodes.length ? nodes : [make('span', { class: 'about' }, 'No runs yet - run a sketch with understudy run.')]));
}

async function loadRuns() {
  const runs = await getJson('api/runs');
  if (!runs) return;
  state.runs = runs;
  rack();
  if (!state.chosen && state.runs.length > 0) choose(state.runs[0].id);
  else if (state.chosen && ['running', 'stalled'].includes(state.chosenState)) {
    const run = await getJson(`api/runs/${state.chosen}`);
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
setInterval(loadRuns, 5000);
