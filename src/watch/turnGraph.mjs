// Sprint 4 (ARCH §3, §5, ADR-0014/0015): a sketch's turn as the watch page
// draws it, and the one way a transition is named - in the log's `state`
// lines and on the diagram's edges alike. Pure: runs in Node and in the
// browser (the watch server serves this file to the page as it is).

const EVENT_NAMES = new Set(['OBSERVE', 'STEP', 'QUIT']);

/**
 * A guard in words: its type, then each parameter as `name value`
 * (`phase is asking`, `showing text Ticket issued`).
 * @param {string|{ type: string, params?: object }|undefined} guard
 */
export function guardLabel(guard) {
  if (guard === undefined || guard === null) return '';
  if (typeof guard === 'string') return guard;
  const parameters = Object.entries(guard.params ?? {}).map(([name, value]) => `${name} ${typeof value === 'string' ? value : JSON.stringify(value)}`);
  return [guard.type, ...parameters].join(' ');
}

/**
 * A transition in words: the event that took it (`OBSERVE`, `STEP`,
 * `QUIT`, `done` when an invoked actor finished, `always`), and its guard.
 * @param {string} eventType as XState names it (`xstate.done.actor...` for onDone)
 * @param {string|object} [guard]
 */
export function transitionLabel(eventType, guard) {
  let on = eventType;
  if (eventType === '' || eventType === undefined) on = 'always';
  else if (eventType.startsWith('xstate.done.')) on = 'done';
  else if (!EVENT_NAMES.has(eventType)) on = eventType;
  return labelOf(on, guard);
}

/**
 * `on`, then `: <guard>` when there is one.
 */
export function labelOf(on, guard) {
  const when = guardLabel(guard);
  return when ? `${on}: ${when}` : on;
}

/**
 * One transition list as a turn writes it: a target name, `{ target,
 * guard }`, or a list of those.
 */
function targetsOf(written) {
  const list = Array.isArray(written) ? written : [written];
  return list.filter((each) => each !== undefined && each !== null)
    .map((each) => (typeof each === 'string' ? { target: each } : each))
    .filter((each) => typeof each.target === 'string');
}

/**
 * A turn as states and labelled transitions, in the order it is written.
 * @param {{ initial: string, states: Record<string, object> }} turn the sketch's `turn:`
 * @returns {{ initial: string, nodes: { id: string, tags: string[], final: boolean }[],
 *   edges: { from: string, to: string, label: string }[] }}
 */
export function turnGraph(turn) {
  const nodes = [];
  const edges = [];
  const states = Object.entries(turn.states ?? {});
  for (const [id, state] of states) {
    nodes.push({ id, tags: state?.tags ?? [], final: state?.type === 'final' });
    const add = (on, written) => {
      const targets = targetsOf(written);
      for (const { target, guard } of targets) edges.push({ from: id, to: target, label: labelOf(on, guard) });
    };
    const events = Object.entries(state?.on ?? {});
    for (const [event, written] of events) add(event, written);
    if (state?.invoke?.onDone !== undefined) add('done', state.invoke.onDone);
    if (state?.always !== undefined) add('always', state.always);
  }
  return { initial: turn.initial, nodes, edges };
}
