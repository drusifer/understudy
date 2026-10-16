// Sprint 6 (ARCH §3, ADR-0023): the dashboard as one thing - its server, and
// the runner (and, from Phase 6, the settings) behind the server's actions.

import { createHub, startDashboard } from './server.mjs';
import { createRunner } from './runner.mjs';

/**
 * Serves the console for `folder` until closed; closing stops any run.
 * @param {{ folder: string, port?: number, host?: string, environment?: object, runOptions?: object }} options
 *   `runOptions` go to every run (tests: a Jev double).
 */
export async function serveDashboard({ folder, port, host, environment = process.env, runOptions = {} }) {
  const hub = createHub();
  const runner = createRunner({ folder, hub, environment, runOptions });
  const server = await startDashboard({
    folder, port, host, hub,
    actions: { play: (body) => runner.play(body), stop: () => runner.stop() },
  });
  return {
    ...server, runner,
    async close() {
      await runner.close();
      await server.close();
    },
  };
}
