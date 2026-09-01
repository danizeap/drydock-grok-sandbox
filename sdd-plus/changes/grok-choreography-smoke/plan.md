# Plan

## Change

grok-choreography-smoke

## Approach

1. Add `src/drydock_sandbox/` with `__init__.py` and `smoke.py` containing a
   single pure function `seaworthy_greeting(name)`. It strips whitespace,
   raises `ValueError` on an empty name, and otherwise returns a fixed
   greeting string. No I/O, no globals, no side effects.
2. Add a root `conftest.py` that puts `src/` on `sys.path`, so the existing CI
   command (`python3 -m pytest -q -p no:cacheprovider`) picks the package up
   without introducing packaging config.
3. Add `tests/test_smoke.py` covering: plain name, surrounding whitespace,
   repeatability (purity), and the empty/whitespace-only rejection.
4. Run the suite with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`.
5. Fill brief, plan, tasks, decision log, and verification evidence; leave the
   verification Result Pending for the verifier.

## Files Expected To Change

- `src/drydock_sandbox/__init__.py` (new)
- `src/drydock_sandbox/smoke.py` (new)
- `conftest.py` (new)
- `tests/test_smoke.py` (new)
- `sdd-plus/changes/grok-choreography-smoke/{brief,plan,tasks,decision-log,verification}.md`

## Risks

- Low. The only repo-wide effect is the root `conftest.py` altering `sys.path`
  for test runs; it inserts one path and does nothing else.
- No protected path is touched, so no hook should fire.

## Rollback

Delete `src/drydock_sandbox/`, `conftest.py`, and `tests/test_smoke.py`, or
revert the single commit. Nothing else imports this code, so removal is safe.
