// Sprint 6 (ARCH §3, ADR-0023): the dashboard as one thing - its server, and
// the runner and settings behind the server's actions.

import { startDashboard } from './server.mjs';

/**
 * Serves the console for `folder` until closed.
 * @param {{ folder: string, port?: number, host?: string, environment?: object, stderr?: { write: Function } }} options
 */
export async function serveDashboard({ folder, port, host }) {
  return startDashboard({ folder, port, host });
}
