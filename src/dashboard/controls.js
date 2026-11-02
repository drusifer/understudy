// The controls: pick a sketch, fill in what it takes, press Play (live or from a captured run), or stop the chosen run.
// What may be started, and by whom, is decided by the server (src/dashboard/runs.py, server.py); this script only asks and
// shows the answer. It shares page.js's helpers ($, make, state, getJson, choose, loadRuns).
'use strict';

const controls = { enabled: false, authorized: false, sketches: [], watching: null };
const SECRET_KEY = 'understudy.secret';
const GATE_LOCKED = 'locked: you can watch, but not start, replay or stop';

function say(text, kind = '') {
  const box = $('start-message');
  box.textContent = text;
  box.className = `start-message ${kind}`;
}

async function post(path, body) {
  try {
    const response = await fetch(path, { method: 'POST', headers: { ...secretHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    setOffline(false);
    return { status: response.status, body: await response.json() };
  } catch {
    setOffline(true);
    return { status: 0, body: { problem: 'the console could not be reached' } };
  }
}

function currentSketch() {
  return controls.sketches.find((each) => each.file === $('sketch-pick').value);
}

// Play and Stop say why they are off, so the next step is clear.
function drawButtons() {
  const sketch = currentSketch();
  const playable = controls.authorized && sketch?.ok;
  $('play').disabled = !playable;
  $('play').title = controls.authorized ? (sketch?.ok ? 'Run this sketch' : 'this file cannot be read as a sketch') : 'needs the access secret';
  const running = ['running', 'stalled'].includes(state.chosenState);
  $('stop').disabled = !(controls.authorized && running);
  $('stop').title = controls.authorized ? (running ? 'Stop the run on screen' : 'the run on screen is not going') : 'needs the access secret';
  $('gate-note').textContent = controls.authorized ? 'unlocked for this tab: Jev level names are shown too' : GATE_LOCKED;
}

function drawFields() {
  const sketch = currentSketch();
  $('sketch-about').textContent = sketch ? (sketch.ok ? sketch.description : `cannot be read as a sketch: ${sketch.problem}`) : '';
  $('fields').replaceChildren(...(sketch?.with ?? []).map((name) => make('div', { class: 'start-field' },
    make('label', { for: `field-${name}` }, name),
    make('input', { id: `field-${name}`, type: 'text', class: 'find-field', 'data-name': name, autocomplete: 'off' }))));
  drawButtons();
}

function drawSketches() {
  $('sketch-pick').replaceChildren(...controls.sketches.map((each) => {
    const option = make('option', { value: each.file }, each.ok ? `${each.name} (${each.file})` : `${each.file} - unreadable`);
    if (!each.ok) option.title = each.problem;
    return option;
  }));
  const first = controls.sketches.find((each) => each.ok) ?? controls.sketches[0];
  if (first) $('sketch-pick').value = first.file;
  drawFields();
}

async function loadControls() {
  const session = await getJson('api/session');
  if (!session) return;
  controls.enabled = session.controls;
  controls.authorized = session.authorized;
  $('controls').hidden = !controls.enabled;
  if (!controls.enabled) return;
  controls.sketches = (await getJson('api/sketches')) ?? [];
  const replays = (await getJson('api/replays')) ?? [];
  $('replay-pick').replaceChildren(make('option', { value: '' }, 'no - run live'), ...replays.map((id) => make('option', { value: id }, id)));
  drawSketches();
}

async function unlock() {
  const value = $('secret-box').value.trim();
  if (!value) return;
  try { sessionStorage.setItem(SECRET_KEY, value); } catch { /* a tab that cannot keep it has to type it again */ }
  $('secret-box').value = '';
  const session = await getJson('api/session');
  controls.authorized = Boolean(session?.authorized);
  if (!controls.authorized) {
    try { sessionStorage.removeItem(SECRET_KEY); } catch { /* nothing kept */ }
    say('that is not this console\'s access secret (it changes every time the console starts)', 'problem');
  } else {
    say('unlocked for this tab', 'ok');
    if (state.chosen) loadJev(state.chosen);
  }
  drawButtons();
}

async function play() {
  const values = {};
  for (const input of document.querySelectorAll('#fields input')) if (input.value.trim()) values[input.dataset.name] = input.value.trim();
  const replay = $('replay-pick').value;
  $('play').disabled = true;
  say('checking the sketch and starting it...');
  const { status, body } = await post('api/start', { sketch: $('sketch-pick').value, with: values, ...(replay ? { replay } : {}) });
  drawButtons();
  if (status === 200) {
    controls.watching = body.run;
    say(body.run ? `started ${body.run}` : 'started; it will appear in the rack in a moment', 'ok');
    await loadRuns();
    if (body.run) choose(body.run);
    return;
  }
  say(body.problem ?? `could not start (${status})`, 'problem');
  const existing = /run-[0-9A-Za-z-]+/.exec(body.problem ?? '');
  if (status === 409 && existing) {
    const open = make('button', { type: 'button', class: 'find-button' }, 'OPEN THAT RUN');
    open.addEventListener('click', () => choose(existing[0]));
    $('start-message').append(' ', open);
  }
}

async function stop() {
  if (!state.chosen) return;
  const { status, body } = await post('api/stop', { run: state.chosen });
  say(status === 200 ? `stopped ${state.chosen}` : body.problem ?? `could not stop (${status})`, status === 200 ? 'ok' : 'problem');
  const run = await getJson(`api/runs/${state.chosen}`);
  if (run) drawStatus(run);
}

// The chosen run changed or finished: Stop follows it, and a run this panel started says how it ended.
function afterStatus(run) {
  drawButtons();
  if (controls.watching === run.id && !['running'].includes(run.state)) {
    say(`run ended: ${run.ended || run.state}`, run.state === 'failed' ? 'problem' : 'ok');
    controls.watching = null;
  }
}

$('sketch-pick').addEventListener('change', drawFields);
$('unlock').addEventListener('click', unlock);
$('secret-box').addEventListener('keydown', (event) => { if (event.key === 'Enter') unlock(); });
$('play').addEventListener('click', play);
$('stop').addEventListener('click', stop);
loadControls();
