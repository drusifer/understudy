# Security Review: the console and the run pipeline (baseline)

- **Verdict:** No blocking findings
- **Date / reviewer:** 2026-11-01 / Switch
- **Target and version:** `understudy dashboard` (`src/dashboard/server.py`, `page.js`, `page.html`), the dashboard command in `src/sketch/cli.py`, run output (`src/sketch/run.py`, `src/paths.py`), Jev capture (`src/sketch/sources/capture.py`), dependency set (`pyproject.toml`, `uv.lock`); `main` at 5cd0927 plus `sprint-22` commit 13d7bbf
- **Assurance level:** L2 standard — a network-reachable, unauthenticated server that reads files and (from Sprint 22) will start processes, handling the owner's private financial exports
- **Findings:** 4 total: Critical 0, High 0, Medium 1, Low 2, Info 1
- **Related work:** Sprint 21 UND-74, decision 4 (listen on 0.0.0.0); Sprint 22 UND-79; ADR-0048; UND-54 (private output rule)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Neo | Fix SEC-001 (cap event streams, idle limit) and SEC-003 (security headers) | Before Sprint 22 UND-77 merges / before UND-79 starts |
| Switch | Threat-model the start-run access secret (`*sec threat sprint 22`) | Sprint 22 design gate, before any UND-79 code |
| User | Renew or end the SEC-002 acceptance | By 2026-12-01 or when UND-79 ships |
| Tank | Add a `security-scan` make target (dependency audit) and record it in `docs/SDLC.md` | Next sprint; until then dependencies are unaudited |

## Scope and Threat Model

- **In scope / out of scope:** In: the console server and page, the dashboard CLI command, how a run writes its folder, the capture cache and the output-path rule, and the dependency list. Out: the Jev service itself, the owner's machine and network, and the content of the sketches' stages beyond how they write files (reviewed in earlier sprints' work only as far as the output rule).
- **Assets worth protecting:** the owner's real transaction exports and the run outputs built from them (private); the TypeSafe API key; the console's availability; later, the ability to start processes on the machine.
- **Entry points and trust boundaries:** HTTP GET requests from any host on the network to port 4180; command-line arguments of the owner; sketch files and CSVs the owner supplies (trusted, owner-written); Jev answers (untrusted text, constrained to a listed set before use); the `.env` file (trusted, git-ignored).
- **Threats considered:** Spoofing and Elevation of privilege (no authentication today: SEC-002; start runs later); Tampering (no write route exists); Information disclosure (path escape tested; run data exposed to the network: SEC-002, SEC-004); Denial of service (SEC-001); Repudiation not applicable (single owner, no accounts); injection in the page (checked: text is written with `textContent`).

## Method and Coverage

- **Reviewed by:** manual read of `server.py` (routing, static allow-list, run-id check, event stream), `page.js` (every DOM write), the dashboard branch of `cli.py`, `run.py` event writing, and the existing tests; a hands-on probe of 200 concurrent event streams; `curl` against the running console.
- **Tool results:** `bobp make secrets` (gitleaks over history and tracked changes): no leaks found, 2026-11-01 11:13. Dependency audit: **not run**, because no `security-scan` target exists and no audit tool is installed (see Tank action). `ruff` (part of `bobp make check`) passes.
- **Not covered:** dependency vulnerabilities in `uv.lock`; the Jev capture file contents (they hold the owner's private values and live under git-ignored `.understudy/`); the `understudy run` stages other than their output paths; browser behaviour beyond reading `page.js`; the Sprint 22 start-run design (not designed yet).

## Area Checklist

| Area | What to check | Result |
|---|---|---|
| Input handling and injection | Untrusted input validated at the boundary; no shell, SQL, path, template, or deserialization injection | Pass: run ids match `run-[0-9A-Za-z-]+` and must be a directory under the root; static names come from one regex allow-list; `..`, `%2F` and unknown files return 404 (tested); no shell or SQL is built from a request |
| Authentication and sessions | Credential handling, session lifetime, token storage, brute-force limits | SEC-002 (none by owner's decision; secret designed in Sprint 22) |
| Authorization and access control | Every sensitive action checks the caller; least privilege | N/A today: no sensitive action exists over HTTP (GET only, `HEAD` and other methods answer 501); becomes in scope with UND-79 |
| Secrets and cryptography | No secrets in code, logs, or history | Pass: gitleaks clean; the API key is read from the environment or `.env`, never printed; the console never reads `.env` |
| Data protection and privacy | Sensitive data minimized and not over-logged | Pass: `summary.json` holds counts only and `events.jsonl` holds stage names and reasons; sink files are never served; SEC-004 notes the sketch path |
| Error handling and logging | Errors leak no internals; logs free of secrets | Pass: the server logs nothing (`log_message` is silent) and a bad path returns a one-word 404; a failed stage's reason (an exception message) appears in the console, which could include a file name |
| Dependencies and supply chain | Pinned versions, lockfile audited, vulnerable packages triaged | Incomplete: versions are pinned and locked; not audited (no tool or target) |
| Configuration, build, and CI | Safe defaults; minimal permissions; no debug in release | SEC-003 (no browser security headers); the listening address is `0.0.0.0` by the owner's choice (SEC-002); there is no CI |
| Files, processes, and network | Safe paths; subprocess use; outbound requests; resource limits | SEC-001 (no limit on concurrent streams); output refused under `data/` and any tracked folder (UND-54 AC4, tested); the console starts no subprocess yet; the only outbound call is to Jev, by the run, never by the console |
| Business logic and abuse cases | Workflows cannot be reordered, replayed, or abused for gain | Pass: the console cannot change or create anything today; replay of a capture cannot go live (tested) |

## Findings

| ID | Title | Severity | Status | Owner |
|---|---|---|---|---|
| [SEC-001](../findings/2026-11-01-sse-streams-unbounded.md) | Event streams are unbounded | Medium | Open | Neo |
| [SEC-002](../findings/2026-11-01-console-open-on-network.md) | Console readable by everyone on the network | Low | Accepted risk (expires 2026-12-01) | User |
| [SEC-003](../findings/2026-11-01-missing-response-headers.md) | No browser security headers | Low | Open | Neo |
| [SEC-004](../findings/2026-11-01-sketch-path-in-events.md) | Sketch path as typed is recorded and shown | Info | Open | Neo |

## Root Causes and Recommendations

The console was built read-only for one owner on a trusted machine and then opened to the network, so three of the four findings are the same gap: the server has no notion of who is asking or how many. The smallest systemic fix is one small layer in `make_handler` (a stream cap, three headers) now, and the access secret in Sprint 22 before anything that starts a process is added. A `security-scan` target would give the dependency area a real result.

## Sign-off

- **Re-review needed:** Yes, at the Sprint 22 design gate and again after UND-79 is built
- **Risk acceptance:** SEC-002 accepted by the owner on 2026-11-01, expires 2026-12-01; no other acceptance
- **Verification:** Pending: SEC-001 and SEC-003 fixes with tests; the dependency audit once a target exists
