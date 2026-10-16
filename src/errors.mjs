// The two ways a command can fail (ADR-U5). The CLI prints either one as
// `understudy: <message>` with no stack trace; only the exit code differs.

/**
 * Refused before anything started - bad arguments, a broken sketch, no
 * key, no browser. Exit 2.
 */
export class UsageError extends Error {}

/**
 * The run started and could not finish - the app exited, the step cap
 * was reached, Jev answered off the list twice. Exit 1.
 */
export class RunError extends Error {
  /**
   * @param {string} message
   * @param {{ outcome?: string, cause?: unknown }} [options] `outcome` is
   *   what the run's final log line says (`step-cap`, `off-list`, ...).
   */
  constructor(message, { outcome = 'error', cause } = {}) {
    super(message, { cause });
    this.outcome = outcome;
  }
}
