# Tasks

## Change

grok-coplan-closure-gate

## Status

Implemented on branch `packet/grok-coplan-closure-gate` (base `b421962` on `main`), awaiting
independent verification. Built on the OQ-1/OQ-2/OQ-3 **defaults** in `plan.md`, as the Owner
authorized: OQ-1 no (untracked non-mutating extras do not fail), OQ-2 no (no content-based
detection), OQ-3 yes (repo-wide tracked-only banned stems). No alternative answer was
implemented (`plan.md` must_not_do 13).

## Implementation

- [x] Confirm the two load-bearing facts on disk: `check_pins()` iterates the pins map only
      (`scripts/start_probe.py:53-69`), and `main()` sums per-check error lists in check order
      (`scripts/start_probe.py:218-242`). Both hold; the pins loop's only input is
      `pins["files"]`, so an unpinned file under `scripts/conductor/` is invisible to it.
- [x] Add module constants `CONDUCTOR_DIR`, `CONDUCTOR_ALLOWED`, `BANNED_STEMS`,
      `BANNED_SUFFIXES` to `scripts/start_probe.py`. Placed below `PINS_PATH`.
      `CONDUCTOR_ALLOWED` is a hardcoded `frozenset`, not derived from the pins at runtime.
- [x] Add `_tracked_files(root)` (fails closed on git error) and
      `_is_banned_name(name, *, allow_extensionless=False)`.
- [x] Add `check_conductor_closure(root=ROOT, tracked=None)` after `check_pins()`. The on-disk
      scan passes `allow_extensionless=True`; the repo-wide tracked scan does not. The
      `continue`-after-banned-tracked-name dedupe is kept, and missing pinned files are
      deliberately not reported here.
- [x] Wire it into `main()`: call after `check_pins()`, one term in the `errors` sum, and the
      `conductor_errors` key immediately after `pin_errors`.
- [x] Write `tests/test_start_probe_conductor_closure.py` — the test functions in `plan.md` §5,
      all fake trees under `tmp_path`, no mutating filename anywhere in the live tree.
      14 test functions (every name in the `plan.md` Tests table); 26 cases with
      parametrization.
- [x] Add the single `check_conductor_closure` stub line to `_stub_other_checks` in
      `tests/test_start_probe_discover.py`; change no assertion there.
- [x] Run `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` until green.
      `75 passed in 0.98s`.
- [x] Re-pin `scripts/start_probe.py` in `drydock-pins.json` — edit first, recompute sha256,
      update that one value, then run the probe (`plan.md` §6 order). New value
      `f71b0a7fa02ac8ea99ddd7f651286363f738d49617138dddaecfab4424f5e9b7`; the six conductor
      pins are untouched.
- [x] Run `python3 scripts/start_probe.py`, `git status --porcelain`, and
      `git ls-files scripts/conductor/ | wc -l`; paste the output into `verification.md`.
      Probe `ok: true`, exit 0; conductor listing is exactly 6.
- [ ] Invoke the verifier subagent; do not self-certify.

## Implementer notes

- `plan.md` §7 item 3's expected output is wrong about its own design: with the §1 dedupe in
  place, `check_conductor_closure(tracked=['scripts/conductor/mutate.py'])` returns `[]` when
  nothing is planted on disk. The code follows §1; the discrepancy, the reachable form of that
  error class, and the evidence are in `verification.md` and `decision-log.md`.
- No commit was made to `main`; nothing was pushed, no PR was opened, `negotiate.py` was not
  run, and no verifier subagent was invoked in this turn.
