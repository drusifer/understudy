// The controls: pick a sketch, fill in what it takes, press Play (live or from a captured run), or stop the chosen run.
// What may be started, and by whom, is decided by the server (src/dashboard/runs.py, server.py); this script only asks and
// shows the answer. It shares page.js's helpers ($, make, state, getJson, choose, loadRuns).
'use strict';

const controls = { enabled: false, holdable: false, authorized: false, sketches: [], watching: null };
const SECRET_KEY = 'understudy.secret';
const GATE_LOCKED = 'locked: you can watch, but not start, replay or stop';
const GATE_LOCKED_HOLD = 'locked: you can watch, but not pause, step or resume';

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
  $('play').title = controls.authorized ? (sketch?.ok ? 'Run this play' : 'this file cannot be read as a play') : 'needs the access secret';
  $('play-held').disabled = !playable;
  $('play-held').title = controls.authorized ? (sketch?.ok ? 'Start this play held before its first beat, then STEP through it'
    : 'this file cannot be read as a play') : 'needs the access secret';
  const running = ['running', 'stalled', 'paused'].includes(state.chosenState);
  $('stop').disabled = !(controls.authorized && running);
  $('stop').title = controls.authorized ? (running ? 'Stop the run on screen' : 'the run on screen is not going') : 'needs the access secret';
  drawHoldButtons();
  $('gate-note').textContent = controls.authorized ? 'unlocked for this tab: Jev level names are shown too'
    : (controls.enabled ? GATE_LOCKED : GATE_LOCKED_HOLD);
}

// Pause holds a run that is going before its next beat; Step and Resume work on a run that is held.
function drawHoldButtons() {
  const goes = state.chosenState === 'running';
  const held = state.chosenState === 'paused';
  const reason = (ok, why) => (controls.authorized ? (ok ? why : 'the run on screen is not in a state that allows this') : 'needs the access secret');
  $('pause').disabled = !(controls.authorized && goes);
  $('pause').title = reason(goes, 'Hold the run before its next beat (the beat in flight finishes first)');
  $('step').disabled = !(controls.authorized && held);
  $('step').title = reason(held, 'Let one beat run, then hold again');
  $('resume').disabled = !(controls.authorized && held);
  $('resume').title = reason(held, 'Run on without holding');
}

const HOLD_SAID = {
  pause: 'pausing: the beat now running finishes first, then the run holds',
  step: 'one beat will run, then the run holds again',
  resume: 'running on',
};

async function hold(action) {
  if (!state.chosen) return;
  const { status, body } = await post(`api/${action}`, { run: state.chosen });
  say(status === 200 ? HOLD_SAID[action] : body.problem ?? `could not ${action} (${status})`, status === 200 ? 'ok' : 'problem');
  const run = await getJson(`api/runs/${state.chosen}`);
  if (run) drawStatus(run);
}

// A number as the sketch will read it: no more places than its step has, and no trailing zeros (0.30 is 0.3, 1.00 is 1).
function numberText(value, step) {
  const places = (String(step).split('.')[1] ?? '').length;
  const text = Number(value).toFixed(places);
  return text.includes('.') ? text.replace(/0+$/, '').replace(/\.$/, '') : text;
}

// Each control keeps the text the run will receive in data-value, so Play reads one place for every kind.
function markInput(element, spec, value) {
  element.dataset.input = '';
  element.dataset.name = spec.name;
  element.dataset.value = value;
  return element;
}

// choice: a dial of the options, one selected; arrow keys move it and stop at the ends.
function dialControl(spec, id) {
  const options = spec.options.map(String);
  const group = markInput(make('div', { id, role: 'radiogroup', 'aria-labelledby': `${id}-label`, class: 'pick-group' }), spec, String(spec.default));
  const buttons = options.map((option) => make('button', { type: 'button', role: 'radio', class: 'pick-option' }, option));
  const select = (index, focus) => {
    buttons.forEach((button, at) => {
      button.setAttribute('aria-checked', String(at === index));
      button.tabIndex = at === index ? 0 : -1;
    });
    group.dataset.value = options[index];
    if (focus) buttons[index].focus();
  };
  buttons.forEach((button, at) => {
    button.addEventListener('click', () => select(at, false));
    button.addEventListener('keydown', (event) => {
      const moves = { ArrowRight: at + 1, ArrowDown: at + 1, ArrowLeft: at - 1, ArrowUp: at - 1, Home: 0, End: options.length - 1 };
      if (!(event.key in moves)) return;
      event.preventDefault();
      select(Math.min(options.length - 1, Math.max(0, moves[event.key])), true);
    });
  });
  select(Math.max(0, options.indexOf(String(spec.default))), false);
  group.append(...buttons);
  return group;
}

// range: a fader between its limits with its value beside it.
function faderControl(spec, id) {
  const fader = markInput(make('input', { id, type: 'range', class: 'slide', min: spec.min, max: spec.max, step: spec.step, value: spec.default }),
    spec, numberText(spec.default, spec.step));
  const readout = make('output', { id: `${id}-readout`, for: id, class: 'readout' }, fader.dataset.value);
  fader.addEventListener('input', () => {
    fader.dataset.value = numberText(fader.value, spec.step);
    readout.textContent = fader.dataset.value;
  });
  return make('div', { class: 'slide-row' }, fader, readout);
}

// count: a whole number with a button either side; typed past a limit it is put back inside.
function stepperControl(spec, id) {
  const box = markInput(make('input', { id, type: 'number', class: 'find-field count-box', min: spec.min, max: spec.max, step: 1, value: spec.default }),
    spec, String(spec.default));
  const less = make('button', { type: 'button', class: 'find-button step-button', 'aria-label': `decrease ${spec.label}` }, '-');
  const more = make('button', { type: 'button', class: 'find-button step-button', 'aria-label': `increase ${spec.label}` }, '+');
  const settle = () => {
    const value = Math.min(spec.max, Math.max(spec.min, Math.round(Number(box.value) || spec.min)));
    box.value = String(value);
    box.dataset.value = String(value);
    less.disabled = value <= spec.min;
    more.disabled = value >= spec.max;
  };
  less.addEventListener('click', () => { box.value = String(Number(box.value) - 1); settle(); });
  more.addEventListener('click', () => { box.value = String(Number(box.value) + 1); settle(); });
  box.addEventListener('change', settle);
  box.addEventListener('input', () => { if (box.value !== '' && Number(box.value) >= spec.min && Number(box.value) <= spec.max) settle(); });
  settle();
  return make('div', { class: 'count-stepper' }, less, box, more);
}

// switch: on or off.
function switchControl(spec, id) {
  const button = markInput(make('button', { id, type: 'button', role: 'switch', class: 'toggle', 'aria-labelledby': `${id}-label` }), spec, spec.default);
  const show = (on) => {
    button.setAttribute('aria-checked', String(on));
    button.dataset.value = on ? 'on' : 'off';
    button.textContent = on ? 'ON' : 'OFF';
  };
  button.addEventListener('click', () => show(button.dataset.value !== 'on'));
  show(spec.default === 'on');
  return button;
}

const CONTROLS = { choice: dialControl, range: faderControl, count: stepperControl, switch: switchControl };

function typedField(spec) {
  const id = `field-${spec.name}`;
  const control = CONTROLS[spec.kind](spec, id);
  const label = make('label', { id: `${id}-label`, class: 'typed-label', ...(['range', 'count'].includes(spec.kind) ? { for: id } : {}) }, spec.label);
  return make('div', { class: 'start-field' }, label, control);
}

function drawFields() {
  const sketch = currentSketch();
  $('sketch-about').textContent = sketch ? (sketch.ok ? sketch.description : `cannot be read as a play: ${sketch.problem}`) : '';
  $('fields').replaceChildren(
    ...(sketch?.inputs ?? []).map(typedField),
    ...(sketch?.with ?? []).map((name) => make('div', { class: 'start-field' },
      make('label', { for: `field-${name}`, class: 'typed-label' }, name),
      make('input', { id: `field-${name}`, type: 'text', class: 'find-field', 'data-name': name, autocomplete: 'off' }))));
  drawButtons();
  drawPlan(sketch);
}

// The picked play's plan: its pieces and beats and who reads what, before any run exists. A beat of the flow can be clicked
// to hold the next run before it; click it again to clear.
async function drawPlan(sketch) {
  $('plan').hidden = !sketch?.ok;
  if (!sketch?.ok) return;
  const plan = await getJson(`api/plan?play=${encodeURIComponent(sketch.file)}`);
  if (currentSketch()?.file !== sketch.file) return; // the pick changed while this was on its way
  if (controls.planFile !== sketch.file) controls.holdAt = null;
  controls.planFile = sketch.file;
  controls.plan = plan?.nodes ? plan : null;
  controls.planProblem = plan?.nodes ? '' : (plan?.problem ?? 'no plan could be read for this play');
  paintPlan();
}

function pickBeat(node) {
  controls.holdAt = controls.holdAt === node.id ? null : node.id;
  paintPlan();
  // the diagram was drawn again, so keyboard focus goes back to the beat that was chosen
  $('plan-wrap').querySelector(`[data-state="${CSS.escape(node.id)}"]`)?.focus();
}

function paintPlan() {
  const plan = controls.plan;
  drawDiagram($('plan-wrap'), plan, { pick: pickBeat, picked: controls.holdAt, mode: 'hold', can: (node) => node.kind === 'beat' && node.flow && !node.final });
  $('plan-note').textContent = !plan ? controls.planProblem
    : controls.holdAt ? `the next run will hold before ${controls.holdAt}; click it again to clear`
    : plan.nodes.length === 0 ? 'this play has no stage pieces and no beats'
    : `${plan.nodes.length} ${plan.nodes.length === 1 ? 'node' : 'nodes'}: pieces are rounded, beats are boxes, a dashed box waits until it is read; click a beat of the flow to hold a run before it`;
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
  controls.holdable = Boolean(session.holdable);
  controls.authorized = session.authorized;
  $('controls').hidden = !(controls.enabled || controls.holdable);
  for (const each of document.querySelectorAll('[data-launcher]')) each.hidden = !controls.enabled;
  for (const each of document.querySelectorAll('[data-hold]')) each.hidden = !controls.holdable;
  if (!controls.enabled) {
    $('controls').querySelector('summary').textContent = 'HOLD THIS RUN';
    $('gate-note').textContent = GATE_LOCKED_HOLD;
    return;
  }
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

// `held` starts the play held before its first beat; otherwise a beat picked on the plan holds the run before it.
async function play(held = false) {
  const values = {};
  for (const typed of document.querySelectorAll('#fields [data-input]')) values[typed.dataset.name] = typed.dataset.value;
  for (const input of document.querySelectorAll('#fields input[type="text"]')) if (input.value.trim()) values[input.dataset.name] = input.value.trim();
  const replay = $('replay-pick').value;
  $('play').disabled = true;
  $('play-held').disabled = true;
  say('checking the play and starting it...');
  const holding = held ? { hold: true } : controls.holdAt ? { hold_at: controls.holdAt } : {};
  const { status, body } = await post('api/start', { sketch: $('sketch-pick').value, with: values, ...(replay ? { replay } : {}), ...holding });
  drawButtons();
  if (status === 200) {
    controls.holdAt = null;
    paintPlan();
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
  if (controls.watching === run.id && !['running', 'paused'].includes(run.state)) {
    say(`run ended: ${run.ended || run.state}`, run.state === 'failed' ? 'problem' : 'ok');
    controls.watching = null;
  }
}

$('sketch-pick').addEventListener('change', drawFields);
$('unlock').addEventListener('click', unlock);
$('secret-box').addEventListener('keydown', (event) => { if (event.key === 'Enter') unlock(); });
$('play').addEventListener('click', () => play(false));
$('play-held').addEventListener('click', () => play(true));
$('stop').addEventListener('click', stop);
for (const action of ['pause', 'step', 'resume']) $(action).addEventListener('click', () => hold(action));
loadControls();
