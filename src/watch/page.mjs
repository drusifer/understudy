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
  return { sketch: null, plays: '', mode: 'live', drawing: null, current: null, taken: null, steps: [], ended: null, final: null, paused: null, lost: false, lastAt: null };
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
  };
}

/**
 * How the run ended, in one line.
 */
export function endingOf(model) {
  if (model.final?.outcome === 'done') return { text: `done after ${model.final.steps} step${model.final.steps === 1 ? '' : 's'}`, isBad: false };
  if (model.final) return { text: model.ended?.message ? `${model.final.outcome}: ${model.ended.message}` : model.final.outcome, isBad: true };
  return null;
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
  if (decision.answer) item.append(element('div', { class: `answer${decision.answer.isBad ? ' bad' : ''}` }, `answer: ${decision.answer.text}`));
  return item;
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

function drawControls(model) {
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

function statusOf(model) {
  if (model.lost) return { text: 'connection lost', className: 'lost' };
  const ending = endingOf(model);
  if (ending) return { text: ending.isBad ? `ended: ${model.final.outcome}` : 'done', className: ending.isBad ? 'ended-bad' : 'ended' };
  if (model.paused) return { text: `paused before step ${model.paused.before_step}`, className: 'paused' };
  if (model.mode === 'replay') return { text: 'replay', className: 'replay' };
  return { text: model.sketch ? 'running' : 'connecting...', className: 'running' };
}

/**
 * Draws the whole page from the model.
 */
export function render(model) {
  document.querySelector('#sketch').textContent = model.sketch ?? 'understudy';
  document.querySelector('#plays').textContent = model.plays ? `playing ${model.plays}` : '';
  const status = statusOf(model);
  const badge = document.querySelector('#status');
  badge.textContent = status.text;
  badge.className = `status ${status.className}`;
  document.querySelector('#controls').replaceChildren(...drawControls(model));
  if (model.drawing) document.querySelector('#diagram').replaceChildren(drawDiagram(model));
  const list = document.querySelector('#steps');
  const isAtBottom = list.parentElement.scrollTop + list.parentElement.clientHeight >= list.parentElement.scrollHeight - 30;
  list.replaceChildren(...model.steps.map((decision) => drawStep(decision)));
  if (isAtBottom) list.parentElement.scrollTop = list.parentElement.scrollHeight;
  const ending = endingOf(model);
  const end = document.querySelector('#ending');
  end.hidden = !ending;
  end.textContent = ending?.text ?? '';
  end.className = ending?.isBad ? 'bad' : '';
  document.title = `${status.text} - ${model.sketch ?? 'understudy'}`;
}

function follow() {
  const model = newModel();
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
    apply(model, JSON.parse(message.data));
    later();
  });
  source.addEventListener('end', () => {
    isEnded = true;
    source.close();
    later();
  });
  source.addEventListener('error', () => {
    // No reconnect loop: the run is over, or the process has gone.
    source.close();
    if (!isEnded) model.lost = true;
    later();
  });
}

if (globalThis.document) follow();
