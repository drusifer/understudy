// Sprint 6 (ARCH §3, docs/design/DASHBOARD.md): the operations console in
// the browser. The pure helpers at the top (colours, readouts, dial geometry,
// the printer's lines) run in Node too, for tests; the DOM wiring below them
// runs only in a page.

import { ringOf, SIZE } from './tube.mjs';

// The themes (UND-36): steampunk is the console as first designed.
export const THEMES = ['steampunk', 'professional', 'starship'];

/**
 * The theme to show: a known `?theme=` wins, then the remembered one, else steampunk.
 */
export function themeOf(query, stored) {
  return [query, stored].find((name) => THEMES.includes(name)) ?? THEMES[0];
}

// Light or dark (UND-38): auto follows the device.
export const MODES = ['auto', 'light', 'dark'];

/**
 * The mode chosen: a known `?mode=` wins, then the remembered one, else auto.
 */
export function modeChoiceOf(query, stored) {
  return [query, stored].find((name) => MODES.includes(name)) ?? MODES[0];
}

/**
 * The mode shown: the one chosen, or with auto the device's.
 */
export function modeOf(choice, isDeviceDark) {
  if (choice !== 'auto') return choice;
  return isDeviceDark ? 'dark' : 'light';
}

/**
 * A `#rrggbb` colour as [r, g, b]; grey for anything else.
 */
export function rgbOf(hex) {
  const match = /^#([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(hex.trim());
  return match ? match.slice(1).map((part) => Number.parseInt(part, 16)) : [128, 128, 128];
}

/**
 * The weight a weight input gives its factors, 0 to 3, whatever its range
 * (as inputs.weightsOf, which the run uses) - the tube's glows and widths
 * are sized for this.
 */
export const levelOf = (value, [low, high]) => (3 * (value - low)) / (high - low);

export const rgb = (colour) => `rgb(${colour.map((part) => Math.round(part)).join(',')})`;

/**
 * The weights' colours mixed in the ratio of their values; grey when all are 0.
 * @param {{ value: number, colour: number[] }[]} weights
 */
export function blendOf(weights) {
  const total = weights.reduce((sum, each) => sum + each.value, 0);
  if (total === 0) return [90, 90, 90];
  return [0, 1, 2].map((part) => weights.reduce((sum, each) => sum + each.colour[part] * each.value, 0) / total);
}

/**
 * A fader's readout: OFF at 0, 11 at the top of its range, else two places.
 */
export function readoutOf(value, [, high]) {
  if (value === 0) return 'OFF';
  if (value >= high) return '11';
  return value.toFixed(2);
}

// A score as the printer shows it: a perfect 1.0 is 11 (owner).
export const scoreText = (value) => (value === 1 ? '11' : String(value));

// UND-42: the gauges' readings, gathered from the run's own lines - every
// needle and bar shows something real (owner).
export const FRESH_METERS = { steps: 0, limit: null, firstMoveMs: null, stallMs: null, confidence: null, shortlist: null, asked: 0, reused: 0, lastMoveAt: null, startedAt: null };

const sumOf = (list, read) => list.reduce((sum, each) => sum + read(each), 0);

/**
 * The readings after one more line of the run, seen at `now` (ms).
 */
export function metersAfter(meters, line, now) {
  if (line.event === 'start') {
    return { ...FRESH_METERS, limit: line.limits?.steps ?? null, firstMoveMs: line.limits?.first_move_ms ?? null, stallMs: line.limits?.stall_ms ?? null, startedAt: now };
  }
  if (line.step === undefined) return meters;
  const decided = line.decided ?? [];
  const left = sumOf(decided, (each) => each.table?.length ?? 0);
  const of = left + sumOf(decided, (each) => each.removed?.length ?? 0) + sumOf(decided, (each) => each.held?.length ?? 0);
  return {
    ...meters,
    steps: line.step,
    confidence: typeof line.confidence === 'number' ? line.confidence : meters.confidence,
    // A step whose decided value needed no shortlist keeps the last real one (owner: it read 0/0).
    shortlist: of > 0 ? { left, of } : meters.shortlist,
    asked: meters.asked + sumOf(decided, (each) => each.jev?.asked ?? 0),
    reused: meters.reused + sumOf(decided, (each) => each.jev?.reused ?? 0),
    lastMoveAt: now,
  };
}

const share = (part, whole) => (whole > 0 ? Math.min(1, Math.max(0, part / whole)) : 0);

/**
 * The five gauges at `now`: each a level from 0 to 1 and what it reads.
 * @returns {{ name: string, level: number, text: string, about: string }[]}
 */
export function gaugesOf(meters, now) {
  const { steps, limit, confidence, shortlist, asked, reused } = meters;
  const since = meters.lastMoveAt ?? meters.startedAt;
  const idle = since === null ? 0 : now - since;
  const idleLimit = meters.lastMoveAt === null ? meters.firstMoveMs : meters.stallMs;
  return [
    { name: 'STEPS', level: share(steps, limit), text: limit === null ? '-' : `${steps}/${limit}`, about: 'steps taken of the step limit' },
    { name: 'SURE', level: confidence ?? 0, text: confidence === null ? '-' : confidence.toFixed(2), about: "how sure Jev was of its last choice" },
    { name: 'SHORTLIST', level: shortlist ? share(shortlist.left, shortlist.of) : 0, text: shortlist ? `${shortlist.left}/${shortlist.of}` : '-', about: 'values still on the shortlist of those considered' },
    { name: 'JEV', level: share(asked, asked + reused), text: `${asked}·${reused}`, about: 'Jev scores asked · reused' },
    { name: 'IDLE', level: share(idle, idleLimit), text: since === null ? '-' : `${(idle / 1000).toFixed(1)}s`, about: 'time since the last move, of the idle limit' },
  ];
}

// An input's value as `--input` text: a switch as on/off.
function wordOf(value) {
  if (typeof value !== 'boolean') return String(value);
  return value ? 'on' : 'off';
}

const shown = (value) => (typeof value === 'string' ? value : JSON.stringify(value));

// The first two of a list, then "..." when there are more.
function firstTwo(items) {
  const more = items.length > 2 ? ', ...' : '';
  return items.slice(0, 2).join(', ') + more;
}

/**
 * Where a dial's options sit: spread over 150°, as angles from straight up.
 */
export function dialAngles(count) {
  if (count <= 1) return [0];
  return Array.from({ length: count }, (_, index) => -75 + (150 * index) / (count - 1));
}

/**
 * Starting values for a sketch's controls: each input's default.
 */
export function startingValues(inputs) {
  return Object.fromEntries(inputs.map((input) => [input.name, input.default]));
}

/**
 * What the printer prints for one line of the run, or null for nothing.
 * @returns {{ text: string, tone?: string, table?: object }[]|null}
 */
export function printed(line) {
  if (line.event === 'start') {
    const inputs = Object.entries(line.inputs ?? {}).map(([name, value]) => `${name}=${wordOf(value)}`).join('  ');
    return [{ text: `=== UNDERSTUDY RUN LOG ===  ${line.sketch}`, tone: 'bold' }, ...(inputs ? [{ text: `inputs  ${inputs}` }] : [])];
  }
  if (line.event === 'dashboard' && line.stderr?.startsWith('holding back')) return [{ text: `  hold  ${line.stderr.slice('holding back '.length)}`, tone: 'held' }];
  if (line.event === 'dashboard' && line.refused) return [{ text: `!! could not start: ${line.refused}`, tone: 'bold' }];
  if (line.event === 'walked-away') return [{ text: '*** WALKED AWAY - nothing qualified ***', tone: 'bold' }];
  if (line.step !== undefined) return stepLines(line);
  if (line.final) return [{ text: `=== ${line.outcome.toUpperCase()} after ${line.steps} step${line.steps === 1 ? '' : 's'} ===`, tone: 'bold' }];
  return null;
}

function stepLines(line) {
  const call = line.response?.call;
  const given = call ? Object.entries(call.arguments ?? {}).map(([name, value]) => `${name}=${shown(value)}`).join(' ') : '';
  const confidence = typeof line.confidence === 'number' ? `  (${line.confidence.toFixed(2)})` : '';
  const lines = [{ text: `step ${line.step}  ${line.move.replace('tool:', '')}  ${given}${confidence}`.trimEnd() }];
  const decisions = line.decided ?? [];
  for (const decided of decisions) {
    if (decided.jev?.asked > 0) lines.push({ text: `  jev   scored ${decided.jev.asked} for ${decided.argument}`, tone: 'jev' });
    const removals = decided.removed.map((each) => each.value + ' (' + each.why + ')');
    if (removals.length > 0) lines.push({ text: `  rules removed ${removals.length}: ${firstTwo(removals)}`, tone: 'note' });
    if (decided.table?.length > 0) lines.push({ table: decided });
  }
  if (line.response?.text?.startsWith('Ticket issued')) lines.push({ text: `*** ${line.response.text} ***`, tone: 'bold' });
  return lines;
}

// Where a dial's option or tick sits, `radius` out from its centre.
function placeOnDial(degrees, radius) {
  return [125 + radius * Math.sin((degrees * Math.PI) / 180), 125 - radius * Math.cos((degrees * Math.PI) / 180)];
}

// What a factor a fader drives does, in a few words.
function factorAbout(factor) {
  if (factor.ask) return `Jev asks "${factor.question}" about the ${factor.looks_at}`;
  const placing = factor.range ? 'from ' + factor.range[0] + ' to ' + factor.range[1] : 'order ' + factor.order.join(', ');
  return `${factor.field} ${placing}`;
}

// A range end as typed: an HH:MM time stays text, anything else is a number.
function asNumber(text) {
  return /^\d\d?:\d\d$/.test(text.trim()) ? text.trim() : Number(text);
}

function panelButton(text, isEnabled, act) {
  const button = element('button', { type: 'button', class: 'panel-button' }, text);
  button.disabled = !isEnabled;
  button.addEventListener('click', act);
  return button;
}

// The edit boxes for one factor a fader drives.
function factorFields(factor) {
  const at = ['decide', factor.argument, 'scores', factor.field];
  if (factor.ask) return [{ label: 'QUESTION', value: factor.question, width: 140, path: [...at, 'ask'] }, { label: 'LOOKS AT', value: factor.looks_at, width: 140, path: ['questions', factor.question, 'looks_at'] }];
  if (factor.order) return [{ label: 'ORDER, BEST FIRST', value: factor.order.join(', '), width: 170, path: [...at, 'order'], parse: (text) => text.split(',').map((each) => each.trim()).filter(Boolean) }];
  return [
    { label: 'FROM', value: factor.range[0], width: 90, path: [...at, 'range'], parse: (text) => [asNumber(text), factor.range[1]] },
    { label: 'TO', value: factor.range[1], width: 90, path: [...at, 'range'], parse: (text) => [factor.range[0], asNumber(text)] },
  ];
}

function factorYaml(factor) {
  if (factor.ask) return `${factor.field}: { ask: ${factor.question}, weight: ${factor.weight} }   looks_at: ${factor.looks_at}`;
  const placing = factor.order ? `order: [${factor.order.join(', ')}]` : `range: [${factor.range.join(', ')}]`;
  return `${factor.field}: { ${placing}, weight: ${factor.weight} }`;
}

function lampClassOf(on, running) {
  if (!on) return 'lamp dark';
  return running ? 'lamp on-air' : 'lamp standby';
}

function statusTextOf(on, running) {
  if (!on) return 'DARK';
  return running ? 'ON AIR' : 'STANDING BY';
}

// What READY's hint says: what the buttons will do now (UND-39 AC4).
function readyHintOf(running, paused) {
  if (!running) return 'PLAY to run, STEP for one move';
  return paused ? 'STEP for the next move, RESUME to run on' : 'press to stop the run';
}

// ---------------------------------------------------------------- page --

const $ = (id) => document.querySelector(`#${id}`);

function element(tag, attributes = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    // Custom properties (--colour) need setProperty; Object.assign drops them.
    if (name === 'style') for (const [property, setting] of Object.entries(value)) node.style.setProperty(property.replaceAll(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`), setting);
    else node.setAttribute(name, value);
  }
  for (const child of children) node.append(child);
  return node;
}

const SVG = 'http://www.w3.org/2000/svg';

function svgElement(tag, attributes = {}) {
  const node = document.createElementNS(SVG, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, String(value));
  return node;
}

// A label over the tube, placed in its 600 x 600 drawing's units.
function label(x, y, text, { class: extra = '', ...look }) {
  const style = { left: `${(x / SIZE) * 100}%`, top: `${(y / SIZE) * 100}%` };
  return element('div', { class: `label ${extra}`.trim(), style: { ...style, ...look } }, text);
}

/**
 * The theme's colours for what the script draws, from the page's CSS custom
 * properties (UND-36): each theme's stylesheet sets them.
 */
function themeLook() {
  const style = globalThis.getComputedStyle(document.documentElement);
  const value = (name) => style.getPropertyValue(`--${name}`).trim();
  return {
    glows: value('tube-glows') !== 'off',
    weights: [1, 2, 3, 4, 5, 6].map((index) => rgbOf(value(`weight-${index}`))),
    track: value('tube-track'), edge: value('tube-edge'), edgeLive: value('tube-edge-live'), edgeTone: value('tube-edge-tone'),
    state: value('tube-state'), stateNow: value('tube-state-now'), stateEdge: value('tube-state-edge'), stateEdgeNow: value('tube-state-edge-now'),
    stateTone: value('tube-state-tone'), stateToneNow: value('tube-state-tone-now'), stateGlow: value('tube-state-glow'),
    shadow: value('tube-shadow'), orbTitle: value('tube-orb-title'),
  };
}

function tubeAria(layout, current) {
  const edges = layout.edges.map((edge) => `${edge.from} -${edge.label}${edge.sub ? ' (' + edge.sub + ')' : ''}-> ${edge.to}`).join('; ');
  return `Statechart: ${edges}. Now: ${current ?? 'not running'}.`;
}

// ------------------------------------------------------------ the tube --

function drawRing(svg, weights, look) {
  const arcs = ringOf(weights.map((each) => ({ ...each, colour: rgb(each.colour) })));
  return arcs.map((arc, index) => {
    const glow = look.glows ? `filter: drop-shadow(0 0 ${2 + levelOf(arc.value, weights[index].range) * 3}px ${arc.colour})` : '';
    svg.append(svgElement('path', { d: arc.track, fill: 'none', stroke: look.track, 'stroke-width': 9, 'stroke-linecap': 'round' }),
      svgElement('path', { d: arc.fill, fill: 'none', stroke: arc.colour, 'stroke-width': 6, 'stroke-linecap': 'round', 'stroke-dasharray': '10 5', class: arc.value > 0 ? 'flowing' : 'faint', style: glow }));
    const text = `${arc.name.toUpperCase()} ${readoutOf(arc.value, weights[index].range)}`;
    return label(arc.lx, arc.ly, text, { color: arc.colour, fontSize: 'clamp(11px,2.4vw,17px)', textShadow: look.glows ? `0 0 6px ${arc.colour}` : 'none' });
  });
}

// How one edge is drawn: the decision edge carries the blend; the one just taken glows.
function edgeLook(edge, power, isLive, look) {
  const isPowered = edge.isDecision && power.weights.length > 0;
  const glow = (colour, size) => (look.glows ? `filter: drop-shadow(0 0 ${size}px ${colour})` : '');
  if (isPowered) return { colour: power.blend, width: 3 + power.level * 1.6, tone: power.blend, glow: glow(power.blend, 3 + power.level * 2.5) };
  if (isLive) return { colour: look.edgeLive, width: 4, tone: look.edgeTone, glow: glow(look.edgeLive, 6) };
  return { colour: look.edge, width: 2.5, tone: look.edgeTone, glow: '' };
}

// UND-41: an arrowhead at the end of a polyline, pointing along its last leg.
function arrowhead(points, size = 8) {
  const [[x1, y1], [x2, y2]] = points.slice(-2);
  const length = Math.hypot(x2 - x1, y2 - y1) || 1;
  const [ux, uy] = [(x2 - x1) / length, (y2 - y1) / length];
  const [bx, by] = [x2 - ux * size, y2 - uy * size];
  return `M ${x2} ${y2} L ${bx - uy * size * 0.55} ${by + ux * size * 0.55} L ${bx + uy * size * 0.55} ${by - ux * size * 0.55} Z`;
}

function flowText(x, y, text, attributes) {
  const node = svgElement('text', { x, y, 'text-anchor': 'middle', ...attributes });
  node.textContent = text;
  return node;
}

// Each transition: an orthogonal arrow, its event and guard written beside it.
function drawEdges(svg, labels, edges, power, { isRunning, liveEdge }, theme) {
  for (const edge of edges) {
    if (edge.points.length < 2) continue;
    const isLive = isRunning && edge.index === liveEdge;
    const look = edgeLook(edge, power, isLive, theme);
    const isFlowing = isRunning && (isLive || edge.isDecision);
    const d = edge.points.map(([x, y], index) => `${index === 0 ? 'M' : 'L'} ${x} ${y}`).join(' ');
    svg.append(svgElement('path', { d, fill: 'none', stroke: look.colour, 'stroke-width': Math.min(look.width, 8), 'stroke-linejoin': 'round', 'stroke-dasharray': isFlowing ? '7 5' : 'none', class: isFlowing ? 'flowing' : 'still', style: look.glow }),
      svgElement('path', { d: arrowhead(edge.points), fill: look.colour, style: look.glow }));
    const halo = { 'paint-order': 'stroke', stroke: theme.shadow, 'stroke-width': 4, 'stroke-linejoin': 'round' };
    labels.append(flowText(edge.lx, edge.ly + 12, edge.label, { class: 'edge-label', fill: look.tone, ...halo }));
    if (edge.sub) labels.append(flowText(edge.lx, edge.ly + 26, edge.sub, { class: 'edge-sub', fill: look.tone, ...halo }));
  }
}

// Each state: a rounded box; the initial one has a dot and an arrow into it, a final one a double border.
function drawStates(svg, labels, nodes, current, look) {
  for (const node of nodes) {
    const isNow = node.id === current;
    const stroke = isNow ? look.stateEdgeNow : look.stateEdge;
    const box = { x: node.x, y: node.y, width: node.width, height: node.height, rx: node.height / 2 };
    svg.append(svgElement('rect', { ...box, fill: isNow ? look.stateNow : look.state, stroke, 'stroke-width': 2.5, class: isNow ? 'now' : '' }));
    if (node.final) svg.append(svgElement('rect', { x: node.x + 4, y: node.y + 4, width: node.width - 8, height: node.height - 8, rx: (node.height - 8) / 2, fill: 'none', stroke, 'stroke-width': 1.5 }));
    if (node.initial) {
      const cx = node.x + node.width / 2;
      svg.append(svgElement('circle', { cx, cy: node.y - 14, r: 5, fill: stroke }), svgElement('path', { d: `M ${cx} ${node.y - 9} L ${cx} ${node.y - 2}`, stroke, 'stroke-width': 2 }));
    }
    const tone = isNow ? look.stateToneNow : look.stateTone;
    labels.append(flowText(node.x + node.width / 2, node.y + node.height / 2 + 5, node.name, { class: 'state-label', fill: tone }));
  }
}

// The weights' shares, as one bar under the screen (was the orb, UND-30 AC3).
function drawPower({ weights, total }, look) {
  if (weights.length === 0) return [];
  const parts = weights.map((weight) => {
    const share = total === 0 ? 0 : Math.round((weight.value / total) * 100);
    return { name: weight.name, share, colour: rgb(weight.colour) };
  });
  const said = parts.map((part) => part.name + ' ' + part.share + '%').join(', ');
  const bar = element('div', { class: 'power-bar', role: 'img', 'aria-label': `Decision power: ${said}` },
    ...parts.map((part) => element('span', { class: 'power-part', style: { flexGrow: String(Math.max(part.share, 0.5)), background: part.colour, boxShadow: look.glows ? `0 0 8px ${part.colour}` : 'none' } })));
  const legend = element('div', { class: 'power-legend', 'aria-hidden': 'true' },
    ...parts.map((part) => element('span', { style: { color: part.colour } }, `${part.name} ${part.share}%`)));
  return [element('div', { class: 'power-title' }, 'DECISION POWER'), bar, legend];
}

async function api(path, body) {
  const response = await fetch(`api/${path}`, body === undefined ? {} : { method: 'POST', body: JSON.stringify(body) });
  let value = {};
  try {
    value = await response.json();
  } catch { /* an empty answer */ }
  return { ok: response.ok, status: response.status, value };
}

/**
 * The console's state, and what draws it.
 */
function boot() {
  const state = { rack: [], sketch: null, values: {}, running: false, paused: false, on: true, current: null, liveEdge: null, open: new Set(), look: null, meters: FRESH_METERS };

  // UND-42: five gauges, built once; each theme shows them its own way -
  // a backlit needle meter, a moving bar cluster, or a plain card.
  const gauges = gaugesOf(FRESH_METERS, Date.now()).map((gauge) => {
    const ticks = Array.from({ length: 11 }, (_, index) => {
      const angle = ((-60 + index * 12) * Math.PI) / 180;
      const [inner, outer] = index % 5 === 0 ? [36, 46] : [40, 46];
      return svgElement('line', { x1: 50 + inner * Math.sin(angle), y1: 56 - inner * Math.cos(angle), x2: 50 + outer * Math.sin(angle), y2: 56 - outer * Math.cos(angle), class: 'tick' });
    });
    const dial = svgElement('svg', { viewBox: '0 0 100 62', class: 'dial', 'aria-hidden': 'true' });
    dial.append(svgElement('path', { d: 'M 10 56 A 46 46 0 0 1 90 56', class: 'arc', fill: 'none' }), ...ticks,
      svgElement('line', { x1: 50, y1: 56, x2: 50, y2: 14, class: 'needle' }), svgElement('circle', { cx: 50, cy: 56, r: 4, class: 'hub' }));
    const bars = element('div', { class: 'bars', 'aria-hidden': 'true' }, ...Array.from({ length: 7 }, (_, index) => element('i', { style: { '--n': String(index) } })));
    const track = element('div', { class: 'track', 'aria-hidden': 'true' }, element('div', { class: 'fill' }));
    const figure = element('div', { class: 'figure' });
    const node = element('div', { class: 'gauge', role: 'meter', 'aria-valuemin': '0', 'aria-valuemax': '1', 'aria-label': gauge.about, title: gauge.about },
      dial, bars, track, figure, element('div', { class: 'gauge-name' }, gauge.name));
    return { node, figure };
  });
  $('gauges').replaceChildren(...gauges.map((each) => each.node));
  function drawGauges() {
    for (const [index, gauge] of gaugesOf(state.meters, Date.now()).entries()) {
      const { node, figure } = gauges[index];
      node.style.setProperty('--level', String(gauge.level));
      node.setAttribute('aria-valuenow', String(gauge.level));
      node.setAttribute('aria-valuetext', `${gauge.name.toLowerCase()} ${gauge.text}`);
      figure.textContent = gauge.text;
    }
  }
  drawGauges();
  // The idle gauge moves between lines.
  setInterval(() => {
    if (state.running) drawGauges();
  }, 500);

  // UND-36, UND-38: the theme and the mode - a known ?theme= / ?mode= wins,
  // then the one this browser remembers; auto mode follows the device.
  function remembered(key) {
    try {
      return globalThis.localStorage.getItem(`understudy-${key}`);
    } catch {
      return null;
    }
  }
  function remember(key, value) {
    try {
      globalThis.localStorage.setItem(`understudy-${key}`, value);
    } catch { /* not remembered: a blocked store */ }
  }
  const query = new URLSearchParams(globalThis.location.search);
  const device = globalThis.matchMedia('(prefers-color-scheme: dark)');
  const look = { theme: themeOf(query.get('theme'), remembered('theme')), mode: modeChoiceOf(query.get('mode'), remembered('mode')) };
  function useLook() {
    const root = document.documentElement;
    root.dataset.theme = look.theme;
    root.dataset.mode = modeOf(look.mode, device.matches);
    state.look = themeLook();
    for (const button of document.querySelectorAll('.theme-choice')) button.setAttribute('aria-pressed', String(button.dataset.theme === look.theme));
    for (const button of document.querySelectorAll('.mode-choice')) button.setAttribute('aria-pressed', String(button.dataset.mode === look.mode));
    if (!state.sketch) return;
    drawControls();
    drawTube();
  }
  useLook();
  device.addEventListener('change', useLook);
  for (const button of document.querySelectorAll('.theme-choice')) {
    button.addEventListener('click', () => {
      look.theme = button.dataset.theme;
      remember('theme', look.theme);
      useLook();
    });
  }
  for (const button of document.querySelectorAll('.mode-choice')) {
    button.addEventListener('click', () => {
      look.mode = button.dataset.mode;
      remember('mode', look.mode);
      useLook();
    });
  }

  function drawRack() {
    const rack = $('rack');
    rack.setAttribute('role', 'tablist');
    rack.replaceChildren(...state.rack.map((entry) => {
      const tab = element('button', { type: 'button', role: 'tab', class: 'sketch-tab', 'aria-selected': String(entry.name === state.sketch?.name), title: entry.ok ? entry.description : entry.problem },
        element('span', { class: 'name' }, entry.name));
      if (!entry.ok) {
        tab.disabled = true;
        tab.title = entry.problem;
      }
      tab.addEventListener('click', () => choose(entry.name));
      return tab;
    }));
  }

  function drawDial(input) {
    const dial = element('div', { class: 'dial', role: 'group', 'aria-label': input.name });
    dial.append(element('div', { class: 'dial-well', 'aria-hidden': 'true' }));
    const angles = dialAngles(input.options.length);
    const pointer = element('div', { class: 'dial-pointer', 'aria-hidden': 'true' }, element('div', { class: 'body' }), element('div', { class: 'line' }), element('div', { class: 'cap' }));
    const update = () => {
      const index = Math.max(0, input.options.indexOf(state.values[input.name]));
      pointer.style.transform = `rotate(${angles[index]}deg)`;
      for (const [each, node] of options.entries()) node.setAttribute('aria-pressed', String(each === index));
      for (const [each, node] of ticks.entries()) node.classList.toggle('on', each === index);
    };
    const ticks = angles.map((degrees) => {
      const [x, y] = placeOnDial(degrees, 62);
      return element('div', { class: 'dial-tick', 'aria-hidden': 'true', style: { left: `${x - 4}px`, top: `${y - 4}px` } });
    });
    const options = input.options.map((option, index) => {
      const [x, y] = placeOnDial(angles[index], 100);
      const button = element('button', { type: 'button', class: 'dial-option', style: { left: `${x - 44}px`, top: `${y - 22}px` } }, option);
      button.addEventListener('click', () => {
        state.values[input.name] = option;
        update();
      });
      return button;
    });
    dial.append(...ticks, pointer, ...options);
    update();
    return element('div', { class: 'dial-block' }, element('div', { class: 'plate-label' }, input.name.toUpperCase()), dial, moodPanel(input));
  }

  function drawFader(input, index) {
    const colour = rgb(state.look.weights[index % state.look.weights.length]);
    const [low, high] = input.range;
    const id = `fader-${input.name}`;
    const fader = element('input', { id, class: 'fader', type: 'range', min: String(low), max: String(high), step: '0.05', value: String(state.values[input.name]), 'aria-orientation': 'vertical' });
    const slot = element('div', { class: 'slot', style: { '--colour': colour } }, element('div', { class: 'ticks', 'aria-hidden': 'true' }), element('div', { class: 'glow', 'aria-hidden': 'true' }), fader);
    const nixie = element('div', { class: 'nixie', style: { '--colour': colour } });
    const chip = element('span', { class: 'chip', style: { '--colour': colour }, 'aria-hidden': 'true' });
    const update = () => {
      const value = Number(fader.value);
      state.values[input.name] = value;
      nixie.textContent = readoutOf(value, input.range);
      fader.setAttribute('aria-valuetext', value === 0 ? 'off' : value.toFixed(2));
      // The slot's glow, the LED and the readout all shine as brightly as the fader is set (owner).
      for (const lit of [slot, chip, nixie]) lit.style.setProperty('--fill', String((value - low) / (high - low)));
      drawTube();
    };
    fader.addEventListener('input', update);
    const label = element('label', { for: id }, chip, input.name);
    const about = input.factors.map((factor) => factorAbout(factor)).join(' · ');
    update();
    const fields = [...input.factors.flatMap((factor) => factorFields(factor)), { label: 'DEFAULT', value: input.default, width: 90, path: ['inputs', input.name, 'default'], parse: Number }];
    const yaml = [...input.factors.map((factor) => factorYaml(factor)), `inputs.${input.name}: { weight: [${input.range.join(', ')}], default: ${input.default} }`].join(' · ');
    const panel = accessPanel(`fader-${input.name}`, `${input.name}: ${about || 'not used by any factor'}`, fields, yaml, [], '▸');
    // The channel strip holds the fader; its drawer opens under all the channels.
    return { channel: element('div', { class: 'channel', title: about }, nixie, slot, label, panel.toggle), drawer: panel.drawer };
  }

  function drawSwitch(input) {
    const isOn = () => state.values[input.name] === true;
    const button = element('button', { type: 'button', class: 'switch', 'aria-pressed': String(isOn()) },
      element('span', { class: 'socket', 'aria-hidden': 'true' }, element('span', { class: 'led' })),
      element('span', {}, element('span', { class: 'label' }, input.name), element('span', { class: 'state' })));
    const update = () => {
      button.setAttribute('aria-pressed', String(isOn()));
      button.querySelector('.state').textContent = isOn() ? 'ON' : 'OFF';
    };
    button.addEventListener('click', () => {
      state.values[input.name] = !isOn();
      update();
    });
    update();
    return button;
  }

  // UND-34: a whole-number input is a brass stepper - − and + round a Nixie.
  function drawStepper(input) {
    const [low, high] = input.range;
    const nixie = element('div', { class: 'nixie stepper-nixie', role: 'status', 'aria-live': 'polite' });
    const down = element('button', { type: 'button', class: 'step', 'aria-label': `${input.name} down` }, '−');
    const up = element('button', { type: 'button', class: 'step', 'aria-label': `${input.name} up` }, '+');
    const update = () => {
      const value = state.values[input.name];
      nixie.textContent = String(value);
      nixie.setAttribute('aria-label', `${input.name} ${value}`);
      down.disabled = value <= low;
      up.disabled = value >= high;
    };
    const by = (change) => () => {
      state.values[input.name] = Math.min(high, Math.max(low, state.values[input.name] + change));
      update();
    };
    down.addEventListener('click', by(-1));
    up.addEventListener('click', by(1));
    update();
    return element('div', { class: 'stepper', role: 'group', 'aria-label': input.name },
      element('div', { class: 'plate-label' }, input.name.toUpperCase()), element('div', { class: 'stepper-body' }, down, nixie, up),
      element('div', { class: 'about' }, `${low} to ${high}`));
  }

  function drawControls() {
    const { sketch } = state;
    $('sketch-title').textContent = sketch.name;
    $('sketch-about').textContent = (sketch.description || '').trim();
    $('sketch-about').title = (sketch.description || '').trim();
    const weights = sketch.inputs.filter((input) => input.kind === 'weight');
    $('dials').replaceChildren(...sketch.inputs.filter((input) => input.kind === 'choose').map((input) => drawDial(input)));
    const strips = weights.map((input, index) => drawFader(input, index));
    $('faders').replaceChildren(...(strips.length > 0 ? [element('div', { class: 'fader-scale', 'aria-hidden': 'true' }, element('span', {}, '▲ MORE'), element('span', {}, 'IMPORTANT'), element('span', {}, '▼ LESS'))] : []),
      ...strips.map((strip) => strip.channel));
    $('fader-drawers').replaceChildren(...strips.map((strip) => strip.drawer));
    $('switches').replaceChildren(...sketch.inputs.filter((input) => input.kind === 'count').map((input) => drawStepper(input)),
      ...sketch.inputs.filter((input) => input.kind === 'switch').map((input) => drawSwitch(input)));
    $('nothing-to-tune').hidden = sketch.inputs.length > 0;
  }

  // UND-30: the statechart in the tube, the weights' ring and their blend.
  function drawTube() {
    const { sketch } = state;
    const going = state.paused ? 'paused' : 'running';
    $('tube-caption').textContent = state.running ? `${going} · ${state.current ?? ''}` : 'idle';
    if (!sketch) return;
    const look = state.look;
    const weights = sketch.inputs.filter((input) => input.kind === 'weight').map((input, index) => ({
      name: input.name, value: state.values[input.name], range: input.range, colour: look.weights[index % look.weights.length],
    }));
    const power = {
      weights, total: weights.reduce((sum, each) => sum + each.value, 0),
      level: weights.reduce((sum, each) => sum + levelOf(each.value, each.range), 0), blend: rgb(blendOf(weights)),
    };
    // The power ring round the rim (the steampunk tube; other screens hide it).
    const ring = svgElement('svg', { viewBox: `0 0 ${SIZE} ${SIZE}`, class: 'ring', 'aria-hidden': 'true' });
    const ringLabels = drawRing(ring, weights, look);
    // UND-41: the statechart as a layered flow, laid out on the server.
    const { flow } = sketch;
    const svg = svgElement('svg', { viewBox: `0 0 ${flow.width} ${flow.height}`, class: 'flow', role: 'img', 'aria-label': tubeAria(flow, state.current) });
    const labels = svgElement('g', { class: 'labels' });
    drawEdges(svg, labels, flow.edges, power, { isRunning: state.running, liveEdge: state.liveEdge }, look);
    drawStates(svg, labels, flow.nodes, state.current, look);
    svg.append(labels);
    $('tube').replaceChildren(ring, element('div', { class: 'ring-labels', 'aria-hidden': 'true' }, ...ringLabels), svg);
    $('decision-power').replaceChildren(...drawPower(power, look));
  }

  // UND-32: a ▸ button that slides down a panel of edit boxes; each box saves on change.
  function accessPanel(id, title, fields, yaml, extra = [], short = null) {
    const drawerId = `drawer-${id}`;
    const isOpen = state.open.has(id);
    const toggle = element('button', { type: 'button', class: short ? 'access compact' : 'access', 'aria-expanded': String(isOpen), 'aria-controls': drawerId, ...(short && { 'aria-label': `Settings for ${title}` }) },
      element('span', { class: 'caret', 'aria-hidden': 'true' }, '▸'), short ? '' : title);
    const problem = element('div', { class: 'problem', role: 'status' });
    const boxes = fields.map((field) => {
      const box = element('input', { type: 'text', value: String(field.value ?? ''), style: { width: `${field.width}px` } });
      box.addEventListener('change', async () => {
        const saved = await save([{ path: field.path, value: field.parse ? field.parse(box.value) : box.value }]);
        box.setAttribute('aria-invalid', String(!saved.ok));
        problem.textContent = saved.ok ? '' : saved.value.problem;
      });
      return element('label', { class: 'field' }, field.label, box);
    });
    const drawer = element('div', { id: drawerId, class: 'drawer' }, ...boxes, ...extra, element('div', { class: 'yaml' }, yaml),
      element('div', { class: 'hint' }, 'Saved to the sketch as you change it. Power the console off and on for its defaults.'), problem);
    drawer.hidden = !isOpen;
    if (short) drawer.prepend(element('div', { class: 'drawer-title' }, title));
    toggle.addEventListener('click', () => {
      if (state.open.has(id)) state.open.delete(id);
      else state.open.add(id);
      drawer.hidden = !state.open.has(id);
      toggle.setAttribute('aria-expanded', String(state.open.has(id)));
    });
    return { toggle, drawer, block: element('div', { class: 'access-block' }, toggle, drawer) };
  }

  function moodPanel(input) {
    const at = ['inputs', input.name];
    const fields = input.options.map((option, index) => ({ label: String(index + 1), value: option, width: 150, path: [...at, 'choose'], parse: (text) => input.options.map((each, other) => (other === index ? text : each)) }));
    // Renaming the default renames it as the default too: one edit, both changes.
    for (const field of fields) {
      const { parse } = field;
      field.parse = (text) => parse(text);
      field.extra = (text) => (input.options[Number(field.label) - 1] === input.default ? [{ path: [...at, 'default'], value: text }] : []);
    }
    const panel = accessPanel(`mood-${input.name}`, `${input.options.length} ${input.name}s · default ${input.default}`, [], `${input.name}: { choose: [${input.options.join(', ')}], default: ${input.default} }`, [
      ...fields.map((field) => moodBox(field)),
      element('div', { class: 'row' }, panelButton('+ ADD', input.options.length < 6, () => save([{ path: [...at, 'choose'], value: [...input.options, `${input.name} ${input.options.length + 1}`] }])),
        panelButton('− REMOVE LAST', input.options.length > 2, () => save([{ path: [...at, 'choose'], value: input.options.slice(0, -1) }, ...(input.options.at(-1) === input.default ? [{ path: [...at, 'default'], value: input.options[0] }] : [])]))),
      moodBox({ label: 'DEFAULT', value: input.default, width: 150, path: [...at, 'default'] }),
    ]);
    return panel.block;
  }

  function moodBox(field) {
    const box = element('input', { type: 'text', value: String(field.value), style: { width: `${field.width}px` } });
    box.addEventListener('change', async () => {
      const value = field.parse ? field.parse(box.value) : box.value;
      const saved = await save([{ path: field.path, value }, ...(field.extra ? field.extra(box.value) : [])]);
      box.setAttribute('aria-invalid', String(!saved.ok));
      box.title = saved.ok ? '' : saved.value.problem;
    });
    return element('label', { class: 'field' }, field.label, box);
  }

  // Saves an edit, then redraws from the saved sketch (keeping the controls' values).
  async function save(changes) {
    const saved = await api('edit', { sketch: state.sketch.name, changes });
    if (saved.ok) {
      await redraw();
      await loadBay();
    } else {
      print({ event: 'dashboard', refused: saved.value.problem });
    }
    return saved;
  }

  // Redraws from the sketch as saved, keeping the controls' values that still fit.
  async function redraw() {
    const { ok, value } = await api(`sketch/${encodeURIComponent(state.sketch.name)}`);
    if (!ok) return;
    const kept = state.values;
    state.sketch = value;
    state.values = { ...startingValues(value.inputs), ...Object.fromEntries(Object.entries(kept).filter(([name, current]) => value.inputs.find((input) => input.name === name)?.options?.includes?.(current) ?? true)) };
    if (value.graph.nodes.every((node) => node.id !== state.current)) state.current = value.graph.initial;
    state.liveEdge = null;
    drawControls();
    drawTube();
    const rack = await api('sketches');
    if (rack.ok) {
      state.rack = rack.value;
      drawRack();
    }
  }

  // UND-35: the bay behind the printer - the sketch's whole file, saved a
  // moment after typing stops, one write at a time; the textarea is never
  // redrawn by its own saves, so the caret and undo stay.
  const bay = { text: $('bay-text'), timer: null, pending: null, queue: Promise.resolve() };

  async function loadBay() {
    if ($('bay').hidden || !state.sketch) return;
    const { ok, value } = await api(`text/${encodeURIComponent(state.sketch.name)}`);
    if (!ok) return;
    bay.text.value = value.text;
    bay.text.setAttribute('aria-invalid', 'false');
    $('bay-problem').textContent = '';
  }

  async function writeBay({ sketch, text }) {
    const written = await api('write', { sketch, text });
    if (sketch !== state.sketch?.name) return;
    bay.text.setAttribute('aria-invalid', String(!written.ok));
    $('bay-problem').textContent = written.ok ? '' : written.value.problem;
    if (written.ok) await redraw();
  }

  // Sends the waiting write now (before Play, or leaving the sketch).
  function flushBay() {
    clearTimeout(bay.timer);
    if (bay.pending) {
      const pending = bay.pending;
      bay.pending = null;
      bay.queue = (async (previous) => {
        await previous;
        await writeBay(pending);
      })(bay.queue);
    }
    return bay.queue;
  }

  bay.text.addEventListener('input', () => {
    clearTimeout(bay.timer);
    bay.pending = { sketch: state.sketch.name, text: bay.text.value };
    bay.timer = setTimeout(flushBay, 500);
  });

  function showBay(isOpen) {
    $('printer').hidden = isOpen;
    $('bay').hidden = !isOpen;
    (isOpen ? bay.text : $('open-printer')).focus();
  }
  $('open-printer').addEventListener('click', async () => {
    showBay(true);
    await loadBay();
  });
  $('refit-printer').addEventListener('click', async () => {
    await flushBay();
    showBay(false);
  });

  function drawStatus() {
    const { running, on } = state;
    $('status-lamp').className = lampClassOf(on, running);
    $('status-text').textContent = statusTextOf(on, running);
    const lamp = $('ready-lamp');
    lamp.className = 'ready-lamp';
    lamp.classList.toggle('running', running);
    lamp.classList.toggle('off', !on || !state.sketch);
    lamp.setAttribute('aria-label', running ? 'Running' : 'Ready');
    $('ready-text').textContent = running ? 'RUNNING' : 'READY';
    $('ready-hint').textContent = readyHintOf(running, state.paused);
    // UND-39: STEP idle or paused; PAUSE while running, RESUME while paused.
    $('step').disabled = !state.sketch || !on || (running && !state.paused);
    $('pause').disabled = !running;
    $('pause').textContent = state.paused ? 'RESUME' : 'PAUSE';
    $('pause').setAttribute('aria-pressed', String(state.paused));
    $('play').classList.toggle('running', running);
    $('play').setAttribute('aria-label', running ? 'Stop the run' : 'Play the sketch');
    $('play-word').textContent = running ? 'STOP' : 'PLAY';
    $('play').disabled = !state.sketch;
    document.querySelector('.controls').classList.toggle('locked', running);
    $('console').classList.toggle('dark', !on);
    $('power').setAttribute('aria-pressed', String(on));
    $('power').setAttribute('aria-label', on ? 'Power off the console' : 'Power on the console (resets the sketches to their factory defaults)');
    $('power-word').textContent = on ? 'ON' : 'OFF';
    $('printer-state').textContent = running ? 'PRINTING' : 'IDLE';
    bay.text.readOnly = running;
    $('bay-note').textContent = running ? 'Read-only while a run plays - stop it to edit.' : 'Saved to sketch.yaml as you type. Power off and on for the factory sketch.';
  }

  // The paper reads top to bottom, spool to spool behind glass (owner): a new
  // print winds on into view unless you have scrolled back to read.
  function print(line) {
    const window = $('paper-window');
    const isFollowing = window.scrollHeight - window.scrollTop - window.clientHeight < 40;
    const paper = document.createDocumentFragment();
    const items = printed(line) ?? [];
    for (const each of items) {
      if (each.table) {
        const { table, argument } = each.table;
        const factors = Object.keys(table[0].factors);
        const head = element('tr', {}, ...['value', ...factors, 'total'].map((name) => element('th', {}, name)));
        const rows = table.map((row) => element('tr', {}, element('td', {}, String(row.value)),
          ...factors.map((name) => element('td', row.factors[name] === 1 ? { class: 'eleven' } : {}, scoreText(row.factors[name]))), element('td', {}, String(row.total))));
        paper.append(element('div', { class: 'line note' }, `  ${argument} - shortlist`), element('table', {}, head, ...rows));
      } else {
        paper.append(element('div', { class: `line ${each.tone ?? ''}` }, each.text));
      }
    }
    $('paper').append(paper);
    if (isFollowing) window.scrollTop = window.scrollHeight;
  }

  // A tab pressed: the sketch, fresh paper. Not while a run plays.
  async function choose(name) {
    if (state.running) return;
    await flushBay();
    if (!(await show(name))) return;
    $('paper').replaceChildren();
    state.meters = FRESH_METERS;
    drawGauges();
    await loadBay();
  }

  /**
   * Draws a sketch: with `playing` (a page opened mid-run), the run's own
   * values and the state it is in; else the defaults from the start.
   */
  async function show(name, playing = null) {
    const { ok, value } = await api(`sketch/${encodeURIComponent(name)}`);
    // A run that started meanwhile wins: its sketch is being shown.
    if (!ok || (!playing && state.running)) return false;
    state.sketch = value;
    state.values = { ...startingValues(value.inputs), ...playing?.inputs };
    state.current = playing ? state.current ?? value.graph.initial : value.graph.initial;
    state.liveEdge = null;
    drawRack();
    drawControls();
    drawTube();
    drawStatus();
    return true;
  }

  $('play').addEventListener('click', async () => {
    if (state.running) {
      await api('stop', {});
      return;
    }
    await flushBay();
    $('paper').replaceChildren();
    const { ok, value } = await api('play', { sketch: state.sketch.name, inputs: state.values });
    if (!ok) print({ event: 'dashboard', refused: value.problem });
  });

  // UND-39: STEP - idle, start paused and make the first move; paused, one more move.
  $('step').addEventListener('click', async () => {
    if (state.running) {
      await api('step', {});
      return;
    }
    await flushBay();
    $('paper').replaceChildren();
    const started = await api('play', { sketch: state.sketch.name, inputs: state.values, paused: true });
    if (!started.ok) {
      print({ event: 'dashboard', refused: started.value.problem });
      return;
    }
    await api('step', {});
  });

  $('pause').addEventListener('click', () => api(state.paused ? 'resume' : 'pause', {}));

  $('power').addEventListener('click', async () => {
    state.on = !state.on;
    await api('power', { on: state.on });
    if (state.on && state.sketch) await choose(state.sketch.name);
    drawStatus();
  });

  const events = new globalThis.EventSource('events');
  events.addEventListener('message', (message) => {
    const line = JSON.parse(message.data);
    if (line.event === 'dashboard' && line.running !== undefined) {
      state.running = line.running;
      state.paused = line.running && line.paused === true;
      // A page opened, or left on another sketch, while a run plays shows that run's sketch.
      if (line.running && line.sketch && line.sketch !== state.sketch?.name) show(line.sketch, line);
      drawStatus();
      drawTube();
    }
    // UND-39: the run's gate - paused before a move, or running on.
    if (line.event === 'dashboard' && line.running === undefined && line.paused !== undefined) {
      state.paused = line.paused;
      drawStatus();
      drawTube();
    }
    // UND-30 AC2: the state the run is in glows; the transition just taken flows.
    if (line.event === 'state') {
      state.current = line.to;
      state.liveEdge = state.sketch?.graph.edges.findIndex((edge) => edge.from === line.from && edge.to === line.to) ?? null;
      drawTube();
    }
    print(line);
    state.meters = metersAfter(state.meters, line, Date.now());
    drawGauges();
  });

  (async () => {
    const { value } = await api('sketches');
    state.rack = value;
    drawRack();
    drawStatus();
    // Open on a sketch with controls to show, else the first that plays -
    // unless a run is playing, whose sketch is shown instead (above).
    const first = value.find((entry) => entry.ok && entry.inputs > 0) ?? value.find((entry) => entry.ok);
    if (first && !state.running && !state.sketch) await show(first.name);
    await loadBay();
  })();
}

if (globalThis.document) boot();
