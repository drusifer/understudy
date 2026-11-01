# SEC-009: A negative or unreadable `Content-Length` made the console wait on the connection (`src/dashboard/server.py` `_body`)

- **Severity:** Low — only reachable by someone who already holds the secret, and it ties up one thread; found while attacking the POST routes.
- **Status:** Fixed (2026-11-01, Sprint 22 phase 5): the length must be digits, else 400 and the connection closes; test `test_a_negative_or_unreadable_content_length_is_400_not_a_wait_for_more_data`
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** `ConsoleHandler._body` in the first build
- **Class / reference:** CWE-400 (uncontrolled resource consumption), CWE-20 (improper input validation)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Neo | Done: validate the header, test it, close the connection | Done |

## Evidence

- **Reproduce / detect:** read `rfile.read(-1)` in the first build: a negative length reads until the client closes.
- **Observed:** after the fix, `-1`, `abc` and `1.5` each get a 400 at once (unit test and the outside attack in the UAT plan).
- **Confidence:** High.

## Impact and Reachability

One handler thread could be held open per request by a client with the secret; the 32-stream cap does not cover POST threads. Runtime scope.

## Recommendation

- **Fix:** done as above.
- **Verify:** the tests above.
- **Alternatives rejected:** a socket timeout for every request (more behavior to explain for the same protection).

## Risk Acceptance

Not accepted.
