// Sprint 6 (ARCH §3, docs/design/DASHBOARD.md): the operations console in
// the browser. The pure helpers at the top (colours, readouts, dial geometry,
// the printer's lines) run in Node too, for tests; the DOM wiring below them
// runs only in a page.

// Each weight's own colour, in the order the sketch declares them.
export const COLOURS = [[255, 72, 56], [176, 98, 255], [56, 196, 255], [120, 236, 70], [255, 176, 32], [255, 110, 190]];

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
  const state = { rack: [], sketch: null, values: {}, running: false, on: true, tube: null };

  function drawRack() {
    const rack = $('rack');
    rack.replaceChildren(...state.rack.map((entry) => {
      const tab = element('button', { type: 'button', class: 'sketch-tab', 'aria-pressed': String(entry.name === state.sketch?.name) },
        element('span', { class: 'name' }, entry.name), element('span', { class: 'line' }, entry.ok ? entry.description : entry.problem));
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
    return element('div', { class: 'dial-block' }, element('div', { class: 'plate-label' }, input.name.toUpperCase()), dial);
  }

  function drawFader(input, index) {
    const colour = rgb(COLOURS[index % COLOURS.length]);
    const [low, high] = input.range;
    const id = `fader-${input.name}`;
    const fader = element('input', { id, class: 'fader', type: 'range', min: String(low), max: String(high), step: '0.01', value: String(state.values[input.name]) });
    const slot = element('div', { class: 'slot', style: { '--colour': colour } }, element('div', { class: 'glow', 'aria-hidden': 'true' }), element('div', { class: 'ticks', 'aria-hidden': 'true' }), fader);
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
    const row = element('div', { class: 'fader-row' }, label, slot, nixie);
    update();
    return [row, element('div', { class: 'fader-about' }, about || 'not used by any factor')];
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

  function drawControls() {
    const { sketch } = state;
    $('sketch-title').textContent = sketch.name;
    $('sketch-about').textContent = (sketch.description || '').trim();
    const weights = sketch.inputs.filter((input) => input.kind === 'weight');
    $('dials').replaceChildren(...sketch.inputs.filter((input) => input.kind === 'choose').map((input) => drawDial(input)));
    $('faders').replaceChildren(...(weights.length > 0 ? [element('div', { class: 'fader-scale', 'aria-hidden': 'true' }, element('span', {}, '◂ LESS IMPORTANT'), element('span', {}, 'MORE IMPORTANT ▸'))] : []),
      ...weights.flatMap((input, index) => drawFader(input, index)));
    $('switches').replaceChildren(...sketch.inputs.filter((input) => input.kind === 'switch').map((input) => drawSwitch(input)));
    $('nothing-to-tune').hidden = sketch.inputs.length > 0;
  }

  // The tube is drawn in Phase 5 (tube.mjs); until then, its caption only.
  function drawTube() {
    $('tube-caption').textContent = state.running ? 'running' : 'idle';
  }

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
    const { ok, value } = await api(`sketch/${encodeURIComponent(name)}`);
    if (!ok) return;
    state.sketch = value;
    state.values = startingValues(value.inputs);
    drawRack();
    drawControls();
    drawTube();
    drawStatus();
    $('paper').replaceChildren();
  }

  $('play').addEventListener('click', async () => {
    if (state.running) {
      await api('stop', {});
      return;
    }
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
    print(line);
  });

  (async () => {
    const { value } = await api('sketches');
    state.rack = value;
    drawRack();
    drawStatus();
    const first = value.find((entry) => entry.ok);
    if (first) await choose(first.name);
  })();
}

if (globalThis.document) boot();
