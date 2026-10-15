# seed/ - recard files waiting to be generalized

Verbatim copies from recard at commit `d817d3c` (2026-10-15), kept at their original
recard paths so their imports still read correctly. They do NOT run here: they import
recard-only modules (`src/gameMasterInvite.js`, `src/identity.js`, `src/peerOptions.js`,
`tools/localPeerServer.mjs`, `tools/gin/*`, ...).

Each one is generalized into `src/` per `docs/EXTRACTION_MAP.md` section 2, then deleted
from here. When `seed/` is empty, delete it.

| Seed file | Becomes |
|---|---|
| `tools/mcp/harnessServer.mjs` | generic MCP layer (later sprint) |
| `tools/jev/tableFile.mjs`, `tableSetup.mjs` (+ tests) | scenario file (later sprint, multi-actor) |
| `tools/jev/games.mjs`, `gameFiles.mjs` | reference for how a part's files are found and loaded |
| `tools/turnRelay.mjs` | only if understudy owns WebRTC transport |

Done: `tools/jev/runner.mjs` -> `src/run.mjs` (sprint 1 phase 4); `tools/botRequests.mjs` dropped (recard-only); `tests/harness/multiplayer.mjs` -> `src/targets/page.mjs` (phase 6).
