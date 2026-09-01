# Brief

## Change

grok-choreography-smoke

## User Need

The Drydock-on-Grok v1 sandbox needs proof that the full choreography
(Implementer writes code and packet artifacts, verifier independently checks
them) runs end to end on a real change rather than on an empty repo.

## Problem

The repo currently has only a placeholder bootstrap test. Nothing exercises the
path of "real source file + real pytest + filled packet", so the choreography
and the hooks around it are untested against actual work.

## Scope

In scope:

- One pure function in `src/drydock_sandbox/smoke.py`.
- A real pytest suite in `tests/test_smoke.py`.
- A minimal root `conftest.py` so the `src` layout is importable.
- Filling the packet artifacts for this change.

Out of scope:

- Any change to `hooks/`, `kernel/`, `scripts/`, `drydock-pins.json`,
  `.github/workflows/`, `.gitleaks.toml`.
- Delta specs (no living capability changes).
- LaunchGuardian, archiving, release work.

## Acceptance Criteria

- [x] `seaworthy_greeting(name: str) -> str` exists and is pure.
- [x] Tests cover the happy path, whitespace handling, repeatability, and the
      empty-name error.
- [x] `python3 -m pytest -q -p no:cacheprovider` passes for the whole repo.
- [x] Packet artifacts are filled; verification Result stays Pending for the
      verifier.
- [x] No `__pycache__` or `.pytest_cache` left behind.

## Impact Areas

- Backend: new `src/drydock_sandbox` package (sandbox only, no callers).
- Frontend: none.
- Data model: none.
- API: none.
- AI/model behavior: none.
- Documentation: none needed; packet artifacts carry the record.
- Operations/security: none. No secrets, no credentials, no protected paths.

## Open Questions

- None.
