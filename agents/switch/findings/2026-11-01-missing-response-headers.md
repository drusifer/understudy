# SEC-003: Console responses carry no browser security headers (`src/dashboard/server.py` `_send`)

- **Severity:** Low — the page loads only its own files and writes text with `textContent`, so no script injection path was found; headers are a second line of defence.
- **Status:** Open
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** `src/dashboard/server.py` `Handler._send` and `_follow`
- **Class / reference:** CWE-693 (protection mechanism failure); OWASP Secure Headers

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Neo | Add `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'` and `Referrer-Policy: no-referrer` to every response, with one test | Before Sprint 22 UND-79 starts (a start button makes clickjacking matter) |

## Evidence

- **Reproduce / detect:** `curl -si http://127.0.0.1:4180/ | head -8` shows none of the three headers (a `HEAD` request is answered 501, so `-I` cannot be used).
- **Observed:** response headers are Content-Type, Content-Length and Cache-Control only. `page.js` builds nodes with `textContent`; its one `innerHTML` assignment is a constant string.
- **Confidence:** High.

## Impact and Reachability

Without `frame-ancestors`, another site could frame the console; harmless while read-only, relevant once Play exists. Runtime scope.

## Recommendation

- **Fix:** three header lines in `_send` and the stream response.
- **Verify:** a unit test reads the headers from `/` and `/api/runs`.
- **Alternatives rejected:** none.

## Risk Acceptance

Not accepted.
