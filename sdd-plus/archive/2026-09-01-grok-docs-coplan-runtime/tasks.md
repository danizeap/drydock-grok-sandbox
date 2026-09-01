# Tasks

## Change

grok-docs-coplan-runtime

## Implementation

- [x] **Step 0 (before any edit)** — run `ls scripts/conductor/`, `grep -E 'scripts/conductor/'
      drydock-pins.json`, and `git ls-files scripts/conductor/`. Confirm the tracked set is exactly
      `negotiate.py`, `review.py`, `codex_bridge.py`, `negotiate_schema.json`, `review_schema.json`,
      `__init__.py`; that all six are pinned; and that `mutate.py`, `coord.py`, `executors.py`,
      `handoff.py` are absent. `__pycache__/` is expected untracked noise, not drift. If the on-disk
      set differs from the pin set, STOP and tell the Owner — do not widen the allowlist.
- [x] `README.md:8` — keep `Do not copy client or LOQ files here.` byte-identical; replace the
      `conductor/` sentence with the two-sided paragraph naming all six allowlisted files and all
      four mutating files (exact string in `plan.md` Step 1).
- [x] `PROJECT_CONTEXT.md` — add the six-file closure to Preferred after line 35; narrow Avoid line
      39 to the four mutating files. Leave Avoid lines 40–42 untouched (exact strings in `plan.md`
      Step 2).
- [x] `sdd-plus/security/scope-contract.yml` — add the `in_scope` entry that lists the six files
      by name (a **file-level allowlist**, not `under scripts/conductor/`); narrow `out_of_scope`
      line 34 and `must_not_do` line 84 to the four mutating files (exact strings in `plan.md`
      Step 3). If `packet_guard` denies this write, STOP and tell the Owner — do not skip the
      contract file, do not land a partial two-file change, do not route around the hook.
- [x] **Post-edit consistency** — `grep -n "mutate.py" README.md PROJECT_CONTEXT.md
      sdd-plus/security/scope-contract.yml` hits all three files; the ten-basename loop in `plan.md`
      Step 4 prints nothing; `git diff main` shows the client/LOQ and ledger-in-tree bans
      byte-identical in all three files.
- [x] Confirm no test asserted the old wording (expected: none). If one did, update it in the same
      commit and log it in `decision-log.md`.
- [x] Run `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`.
- [x] Run `python3 scripts/start_probe.py` (expect exit 0).
- [x] Confirm the diff touches only the three target files plus this packet — no pins, no `scripts/`,
      no `tests/`, no `.github/`, no `hooks/`, no `sdd-plus/archive/`.
- [x] Fill `verification.md` with evidence and set Result. Stop there — no commit, no push, no
      archive until the Owner says so.

Notes:

- `packet_guard` did not deny any of the three writes, including the yaml. All three landed; no
  partial state.
- Commit: the Owner's implementer assignment explicitly overrode the plan's "no commit" line and
  required one commit on `packet/grok-docs-coplan-runtime`. No push, no archive, no amend.
- Verification is implementer-checked only. The verifier subagent was not invoked (per assignment);
  verifier-owned Manual Checks in `verification.md` are left unchecked.
