# SEC-006: `--with` values from the console could point a sketch at any file the console's user can read (Sprint 22 design)

- **Severity:** Low — the sketch only reads the file as a source; the console never serves run output files; but error text from a failed read is shown in the console.
- **Status:** Open (design finding)
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch
- **Affected:** proposed `POST /api/start` `with` values passed to `understudy run --with name=value`
- **Class / reference:** CWE-22 (path traversal), CWE-209 (error message with sensitive information)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Morpheus | Add to the design: a `--with` value that names an existing file must resolve (symlinks followed) to a path inside the project root, else the start is refused with "that file is outside the project" | Before UND-79 is built |
| Neo | Implement it with a test (`../`, an absolute path outside the root, a symlink out) | In UND-79 |

## Evidence

- **Reproduce / detect:** design read: values are passed through unchanged; `cli._values` resolves an existing relative path to an absolute one without any root check.
- **Observed:** none yet (no code).
- **Confidence:** Medium (depends on how a stage echoes a failed read; the existing CSV and JSONL readers name the file and line).

## Impact and Reachability

Someone holding the secret could make a run read `/etc/passwd` or another user file as a source; the content would not be served, but a parse error naming a line could be. Limited to files the console's user can read.

## Recommendation

- **Fix:** root check on file-valued `--with` (above); also cap concurrent children (4) and require the `Origin` header, when present, to match the `Host`; replay ids must match `run-[0-9A-Za-z-]+` and exist in the capture store.
- **Verify:** tests for each refusal.
- **Alternatives rejected:** an allow-list of data folders (more to configure; the project root is enough for one owner).

## Risk Acceptance

Not accepted.
