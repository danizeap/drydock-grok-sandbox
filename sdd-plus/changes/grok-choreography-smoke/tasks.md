# Tasks

## Change

grok-choreography-smoke

## Implementation

- [x] Confirm scope and standards (LITE mode; protected paths identified and avoided).
- [x] Add tests: `tests/test_smoke.py` with 4 cases (5 including parametrize expansion).
- [x] Implement the smallest coherent change: `src/drydock_sandbox/smoke.py` plus
      `__init__.py` and a root `conftest.py` for import path.
- [x] Docs/specs: no behavior, setup, data, API, or workflow change beyond the
      sandbox module; no living capability touched, so no delta spec.
- [x] Run tests locally and record actual output in `verification.md`.
- [x] Confirm no `__pycache__` / `.pytest_cache` artifacts remain.

## Verification (verifier subagent — not the Implementer)

- [ ] Independently re-run the test suite.
- [ ] Review the diff against brief scope and protected-path constraints.
- [ ] Confirm evidence claims in `verification.md`.
- [ ] Set the verification Result.
