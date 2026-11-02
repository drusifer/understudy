# SEC-002: The console is readable by everyone on the network (`understudy dashboard`, 0.0.0.0, no login)

- **Severity:** Low — the console serves run logs, stage names, counts and `summary.json`, never the sink files; exploit needs only network reach.
- **Status:** Accepted risk
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** `src/dashboard/server.py` `serve()` default host `0.0.0.0`; no authentication on any route
- **Class / reference:** CWE-306 (missing authentication), CWE-200 (information exposure)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| User | Renew or end the acceptance | By 2026-12-01, or when the console can start runs (Sprint 22 UND-79), whichever is first |
| Switch | Design the access secret for start, stop and replay at the Sprint 22 design gate | Before any UND-79 code |

## Evidence

- **Reproduce / detect:** `curl http://<this machine>:4180/api/runs` from another host returns the list of runs with no credentials (checked from this machine against its LAN address on 2026-11-01: HTTP 200).
- **Observed:** all `/api/runs*` and `/events/*` routes answer anyone; only GET exists; only allow-listed page files and run folders are reachable; `../` and `%2F` escapes return 404 (tested in `tests/python/test_dashboard.py`).
- **Confidence:** High.

## Impact and Reachability

Anyone on the same network can read what runs ran, when, which stages, how many Jev requests and the stage failure reasons. No transaction values are in these files by design (counts only). Reachable now. Becomes more serious once starting runs is added.

## Recommendation

- **Fix:** for watching, none needed on a trusted home network; for starting runs, require the access secret (Sprint 22 UND-79 criterion 8). A `--host` option for loopback only is the cheap alternative if the network stops being trusted.
- **Verify:** an unauthenticated start request is refused (UND-79 test).
- **Alternatives rejected:** a login page for watching (a second mechanism for no stated need).

## Risk Acceptance

Accepted by the owner on 2026-11-01 (decision 4 of `docs/sprints/OWNER_DECISIONS_SPRINT21.md`: "use 0.0.0.0"), **expires 2026-12-01**: scope is read-only watching on the home network; re-check when UND-79 ships or the machine joins another network.
