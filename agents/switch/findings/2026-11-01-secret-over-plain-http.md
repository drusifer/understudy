# SEC-005: The access secret travels over plain HTTP on the network (Sprint 22 design, `ARCH_SPRINT22.md` section 6)

- **Severity:** Medium — anyone who can read traffic on the same network (shared Wi-Fi, a compromised device) can copy the secret and start allowed sketches; the damage is bounded to Jev cost, CPU and the run folders, because the sketches and their output location are fixed.
- **Status:** Accepted risk (design finding; no code exists yet)
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** the proposed `X-Understudy-Secret` header on `POST /api/start` and `/api/stop`; the console serves HTTP only
- **Class / reference:** CWE-319 (cleartext transmission of sensitive information)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| User | Renew or end the acceptance (options were: accept, TLS with `--tls-cert` and `--tls-key`, or Play from this machine only) | By 2027-01-30 or at the re-check trigger below |
| Morpheus | Record the choice in ARCH_SPRINT22 and ADR-0049 (done 2026-11-01) | Done |

## Evidence

- **Reproduce / detect:** design read: the console is `http.server` on 0.0.0.0 with no TLS; the proposed secret is a request header.
- **Observed:** nothing is encrypted between the browser and the console.
- **Confidence:** High (follows directly from the design).

## Impact and Reachability

Reachable by an attacker who is on the network path. They need the secret, which appears in every Play and Stop request. With it they can start any sketch in the allowed folder with `--with` values of their choosing (subject to SEC-006) and stop runs.

## Recommendation

- **Fix:** option (b) is the only one that protects the secret; (c) removes the exposure by removing remote Play; (a) leaves it. Smallest code: (b) is about ten lines and two flags.
- **Verify:** with TLS on, `curl` over `http://` is refused and a sniffed request is not readable; with (c), a POST from another address is 403.
- **Alternatives rejected:** a login page (the secret would still cross the network in the clear).

## Risk Acceptance

Accepted by the owner on 2026-11-01, option (a), **expires 2027-01-30** (90 days): reason, the console is used on a trusted home network from the owner's own devices; scope, the start, stop and replay secret over plain HTTP; re-check trigger, the expiry, or the machine or the owner's devices joining any other network, or any request to expose the console beyond the home network, whichever is first.
