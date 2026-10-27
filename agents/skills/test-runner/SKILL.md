---
name: test-runner
description: Run tests using the project Makefile. Use for executing test suites, running specific tests, and validating code changes.
triggers: ["*test", "*qa test"]
---

One-line summary: Run the project test suite through the Makefile for consistent environment setup.

TLDR:
    Use `bobp make test` to run all tests; use `pytest` directly (with `.venv` activated) for targeted runs by file, pattern, or coverage.
    On failure: read the error, fix the issue, re-run the specific failing test first, then the full suite.
    Used by Neo (`*swe test`) after implementation changes and by Trin (`*qa test`) for full verification.

# Test Runner Skill

## Overview

This skill provides standardized test execution using the project's Makefile. All test commands should go through `make` to ensure consistent environment setup.

## Test Pyramid and Iteration

Start with the smallest test level that can prove the changed behavior:

1. **Unit:** Prefer focused tests for deterministic logic and CSS contracts (for example, asserting that the relevant rule sets the required property). Keep these fast and isolated.
2. **Browser/integration:** Add this level only when the remaining behavior depends on browser-computed layout, rendering, or interactions that the unit test cannot establish.
3. **End-to-end:** Use it only when a cross-component user flow remains uncovered by lower-level tests.

Move up one level at a time to close a named coverage gap. Do not default CSS changes to a full browser or end-to-end suite. Before iterating, confirm that the project's Makefile actually supports the requested test filter; check the resulting test count so a broad run is not mistaken for a targeted one.

## Commands

### Run All Tests
```bash
bobp make test
```
Runs the complete test suite with pytest.

### Run Specific Test File
```bash
source .venv/bin/activate && pytest tests/unit/test_store.py -v
```

### Run Tests Matching Pattern
```bash
source .venv/bin/activate && pytest -k "test_pattern" -v
```

### Run with Coverage
```bash
source .venv/bin/activate && pytest --cov=via tests/ -v
```

## Quick Reference

| Action | Command |
|--------|---------|
| All tests | `bobp make test` |
| Unit tests only | `source .venv/bin/activate && pytest tests/unit/ -v` |
| Integration tests | `source .venv/bin/activate && pytest tests/integration/ -v` |
| Single file | `source .venv/bin/activate && pytest tests/unit/test_X.py -v` |
| By pattern | `source .venv/bin/activate && pytest -k "pattern" -v` |
| Verbose output | Add `-v` or `-vv` flag |
| Stop on first fail | Add `-x` flag |

## Workflow

1. **Before testing**: Ensure dependencies are installed (`bobp make install`)
2. **Run tests**: Use appropriate command from above
3. **On failure**: Read error output, identify failing test, fix issue
4. **Re-run**: Run specific failing test first, then full suite

## Integration with Personas

- **Neo** (`*swe test`): Run tests after implementing changes
- **Trin** (`*qa test`): Run full test suite for verification
