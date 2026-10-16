// Sprint 4 UND-15 (ARCH §4 "Pause gate", ADR-0016): pause, step and resume
// a live run from the watch page. The run loop asks `beforeMove()` before
// each move - the Jev request is inside the move, so a paused run asks Jev
// nothing. Step lets exactly one move through; Ctrl-C lets the loop go to
// stop. Time spent paused is kept so the idle limits count running time only.

/**
 * @param {{ isPaused?: boolean, clock?: () => number, onChange?: (state: { paused: boolean, waiting: boolean }) => void }} [options]
 */
export function createGate({ isPaused = false, clock = Date.now, onChange = () => {} } = {}) {
  const state = { isPaused, isEnded: false, isStopping: false, allowOne: false, waiter: null, since: isPaused ? clock() : null, total: 0 };
  const changed = () => onChange({ paused: state.isPaused, waiting: state.waiter !== null });
  const wake = () => {
    const waiter = state.waiter;
    state.waiter = null;
    waiter?.();
  };
  /**
   * Before a move: at once when running; when paused, after a step, a
   * resume, or Ctrl-C.
   * @returns {Promise<'go'|'stop'>}
   */
  const beforeMove = async () => {
    for (;;) {
      if (state.isStopping) return 'stop';
      if (!state.isPaused) return 'go';
      if (state.allowOne) {
        state.allowOne = false;
        return 'go';
      }
      await new Promise((resolve) => {
        state.waiter = resolve;
        changed();
      });
    }
  };
  return {
    isPaused: () => state.isPaused,
    beforeMove,
    pause() {
      if (state.isEnded || state.isPaused) return false;
      Object.assign(state, { isPaused: true, since: clock(), allowOne: false });
      changed();
      return true;
    },
    step() {
      if (state.isEnded || !state.isPaused) return false;
      state.allowOne = true;
      wake();
      changed();
      return true;
    },
    resume() {
      if (state.isEnded || !state.isPaused) return false;
      state.total += clock() - state.since;
      Object.assign(state, { isPaused: false, since: null, allowOne: false });
      wake();
      changed();
      return true;
    },
    /**
     * Ctrl-C: whoever waits goes on, to stop.
     */
    stop() {
      // Only a paused run stops at once; a running one stops as it always
      // does, at its next safe state (so watching changes nothing).
      if (!state.isPaused) return;
      state.isStopping = true;
      wake();
    },
    end() {
      state.isEnded = true;
    },
    /**
     * How long the run has been paused in all, so far.
     */
    pausedMs: () => state.total + (state.isPaused ? clock() - state.since : 0),
  };
}

/**
 * The gate of a run nobody watches: always open.
 */
export const OPEN_GATE = {
  isPaused: () => false,
  beforeMove: async () => 'go',
  pause: () => false,
  step: () => false,
  resume: () => false,
  stop() {},
  end() {},
  pausedMs: () => 0,
};
