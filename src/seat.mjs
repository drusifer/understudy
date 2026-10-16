// US-129/D154: the one seat every part uses - its turn file, running.
//
// The run loop asks a seat "is it my move?" and then "take one step".
// This seat answers both from a statechart: it looks at the app through
// its target, tells the machine what changed as an `OBSERVE` event, waits
// until no `busy` state is active, and reads the answer off the state's
// tags. The MEMORY of what was seen lives here, not in any turn file: what
// changed since the last look, how long the talk channel has been quiet,
// and which talk lines were the understudy's own (its own words are never
// news - recard lessons, US-127 and US-128). An author never writes
// bookkeeping.

import { createActor, waitFor } from 'xstate';
import { transitionLabel } from './watch/turnGraph.mjs';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export class MachineSeat {
  #actor;
  #services;
  #clock;
  #pollMs;
  #isQuitSent = false;
  #seen = { talk: null, seq: undefined, changedAt: null, lastTalkAt: null };
  // Sprint 4 (ADR-0014): the state changes since they were last drained,
  // and how many looks changed nothing (folded into one number).
  #changes = [];
  #idleLooks = 0;

  /**
   * @param {{ machine: import('xstate').AnyStateMachine, services: object, input?: object,
   *   clock?: () => number, pollMs?: number }} options
   *   `services` is what the library's actors use (target, judge, name,
   *   questions, player, app); the seat adds `seat` and `onRecord`.
   */
  constructor({ machine, services, input = {}, clock = Date.now, pollMs = 1500 }) {
    this.#services = services;
    this.#clock = clock;
    this.#pollMs = pollMs;
    services.seat = { markSeen: () => this.#markSeen() };
    services.onRecord = (record) => { this.lastRecord = record; };
    this.lastRecord = null;
    this.#actor = createActor(machine, { input, inspect: (event) => this.#record(event) }).start();
  }

  /**
   * @param {{ shouldStop: () => boolean }} options
   * @returns {Promise<'move'|'wait'|'done'>}
   */
  async nextMove({ shouldStop }) {
    if (shouldStop() && !this.#isQuitSent) {
      this.#isQuitSent = true;
      this.#actor.send({ type: 'QUIT' });
    }
    if (this.#actor.getSnapshot().status === 'done') return 'done';
    const before = { value: this.state, changes: this.#changes.length };
    this.#actor.send({ type: 'OBSERVE', ...(await this.#look()) });
    const snapshot = await this.#settle();
    if (snapshot.status === 'done') return 'done';
    if (snapshot.hasTag('move')) return 'move';
    if (this.state === before.value) {
      // A look that ended where it began: counted, not listed.
      this.#changes.length = before.changes;
      this.#idleLooks += 1;
    }
    await sleep(this.#pollMs);
    return 'wait';
  }

  /**
   * The state changes since the last call, oldest first; the first one
   * carries how many idle looks came before it.
   * @returns {{ from: string, to: string, on: string, at: string, idle_looks?: number }[]}
   */
  drainChanges() {
    const changes = this.#changes;
    this.#changes = [];
    if (changes.length > 0 && this.#idleLooks > 0) {
      changes[0] = { ...changes[0], idle_looks: this.#idleLooks };
      this.#idleLooks = 0;
    }
    return changes;
  }

  /**
   * XState's inspection: each transition that moved to a state.
   */
  #record(event) {
    if (event.type !== '@xstate.microstep') return;
    const transitions = event._transitions ?? [];
    for (const transition of transitions) {
      const target = transition.target?.[0];
      if (!target) continue;
      this.#changes.push({
        from: transition.source.key, to: target.key,
        on: transitionLabel(transition.eventType, transition.guard), at: new Date(this.#clock()).toISOString(),
      });
    }
  }

  /**
   * One step: the machine plays it; the record is what the `play` actor
   * reported.
   */
  async step() {
    this.lastRecord = null;
    this.#actor.send({ type: 'STEP' });
    await this.#settle();
    // What the understudy just did is not news either: its own moves must
    // not make it wonder whether its turn has come round again.
    await this.#markSeen();
    return this.lastRecord;
  }

  /**
   * Which state the machine is in - for logs and tests.
   */
  get state() {
    return this.#actor.getSnapshot().value;
  }

  async #settle() {
    return waitFor(this.#actor, (snapshot) => snapshot.status !== 'active' || !snapshot.hasTag('busy'));
  }

  /**
   * What the app shows now, and what is NEW since the last look. The
   * first look only SEEDS - starting mid-way is not a sudden change -
   * but it still marks THIS MOMENT as the reference point a later quiet
   * check measures from. Without that, a table whose only relevant talk
   * (a dice roll, an announcement) landed before this seat's first look
   * could never be noticed quiet either: `changed` stays false forever
   * (nothing it hasn't already seen), and `quietFor` never starts
   * counting because it has no "since when" to count from - the seat
   * would wait forever for a change it can, by definition, never see
   * (recard D158, found running two bots against a table whose setup
   * all landed within the first second or two).
   */
  async #look() {
    const { target, name } = this.#services;
    const view = await target.view();
    const talk = await target.talk();
    const now = this.#clock();
    const seq = view.seq ?? null;
    const seen = this.#seen;
    if (seen.talk === null) {
      // `lastTalkAt` stays null (nobody has spoken WHILE this seat was
      // watching - the existing talk predates it), so `quietFor` grows
      // from `changedAt` starting now, same as after any real change.
      Object.assign(seen, { talk: talk.length, seq, changedAt: now });
      return { view, talk, heard: [], changed: false, quietFor: 0, now };
    }
    const heard = talk.slice(seen.talk).filter((entry) => entry.name !== name);
    const hasMoved = seq !== seen.seq;
    if (hasMoved) seen.changedAt = now;
    if (heard.length > 0) seen.lastTalkAt = now;
    Object.assign(seen, { talk: talk.length, seq });
    const isQuietSinceChange = seen.changedAt !== null && (seen.lastTalkAt === null || seen.lastTalkAt < seen.changedAt);
    return { view, talk, heard, changed: hasMoved || heard.length > 0, quietFor: isQuietSinceChange ? now - seen.changedAt : 0, now };
  }

  /**
   * After the understudy asked something, the question and its
   * answer are not news to judge again - that is how an unsure judgment
   * would ask forever (US-128).
   */
  async #markSeen() {
    const talk = await this.#services.target.talk();
    const view = await this.#services.target.view();
    this.#seen.talk = talk.length;
    this.#seen.seq = view.seq ?? null;
    this.#seen.lastTalkAt = this.#clock();
  }
}
