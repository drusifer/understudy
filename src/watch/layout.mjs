// Sprint 4 (ARCH §3, ADR-0015): where the watch page draws each state and
// transition. Turns are flat and small, so a layered layout is enough:
// each state's column is its distance from the initial state, states in a
// column stack top to bottom in the order the turn names them, transitions
// that go forward are curves to the right, and the rest arc above the top
// row, out of the forward edges' way. A gap between columns is as wide as
// the longest label that crosses it.
// Pure geometry: runs in Node and in the browser.

const ROW = 110;
const MARGIN = 30;
const MIN_GAP = 70;
const LABEL_CHAR = 6.6;
const ARC = 34;
const ARC_STEP = 24;
const NODE_HEIGHT = 44;
const CHAR = 7.5;

/**
 * Each node's column: its distance from `initial` along the transitions;
 * a state nothing reaches goes in a column after the rest.
 */
function columnsOf(graph) {
  const column = new Map([[graph.initial, 0]]);
  const queue = [graph.initial];
  while (queue.length > 0) {
    const id = queue.shift();
    for (const edge of graph.edges) {
      if (edge.from !== id || column.has(edge.to)) continue;
      column.set(edge.to, column.get(id) + 1);
      queue.push(edge.to);
    }
  }
  const last = Math.max(0, ...column.values());
  for (const node of graph.nodes) if (!column.has(node.id)) column.set(node.id, last + 1);
  return column;
}

/**
 * The point at `t` on a cubic Bezier curve.
 */
function pointOn([p0, p1, p2, p3], t) {
  const u = 1 - t;
  const at = (axis) => (u ** 3 * p0[axis]) + (3 * u * u * t * p1[axis]) + (3 * u * t * t * p2[axis]) + (t ** 3 * p3[axis]);
  return { x: at(0), y: at(1) };
}

function curve(points) {
  const [p0, p1, p2, p3] = points.map(([x, y]) => `${Math.round(x)},${Math.round(y)}`);
  return `M ${p0} C ${p1} ${p2} ${p3}`;
}

/**
 * The curve for one transition, by how its ends sit.
 */
function edgePoints(from, to, nth, top) {
  if (from === to) {
    const x = from.x + from.w / 2;
    return [[x - 12, from.y], [x - 40, from.y - 45], [x + 40, from.y - 45], [x + 12, from.y]];
  }
  if (to.column > from.column) {
    const start = [from.x + from.w, from.y + from.h / 2 + (nth * 8)];
    const end = [to.x, to.y + to.h / 2 + (nth * 8)];
    const bend = (end[0] - start[0]) / 2;
    return [start, [start[0] + bend, start[1]], [end[0] - bend, end[1]], end];
  }
  // Back (or same-column) edges arc over the top row; each further one higher.
  const start = [from.x + (from.w / 2) + 10, from.y];
  const end = [to.x + (to.w / 2) - 10, to.y];
  return [start, [start[0], top - (nth * ARC_STEP)], [end[0], top - (nth * ARC_STEP)], end];
}

/**
 * Positions for every state and a path for every transition.
 * @param {ReturnType<import('./turnGraph.mjs').turnGraph>} graph
 */
export function layout(graph) {
  const column = columnsOf(graph);
  const columns = Math.max(...column.values()) + 1;
  const widest = Array.from({ length: columns }, () => 0);
  const gap = Array.from({ length: columns }, () => MIN_GAP);
  const widthOf = (id) => Math.max(110, Math.round((id.length * CHAR) + 32));
  for (const node of graph.nodes) widest[column.get(node.id)] = Math.max(widest[column.get(node.id)], widthOf(node.id));
  const backEdges = graph.edges.filter((edge) => column.get(edge.to) <= column.get(edge.from));
  for (const edge of graph.edges) {
    const from = column.get(edge.from);
    if (column.get(edge.to) > from) gap[from] = Math.max(gap[from], Math.round((edge.label.length * LABEL_CHAR) + 30));
  }
  const left = [MARGIN];
  for (let col = 1; col < columns; col++) left.push(left[col - 1] + widest[col - 1] + gap[col - 1]);
  // Room above the top row for the back-edge arcs and their labels.
  const arcs = Math.max(1, backEdges.length);
  const firstRow = MARGIN + ARC + (arcs * ARC_STEP) + 14;
  const rows = new Map();
  const nodes = graph.nodes.map((node) => {
    const col = column.get(node.id);
    const row = rows.get(col) ?? 0;
    rows.set(col, row + 1);
    return { ...node, column: col, x: left[col], y: firstRow + (row * ROW), w: widthOf(node.id), h: NODE_HEIGHT };
  });
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const top = firstRow - ARC;
  const seen = new Map();
  let backs = 0;
  const edges = graph.edges.filter((edge) => byId.has(edge.from) && byId.has(edge.to)).map((edge, index) => {
    const pair = `${edge.from}>${edge.to}`;
    const isBack = column.get(edge.to) <= column.get(edge.from) && edge.from !== edge.to;
    // Back edges each get their own arc height; forward pairs fan out by `nth`.
    const nth = isBack ? backs++ : (seen.get(pair) ?? 0);
    seen.set(pair, (seen.get(pair) ?? 0) + 1);
    const points = edgePoints(byId.get(edge.from), byId.get(edge.to), nth, top);
    const middle = pointOn(points, 0.5);
    return { ...edge, id: `e${index}`, path: curve(points), labelX: Math.round(middle.x), labelY: Math.round(middle.y) - 6 };
  });
  const width = Math.max(...nodes.map((node) => node.x + node.w)) + MARGIN;
  const lowest = Math.max(...nodes.map((node) => node.y + node.h));
  return { width, height: lowest + MARGIN, nodes, edges };
}
