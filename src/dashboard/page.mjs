// Sprint 6 (ARCH §3, docs/design/DASHBOARD.md): the operations console in
// the browser. The pure helpers at the top (colours, readouts, dial geometry,
// the printer's lines) run in Node too, for tests; the DOM wiring below them
// runs only in a page.

import { ringOf, SIZE, tubeLayout } from './tube.mjs';

// The themes (UND-36): steampunk is the console as first designed.
export const THEMES = ['steampunk', 'professional', 'starship'];

/**
 * The theme to show: a known `?theme=` wins, then the remembered one, else steampunk.
 */
export function themeOf(query, stored) {
  return [query, stored].find((name) => THEMES.includes(name)) ?? THEMES[0];
}

/**
 * A `#rrggbb` colour as [r, g, b]; grey for anything else.
 */
export function rgbOf(hex) {
  const match = /^#([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(hex.trim());
  return match ? match.slice(1).map((part) => Number.parseInt(part, 16)) : [128, 128, 128];
}

/**
 * How strongly a weight is set, 0 to 3, whatever its range - the tube's
 * glows and widths are sized for this.
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
    svg.append(svgElement('path', { d: arc.track, fill: 'none', stroke: look.track, 'stroke-width': 16, 'stroke-linecap': 'round' }),
      svgElement('path', { d: arc.fill, fill: 'none', stroke: arc.colour, 'stroke-width': 12, 'stroke-linecap': 'round', 'stroke-dasharray': '10 5', class: arc.value > 0 ? 'flowing' : 'faint', style: glow }));
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

function drawEdges(svg, edges, power, { isRunning, liveEdge }, theme) {
  const labels = [];
  for (const edge of edges) {
    const isLive = isRunning && edge.index === liveEdge;
    const look = edgeLook(edge, power, isLive, theme);
    const isFlowing = isRunning && (isLive || edge.isDecision);
    svg.append(svgElement('path', { d: edge.d, fill: 'none', stroke: look.colour, 'stroke-width': look.width, 'stroke-linecap': 'round', 'stroke-dasharray': '7 5', class: isFlowing ? 'flowing' : 'still', style: look.glow }));
    labels.push(label(edge.lx, edge.ly - 6, edge.label, { color: look.tone, fontSize: 'clamp(11px,2.3vw,17px)', textShadow: theme.glows ? `0 0 5px ${theme.shadow}, 0 0 8px ${look.tone}` : 'none' }));
    if (edge.sub) labels.push(label(edge.lx, edge.ly + 10, edge.sub, { color: look.tone, fontSize: 'clamp(9px,1.7vw,13px)', opacity: '.8', textShadow: theme.glows ? `0 0 4px ${theme.shadow}` : 'none' }));
  }
  return labels;
}

function drawOrb(svg, { weights, total, level, blend }, look) {
  if (weights.length === 0) return [];
  svg.append(svgElement('circle', { cx: 300, cy: 318, r: 14 + level * 2, fill: blend, class: 'orb', style: look.glows ? `filter: drop-shadow(0 0 ${8 + level * 4}px ${blend})` : '' }));
  const shares = weights.map((weight, index) => {
    const share = total === 0 ? 0 : Math.round((weight.value / total) * 100);
    const colour = rgb(weight.colour);
    return label(300 + (index - (weights.length - 1) / 2) * 46, 380, `${share}%`, { color: colour, fontSize: 'clamp(11px,2.2vw,17px)', textShadow: look.glows ? `0 0 6px ${colour}` : 'none' });
  });
  return [label(300, 362, 'DECISION POWER', { class: 'orb-title', color: look.orbTitle }), ...shares];
}

function drawStates(svg, nodes, current, look) {
  return nodes.map((node) => {
    const isNow = node.id === current;
    const edge = isNow ? look.stateEdgeNow : look.stateEdge;
    svg.append(svgElement('circle', { cx: node.x, cy: node.y, r: isNow ? 20 : 15, fill: isNow ? look.stateNow : look.state, stroke: edge, 'stroke-width': 2.5, class: isNow ? 'now' : '' }));
    if (node.final) svg.append(svgElement('circle', { cx: node.x, cy: node.y, r: isNow ? 14 : 10, fill: 'none', stroke: edge, 'stroke-width': 1.5 }));
    const tone = isNow ? look.stateToneNow : look.stateTone;
    return label(node.lx, node.ly, node.id.replaceAll('_', ' '), { color: tone, fontSize: 'clamp(13px,2.8vw,21px)', textShadow: look.glows ? `0 0 6px ${look.stateGlow}, 0 0 3px ${look.shadow}` : 'none' });
  });
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
  const state = { rack: [], sketch: null, values: {}, running: false, on: true, current: null, liveEdge: null, open: new Set(), look: null };

  // UND-36: the theme - a known ?theme= wins, then the one this browser remembers.
  const STORE = 'understudy-theme';
  function remembered() {
    try {
      return globalThis.localStorage.getItem(STORE);
    } catch {
      return null;
    }
  }
  function useTheme(name) {
    document.documentElement.dataset.theme = name;
    state.look = themeLook();
    for (const button of document.querySelectorAll('.theme-choice')) button.setAttribute('aria-pressed', String(button.dataset.theme === name));
  }
  useTheme(themeOf(new URLSearchParams(globalThis.location.search).get('theme'), remembered()));
  for (const button of document.querySelectorAll('.theme-choice')) {
    button.addEventListener('click', () => {
      useTheme(button.dataset.theme);
      try {
        globalThis.localStorage.setItem(STORE, button.dataset.theme);
      } catch { /* not remembered: a blocked store */ }
      if (!state.sketch) return;
      drawControls();
      drawTube();
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
    const update = () => {
      const value = Number(fader.value);
      state.values[input.name] = value;
      nixie.textContent = readoutOf(value, input.range);
      fader.setAttribute('aria-valuetext', value === 0 ? 'off' : value.toFixed(2));
      slot.style.setProperty('--fill', String((value - low) / (high - low)));
      drawTube();
    };
    fader.addEventListener('input', update);
    const label = element('label', { for: id }, element('span', { class: 'chip', style: { '--colour': colour }, 'aria-hidden': 'true' }), input.name);
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
    $('tube-caption').textContent = state.running ? `running · ${state.current ?? ''}` : 'idle';
    if (!sketch) return;
    const look = state.look;
    const weights = sketch.inputs.filter((input) => input.kind === 'weight').map((input, index) => ({
      name: input.name, value: state.values[input.name], range: input.range, colour: look.weights[index % look.weights.length],
    }));
    const power = {
      weights, total: weights.reduce((sum, each) => sum + each.value, 0),
      level: weights.reduce((sum, each) => sum + levelOf(each.value, each.range), 0), blend: rgb(blendOf(weights)),
    };
    const layout = tubeLayout(sketch.graph, sketch.decision);
    const svg = svgElement('svg', { viewBox: `0 0 ${SIZE} ${SIZE}`, role: 'img', 'aria-label': tubeAria(layout, state.current) });
    const labels = [
      ...drawRing(svg, weights, look),
      ...drawEdges(svg, layout.edges, power, { isRunning: state.running, liveEdge: state.liveEdge }, look),
      ...drawOrb(svg, power, look),
      ...drawStates(svg, layout.nodes, state.current, look),
    ];
    $('tube').replaceChildren(svg, element('div', { class: 'labels', 'aria-hidden': 'true' }, ...labels));
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
    (isOpen ? bay.text : $('remove-printer')).focus();
  }
  $('remove-printer').addEventListener('click', async () => {
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
    $('ready-hint').textContent = running ? 'press to stop the run' : 'press to play the sketch';
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

  function print(line) {
    const paper = $('paper');
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
    const window = $('paper-window');
    window.scrollTop = window.scrollHeight;
  }

  async function choose(name) {
    if (state.running) return;
    await flushBay();
    const { ok, value } = await api(`sketch/${encodeURIComponent(name)}`);
    if (!ok) return;
    state.sketch = value;
    state.values = startingValues(value.inputs);
    state.current = value.graph.initial;
    state.liveEdge = null;
    drawRack();
    drawControls();
    drawTube();
    drawStatus();
    $('paper').replaceChildren();
    await loadBay();
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
      drawStatus();
      drawTube();
    }
    // UND-30 AC2: the state the run is in glows; the transition just taken flows.
    if (line.event === 'state' && state.sketch) {
      state.current = line.to;
      state.liveEdge = state.sketch.graph.edges.findIndex((edge) => edge.from === line.from && edge.to === line.to);
      drawTube();
    }
    print(line);
  });

  (async () => {
    const { value } = await api('sketches');
    state.rack = value;
    drawRack();
    drawStatus();
    // Open on a sketch with controls to show, else the first that plays.
    const first = value.find((entry) => entry.ok && entry.inputs > 0) ?? value.find((entry) => entry.ok);
    if (first) await choose(first.name);
  })();
}

if (globalThis.document) boot();
