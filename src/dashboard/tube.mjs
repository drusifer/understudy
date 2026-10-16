// Sprint 6 UND-30 (ARCH §3, docs/design/DASHBOARD.md "State tube"): the
// statechart as the tube draws it, in a 600 x 600 drawing - pure, so Node
// tests it and the page draws it. States run clockwise round a circle from
// the initial one; final states sit inside it. Every transition is a curve
// bowed towards the centre, labelled with its event and its guard. Around
// the rim, one arc per weight, filled by its value.

export const SIZE = 600;
const CENTRE = SIZE / 2;
const LOOP = 170;
const INSIDE = 96;
const RIM = 266;
const GUARD_CHARS = 24;

const point = (degrees, radius) => [CENTRE + radius * Math.cos((degrees * Math.PI) / 180), CENTRE + radius * Math.sin((degrees * Math.PI) / 180)];
const fixed = (value) => Math.round(value * 10) / 10;

/**
 * An arc of the circle of `radius`, clockwise from `from` to `to` degrees.
 */
export function arcPath(from, to, radius) {
  const [x1, y1] = point(from, radius);
  const [x2, y2] = point(to, radius);
  return `M ${fixed(x1)} ${fixed(y1)} A ${radius} ${radius} 0 ${to - from > 180 ? 1 : 0} 1 ${fixed(x2)} ${fixed(y2)}`;
}

/**
 * Where each state sits: the others round the loop from the initial one
 * (at the left), finals inside across the top.
 */
function placesOf(graph) {
  const loop = graph.nodes.filter((node) => !node.final);
  const finals = graph.nodes.filter((node) => node.final);
  const start = Math.max(0, loop.findIndex((node) => node.id === graph.initial));
  const ordered = [...loop.slice(start), ...loop.slice(0, start)];
  const places = new Map();
  for (const [index, node] of ordered.entries()) {
    const degrees = 180 + (360 * index) / ordered.length;
    places.set(node.id, { degrees, at: point(degrees, LOOP), final: false });
  }
  // A final state sits inside, beside the state that leads to it; several
  // finals from the same state fan out either side of it.
  const bySource = new Map();
  for (const node of finals) {
    const source = graph.edges.find((edge) => edge.to === node.id && places.has(edge.from))?.from;
    const degrees = source === undefined ? 270 : places.get(source).degrees;
    bySource.set(degrees, [...bySource.get(degrees) ?? [], node]);
  }
  for (const [degrees, group] of bySource) {
    for (const [index, node] of group.entries()) {
      const fan = group.length === 1 ? 0 : -40 + (80 * index) / (group.length - 1);
      places.set(node.id, { degrees: degrees + fan, at: point(degrees + fan, INSIDE), final: true });
    }
  }
  return places;
}

/**
 * A transition's label as two lines: the event, then its guard (shortened).
 */
function labelLines(label) {
  const [on, ...rest] = label.split(': ');
  const guard = rest.join(': ');
  return { label: on, sub: guard.length > GUARD_CHARS ? `${guard.slice(0, GUARD_CHARS - 1)}…` : guard };
}

/**
 * A transition between neighbours, along the loop: clockwise outside, or
 * back the other way just inside.
 */
function alongLoop(from, to, isClockwise) {
  const a = from.degrees;
  let b = to.degrees;
  if (isClockwise && b <= a) b += 360;
  if (!isClockwise && b >= a) b -= 360;
  const step = isClockwise ? 11 : -11;
  const radius = isClockwise ? LOOP : LOOP - 18;
  const [x1, y1] = point(a + step, radius);
  const [x2, y2] = point(b - step, radius);
  const middle = (a + b) / 2;
  const [lx, ly] = point(middle, isClockwise ? LOOP + 30 : LOOP - 44);
  const d = `M ${fixed(x1)} ${fixed(y1)} A ${radius} ${radius} 0 0 ${isClockwise ? 1 : 0} ${fixed(x2)} ${fixed(y2)}`;
  return { d, lx: fixed(lx), ly: fixed(ly) };
}

/**
 * Any other transition: a straight line (a second one between the same
 * two states bows aside), labelled beside it on the side away from the centre.
 */
function chord(from, to, repeat) {
  const [x1, y1] = from.at;
  const [x2, y2] = to.at;
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const side = repeat % 2 === 0 ? -1 : 1;
  const bow = repeat === 0 ? 0 : 0.25 * side;
  const cx = mx + (CENTRE - mx) * bow;
  const cy = my + (CENTRE - my) * bow;
  // Beside the line: perpendicular to it, towards whichever side is further from the centre.
  const length = Math.hypot(x2 - x1, y2 - y1) || 1;
  let nx = -(y2 - y1) / length;
  let ny = (x2 - x1) / length;
  if ((mx + nx - CENTRE) ** 2 + (my + ny - CENTRE) ** 2 < (mx - CENTRE) ** 2 + (my - CENTRE) ** 2) {
    nx = -nx;
    ny = -ny;
  }
  const lx = 0.25 * x1 + 0.5 * cx + 0.25 * x2 + nx * 62;
  const ly = 0.25 * y1 + 0.5 * cy + 0.25 * y2 + ny * 26;
  return { d: `M ${fixed(x1)} ${fixed(y1)} Q ${fixed(cx)} ${fixed(cy)} ${fixed(x2)} ${fixed(y2)}`, lx: fixed(lx), ly: fixed(ly) };
}

function selfLoop(from) {
  const [x, y] = from.at;
  const [cx, cy] = point(from.degrees, LOOP + 50);
  return { d: `M ${fixed(x)} ${fixed(y)} Q ${fixed(cx)} ${fixed(cy)} ${fixed(x + 1)} ${fixed(y + 1)}`, lx: fixed(cx), ly: fixed(cy) };
}

/**
 * The tube's drawing for a statechart.
 * @param {{ initial: string, nodes: { id: string, final: boolean }[], edges: { from: string, to: string, label: string }[] }} graph
 * @param {number[]} decision indices of the edges the decision's power flows along
 */
export function tubeLayout(graph, decision = []) {
  const places = placesOf(graph);
  const nodes = graph.nodes.map((node) => {
    const { at, degrees, final } = places.get(node.id);
    const [x, y] = at;
    // Loop states label outward; finals label below themselves.
    const [lx, ly] = final ? [x, y + 32] : point(degrees, LOOP + 38);
    return { id: node.id, x: fixed(x), y: fixed(y), final, lx: fixed(lx), ly: fixed(ly) };
  });
  const loop = graph.nodes.filter((node) => !node.final).map((node) => node.id);
  const order = [...places].filter(([, place]) => !place.final).toSorted((a, b) => a[1].degrees - b[1].degrees).map(([id]) => id);
  const next = (id) => order[(order.indexOf(id) + 1) % order.length];
  const seen = new Map();
  const edges = graph.edges.map((edge, index) => {
    const from = places.get(edge.from);
    const to = places.get(edge.to);
    if (!from || !to) return null;
    const pair = `${edge.from}>${edge.to}`;
    const repeat = seen.get(pair) ?? 0;
    seen.set(pair, repeat + 1);
    const base = { index, from: edge.from, to: edge.to, ...labelLines(edge.label), isDecision: decision.includes(index) };
    if (edge.from === edge.to) return { ...base, ...selfLoop(from) };
    // Neighbours round the loop: along the circle, labelled just outside it.
    const isNeighbour = next(edge.from) === edge.to || next(edge.to) === edge.from;
    if (repeat === 0 && isNeighbour && loop.length > 2 && !from.final && !to.final) {
      return { ...base, ...alongLoop(from, to, next(edge.from) === edge.to) };
    }
    return { ...base, ...chord(from, to, repeat) };
  }).filter(Boolean);
  return { size: SIZE, nodes, edges };
}

/**
 * The power ring: one arc per weight, its share of the rim, filled by its
 * value within its range; the label sits just inside the arc.
 * @param {{ name: string, value: number, range: number[], colour: string }[]} weights
 */
export function ringOf(weights) {
  if (weights.length === 0) return [];
  const span = 360 / weights.length;
  const gap = Math.min(10, span / 6);
  // Arcs start at the upper right, so with four states each sits between two.
  return weights.map((weight, index) => {
    const from = -45 - span / 2 + index * span + gap / 2;
    const to = from + span - gap;
    const [low, high] = weight.range;
    const share = (weight.value - low) / (high - low);
    const [lx, ly] = point((from + to) / 2, RIM - 30);
    return {
      name: weight.name, colour: weight.colour, value: weight.value,
      track: arcPath(from, to, RIM), fill: arcPath(from, from + Math.max(0.5, (to - from) * share), RIM),
      lx: fixed(lx), ly: fixed(ly),
    };
  });
}
