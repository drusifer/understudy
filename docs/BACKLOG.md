# Backlog

Groomed by Cypher from the sprint 1 retro (2026-10-15). Owner, 2026-10-15: recard is no longer
a goal - no migration work. README done in the post-sprint docs groom. Not yet sized or ordered beyond
"Next" vs "Later".

## Sprint 2
Done - see `CHANGELOG.md` (HTTP target; hookless pages with the generic page app).

## Sprint 3 (owner, 2026-10-15) - MCP target for sketches
- **MCP target** (`kind: 'mcp'`) - understudy is an MCP *client* and plays any MCP server: a look
  lists its tools/resources (plus the last call's result), a move is a tool call; a tool error is
  the app's answer. Built on the off-the-shelf `@modelcontextprotocol/sdk` client (stdio and
  streamable HTTP transports). **Both** local (stdio command) and remote (HTTP url) servers.
- **MCP config = the de facto `mcpServers` shape** (Claude Desktop / Claude Code `.mcp.json`):
  local `command`/`args`/`env`, remote `type: http` + `url`/`headers` (Claude Code's variant).
  Two ways to name the server, both supported: a **file reference**
  (`target: { kind: mcp, config: .mcp.json, server: via }`) or the **same entry inline** in YAML.
  Secrets as `${VAR}` from the environment.
- **Tool arguments** (owner decided, 2026-10-15): a sketch may list fixed calls (tool + args) as
  moves; any tool not listed, or listed with open args, gets its arguments filled by Jev from the
  tool's JSON input schema.
- **Remote auth** (owner decided, 2026-10-15): token headers only - `headers:` in the mcpServers
  entry with `${VAR}` from the environment. OAuth is out of scope (see Later).
- **One YAML per sketch** (owner asked, 2026-10-15): a single `sketch.yaml` holding name, target
  (incl. the MCP server inline or by `config:` reference), player params, default steps, `turn:`
  (statechart) and `questions:`. Targets with generic apps (page, mcp) need no code; others name a
  hooks module (`app: hooks.mjs`). **Owner decided (2026-10-15):** `sketch.yaml` is the ONLY
  format - sprint 3 converts examples/cli, web, http and removes the old part + `adapter.mjs` layout
  (no back-compat).
- Not an MCP *server* for understudy (owner, 2026-10-15). `seed/recard/tools/mcp/harnessServer.mjs`
  is therefore not a starting point.

## Later
- OAuth for remote MCP servers (sprint 3 does token headers only). (Morpheus)
- Typing into text fields on pages (needs a source for the text). (Morpheus)
- Auth headers / cookies for the HTTP target. (Morpheus)
- Make the first-move and stall limits configurable (`--wait`). (Neo)
- `npm test` with `--test-timeout`, so a hanging test fails instead of freezing the suite. (Trin)
- `check` could warn when a generic-page part has no `showing` guard. (Smith)
- Scenario file / multi-actor runs (only if useful for understudy itself).
- A second Ctrl-C should say "stopped at once" instead of whatever error closing causes. (Neo)
- `unexpected error:` should say how to get the stack (e.g. `UNDERSTUDY_DEBUG=1`). (Neo)
- `make test-live` should check each run's final `outcome`, not only the exit code. (Trin)
- DEF-04: the no-key message repeats "understudy" after the `understudy:` prefix. (Smith)
- `--quiet` to drop the per-step stderr lines. (Smith)
