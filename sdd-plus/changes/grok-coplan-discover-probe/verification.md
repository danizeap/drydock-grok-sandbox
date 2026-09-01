# Verification

## Change

grok-coplan-discover-probe

## Automated Checks

- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` — **51 passed in 0.92s**
      (44 pre-existing + 7 new `check_discover` tests + 2 new `main()`/stdout JSON tests).
      Re-run after the pin update; still 51 passed.
- [x] `python3 scripts/start_probe.py` — exit 0, `ok: true`, `check_pins()` green against the
      updated `drydock-pins.json`.

```
$ PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
...................................................                      [100%]
51 passed in 0.92s
```

## Manual Checks

- [x] **Probe on this VM (happy path).** `python3 scripts/start_probe.py`; `EXIT=0`. JSON excerpt:

```
{
  "ok": true,
  "pin_errors": [],
  "hook_errors": [],
  "secret_tree_errors": [],
  "pre_push_errors": [],
  "pre_commit_errors": [],
  "discover_errors": [],
  "discover_skipped": "",
  "hook_evidence": [ ... deny / deny / allow, all exit 0 ... ]
}
```

- [x] **Negative (missing core, `GITHUB_ACTIONS` unset) — fails closed.** Direct call, so the
      other checks keep their real environment and no workflow is edited:

```
$ python3 -c "import sys; sys.path.insert(0,'scripts'); import start_probe; \
  print(start_probe.check_discover(localappdata='', path_env='', home='/nonexistent'))"
(["no Codex core found: discover_core() returned None; coplan would fail closed later at negotiate stage 'discover'"], '')
```

- [x] **Skip path (`GITHUB_ACTIONS=true`) — no error, reason recorded.**

```
$ GITHUB_ACTIONS=true python3 -c "import sys; sys.path.insert(0,'scripts'); import start_probe; \
  print(start_probe.check_discover(localappdata='', path_env='', home='/nonexistent'))"
([], 'skipped on GitHub Actions: hosted runners have no Codex core; discovery is enforced on developer machines only')
```

- [x] **`discover_core()` and `scripts/conductor/*` untouched.** `git diff --stat` is two files:

```
 drydock-pins.json      |  2 +-
 scripts/start_probe.py | 34 +++++++++++++++++++++++++++++++++-
 2 files changed, 34 insertions(+), 2 deletions(-)
$ git diff --name-only -- scripts/conductor/ | wc -l
0
```

- [x] **Pins re-computed last**, after the final edit to `scripts/start_probe.py`:
      `af48884779ce…` → `ffcd8ec3ca42b2f7e03d9de612a8182218342cbe1147fdf0bc6f02a9815e46b1`.
      One value changed; the new test file is not pinned.
- [x] **Token-free.** `test_check_discover_never_spawns_codex` raises on
      `conductor.codex_bridge.subprocess.Popen` and `.run`; `check_discover` still returns
      `([], "")` on a found-core tree. No Codex CLI, no `negotiate.py`, no gauge/route/delegate.
- [x] **`main()` / stdout JSON wiring** (folded in from Codex round-2 non-blocking gap):
      `test_main_reports_a_missing_core_and_exits_1` (discover alone flips `ok` false and returns 1,
      `discover_skipped == ""`) and `test_main_records_the_skip_without_flipping_ok`
      (`discover_errors == []`, non-empty `discover_skipped`, `ok` true, returns 0). Both parse
      real stdout via `capsys` with the other five checks stubbed, so neither needs a live Codex
      binary or the real pin/hook tree.

## Documentation Updates

- [ ] README or user-facing docs updated, if needed.
- [ ] Project context updated, if needed.
- [ ] Specs updated, if needed.
- [x] No documentation update needed. Reason: the probe JSON change is purely additive (two new
      keys, none removed/renamed/retyped) and `discover_core()`'s signature is unchanged, so no
      user-facing doc describes anything that moved.

## Result

implementer-checked.

`scripts/start_probe.py` now fails closed when `discover_core()` finds no installed Codex core,
skips that check (visibly, via a non-empty `discover_skipped`) under `GITHUB_ACTIONS`, and reports
both new keys in every run. Tests, probe, and the negative/skip one-liners match plan.md.

This report is the implementer's own evidence, not independent verification. No verifier subagent
was invoked for this packet.
