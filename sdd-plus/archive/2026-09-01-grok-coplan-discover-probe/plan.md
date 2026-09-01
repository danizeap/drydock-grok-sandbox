# Plan

## Change

grok-coplan-discover-probe

## Mode

LITE. One file of production code (`scripts/start_probe.py`), one test file, one pin line.
No contract change (`discover_core()` signature untouched), no schema, no auth, no side effects
beyond the probe's existing exit code and JSON. Round 2 of coplan negotiation (final).

## Load-bearing fact, checked on disk

`scripts/conductor/codex_bridge.py:88` — `def discover_core(localappdata=None, path_env=None, home=None)`.
Lines 100–122 are the whole body, and they read exactly three ambient sources:

- line 100: `localappdata` kwarg, else `os.environ.get("LOCALAPPDATA", "")`
- line 107: `path_env` kwarg, else `os.environ.get("PATH", "")`
- line 116: `home` kwarg, else `os.path.expanduser("~")`

There is no config file, no registry read, no `shutil.which`, no other env var. **Passing all
three kwargs is therefore not a partial seam — it is total substitution of the search input.**
This closes the round-1 objection that the seam was "assumed, not proven", and it closes the
objection that blanking only `LOCALAPPDATA` / `PATH` / `HOME` might leave an ambient source open:
those three *are* the ambient surface.

One nuance that makes the existing fixture correct: `tests/test_codex_discover.py:33` does
`monkeypatch.setenv("HOME", "")` rather than `delenv`, because `os.path.expanduser("~")` falls
back to the passwd database when `HOME` is absent (see `tests/test_codex_discover.py:103-113`,
which relies on exactly that). Reuse `setenv(..., "")`, do not "improve" it to `delenv`.

## Approach

### 1. Add `check_discover()` to `scripts/start_probe.py`

Next to `check_pins()` / `check_hooks()` / `check_secret_tree()`. It returns a **tuple**
`(errors, skipped_reason)` — mirroring `check_hooks()`, which already returns
`tuple[list[str], list[dict]]`, so the tuple shape is established house style rather than a new
idiom. A bare `list[str]` cannot express "skipped" without smuggling a sentinel into the error
list, which is the one thing the Owner ruled out (the skip must be recorded, not silent).

`scripts/start_probe.py` does **not currently import `os`** (imports are `hashlib`, `json`,
`subprocess`, `sys`, `pathlib.Path` at lines 9–13). Add `import os` to the stdlib block.

```python
def check_discover(**kwargs) -> tuple[list[str], str]:
    """Fail closed when no installed Codex core is findable.

    Token-free: imports and calls discover_core() only; never spawns the Codex CLI.
    Returns (errors, skipped_reason). skipped_reason is "" unless the check was skipped.
    """
    if os.environ.get("GITHUB_ACTIONS"):
        return [], ("skipped on GitHub Actions: hosted runners have no Codex core; "
                    "discovery is enforced on developer machines only")

    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:          # real membership guard: repeated calls
        sys.path.insert(0, scripts_dir)      # (tests call this many times) must not grow sys.path
    try:
        from conductor.codex_bridge import discover_core
    except Exception as e:
        return [f"cannot import discover_core: {e}"], ""
    try:
        core = discover_core(**kwargs)
    except Exception as e:
        return [f"discover_core raised: {e}"], ""
    if not core:
        return ["no Codex core found: discover_core() returned None; "
                "coplan would fail closed later at negotiate stage 'discover'"], ""
    return [], ""
```

The `sys.path` guard above is the **actual membership check** round 1 promised in prose but did
not show in the snippet (round 1 line 22 inserted unconditionally). This is the fix.

### 2. The `GITHUB_ACTIONS` skip — exact semantics

The Owner's 2026-09-01 call, made implementable:

- **Placement: first statement in `check_discover`, before the `sys.path` work and before the
  import.** On a runner the function therefore never imports `codex_bridge` and never calls
  `discover_core()` at all — no filesystem walk, no import-time side effects, no way for a
  broken vendored bridge to redden CI. This is the strongest reading of "skip the check".
- **Trigger: `os.environ.get("GITHUB_ACTIONS")` truthy**, i.e. set *and* non-empty. GitHub sets
  it to the literal `"true"` on every hosted and self-hosted runner. `GITHUB_ACTIONS=` (empty)
  does not skip — treating an empty value as "in CI" would widen the hole for no benefit.
- **Effect on `ok`: none.** The skip returns `[]`, so nothing enters the `errors` sum and `ok`
  cannot be flipped by discover in either direction.
- `discover_errors` is `[]`; `discover_skipped` is the non-empty reason string above.
- **When `GITHUB_ACTIONS` is unset, behavior is round 1 verbatim:** `None` produces the
  missing-core error string, it lands in `errors`, `ok` goes false, exit 1.
- **Not a local opt-out.** No `DRYDOCK_ALLOW_MISSING_CORE`, no `--skip-discover` flag, no config
  key. `GITHUB_ACTIONS` is platform-set; nothing in this repo sets or exports it (verified:
  `grep -rn GITHUB_ACTIONS` over `*.py` and `*.yml` returns nothing today).
- `.github/workflows/drydock.yml` is **not edited**. Line 24 keeps running
  `python3 scripts/start_probe.py` unchanged; the probe adapts to the runner, not the reverse.

### 3. Wire into `main()`

```python
discover_errors, discover_skipped = check_discover()
errors = (pin_errors + hook_errors + secret_tree_errors
          + pre_push_errors + pre_commit_errors + discover_errors)
```

`main()` calls with **no kwargs**, i.e. real environment resolution. `ok` is already
`not errors` (line 198), so it flips automatically. The existing
`START PROBE FAILED: ...` stderr line (line 208) picks the message up for free.

### 4. New JSON keys and their compatibility contract

The result dict (currently `start_probe.py:197-205`) gains **two additive keys and loses none**:

| Key | Type | Always present? | Value |
| --- | --- | --- | --- |
| `discover_errors` | `list[str]` | yes | `[]` when the core is found **and** `[]` when skipped; one error string otherwise |
| `discover_skipped` | `str` | yes | `""` when the check ran; non-empty reason when skipped |

**Placement.** `discover_errors` goes after `pre_commit_errors`, so all six `*_errors` lists stay
contiguous. `discover_skipped` goes immediately after `discover_errors` — the reason sits next to
the list it explains — and both sit before `hook_evidence`, which stays last as the bulky
evidence blob.

**Chosen: always present, `""` for "not skipped" — not absent-vs-present.** Justification: a
stable key set means the JSON has one shape in every run, so a human diffing two probe outputs
or a future `jq` filter never has to distinguish "missing key" from "did not skip", and
`if result["discover_skipped"]:` is the natural predicate. Absent-vs-present would make the CI
log and the local log structurally different documents, which is the opposite of what a probe is
for. It would also make an older probe (no key at all) indistinguishable from a new probe that
did not skip.

**Compatibility.** No existing key is removed, renamed, or retyped, and `ok` keeps its exact
meaning (`not errors`). Verified there is no machine consumer to break: `grep` for `pin_errors` /
`hook_evidence` / `start_probe` across `*.py` and `*.yml` finds no reader of this stdout outside
`start_probe.py` itself, and `.github/workflows/drydock.yml:24` consumes the **exit code** only.
Additive-only keys are therefore safe for the one existing consumer (CI) and for the intended
human reader; the contract above is what future consumers may rely on.

### 5. Do not touch `discover_core()`

Search order, the `.sandbox-bin` exclusion, and the signature stay byte-identical.
`scripts/conductor/` stays as vendored and pinned.

### 6. Tests — new file `tests/test_start_probe_discover.py`

`tests/test_codex_discover.py` stays untouched (it tests the bridge's own behavior); this file
tests the probe's *use* of it. Preamble copies `tests/test_ensure_pre_push.py:7-9` verbatim
(`ROOT`, `sys.path.insert(0, str(ROOT / "scripts"))`, `import start_probe`). Build fake trees
under `tmp_path` with that suite's `_exe()` helper (`#!/bin/sh` stub + `chmod 0o755`).

**Autouse fixture — four env vars, not three:**

```python
@pytest.fixture(autouse=True)
def _no_ambient_env(monkeypatch):
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("PATH", "")          # setenv "" — see the expanduser nuance above
    monkeypatch.setenv("HOME", "")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)   # <- required
```

The fourth line is load-bearing and is **not** optional: this repo's own CI runs pytest on a
GitHub runner, where `GITHUB_ACTIONS=true` is already in the environment. Without the `delenv`,
every fail-closed test below would take the skip branch and pass for the wrong reason — the exact
class of silent hole this packet exists to close.

Every test passes **all three** kwargs (`localappdata`, `path_env`, `home`) explicitly, which per
the load-bearing fact substitutes the entire search input; the fixture is belt-and-braces against
a future ambient read.

- `test_found_core_yields_no_errors` — fake `bin/codex`; `check_discover(localappdata="",
  path_env=str(tmp_path / "bin"), home="")` returns `([], "")`.
- `test_missing_core_is_an_error` — empty tree; `check_discover(localappdata="", path_env="",
  home=str(tmp_path))` returns exactly one error mentioning `discover_core`, and `skipped == ""`.
- `test_sandbox_bin_copy_does_not_count_as_found` — fake exe at `.codex/.sandbox-bin/codex`,
  `path_env` at that dir, `home` at `tmp_path`; asserts the missing-core error. A stale sandbox
  copy is not a core.
- `test_check_discover_never_spawns_codex` — monkeypatch `subprocess.Popen` **and**
  `subprocess.run` on `conductor.codex_bridge` to raise `AssertionError`, then call
  `check_discover(...)` on the found-core tree and assert `([], "")`. Turns the token-free
  acceptance criterion into a test instead of a claim, and keeps it true if `discover_core` ever
  grows a probe call.
- `test_github_actions_skips_the_check` — `monkeypatch.setenv("GITHUB_ACTIONS", "true")` with an
  **empty** tree (no findable core); assert `errors == []`, `skipped` is a non-empty `str`, and
  that it mentions GitHub Actions.
- `test_github_actions_skip_does_not_call_discover_core` — set `GITHUB_ACTIONS=true`, monkeypatch
  `conductor.codex_bridge.discover_core` to raise `AssertionError`, call `check_discover()`;
  proves the skip short-circuits *before* the call, not merely before the error.
- `test_empty_github_actions_does_not_skip` — `monkeypatch.setenv("GITHUB_ACTIONS", "")` on an
  empty tree; assert the missing-core error still fires. Pins "set and non-empty".

### 7. Re-pin — last

`scripts/start_probe.py` **is** pinned (`drydock-pins.json:12`, currently `af48884779ce…`).
Ordering, strictly: (a) finish every edit to `scripts/start_probe.py`; (b) recompute
`python3 -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('scripts/start_probe.py').read_bytes()).hexdigest())"`;
(c) replace that one value; (d) only then run the probe. Re-pinning before the edit is final
leaves the probe failing its own `check_pins()`. Nothing else in the pins map changes — the new
test file is not pinned and `scripts/conductor/*` is untouched.

### 8. Verify (evidence for `verification.md`, filled by the implementer, not here)

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`
2. `python3 scripts/start_probe.py` on this VM — expect exit 0, `discover_errors: []`,
   `discover_skipped: ""`.
3. Negative, without editing the workflow or the environment of the other checks:
   ```
   python3 -c "import sys; sys.path.insert(0,'scripts'); import start_probe; \
   print(start_probe.check_discover(localappdata='', path_env='', home='/nonexistent'))"
   ```
   expect `([<missing-core error>], '')`. (Round 1 hand-waved this as "`env -i` won't work"; a
   direct call is the correct instrument, since the other checks need a real environment.)
4. Skip path: the same one-liner with `GITHUB_ACTIONS=true` prefixed — expect
   `([], '<non-empty reason>')`.
5. Capture 2–4 plus the pytest summary in `verification.md`.

## Files Expected To Change

- `scripts/start_probe.py` — `import os`; new `check_discover()` (~20 lines); `main()` gains one
  call, one term in the `errors` sum, two JSON keys. No existing check is modified or weakened.
- `tests/test_start_probe_discover.py` — new, ~90 lines, seven tests plus the fixture.
- `drydock-pins.json` — one value updated: `scripts/start_probe.py`.
- Packet artifacts only otherwise (`tasks.md`, `verification.md`, `decision-log.md`).

Explicitly **not** changed: `scripts/conductor/*` (incl. `discover_core`), `kernel/`, `hooks/`,
`backstops/`, `.github/workflows/drydock.yml`, `tests/test_codex_discover.py`.

## Risks

- **The skip could be mistaken for a local opt-out.** Someone exporting `GITHUB_ACTIONS=1` on a
  developer machine would disable the check. Mitigations, all in-plan: the trigger is a
  platform-set variable that nothing in this repo writes; there is deliberately no
  `DRYDOCK_ALLOW_MISSING_CORE` and no CLI flag; and the non-empty `discover_skipped` string
  appears in **every** probe run's JSON, so a skip is always visible in the artifact rather than
  silent. A silent escape hatch would recreate the exact hole this packet closes.
- **The test suite itself runs under `GITHUB_ACTIONS`.** Without the fixture's
  `delenv("GITHUB_ACTIONS")`, the fail-closed tests would pass vacuously in CI while genuinely
  regressing. Mitigated by step 6's fourth fixture line, and by
  `test_empty_github_actions_does_not_skip` pinning the truthiness rule.
- **Import-time side effects of `codex_bridge`.** It inserts `<root>/hooks` into `sys.path` and
  imports `protect_secrets` at module scope. Harmless in the probe process (the probe already
  runs hooks as subprocesses), but importing the bridge is not free of side effects. Mitigated by
  the lazy in-function import, the broad `except Exception`, and — on runners — by the skip
  returning before the import happens at all.
- **Accidental token spend.** Nothing in this path spawns Codex.
  `test_check_discover_never_spawns_codex` is what keeps that true under future change.
- **Ambient-environment flakiness in tests.** A real `/home/box/.local/bin/codex` on this VM
  could make a "missing core" test pass for the wrong reason. Mitigated by always passing all
  three kwargs (total substitution per the load-bearing fact) plus the autouse fixture.
- **Pin/edit ordering.** Editing `start_probe.py` without re-pinning makes the probe fail its own
  `check_pins()` — confusing and self-inflicted. Mitigated by step 7's explicit ordering.
- **Scope creep.** The leftover holes (`.env` writes, `brief_engine.py` completeness-only, GitHub
  FF `--force`) and any further conductor vendoring stay out, per the brief.

## Rollback

Single-commit revert. The change is three files and additive: `git revert <sha>` restores the
prior `start_probe.py`, drops the new test file, and restores the prior pin hash together — the
pin and the file it pins move as one unit, so there is no half-reverted state where the probe
fails on its own hash. No migration, no data, no config, no external state; nothing to undo on
the VM or in `.git/hooks`. Manual fallback if the revert is awkward mid-stack: delete
`check_discover()` and its `main()` call-site lines, drop the two JSON keys and the `import os`,
delete `tests/test_start_probe_discover.py`, restore the `af48884779ce…` pin value.
