// Sprint 4 UND-14/15/16 (ARCH §3, §4, ADR-0015): the watch page. It reads
// a run's lines from the server (Server-Sent Events) and shows the sketch's
// statechart with the current state and the last transition marked, and a
// feed of Jev's decisions. The model (`apply`) and the text it shows are
// plain functions, tested in Node; the DOM part runs only in a browser.

import { turnGraph } from './turnGraph.mjs';
import { layout } from './layout.mjs';

const ANSWER_CHARS = 120;

/**
 * An empty run, before its start line.
 */
export function newModel() {
  return { sketch: null, plays: '', mode: 'live', drawing: null, current: null, taken: null, steps: [], ended: null, final: null, paused: null, lost: false, lastAt: null, isCut: false };
}

// ---- replay (UND-16) ----

/**
 * Where each replay frame ends in the log: one frame per line - the start,
 * each state change, each step - so stepping through a replay walks the
 * statechart as the run did. An `ended` line shares the final line's frame.
 * @param {object[]} history every line of the log, in order
 * @returns {number[]} the index of each frame's last line
 */
export function framesOf(history) {
  return history.keys().filter((index) => history[index].event !== 'ended' || index === history.length - 1).toArray();
}

/**
 * The frame that shows step `number` just made.
 */
export function frameOfStep(history, frames, number) {
  return frames.findIndex((end) => history[end].step === number && !history[end].event);
}

/**
 * The run as it was at the end of one frame. A log that stops without a
 * final line says so on its last frame.
 */
export function modelAt(history, frames, frame) {
  const model = newModel();
  model.mode = 'replay';
  const shown = history.slice(0, frames[frame] + 1);
  for (const line of shown) apply(model, line);
  model.isCut = frame === frames.length - 1 && history.every((line) => !line.final);
  return model;
}

/**
 * The app's answer to a move, as one short line.
 * @param {object|undefined} response
 * @returns {{ text: string, isBad: boolean }|null}
 */
export function answerOf(response) {
  if (!response) return null;
  if (typeof response.status === 'number') return { text: `status ${response.status}`, isBad: response.status >= 400 };
  if (response.call) {
    const [first = ''] = String(response.text ?? '').split('\n', 1);
    const text = first.length > ANSWER_CHARS ? `${first.slice(0, ANSWER_CHARS)}...` : first;
    return { text: response.isError ? `error: ${text}` : text, isBad: response.isError === true };
  }
  return null;
}

/**
 * One decision, as the feed shows it.
 */
export function decisionOf(line) {
  const confidence = typeof line.confidence === 'number' ? ` (${line.confidence})` : '';
  const chosen = line.response?.call?.arguments ?? {};
  return {
    step: line.step, phase: line.phase, options: line.options ?? [], move: line.move, picked: `${line.move}${confidence}`,
    retry: line.offList ? `first answered ${JSON.stringify(line.answer)} (not on offer), asked again` : null,
    args: Object.entries(chosen).map(([name, value]) => `${name}=${typeof value === 'string' ? value : JSON.stringify(value)}`).join(', '),
    answer: answerOf(line.response),
    decided: (line.decided ?? []).map((each) => decidedOf(each)),
  };
}

/**
 * The first three of a list, and "..." when there are more.
 */
function listed(items) {
  const more = items.length > 3 ? ', ...' : '';
  return items.slice(0, 3).join(', ') + more;
}

/**
 * One decided argument as the feed shows it (UND-22 AC5): the score
 * table, how many values the gates and zero scores removed (the first
 * few with why), and what is held back.
 */
export function decidedOf({ argument, table = null, removed = [], held = [] }) {
  const factors = table?.[0] ? Object.keys(table[0].factors) : [];
  return {
    argument,
    columns: ['value', ...factors, 'total'],
    rows: (table ?? []).map((each) => [String(each.value), ...factors.map((name) => String(each.factors[name])), String(each.total)]),
    removed: removed.length === 0 ? null : `removed ${removed.length}: ${listed(removed.map((each) => each.value + ' (' + each.why + ')'))}`,
    held: held.length === 0 ? null : 'held back: ' + held.map((each) => `${each.value} (no ${each.missing})`).join(', '),
  };
}

/**
 * How the run ended, in one line.
 */
export function endingOf(model) {
  if (model.isCut) return { text: 'log ends without a final line (the run was killed?)', isBad: true };
  if (model.final?.outcome === 'done') return { text: `done after ${model.final.steps} step${model.final.steps === 1 ? '' : 's'}`, isBad: false };
  if (!model.final) return null;
  const { outcome } = model.final;
  const message = model.ended?.message;
  // Some messages already start with their outcome (`stalled: ...`): say it once (DEF-12).
  if (!message) return { text: outcome, isBad: true };
  return { text: message.startsWith(`${outcome}:`) ? message : `${outcome}: ${message}`, isBad: true };
}

/**
 * The model after one line.
 * @param {ReturnType<typeof newModel>} model
 * @param {object} line
 */
export function apply(model, line) {
  model.lastAt = line.at ?? model.lastAt;
  const handle = EVENTS[line.event];
  if (handle) handle(model, line);
  else if (line.final) Object.assign(model, { final: line, paused: null });
  else if (typeof line.step === 'number') model.steps.push(decisionOf(line));
  return model;
}

const EVENTS = {
  hello: (model, line) => { model.mode = line.mode; },
  start: (model, line) => {
    Object.assign(model, { sketch: line.sketch, plays: line.plays, drawing: layout(turnGraph(line.turn)), current: line.turn.initial, taken: null });
  },
  state: (model, line) => Object.assign(model, { current: line.to, taken: line }),
  ended: (model, line) => { model.ended = line; },
  control: (model, line) => { model.paused = line.paused ? line : null; },
};

// ---- the DOM (browser only) ----

const SVG = 'http://www.w3.org/2000/svg';

function element(name, attributes = {}, text = null) {
  const node = name.startsWith('svg:') ? document.createElementNS(SVG, name.slice(4)) : document.createElement(name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text !== null) node.textContent = text;
  return node;
}

function drawDiagram(model) {
  const { drawing } = model;
  const svg = element('svg:svg', { viewBox: `0 0 ${drawing.width} ${drawing.height}`, width: drawing.width, height: drawing.height, role: 'img' });
  const marker = element('svg:marker', { id: 'arrow', viewBox: '0 0 10 10', refX: '10', refY: '5', markerWidth: '7', markerHeight: '7', orient: 'auto' });
  marker.append(element('svg:path', { d: 'M0,0L10,5L0,10z', fill: 'currentColor' }));
  const defs = element('svg:defs');
  defs.append(marker);
  svg.append(defs);
  const isTaken = (edge) => model.taken && edge.from === model.taken.from && edge.to === model.taken.to && edge.label === model.taken.on;
  const labels = [];
  for (const edge of drawing.edges) {
    const group = element('svg:g', { class: `edge${isTaken(edge) ? ' taken' : ''}` });
    group.append(element('svg:path', { d: edge.path, 'marker-end': 'url(#arrow)' }));
    svg.append(group);
    const label = element('svg:g', { class: `edge${isTaken(edge) ? ' taken' : ''}` });
    label.append(element('svg:text', { x: edge.labelX, y: edge.labelY, 'text-anchor': 'middle' }, edge.label));
    labels.push(label);
  }
  for (const node of drawing.nodes) {
    const group = element('svg:g', { class: ['node', node.final ? 'final' : '', node.id === model.current ? 'current' : ''].join(' ').trim() });
    group.append(element('svg:rect', { x: node.x, y: node.y, width: node.w, height: node.h, rx: 10 }));
    group.append(element('svg:text', { x: node.x + (node.w / 2), y: node.y + (node.tags.length > 0 ? 20 : 27), 'text-anchor': 'middle' }, node.id));
    if (node.tags.length > 0) group.append(element('svg:text', { class: 'tag', x: node.x + (node.w / 2), y: node.y + 35, 'text-anchor': 'middle' }, node.tags.join(' ')));
    svg.append(group);
  }
  svg.append(...labels);
  return svg;
}

function drawStep(decision) {
  const item = element('li', { 'data-step': decision.step });
  const head = element('div', { class: 'step-head' });
  head.append(element('b', {}, `step ${decision.step}`), element('span', {}, decision.phase ?? ''), element('span', {}, `-> ${decision.picked}`));
  const options = element('div', { class: 'options' }, 'offered: ');
  for (const [index, option] of decision.options.entries()) {
    if (index > 0) options.append(', ');
    options.append(element('span', option === decision.move ? { class: 'picked' } : {}, option));
  }
  item.append(head, options);
  if (decision.retry) item.append(element('div', { class: 'retry' }, decision.retry));
  if (decision.args) item.append(element('div', { class: 'args' }, `arguments: ${decision.args}`));
  // An argument with nothing ranked, removed or held (no rules) says nothing worth a line.
  for (const decided of decision.decided) {
    if (decided.rows.length > 0 || decided.removed || decided.held) item.append(drawDecided(decided));
  }
  if (decision.answer) item.append(element('div', { class: `answer${decision.answer.isBad ? ' bad' : ''}` }, `answer: ${decision.answer.text}`));
  return item;
}

function drawDecided(decided) {
  const box = element('div', { class: 'decided' }, decided.argument);
  if (decided.rows.length > 0) {
    const table = element('table', { class: 'scores' });
    const head = element('tr', {});
    head.append(...decided.columns.map((name) => element('th', {}, name)));
    table.append(head);
    for (const cells of decided.rows) {
      const row = element('tr', {});
      row.append(...cells.map((cell) => element('td', {}, cell)));
      table.append(row);
    }
    box.append(table);
  }
  if (decided.removed) box.append(element('div', { class: 'removed' }, decided.removed));
  if (decided.held) box.append(element('div', { class: 'held' }, decided.held));
  return box;
}

/**
 * Which of Pause / Step / Resume apply now (UND-15 AC1): Pause while a
 * live run is running, Step and Resume while it is paused, none once it
 * has ended (or in a replay, which has its own controls).
 */
export function controlsOf(model) {
  const isLive = model.mode === 'live' && model.sketch !== null && !model.final && !model.lost;
  return { pause: isLive && !model.paused, step: isLive && Boolean(model.paused), resume: isLive && Boolean(model.paused) };
}

function button(label, { isEnabled, action, onClick }) {
  const node = element('button', { type: 'button', 'data-action': action }, label);
  node.disabled = !isEnabled;
  node.addEventListener('click', onClick);
  return node;
}

/**
 * Replay's own controls: play / pause, step back, step forward.
 */
function drawReplayControls(replay) {
  const last = replay.frames.length - 1;
  return [
    button(replay.isPlaying ? 'Pause' : 'Play', { isEnabled: replay.frame < last || replay.isPlaying, action: 'play', onClick: replay.onPlay }),
    button('Step back', { isEnabled: replay.frame > 0, action: 'back', onClick: () => replay.onGo(replay.frame - 1) }),
    button('Step forward', { isEnabled: replay.frame < last, action: 'forward', onClick: () => replay.onGo(replay.frame + 1) }),
  ];
}

function drawControls(model, replay) {
  if (replay) return drawReplayControls(replay);
  const enabled = controlsOf(model);
  const buttons = [['pause', 'Pause', enabled.pause], ['step', 'Step', enabled.step], ['resume', 'Resume', enabled.resume]].map(([action, label, isEnabled]) => {
    const button = element('button', { type: 'button', 'data-action': action }, label);
    button.disabled = !isEnabled;
    button.addEventListener('click', () => {
      button.disabled = true;
      fetch('control', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action }) });
    });
    return button;
  });
  return model.mode === 'live' ? buttons : [];
}

function statusOf(model, replay) {
  if (model.lost) return { text: 'connection lost', className: 'lost' };
  const ending = endingOf(model);
  if (ending) return { text: ending.isBad ? `ended: ${model.final?.outcome ?? 'log cut short'}` : 'done', className: ending.isBad ? 'ended-bad' : 'ended' };
  if (model.paused) return { text: `paused before step ${model.paused.before_step}`, className: 'paused' };
  if (replay) return { text: `replay - step ${model.steps.length} of ${replay.steps.length}`, className: 'replay' };
  return { text: model.sketch ? 'running' : 'connecting...', className: 'running' };
}

/**
 * The feed: the steps so far; in a replay, every step, those still to come
 * faded, each one a way to jump there.
 */
function drawFeed(model, replay) {
  if (!replay) return model.steps.map((decision) => drawStep(decision));
  return replay.steps.map((decision) => {
    const item = drawStep(decision);
    if (decision.step > model.steps.length) item.classList.add('future');
    if (decision.step === model.steps.length) item.classList.add('here');
    item.title = `show the run at step ${decision.step}`;
    item.addEventListener('click', () => replay.onGo(replay.frameOfStep(decision.step)));
    return item;
  });
}

/**
 * Draws the whole page from the model (and, in a replay, where it is).
 */
export function render(model, replay = null) {
  document.querySelector('#sketch').textContent = model.sketch ?? 'understudy';
  document.querySelector('#plays').textContent = model.plays ? `playing ${model.plays}` : '';
  const status = statusOf(model, replay);
  const badge = document.querySelector('#status');
  badge.textContent = status.text;
  badge.className = `status ${status.className}`;
  document.querySelector('#controls').replaceChildren(...drawControls(model, replay));
  if (model.drawing) document.querySelector('#diagram').replaceChildren(drawDiagram(model));
  const list = document.querySelector('#steps');
  const isAtBottom = list.parentElement.scrollTop + list.parentElement.clientHeight >= list.parentElement.scrollHeight - 30;
  list.replaceChildren(...drawFeed(model, replay));
  if (isAtBottom && !replay) list.parentElement.scrollTop = list.parentElement.scrollHeight;
  const ending = endingOf(model);
  const end = document.querySelector('#ending');
  end.hidden = !ending;
  end.textContent = ending?.text ?? '';
  end.className = ending?.isBad ? 'bad' : '';
  document.title = `${status.text} - ${model.sketch ?? 'understudy'}`;
}

/**
 * A replay: every line arrived; show it frame by frame.
 */
function replayLog(history) {
  const frames = framesOf(history);
  const everything = modelAt(history, frames, frames.length - 1);
  const replay = {
    frames, frame: 0, steps: everything.steps, isPlaying: false, timer: null,
    frameOfStep: (number) => frameOfStep(history, frames, number),
  };
  const show = () => render(modelAt(history, frames, replay.frame), replay);
  const stop = () => {
    clearInterval(replay.timer);
    replay.isPlaying = false;
  };
  replay.onGo = (frame) => {
    stop();
    replay.frame = Math.max(0, Math.min(frames.length - 1, frame));
    show();
  };
  replay.onPlay = () => {
    if (replay.isPlaying) {
      stop();
      show();
      return;
    }
    if (replay.frame === frames.length - 1) replay.frame = 0;
    replay.isPlaying = true;
    replay.timer = setInterval(() => {
      replay.frame += 1;
      if (replay.frame === frames.length - 1) stop();
      show();
    }, 500);
    show();
  };
  show();
}

function follow() {
  const model = newModel();
  const history = [];
  let isQueued = false;
  const later = () => {
    if (isQueued) return;
    isQueued = true;
    globalThis.requestAnimationFrame(() => {
      isQueued = false;
      render(model);
    });
  };
  const source = new globalThis.EventSource('events');
  let isEnded = false;
  source.addEventListener('message', (message) => {
    const line = JSON.parse(message.data);
    // A replay keeps every line and shows them once all have arrived.
    if (model.mode === 'replay' && line.event !== 'hello') history.push(line);
    else apply(model, line);
    if (model.mode !== 'replay') later();
  });
  source.addEventListener('end', () => {
    isEnded = true;
    source.close();
    if (model.mode === 'replay') replayLog(history);
    else later();
  });
  source.addEventListener('error', () => {
    // No reconnect loop: the run is over, or the process has gone.
    source.close();
    if (!isEnded) model.lost = true;
    later();
  });
}

if (globalThis.document) follow();
