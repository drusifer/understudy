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
  $('gauges').replaceChildren(...run.gauges.map(gauge));
  $('tube-caption').textContent = `${run.sketch} · ${WORDS[run.state]} · ${run.mode}`;
  $('ended').textContent = run.ended;
  $('printer-state').textContent = run.state === 'running' ? 'PRINTING' : WORDS[run.state];
  $('status-lamp').className = `lamp ${LAMPS[run.state]}`;
  $('status-text').textContent = WORDS[run.state];
  drawBanner(run);
  drawSummary(run);
  state.chosenState = run.state;
}

// The stages the stage filter offers: each top-level stage and each group of nested stages.
function fillStageFilter(run) {
  const names = run.tube.flatMap((stage) => [stage.name, ...stage.groups.map((group) => group.name)]);
  $('find-stage').replaceChildren(make('option', { value: '' }, 'all stages'), ...names.map((name) => make('option', { value: name }, name)));
}

function draw(run) {
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
  state.follow?.close();
  state.chosen = id;
  rack();
  const run = await getJson(`api/runs/${id}`);
  if (!run) return;
  draw(run);
  if (run.state !== 'running') return;
  const source = new EventSource(`events/${id}`);
  state.follow = source;
  let skip = run.count;
  source.onmessage = (message) => { if (skip > 0) skip -= 1; else append(JSON.parse(message.data)); };
  source.addEventListener('end', async () => { source.close(); const done = await getJson(`api/runs/${id}`); if (done) drawStatus(done); loadRuns(); });
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
