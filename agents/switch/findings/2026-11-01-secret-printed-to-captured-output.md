# SEC-008: The access secret was printed to the terminal, where `bobp make` copies output into the tracked chat (`src/dashboard/server.py`)

- **Severity:** Medium — `bobp make <target>` captures a command's output into `build/build.out` and posts its tail to `agents/CHAT.md`, which is tracked by git and pushed; the secret would have been published to the repository history.
- **Status:** Fixed (2026-11-01, Sprint 22 phase 5): the secret is saved to `.understudy/dashboard.secret` (git-ignored, mode 0600, replaced at every start) and the output names only that file
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** the first build of `serve_forever` / `announce` in `src/dashboard/server.py`
- **Class / reference:** CWE-532 (insertion of sensitive information into a log file)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Neo | Done: `save_secret`, `announce` rewritten, tests `AnnounceTest` (file mode 0600, secret absent from output, the file git-ignored) | Done |
| Switch | Re-check at the Phase 6 review that the page and the logs never hold the secret | Phase 6 |

## Evidence

- **Reproduce / detect:** design read plus the chat log: earlier `bobp make` build lines in `agents/CHAT.md` show the last lines of command output. With the first build, `bobp make dashboard` would have written the secret into that tail when the console stopped.
- **Observed:** after the fix, the real console's output contains the path and not the secret (`secret in the output? False`), and the file has mode 0600.
- **Confidence:** High (the capture behavior is visible in the chat history).

## Impact and Reachability

Anyone who could read the repository or its remote could start allowed sketches (SEC-005's scope) until the console was restarted; each restart makes a new secret, so the exposure is limited to one console session.

## Recommendation

- **Fix:** done as above.
- **Verify:** `tests/python/test_launcher.py::AnnounceTest`; the live check in the UAT plan.
- **Alternatives rejected:** printing only on a terminal (a terminal can still be logged); asking `bobp make` to redact (a rule outside this repository).

## Risk Acceptance

Not accepted.
