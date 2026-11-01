# SEC-001: Event streams in the console are unbounded (`src/dashboard/server.py` `follow`)

- **Severity:** Medium — anyone on the network can open streams until the Pi runs out of threads or memory and the console stops answering; only the console is affected, not the run files.
- **Status:** Fixed (2026-11-01): `MAX_STREAMS = 32` (a further watcher gets 503 "too many watchers"), `IDLE_SECONDS = 600` ends a silent stream; tests `StreamLimitTest`. Re-probe: 200 streams now hold 34 threads (was 202) and fall back to 2 when the clients close.
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** `src/dashboard/server.py` `follow()` and `ThreadingHTTPServer` (one thread per request, no cap)
- **Class / reference:** CWE-770 (allocation of resources without limits)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Neo | Cap concurrent event streams (for example 32; a further request gets 503 "too many watchers"), end a stream for a run with no new line for 10 minutes, and add a test for both | Before Sprint 22 UND-77 merges |
| Trin | Re-run the 200-stream probe below and confirm the cap holds | After Neo's fix |

## Evidence

- **Reproduce / detect:** start the server over a folder holding one run with no `run_finished` line, open 200 connections to `/events/<run-id>`, and count threads (`threading.active_count()`).
- **Observed:** 2 threads before; 202 with 200 open streams; back to 2 after the clients closed. A run that crashed without `run_finished` keeps its stream open for as long as the client stays.
- **Confidence:** High (measured on this machine on 2026-11-01).

## Impact and Reachability

Reachable from any host on the network because the console listens on 0.0.0.0 (Sprint 21 decision 4) with no login. Runtime scope. Cost to the attacker is one open socket per thread; cost to the machine is a thread and a file read every half second per stream.

## Recommendation

- **Fix:** a module constant `MAX_STREAMS` and a counter guarded by a lock in `make_handler`; return 503 beyond it. Give `follow()` an idle limit.
- **Verify:** the unit test opens `MAX_STREAMS + 1` streams and sees one 503; the 200-stream probe shows at most `MAX_STREAMS` threads.
- **Alternatives rejected:** swapping `http.server` for an async framework (a new dependency for a one-user console).

## Risk Acceptance

Not accepted.
