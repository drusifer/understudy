// Sprint 6 UND-30 (ARCH §3, docs/design/DASHBOARD.md "State tube"): the
// tube's power ring, in a 600 x 600 drawing - pure, so Node tests it and the
// page draws it: one arc per weight round the rim, filled by its value.
// Sprint 14 UND-41: the statechart inside it is a layered flow (flow.mjs).

export const SIZE = 600;
const CENTRE = SIZE / 2;
// At the very edge of the glass, so the flow inside has the tube to itself.
const RIM = 288;

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
 * The power ring: one arc per weight, its share of the rim, filled by its
 * value within its range; the label sits just inside the arc.
 * @param {{ name: string, value: number, range: number[], colour: string }[]} weights
 */
export function ringOf(weights) {
  if (weights.length === 0) return [];
  const span = 360 / weights.length;
  const gap = Math.min(10, span / 6);
  // Arcs start at the upper right.
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
