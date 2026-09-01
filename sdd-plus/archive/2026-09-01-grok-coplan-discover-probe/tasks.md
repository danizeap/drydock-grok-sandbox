# Tasks

## Change

grok-coplan-discover-probe

## Implementation

- [x] Add `import os` to `scripts/start_probe.py` (it currently imports only `hashlib`, `json`,
      `subprocess`, `sys`, `pathlib.Path`).
- [x] Add `check_discover(**kwargs) -> tuple[list[str], str]` to `scripts/start_probe.py`:
      returns `(errors, skipped_reason)`, mirroring `check_hooks()`'s tuple shape. Lazy, guarded
      `from conductor.codex_bridge import discover_core`; import failure and raised exception each
      become an error string; `None` becomes the missing-core error; kwargs pass straight through.
- [x] Guard the `sys.path` insert with a real membership check
      (`if scripts_dir not in sys.path:`) so repeated calls from tests do not grow `sys.path`.
- [x] Implement the `GITHUB_ACTIONS` skip as the **first** statement in `check_discover`, before
      the `sys.path` work and before the import: when `os.environ.get("GITHUB_ACTIONS")` is
      truthy (set and non-empty), return `([], "<non-empty reason>")` without calling
      `discover_core()` at all. `ok` must not be flipped by discover in either direction. No
      `DRYDOCK_ALLOW_MISSING_CORE`, no CLI flag, no edit to `.github/workflows/`.
- [x] Wire into `main()`: `discover_errors, discover_skipped = check_discover()`; add
      `discover_errors` to the `errors` sum; add both keys to the printed JSON —
      `discover_errors` after `pre_commit_errors` (keeping the `*_errors` lists contiguous),
      `discover_skipped` immediately after it, both before `hook_evidence`. Both keys always
      present; `discover_skipped` is `""` when the check ran. Remove/rename/retype no existing key.
- [x] Add `tests/test_start_probe_discover.py`: found / missing / sandbox-bin-rejected /
      never-spawns-Codex, plus the three skip tests (skip sets a non-empty reason with
      `discover_errors == []`; skip short-circuits before `discover_core` is called;
      `GITHUB_ACTIONS=""` does **not** skip). Every test passes all three kwargs
      (`localappdata`, `path_env`, `home`) on a `tmp_path` tree. No live Codex binary required.
- [x] Autouse fixture must blank **four** vars: `delenv LOCALAPPDATA`, `setenv PATH ""`,
      `setenv HOME ""` (not `delenv` — `expanduser` falls back to the passwd db), and
      `delenv GITHUB_ACTIONS` (otherwise the fail-closed tests pass vacuously under CI).
- [x] Confirm `discover_core()` and `scripts/conductor/*` are untouched (`git diff --stat`).
- [x] Re-pin `scripts/start_probe.py` in `drydock-pins.json` — last, after the edit is final,
      then run the probe.
- [x] Run `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`.
- [x] Run `python3 scripts/start_probe.py` on this VM: expect exit 0, `discover_errors: []`,
      `discover_skipped: ""`.
- [x] Capture the negative case as evidence: a direct
      `check_discover(localappdata="", path_env="", home="/nonexistent")` call (expect one error,
      `skipped == ""`) and the same call prefixed with `GITHUB_ACTIONS=true` (expect `[]` plus a
      non-empty reason).
- [x] Fill `verification.md` and run `python3 scripts/sdd.py verify grok-coplan-discover-probe`.
