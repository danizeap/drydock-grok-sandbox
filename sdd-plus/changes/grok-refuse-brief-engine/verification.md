# Verification

## Change

grok-refuse-brief-engine

Implemented on branch `packet/grok-refuse-brief-engine` under the Owner decision of 2026-09-02
(OQ-1 → strict matcher; see `decision-log.md`). Every command below was run by the **implementer**
and its output is pasted verbatim from plan §Verification commands. Implementer evidence is
evidence, not verification: the Verifier Subagent box stays unchecked and the Result stays
**Pending** by Owner override this turn.

Packet name is `does-not-exist` or `BAD_NAME` throughout; verdict files are under `/tmp`. No real
packet, no real passing gate, and no `verify-run` ledger event was created.

## Automated Checks

- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` — green, including the
      unmodified `tests/test_brief_wrapper.py` and `tests/test_record_verify_bound.py`.

```
........................................................................ [ 83%]
..............                                                           [100%]
86 passed in 1.45s
```

- [x] `python3 scripts/start_probe.py` — `"ok": true`, `"pin_errors": []`.

```
{
  "ok": true,
  "pin_errors": [],
  "conductor_errors": [],
  "hook_errors": [],
  "secret_tree_errors": [],
  "pre_push_errors": [],
  "pre_commit_errors": [],
  "discover_errors": [],
  "discover_skipped": "",
  "hook_evidence": [
    {
      "name": "git_safety_deny",
      "expect": "deny",
      "got": "deny",
      "exit": 0,
      ...
    },
    {
      "name": "protect_secrets_deny",
      "expect": "deny",
      "got": "deny",
      "exit": 0,
      ...
    },
    {
      "name": "git_safety_allow_benign",
      "expect": "allow",
      "got": "allow",
      "exit": 0,
      "raw_preview": ""
    }
  ]
}
exit=0
```

(`hook_evidence` `raw_preview` strings elided for length; all three hook self-tests matched their
expectation. The machine-readable assertion is `ok: True pin_errors: []`, printed from the probe's
own JSON.)

- [x] `sha256sum kernel/brief_complete_engine.py` —
      `aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b`.

Asserted at four separate moments, per plan Steps 3 / 4a / 8 and verification command 2 — after the
copy, after the risky overwrite of `kernel/brief_engine.py`, immediately before the pin write, and
again during the verification run. All four printed:

```
aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b  kernel/brief_complete_engine.py
```

- [x] `git status --porcelain` — only the intended files; new file `git add`ed.

```
 M drydock-pins.json
A  kernel/brief_complete_engine.py
 M kernel/brief_engine.py
 M scripts/record_verify_bound.py
 M tests/test_kernel_brief_overlay.py
?? sdd-plus/changes/grok-refuse-brief-engine/
```

No `.env`, no `scripts/conductor/` entry, no `__pycache__`.

## Manual Checks

- [x] **1 — the hole, closed.** `python3 kernel/brief_engine.py --record-verify does-not-exist`
      → `recorded: false`, `reason: "bare-record-verify-refused"`, exit 1.

```
refused: bare --record-verify is not provenance. usage: python3 kernel/brief_engine.py --record-verify <packet> <verdict-file> <expected-sha256> <required-verdict-string>
{
  "recorded": false,
  "reason": "bare-record-verify-refused",
  "detail": "kernel/brief_engine.py --record-verify requires <packet> <verdict-file> <expected-sha256> <required-verdict-string>, spelled exactly; completeness-only kernel/brief_complete_engine.py is not provenance"
}
exit=1
```

- [x] **2 — bytes intact, hooks resolve.** `python3 kernel/brief_complete_engine.py` → FACTS JSON,
      exit 0 (proves the `hooks/_drydock_common.py` module-scope import still resolves).

```
aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b  kernel/brief_complete_engine.py
{
 "drydock": "ok",
 "engine": 1,
exit=0
```

- [x] **3 — delegation.** `python3 kernel/brief_engine.py` → FACTS JSON, exit 0.

```
{
 "drydock": "ok",
 "engine": 1,
exit=0
```

- [x] **3a — wrapper-path hop is transparent** (Codex gap 2).
      `diff <(python3 scripts/brief.py) <(python3 kernel/brief_complete_engine.py)` → empty.

```
HOP OK: identical
```

Three interpreter starts (`scripts/brief.py` → overlay → completeness) produce FACTS byte-identical
to the direct call; `diff` emitted nothing and exited 0.

- [x] **4 — bound form reaches `check_verdict`.** Wrong digest → `reason: "check_verdict-failed"`.

```
missing verdict file: /tmp/v.md
{
  "recorded": false,
  "reason": "check_verdict-failed",
  "check_verdict_exit": 1,
  "detail": "missing verdict file: /tmp/v.md\n"
}
exit=1
```

(Command 4 runs before command 4a writes `/tmp/v.md`, so `check_verdict` fails on the missing file
rather than on the all-zero digest. Either way it is `check_verdict-failed`, not
`bare-record-verify-refused` — the overlay reached `record_verify_bound.py`.)

- [x] **4a — bound form gets PAST `check_verdict`** (Codex gap 2). Correct digest → a
      completeness-side reason (`bad-name` / `packet-not-found` / `gate-failed`). A
      `bare-record-verify-refused` here is the self-refusal deadlock, **not** a success.

```
{
 "recorded": false,
 "reason": "gate-failed",
 "detail": ""
}
exit=0
```

`gate-failed` is a completeness-side reason emitted by `record_verify()` in the moved engine, so
`check_verdict` passed and `kernel/brief_complete_engine.py` was reached. Not the deadlock. Note
the one-space `indent=1` JSON, which is the moved engine's own formatting — further evidence the
output came from completeness and not from the overlay. `recorded` is false and no ledger event was
written (`does-not-exist` has no packet gate to pass).

- [x] **5 — siblings unchanged on the canonical spelling.** `scripts/brief.py` and
      `kernel/brief.py` bare `--record-verify` still refuse, exit 1.

```
refused: bare --record-verify is not provenance. usage: python3 scripts/brief.py --record-verify <packet> <verdict-file> <expected-sha256> <required-verdict-string>
{
  "recorded": false,
  "reason": "bare-record-verify-refused",
  "detail": "scripts/brief.py --record-verify requires <packet> <verdict-file> <expected-sha256> <required-verdict-string>; completeness-only kernel/brief_engine.py is not provenance"
}
exit=1
refused: bare --record-verify is not provenance. usage: python3 kernel/brief.py --record-verify <packet> <verdict-file> <expected-sha256> <required-verdict-string>
{
  "recorded": false,
  "reason": "bare-record-verify-refused",
  "detail": "kernel/brief.py --record-verify requires <packet> <verdict-file> <expected-sha256> <required-verdict-string>; completeness-only kernel/brief_engine.py is not provenance"
}
exit=1
```

Both refuse in their own process, before any hop, exactly as before. Their `detail` strings still
name `kernel/brief_engine.py` as "completeness-only" — now stale prose, since that path is the
overlay and completeness moved. Neither file is edited by this packet (plan must_not_do 6), so the
staleness is carried deliberately rather than fixed; flagged here for the reviewer.

- [x] **5a — siblings tightened on the bypass spellings** (OQ-1 default; plan §Behavior deltas).
      `kernel/brief.py --record-verify=BAD_NAME` and `scripts/brief.py --record-ver BAD_NAME` →
      refused, exit 1. Pre-change baseline recorded during the round-2 audit: both returned
      `{"recorded": false, "reason": "bad-name"}` at exit **0**.

```
refused: bare --record-verify is not provenance. usage: python3 kernel/brief_engine.py --record-verify <packet> <verdict-file> <expected-sha256> <required-verdict-string>
{
  "recorded": false,
  "reason": "bare-record-verify-refused",
  "detail": "kernel/brief_engine.py --record-verify requires <packet> <verdict-file> <expected-sha256> <required-verdict-string>, spelled exactly; completeness-only kernel/brief_complete_engine.py is not provenance"
}
exit=1
refused: bare --record-verify is not provenance. usage: python3 kernel/brief_engine.py --record-verify <packet> <verdict-file> <expected-sha256> <required-verdict-string>
{
  "recorded": false,
  "reason": "bare-record-verify-refused",
  "detail": "kernel/brief_engine.py --record-verify requires <packet> <verdict-file> <expected-sha256> <required-verdict-string>, spelled exactly; completeness-only kernel/brief_complete_engine.py is not provenance"
}
exit=1
```

The delta predicted in plan §Behavior deltas on unedited files, observed: two files this packet does
not edit and does not re-pin moved from "records, exit 0" to "refused, exit 1". The refusal is
emitted by the overlay (note the usage line naming `kernel/brief_engine.py`), inherited through the
delegation edge.

- [x] **6 — residual is one unadvertised path** (plan §Review criterion 2). `grep -rn
      "brief_complete_engine"` over tracked non-`sdd-plus` files returns only
      `scripts/record_verify_bound.py`, `tests/test_kernel_brief_overlay.py`, `drydock-pins.json`,
      and the overlay's own docstring.

```
./scripts/record_verify_bound.py:7:runs. Completeness is kernel/brief_complete_engine.py; do not call it --record-verify directly. kernel/brief.py, kernel/brief_complete.py, scripts/brief.py and kernel/brief_engine.py all refuse the bare form.
./scripts/record_verify_bound.py:21:BRIEF = ROOT / "kernel" / "brief_complete_engine.py"
./kernel/brief_engine.py:4:Completeness lives at kernel/brief_complete_engine.py (bytes unchanged from
./kernel/brief_engine.py:14:kernel/brief_complete_engine.py). Other modes are delegated unchanged to
./kernel/brief_engine.py:15:kernel/brief_complete_engine.py.
./kernel/brief_engine.py:25:COMPLETE = ROOT / "kernel" / "brief_complete_engine.py"  # NEVER this file: execv loop
./kernel/brief_engine.py:34:    against kernel/brief_complete_engine.py:545-549. The plain
./kernel/brief_engine.py:62:                            "completeness-only kernel/brief_complete_engine.py "
./kernel/brief_engine.py:90:        print("missing kernel/brief_complete_engine.py", file=sys.stderr)
./tests/test_kernel_brief_overlay.py:14:ENGINE = ROOT / "kernel" / "brief_complete_engine.py"
./tests/test_kernel_brief_overlay.py:45:    the new unadvertised path kernel/brief_complete_engine.py. The claim this
./drydock-pins.json:26:    "kernel/brief_complete_engine.py": "aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b",
```

Exactly the four expected files: the gate, the overlay's own docstring and constants, the tests, and
the pins. No `README.md`, no `AGENTS.md`, no `PROJECT_CONTEXT.md`, no workflow, no wrapper names the
new path as a thing to run.

- [ ] **7 — review criterion.** All four checks in plan §Review criterion hold.

Left unticked deliberately: this is the reviewer's pass/fail judgement, not an implementer check.
The raw evidence for each of the four is above, so it can be applied without re-running anything —
criterion 1 from checks 1 and 5 plus the parametrized test, criterion 2 from check 6, criterion 3
from check 4a and `tests/test_record_verify_bound.py`, criterion 4 from the retargeted
`test_completeness_engine_still_has_bare_mode` docstring and plan §Risks.

## Tests added

`tests/test_kernel_brief_overlay.py`, all seven from plan §4 including the OQ-1 parametrized test.
`ENGINE` retargeted to `kernel/brief_complete_engine.py`, `ENGINE_OVERLAY` added for
`kernel/brief_engine.py`. The four existing tests covering `kernel/brief.py` and
`kernel/brief_complete.py` are untouched. `tests/test_brief_wrapper.py` and
`tests/test_record_verify_bound.py` were not modified and are green across the extra `execv` hop and
the `BRIEF` retarget.

## Pins

| Key | Value |
| --- | --- |
| `kernel/brief_engine.py` (now the overlay) | `1a47652207dabf4388a22e4def2b07a6e475b1f46fc5cf714199694ff439f3db` |
| `kernel/brief_complete_engine.py` (moved bytes, frozen) | `aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b` |
| `scripts/record_verify_bound.py` (retargeted) | `ed11e76329008ab104bfabe93a281feefe01861d4752affab390427532b71f9c` |

No other pin moved. `scripts/start_probe.py` was not edited — the new key is pure data to
`check_pins()`.

## Documentation Updates

- [ ] README or user-facing docs updated, if needed.
- [ ] Project context updated, if needed.
- [ ] Specs updated, if needed.
- [x] No documentation update needed. Reason: `grep -rn brief_engine` over tracked
      `*.py`/`*.md`/`*.json`/`*.yml` (excluding `sdd-plus/archive/`) finds no reference in
      `README.md`, `AGENTS.md`, or `PROJECT_CONTEXT.md`. The only prose naming the completeness
      path is `scripts/record_verify_bound.py:7`, which this packet rewrites as part of the change
      itself (plan §3). Re-confirm at Step 10 rather than trusting this box.

      *Box carried from planning and not re-confirmed by the implementer this turn; check 6 above
      is the closest evidence — it shows no doc or wrapper acquired the new path.*

## Verifier Subagent

- [ ] Verifier subagent invoked and its findings recorded here. Implementer evidence is evidence,
      not verification; the Result below does not move without it.

      *Not invoked: Owner override for this turn deferred verification (plan Step 12 skipped).
      Nothing in this file may be read as independent verification.*

## Result

Pending.
