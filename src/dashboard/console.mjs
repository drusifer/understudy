// Sprint 6 (ARCH §3, ADR-0023): the dashboard as one thing - its server, and
// the runner and the settings behind the server's actions.

import { createHub, startDashboard } from './server.mjs';
import { createRunner } from './runner.mjs';
import { createSettings } from './settings.mjs';

/**
 * Serves the console for `folder` until closed; closing stops any run.
 * @param {{ folder: string, port?: number, host?: string, environment?: object, runOptions?: object }} options
 *   `runOptions` go to every run (tests: a Jev double).
 */
export async function serveDashboard({ folder, port, host, environment = process.env, runOptions = {} }) {
  const hub = createHub();
  const runner = createRunner({ folder, hub, environment, runOptions });
  const settings = createSettings({ folder });
  const server = await startDashboard({
    folder, port, host, hub,
    actions: {
      play: (body) => runner.play(body),
      stop: () => runner.stop(),
      // UND-32 AC5: no edits while a run is going.
      edit: async (body) => (runner.isRunning() ? { status: 409, value: { problem: 'stop the run before changing the settings' } } : settings.edit(body)),
      // UND-32 AC4: off stops a run; on puts the factory settings back.
      async power({ on }) {
        if (!on) {
          await runner.close();
          return { status: 200, value: { on: false } };
        }
        return { status: 200, value: { on: true, restored: settings.restore() } };
      },
    },
  });
  return {
    ...server, runner,
    async close() {
      await runner.close();
      await server.close();
    },
  };
}
