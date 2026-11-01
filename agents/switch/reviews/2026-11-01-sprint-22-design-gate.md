# Security Review: Sprint 22 design (start, stop and replay runs from the console)

- **Verdict:** No blocking findings
- **Date / reviewer:** 2026-11-01 / Switch
- **Target and version:** `docs/sprints/ARCH_SPRINT22.md` and `USER_STORIES_SPRINT22.md` (design only; no code yet), on `sprint-22`
- **Assurance level:** L2 standard — a network-reachable, unauthenticated-for-reads server that will start local processes; the secret and the allow-list are the whole control
- **Findings:** 2 total: Critical 0, High 0, Medium 1 (SEC-005), Low 1 (SEC-006), Info 0
- **Related work:** SEC-001 to SEC-004, `2026-11-01-console-and-run-pipeline.md`, UND-79, ADR-0049 (to record)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| User | Decide SEC-005: accept on the home network (with an expiry), provide a TLS certificate, or allow Play from this machine only | Before UND-79 is built |
| Morpheus | Add the SEC-006 rules (root check on file values, child cap 4, Origin check, replay id check) to ARCH_SPRINT22 | Before UND-79 is built |
| Switch | Re-review the UND-79 diff against this threat model | After the build, before Morpheus's code review |

## Scope and Threat Model

- **In scope / out of scope:** In: the start, stop, replay and sketch-list routes, the secret, the subprocess launch, the Jev list, and the `run.json` additions. Out: the content of the owner's sketches and stages; TLS certificate issuance.
- **Assets worth protecting:** the right to start processes on the machine; the Jev API key and its cost; the owner's input files; run folders.
- **Entry points and trust boundaries:** POST requests from the network (untrusted until the secret is checked); `--with` values and sketch names in the request (untrusted); the sketches folder (trusted, owner-written); the child process (trusted code, untrusted arguments).
- **Threats considered:** Spoofing (wrong or stolen secret: SEC-005); Tampering (request fields altering the command line: argument list with no shell, name and path allow-lists); Information disclosure (path to arbitrary files, error text: SEC-006; the Jev list shows levels and probabilities only); Denial of service (many starts: one per sketch plus a global cap of 4; many streams: SEC-001 fixed); Elevation of privilege (running a sketch outside the folder: refused by resolved-path check; killing an arbitrary process: Stop uses only processes the console itself started, looked up by run id, never a pid from the request); CSRF (custom header plus an Origin check, no CORS headers); Repudiation not applicable (one owner).

## Method and Coverage

- **Reviewed by:** manual read of the design against OWASP ASVS V2/V4/V12 themes (authentication, access control, files) and the STRIDE list above; the existing `server.py` and `cli._values` read for what the new routes would reuse.
- **Tool results:** no scanner applies to a design; `bobp make security-scan` clean on 2026-11-01 for the current dependencies.
- **Not covered:** the implementation (none yet); TLS configuration details; behaviour on a network with other hostile devices beyond SEC-005.

## Area Checklist

| Area | What to check | Result |
|---|---|---|
| Input handling and injection | Untrusted input validated at the boundary | Pass (design): argument list, no shell; names matched to the sketch's own; replay ids by regex; SEC-006 adds the file-root rule |
| Authentication and sessions | Credential handling, token storage, brute-force limits | SEC-005 (cleartext); 32-byte random secret, constant-time compare, per-address pause, `sessionStorage` only |
| Authorization and access control | Every sensitive action checks the caller | Pass (design): every POST handler runs behind the one secret check; reads stay open by the owner's decision (SEC-002) |
| Secrets and cryptography | No secrets in code, logs, or history | Pass (design): generated at start, printed to the terminal once, never in URL, page, log or event; Jev key unchanged |
| Data protection and privacy | Sensitive data minimized | Pass (design): `with` values are file paths (SEC-004 note); the Jev list never shows the text Jev read |
| Error handling and logging | Errors leak no internals | SEC-006 (a stage error may name a file line); 401/403/409 bodies are one short sentence |
| Dependencies and supply chain | Pinned, audited | Pass: no new dependency; scan clean |
| Configuration, build, and CI | Safe defaults | Pass (design): headers already set (SEC-003 fixed); Play disabled until the secret is entered |
| Files, processes, and network | Safe paths; subprocess use; limits | Pass with SEC-006 rules: resolved sketch path inside the folder, symlinks followed, `.yaml` only, `start_new_session` and process-group stop, child cap |
| Business logic and abuse cases | Cannot be reordered, replayed or abused | Pass (design): one run per sketch, 409 on a second; a replayed POST just starts the same allowed run |

## Findings

| ID | Title | Severity | Status | Owner |
|---|---|---|---|---|
| [SEC-005](../findings/2026-11-01-secret-over-plain-http.md) | The secret travels over plain HTTP | Medium | Open | User |
| [SEC-006](../findings/2026-11-01-with-values-reach-any-file.md) | `--with` file values could point anywhere | Low | Open | Morpheus |

## Root Causes and Recommendations

Both findings come from adding control to a server that was designed to read only. The smallest systemic answer is the rule set already in the design plus the SEC-006 additions, and an explicit owner decision on transport (SEC-005): the design is sound for a trusted home network and weak anywhere else.

## Sign-off

- **Re-review needed:** Yes, after UND-79 is built
- **Risk acceptance:** None recorded yet; SEC-002 (reads) stays accepted until 2026-12-01
- **Verification:** Pending: owner's decision on SEC-005; the UND-79 diff review
