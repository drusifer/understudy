# Owner decisions: Sprint 22

1. (2026-11-01) Sprint 22 is the feature gap sprint from `UX_GAPS_SPRINT22.md`: the console both **watches and starts runs** (themes A, B, C and D, about 26 points). Because the console listens on 0.0.0.0, starting runs needs access control: designed at Switch's security design gate before any code.
2. (2026-11-01) Starting runs from the console: the access secret travels over plain HTTP on the home network; the owner accepts the risk until 2027-01-30 (SEC-005). No TLS in Sprint 22.
3. (2026-11-02) Runs live in `.understudy/runs` by default (git-ignored, private, beside the Jev captures), not under `build/`, so `bobp make clean` cannot delete them. Existing runs are moved there.
