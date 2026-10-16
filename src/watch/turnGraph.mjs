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
  const when = guardLabel(guard);
  return when ? `${on}: ${when}` : on;
}
