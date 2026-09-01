# Plan

## Change

grok-docs-coplan-runtime

Mode: LITE. Docs + one LGF contract correction. No behavior change, no code change.

Revision: round 2 of 2 (final). Round 1 was critiqued by Codex; two blocking concerns were
accepted and are addressed below (file-level allowlist in the yaml, §Step 3; re-runnable closure
check, §Step 0). See `decision-log.md`.

## Approach

Three committed files still encode the v1-before-coplan rule "`conductor/` is forbidden on this
VM". PR #10 vendored the six-file negotiate import closure and PR #12/#13 live-fired it, so that
wholesale ban is now stale and would tell the next session to refuse a loop that is already
runtime. The fix is a wording correction in three places that *narrows* the ban rather than
deleting it: the vendored read-only closure becomes allowed; mutating/unvendored conductor stays
forbidden.

Two sets of basenames drive every edit. All three target files must name **both sets in full** —
no file may list one set while another names only a directory or an abbreviation.

**Six-file allowlist** (vendored, pinned, read-only coplan runtime):

`negotiate.py`, `review.py`, `codex_bridge.py`, `negotiate_schema.json`, `review_schema.json`,
`__init__.py`

**Four-file mutating ban** (not vendored, not pinned, must not be vendored or run):

`mutate.py`, `coord.py`, `executors.py`, `handoff.py`

`mutate.py:477` carries the `subprocess-shell-true` Gate 7 finding that the archived
`grok-coplan-linux-discover` packet accepted *on the grounds that this repo forbids running it*.
Every edit below must leave that ban true and findable in prose, or that archived acceptance goes
stale.

### Step 0 — Re-confirm the closure invariant (BEFORE any edit)

The permission change is only sound if the vendored closure on disk is exactly the six pinned
files. Do not take that from this plan; re-run it:

```
ls scripts/conductor/
grep -E 'scripts/conductor/' drydock-pins.json
git ls-files scripts/conductor/
```

Confirm all three:

1. The tracked file set is exactly those six files. `ls` will also show `__pycache__/` — that is
   an untracked bytecode directory, not a vendored file. Ignore it; `git ls-files` is the
   authoritative form of the check and will not list it.
2. All six appear in `drydock-pins.json` under `scripts/conductor/<file>` (six pin lines, one per
   file).
3. None of `mutate.py`, `coord.py`, `executors.py`, `handoff.py` is present.

**If the on-disk set differs from the six-file pin set in either direction — an extra file, a
missing file, an unpinned file — STOP and tell the Owner.** Do not write an allowlist that does
not match the tree, and do not widen the allowlist to cover whatever happens to be sitting there.
A dirty tree is new information, not a licence to enlarge the permission.

(Checked at plan time on this branch: the six files were present, all six pinned, and none of the
four mutating files existed. That is a plan-time observation with a shelf life, not a substitute
for re-running the check at edit time.)

### Step 1 — `README.md:8`

Current line 8:

```
Do not copy client or LOQ files here. Do not run `conductor/` on this VM in v1.
```

Replace with (the client/LOQ sentence survives byte-identical; only the second sentence changes,
and the file gains one paragraph):

```
Do not copy client or LOQ files here.

The vendored read-only coplan closure is runtime on this VM: `scripts/conductor/negotiate.py`,
`review.py`, `codex_bridge.py`, `negotiate_schema.json`, `review_schema.json`, `__init__.py` —
those six files only, pinned in `drydock-pins.json`. Mutating conductor (`mutate.py`, `coord.py`,
`executors.py`, `handoff.py`) is not vendored and must not be vendored or run here.
```

Keep the ledger sentence at `README.md:6` intact and do not restate it; do not restructure the
file.

### Step 2 — `PROJECT_CONTEXT.md`

Two touches, both inside "Stack And Tools".

**Preferred** — add one bullet after `hashed scripts/check_verdict.py` (line 35):

```
- vendored read-only coplan closure — `scripts/conductor/` `negotiate.py`, `review.py`,
  `codex_bridge.py`, `negotiate_schema.json`, `review_schema.json`, `__init__.py` (those six files
  only, pinned in `drydock-pins.json`)
```

**Avoid line 39** — replace `- conductor/ on this VM` with:

```
- mutating/unvendored conductor: `mutate.py`, `coord.py`, `executors.py`, `handoff.py` (not
  vendored; must not be vendored or run on this VM)
```

Leave the other three Avoid entries (released LaunchGuardian 0.2.0 at line 40, client/LOQ files at
41, ledger in tree at 42) byte-identical. Do not touch Constraints, Durable Decisions, or
Definition Of Done — this packet is not a durable-decision change.

### Step 3 — `sdd-plus/security/scope-contract.yml`

String-level edits only. YAML keys, ordering, and list structure stay exactly as they are so the
document remains a valid LGF scope contract.

**`in_scope` — append as the last entry, after line 31.** This is the authoritative permission
grant, so it states the six files explicitly. Round 1 proposed "…negotiate closure under
`scripts/conductor/`"; that reads as a directory exception permitting anything later dropped into
the directory, and is the defect Codex flagged. Use this string verbatim:

```yaml
    - "Read-only coplan on the shared VM via the vendored six-file negotiate closure: scripts/conductor/{negotiate.py, review.py, codex_bridge.py, negotiate_schema.json, review_schema.json, __init__.py} — those six files only"
```

The braces are inside a double-quoted scalar, so they are literal text, not a YAML flow mapping.
The parse check in `verification.md` confirms this.

**`out_of_scope` line 34** — replace `- "conductor/ on this VM"` with:

```yaml
    - "Mutating/unvendored conductor (mutate.py, coord.py, executors.py, handoff.py) — not vendored, not run on this VM"
```

**`must_not_do` line 84** — replace `- "Copy client/LOQ files or run conductor/"` with:

```yaml
    - "Copy client/LOQ files, or vendor or run mutating conductor (mutate.py, coord.py, executors.py, handoff.py)"
```

The client/LOQ ban and the ledger-in-tree ban (`out_of_scope` lines 33 and 36, `must_not_do` line
85) are untouched.

### Step 4 — Post-edit consistency check (BEFORE filling verification)

All three files must name the same six allowlisted files and the same four banned files. Run:

```
grep -n "mutate.py" README.md PROJECT_CONTEXT.md sdd-plus/security/scope-contract.yml
```

Expect at least one hit in each of the three files. Then prove both sets are complete everywhere:

```
for f in README.md PROJECT_CONTEXT.md sdd-plus/security/scope-contract.yml; do
  for b in negotiate.py review.py codex_bridge.py negotiate_schema.json review_schema.json \
           __init__.py mutate.py coord.py executors.py handoff.py; do
    grep -qF "$b" "$f" || echo "MISSING $b in $f"
  done
done
```

Expect no output. Any `MISSING` line means one document is narrower or broader than the others —
fix it before proceeding; do not record a Result while the three disagree.

Then confirm nothing else moved:

```
git diff main -- README.md PROJECT_CONTEXT.md sdd-plus/security/scope-contract.yml
```

Read the diff and confirm the client/LOQ bans and the ledger-in-tree bans are byte-identical to
`main`: `README.md` keeps `Do not copy client or LOQ files here.` verbatim and line 6 unchanged;
`PROJECT_CONTEXT.md` lines 40–42 unchanged; `scope-contract.yml` lines 33, 36, 85 unchanged.

### Guard behavior (checked, not assumed)

- `packet_guard.py` will **not** deny any of these three writes. `is_exempt()`
  (`hooks/packet_guard.py:85`) exempts `*.md` basenames and any path with `sdd-plus` in its
  project-relative parts, which covers all three files; and `packet_active()` is true regardless,
  because this packet carries `tasks.md`.
- `protect_secrets.py` will not fire: its secret-name regex is `secrets?\.(json|ya?ml|toml)`, which
  does not match `scope-contract.yml`.
- **If `packet_guard` denies the yaml edit anyway: stop and tell the Owner.** Do not skip the
  contract file, do not land a partial two-file change and call it done, and do not route around
  the hook with shell redirection, `python -c`, `sed -i`, or any other write path. A README and
  PROJECT_CONTEXT that permit the closure while the LGF contract still bans it is worse than the
  current state, because the two would then disagree.

### Explicitly not in this change

- No `drydock-pins.json` edits. The six vendored files and their hashes are unchanged.
- No `scripts/start_probe.py` change, no `scripts/conductor/` change, no `discover_core` change.
- No `.github/workflows/` change, no CI change, no hook change, no scanner change.
- No test changes. Verified: nothing under `tests/` asserts the old sentences (no hit for `README`,
  `PROJECT_CONTEXT`, or `scope-contract` anywhere in `tests/`; the only `conductor` references
  there are `from conductor import codex_bridge` in the two discovery tests, which this change does
  not affect). If an implementer finds a test that does assert the old wording, that is new
  information — update the test in the same commit and record it in `decision-log.md`.
- No archive edits. `sdd-plus/archive/2026-09-01-grok-coplan-linux-discover/` is history and stays
  byte-identical, including its Gate 7 rationale that cites the README and the contract.
- No leftover-hole work: `.env` writes, `brief_engine.py` completeness, and the GitHub FF `--force`
  hole are out of scope for this packet and stay untouched.
- No commit, no push, no archive — not in the PLAN turn, and not as part of these implementation
  steps either. The implementer stops after `verification.md`; the Owner decides when to commit.

## Files Expected To Change

| File | Change | Lines |
| --- | --- | --- |
| `README.md` | Narrow the conductor ban to the four mutating files; name the six-file closure as runtime | 8 (+1 paragraph) |
| `PROJECT_CONTEXT.md` | Add the six-file closure to Preferred; narrow the Avoid entry to the four mutating files | ~35 (add), 39 (edit) |
| `sdd-plus/security/scope-contract.yml` | Narrow `out_of_scope` and `must_not_do` to the four mutating files; add a file-level six-file `in_scope` allowlist | 34, 84, +1 after 31 |
| `sdd-plus/changes/grok-docs-coplan-runtime/tasks.md` | Tick tasks as done | — |
| `sdd-plus/changes/grok-docs-coplan-runtime/verification.md` | Record evidence and Result | — |
| `sdd-plus/changes/grok-docs-coplan-runtime/decision-log.md` | Already records the two decisions; add rows only for new ones | — |

No other file is expected to change. A diff touching `drydock-pins.json`, `scripts/`, `tests/`,
`.github/`, `hooks/`, or `sdd-plus/archive/` means the change has drifted out of scope.

## Risks

- **Over-widening via directory-exception wording.** The specific failure mode: granting the
  permission as a path prefix — "the closure under `scripts/conductor/`" — instead of an
  enumerated allowlist. That phrasing permits whatever is in the directory *later*, so vendoring
  `mutate.py` tomorrow would land pre-approved by the contract that was supposed to forbid it. This
  is the round-1 defect Codex caught in the proposed `in_scope` line. Mitigation: the yaml
  `in_scope` string names all six basenames and ends "those six files only" (Step 3); the Step 0
  check ties that list to the pin file before the edit; Step 4 proves all three documents carry the
  same ten basenames.
- **Over-widening by deletion.** Deleting the conductor entries outright would silently permit
  `mutate.py` and its `shell=True` surface. Mitigation: every edit replaces the ban with a narrower
  ban; none removes a line without a replacement. Reviewer check: the Step 4 `mutate.py` grep must
  return hits in all three files.
- **Editing against a drifted tree.** If someone vendored a seventh file, an allowlist written from
  this plan would either be wrong or would be widened to bless it. Mitigation: Step 0 runs before
  any edit and STOPs on mismatch rather than adapting. Secondary trap: `ls` shows `__pycache__`,
  which is not drift — do not STOP on it, and do not "fix" it by adding it to the allowlist.
- **Stranding the archived Gate 7 acceptance.**
  `sdd-plus/archive/2026-09-01-grok-coplan-linux-discover/verification.md:46` accepts the
  `subprocess-shell-true` finding because "running mutating delegation on this VM is already
  forbidden by `README.md` and `sdd-plus/security/scope-contract.yml`". If the new wording stops
  naming `mutate.py` specifically, that citation no longer resolves. Mitigation: name all four
  mutating files explicitly in all three documents. Do not edit the archive to compensate.
- **Under-fixing / partial landing.** Fixing README and PROJECT_CONTEXT but not the yaml leaves the
  authoritative security contract still banning the loop, and docs now contradicting it. Mitigation:
  all three or none; if the yaml is blocked, stop and escalate to the Owner (see Guard behavior).
- **Prose does not enforce.** This change moves a permission boundary in prose only. Nothing in the
  tree mechanically prevents someone vendoring `mutate.py` tomorrow — the pin file would flag an
  unpinned addition, but that is a side effect, not a guard. Accepted for LITE; if the Owner wants
  enforcement, that is a separate packet (a pin/closure check), not this one.
- **YAML validity.** Hand-editing quoted strings can break the document, and the new `in_scope`
  string contains `{`, `}`, and `—`. Low risk (no script parses it today, so a break would be
  silent), so verification parses it explicitly rather than assuming.
- **Scope creep into the smoke/leftover backlog.** The brief lists tempting adjacent holes. They are
  out of scope; a LITE docs packet does not become a cleanup sweep.

## Rollback

Doc-only and fully reversible; no runtime state, no schema, no pins, no deployed surface.

- Before commit: `git checkout -- README.md PROJECT_CONTEXT.md sdd-plus/security/scope-contract.yml`.
- After commit on the packet branch: `git revert <sha>`, or abandon `packet/grok-docs-coplan-runtime`
  without merging. Never `reset --hard` or force-push — the git-safety hook blocks it and the Owner
  has not authorized it.
- Reverting restores the wholesale `conductor/` ban. That is a safe fallback: it is more restrictive
  than the new wording, so nothing that depends on the ban is weakened by a rollback. The only cost
  is the stale-refusal defect returning.
- Partial rollback (reverting one file, keeping the other two) is not a valid state — the three
  documents must agree. Roll back all three or none.
