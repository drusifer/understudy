// Sprint 14 UND-41 (ADR-0035): the statechart as a layered flow - the
// standard way to draw one (as Graphviz and the XState visualiser do):
// states in layers from the initial one down, each transition an orthogonal
// arrow labelled with its event and guard, laid out by ELK so nothing
// overlaps. Runs on the server (Node); the page only draws what it returns.

import ELK from 'elkjs/lib/elk.bundled.js';

const GUARD_CHARS = 26;
const CHAR = 7;
const LINE = 15;
const STATE_HEIGHT = 34;

const elk = new ELK();
const fixed = (value) => Math.round(value * 10) / 10;

/**
 * A transition's label as two lines: the event, then its guard (shortened).
 */
export function labelLines(label) {
  const [on, ...rest] = label.split(': ');
  const guard = rest.join(': ');
  return { label: on, sub: guard.length > GUARD_CHARS ? `${guard.slice(0, GUARD_CHARS - 1)}…` : guard };
}

const shown = (id) => id.replaceAll('_', ' ');

/**
 * The flow's drawing for a statechart: where each state and arrow goes.
 * @param {{ initial: string, nodes: { id: string, final: boolean }[], edges: { from: string, to: string, label: string }[] }} graph
 * @param {number[]} decision indices of the edges the decision's power flows along
 * @returns {Promise<{ width: number, height: number, nodes: object[], edges: object[] }>}
 */
export async function flowLayout(graph, decision = []) {
  // The initial state first, the rest as written: ELK keeps this order when it breaks cycles.
  const nodes = [...graph.nodes.filter((node) => node.id === graph.initial), ...graph.nodes.filter((node) => node.id !== graph.initial)];
  const labels = graph.edges.map((edge) => labelLines(edge.label));
  const laid = await elk.layout({
    id: 'turn',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'DOWN',
      'elk.edgeRouting': 'ORTHOGONAL',
      'elk.edgeLabels.placement': 'CENTER',
      'elk.layered.cycleBreaking.strategy': 'MODEL_ORDER',
      'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
      'elk.layered.spacing.nodeNodeBetweenLayers': '56',
      'elk.spacing.nodeNode': '36',
      'elk.spacing.edgeLabel': '4',
      'elk.padding': '[top=16,left=16,bottom=16,right=16]',
    },
    children: nodes.map((node) => ({ id: node.id, width: 28 + shown(node.id).length * 10, height: STATE_HEIGHT })),
    edges: graph.edges.map((edge, index) => ({
      id: `e${index}`, sources: [edge.from], targets: [edge.to],
      labels: [{ text: edge.label, width: CHAR * Math.max(labels[index].label.length, labels[index].sub.length), height: labels[index].sub ? 2 * LINE : LINE }],
    })),
  });
  const finals = new Set(graph.nodes.filter((node) => node.final).map((node) => node.id));
  return {
    width: fixed(laid.width), height: fixed(laid.height),
    nodes: laid.children.map((child) => ({
      id: child.id, name: shown(child.id), x: fixed(child.x), y: fixed(child.y), width: child.width, height: child.height,
      final: finals.has(child.id), initial: child.id === graph.initial,
    })),
    edges: laid.edges.map((laidEdge, index) => {
      const [section] = laidEdge.sections ?? [];
      const points = section ? [section.startPoint, ...(section.bendPoints ?? []), section.endPoint].map((point) => [fixed(point.x), fixed(point.y)]) : [];
      const [label] = laidEdge.labels;
      return {
        index, from: graph.edges[index].from, to: graph.edges[index].to, ...labels[index], points,
        lx: fixed(label.x + label.width / 2), ly: fixed(label.y), isDecision: decision.includes(index),
      };
    }),
  };
}
