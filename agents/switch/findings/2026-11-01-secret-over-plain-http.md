# SEC-005: The access secret travels over plain HTTP on the network (Sprint 22 design, `ARCH_SPRINT22.md` section 6)

- **Severity:** Medium — anyone who can read traffic on the same network (shared Wi-Fi, a compromised device) can copy the secret and start allowed sketches; the damage is bounded to Jev cost, CPU and the run folders, because the sketches and their output location are fixed.
- **Status:** Open (design finding; no code exists yet)
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** the proposed `X-Understudy-Secret` header on `POST /api/start` and `/api/stop`; the console serves HTTP only
- **Class / reference:** CWE-319 (cleartext transmission of sensitive information)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| User | Choose: (a) accept the risk on the home network, with an expiry (at most 90 days); (b) turn on TLS with a certificate the owner supplies (`--tls-cert`, `--tls-key`, standard-library `ssl`); or (c) allow Play only from the machine itself (loopback) | Before UND-79 is built |
| Morpheus | Record the choice in ARCH_SPRINT22 and ADR-0049 | After the owner chooses |

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

Not accepted.
