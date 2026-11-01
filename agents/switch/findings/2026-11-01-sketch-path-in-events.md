# SEC-004: Events show the sketch path as typed, which may include a home directory (`src/sketch/run.py` `run_started`)

- **Severity:** Info — a path is not a secret, but it tells a network reader the user name and folder layout.
- **Status:** Open
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** `src/sketch/run.py:198` (`record.emit("run_started", sketch=str(sketch.path), ...)`), shown by the console printer
- **Class / reference:** CWE-200 (information exposure), low

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Neo | Record the sketch file name relative to the project root (or the name alone) instead of the path as typed, with a test | With Sprint 23 UND-81 (the event stream is being changed then) |

## Evidence

- **Reproduce / detect:** `head -1 build/runs/<run>/events.jsonl` shows `"sketch": "examples/household/household.yaml"` for a relative path, and the absolute path if one was typed.
- **Observed:** the stored value is exactly what the user typed.
- **Confidence:** High.

## Impact and Reachability

Visible to anyone who can reach the console (see SEC-002). No credentials or transaction values.

## Recommendation

- **Fix:** store the path relative to the project root, or the file name.
- **Verify:** a run started with an absolute path writes a relative one.
- **Alternatives rejected:** hiding it in the console only (the file on disk would still hold it).

## Risk Acceptance

Not accepted.
