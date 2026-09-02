# Verification

## Change

grok-coplan-closure-gate

Implementer turn. The commands below were run on branch `packet/grok-coplan-closure-gate`,
based on `b421962` on `main`. Output is pasted verbatim.

The read-only inventory commands recorded in `plan.md` §0 were run during round-2 planning to
settle Codex's BC-2. They are evidence about the *current* tree, not verification of this change,
and they are not counted as any checkbox below.

Implementer evidence is evidence, not verification. `Result` stays `Pending` until the verifier
subagent reviews this independently.

## Automated Checks

- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` — full suite green,
      including the 14 new test functions in `tests/test_start_probe_conductor_closure.py`.

```
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 0.98s
```

- [x] `python3 scripts/start_probe.py; echo $?` — exit 0, `"ok": true`,
      `"conductor_errors": []`, `"discover_errors": []`, `"discover_skipped": ""`.

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
      "raw_preview": "{\"hookSpecificOutput\": {\"hookEventName\": \"PreToolUse\", \"permissionDecision\": \"deny\", ..."
    },
    {
      "name": "protect_secrets_deny",
      "expect": "deny",
      "got": "deny",
      "exit": 0,
      "raw_preview": "{\"hookSpecificOutput\": {\"hookEventName\": \"PreToolUse\", \"permissionDecision\": \"deny\", ..."
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
EXIT:0
```

(`hook_evidence` `raw_preview` values truncated here for length only; the run printed them in
full and the three `expect`/`got` pairs above are verbatim.)

- [x] Negative path without planting anything in the live tree. **The command as written in
      `plan.md` §7 item 3 returns `[]`, not an error** — see the discrepancy note below. All
      three injections were run:

```
--- as written in plan §7 / task: tracked INSIDE scripts/conductor/, not on disk ---
[]
--- same class, tracked OUTSIDE the directory ---
['mutating conductor tracked: scripts/mutate.py']
--- tracked-set closure: an extra tracked file under the directory ---
['unpinned file tracked under scripts/conductor/: scripts/conductor/extra.py']
```

- [x] `git ls-files scripts/conductor/ | wc -l` — expect `6`.

```
scripts/conductor/__init__.py
scripts/conductor/codex_bridge.py
scripts/conductor/negotiate.py
scripts/conductor/negotiate_schema.json
scripts/conductor/review.py
scripts/conductor/review_schema.json
6
```

### Discrepancy: plan §7 item 3 contradicts plan §1

`check_conductor_closure(tracked=['scripts/conductor/mutate.py'])` returns `[]` on a tree where
that file does not exist on disk. This is the plan's own code behaving exactly as `plan.md` §1
specifies, not a defect in the implementation:

- the tracked loop matches the banned stem, then `continue`s **without** appending, because
  `norm.startswith("scripts/conductor/")` — `plan.md` §1 calls this out as the dedupe the
  implementer must not simplify away ("in-dir hits belong to the presence scan", and "A banned
  name tracked *outside* the directory is reported by the tracked branch, because the presence
  scan does not look there");
- the presence scan then finds nothing, because nothing was planted (correctly — planting is
  forbidden by `must_not_do` 1).

So the `mutating conductor tracked:` class is reachable only for a path **outside**
`scripts/conductor/`, which is what the second injection above demonstrates. The in-directory
tracked+on-disk case is covered by `test_banned_file_reported_once` under `tmp_path`, which
asserts exactly one error, from the presence scan.

The implementation follows `plan.md` §1 (code) rather than `plan.md` §7 item 3 (expected output).
Recorded in `decision-log.md`.

## Manual Checks

- [x] `git status --porcelain` shows no `scripts/conductor/` entry of any kind, and no file
      named `mutate.py`, `coord.py`, `executors.py`, or `handoff.py` anywhere in the tree.

```
 M drydock-pins.json
 M scripts/start_probe.py
 M tests/test_start_probe_discover.py
?? sdd-plus/changes/grok-coplan-closure-gate/
?? tests/test_start_probe_conductor_closure.py
```

Banned-stem sweep of the live tree, tracked and untracked (both empty):

```
$ git ls-files | awk -F/ '{n=$NF; split(n,a,"."); \
    if (a[1]=="mutate"||a[1]=="coord"||a[1]=="executors"||a[1]=="handoff") print}'
(no output)

$ find . -path ./.git -prune -o -type f -print | awk -F/ '{n=$NF; split(n,a,"."); \
    if (a[1]=="mutate"||a[1]=="coord"||a[1]=="executors"||a[1]=="handoff") print}'
(no output)
```

- [x] `drydock-pins.json` diff touches **only** the `scripts/start_probe.py` value (line 12);
      the six conductor pins (lines 26-31) are byte-identical.

```
-    "scripts/start_probe.py": "ffcd8ec3ca42b2f7e03d9de612a8182218342cbe1147fdf0bc6f02a9815e46b1",
+    "scripts/start_probe.py": "f71b0a7fa02ac8ea99ddd7f651286363f738d49617138dddaecfab4424f5e9b7",
```

One changed line in the whole file (`git diff --stat`: `drydock-pins.json | 2 +-`).

- [x] The re-pin happened after the last edit to `scripts/start_probe.py`, per `plan.md` §6.
      Order actually followed: all `start_probe.py` edits → test files written → full suite green
      → `sha256` recomputed → single pins value replaced → probe run (`ok: true`, `pin_errors: []`).

- [x] `tests/test_start_probe_discover.py` diff is exactly one added stub line; no assertion
      changed.

```
 def _stub_other_checks(monkeypatch):
     """Make every check but discover pass, so main() depends on no pin/hook tree."""
     monkeypatch.setattr(start_probe, "check_pins", lambda: [])
+    monkeypatch.setattr(start_probe, "check_conductor_closure", lambda: [])
     monkeypatch.setattr(start_probe, "check_hooks", lambda: ([], []))
```

- [x] `.github/workflows/drydock.yml`, `hooks/`, `kernel/`, and `scripts/conductor/*` are
      unmodified.

```
$ git status --porcelain -- .github hooks kernel scripts/conductor backstops \
    README.md PROJECT_CONTEXT.md sdd-plus/security
(no output)

$ git diff --stat
 drydock-pins.json                  |  2 +-
 scripts/start_probe.py             | 89 +++++++++++++++++++++++++++++++++++++-
 tests/test_start_probe_discover.py |  1 +
 3 files changed, 90 insertions(+), 2 deletions(-)
```

- [ ] Verifier subagent reviewed the diff, tests, and evidence claims independently.

## Documentation Updates

- [ ] README or user-facing docs updated, if needed.
- [ ] Project context updated, if needed.
- [ ] Specs updated, if needed.
- [x] No documentation update needed. Reason: `README.md:10-13`,
      `PROJECT_CONTEXT.md:36-43`, and `sdd-plus/security/scope-contract.yml:32,35,85` already
      state the six-file closure and the mutating-four ban. This packet makes the existing prose
      mechanically enforced; it does not change the rule, so there is nothing new to document.

## Result

Pending.
