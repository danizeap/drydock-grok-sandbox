# Verification

## Change

grok-docs-coplan-runtime

## Automated Checks

- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passes.
- [x] `python3 scripts/start_probe.py` exits 0.
- [x] `python3 -c "import yaml,sys; yaml.safe_load(open('sdd-plus/security/scope-contract.yml'))"`
      parses (the edited contract is still valid YAML).
- [x] `git status --porcelain` shows only `README.md`, `PROJECT_CONTEXT.md`,
      `sdd-plus/security/scope-contract.yml`, and this packet directory.

### Evidence (implementer run, 2026-09-01, branch `packet/grok-docs-coplan-runtime`, base `e948054`)

**Step 0 — closure invariant, run before any edit.**

`git ls-files scripts/conductor/` (authoritative) returned exactly six paths:
`__init__.py`, `codex_bridge.py`, `negotiate.py`, `negotiate_schema.json`, `review.py`,
`review_schema.json`. `ls scripts/conductor/` returned the same six plus untracked `__pycache__`
(expected bytecode noise, not drift). `grep -E 'scripts/conductor/' drydock-pins.json` returned six
pin lines, one per file, matching the tracked set exactly. None of `mutate.py`, `coord.py`,
`executors.py`, `handoff.py` was present in any of the three outputs. No drift; no STOP condition;
allowlist written from the tree, not widened to it.

**Post-edit consistency (plan Step 4).**

`grep -n "mutate.py" README.md PROJECT_CONTEXT.md sdd-plus/security/scope-contract.yml` → 4 hits,
at least one in each of the three files: `README.md:12`, `PROJECT_CONTEXT.md:42`,
`scope-contract.yml:35` and `:85`. The archived Gate 7 acceptance rationale still resolves.

Ten-basename × three-file loop (six allowlisted + four banned) printed **no output** — no `MISSING`
line. All three documents carry both sets in full.

**YAML parse.**

```
$ python3 -c "import yaml; d=yaml.safe_load(open('sdd-plus/security/scope-contract.yml')); ..."
YAML_OK
in_scope entries: 5
'Read-only coplan on the shared VM via the vendored six-file negotiate closure: scripts/conductor/{negotiate.py, review.py, codex_bridge.py, negotiate_schema.json, review_schema.json, __init__.py} — those six files only'
```

PyYAML was present; no fallback needed. The braces round-trip as literal characters inside the
double-quoted scalar — the parser returns a string, not a flow mapping, so the document is still a
valid LGF scope contract.

**Tests.**

```
$ PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
51 passed in 0.90s
```

No test asserted the old wording. A case-insensitive grep of `tests/` for `README`,
`PROJECT_CONTEXT`, `scope-contract`, and `conductor/ on this VM` matched only
`tests/test_pre_commit_tree.py:32-33`, which writes a synthetic `readme.txt` fixture inside a temp
repo and is unrelated to this repo's `README.md`. No test change was needed, so no new
decision-log row.

**Start probe.**

```
$ python3 scripts/start_probe.py ; echo $?
{"ok": true, "pin_errors": [], "hook_errors": [], "secret_tree_errors": [],
 "pre_push_errors": [], "pre_commit_errors": [], "discover_errors": [], ...}
0
```

`hook_evidence` recorded all three self-tests as expected: `git_safety_deny` → deny,
`protect_secrets_deny` → deny, `git_safety_allow_benign` → allow. Pins still verify, so the six
conductor hashes are unchanged by this packet.

**Scope of the diff.**

```
$ git status --porcelain
 M PROJECT_CONTEXT.md
 M README.md
 M sdd-plus/security/scope-contract.yml
?? sdd-plus/changes/grok-docs-coplan-runtime/
```

Three target files plus this packet directory. No `drydock-pins.json`, no `scripts/`, no `tests/`,
no `.github/`, no `hooks/`, no `sdd-plus/archive/`.

**Guard behavior.**

`packet_guard` did **not** deny any of the three writes, including
`sdd-plus/security/scope-contract.yml` — matching the plan's predicted `is_exempt()` behavior. All
edits went through the Edit tool with hooks live; nothing was routed around a hook via shell
redirection, `python -c`, or `sed -i`. No partial two-file landing.

## Manual Checks

- [ ] `README.md` no longer forbids running the vendored negotiate closure on this VM.
- [ ] `PROJECT_CONTEXT.md` Avoid list bans mutating conductor; Preferred names the closure.
- [ ] `scope-contract.yml` `out_of_scope` and `must_not_do` no longer ban `conductor/` wholesale, and
      still ban mutating/unvendored conductor plus client/LOQ copies.
- [ ] Client/LOQ and ledger-in-tree bans are byte-identical to `main` in all three files.
- [ ] `grep -rn "mutate.py" README.md PROJECT_CONTEXT.md sdd-plus/security/scope-contract.yml`
      returns a hit in each — the archived Gate 7 acceptance rationale still resolves.
- [ ] `sdd-plus/archive/` is unmodified.

**Manual checks are verifier-owned and deliberately left unchecked.** The verifier subagent was not
invoked for this packet. The notes below are implementer observations offered as an audit trail, not
verification — a verifier should confirm them independently against the diff.

Implementer notes for the auditor:

- `README.md:8` now reads `Do not copy client or LOQ files here.` byte-identical to `main`; the
  wholesale `Do not run conductor/ on this VM in v1.` sentence is replaced by a paragraph that
  names the six-file closure as runtime and the four mutating files as forbidden. `README.md:6`
  (ledger sentence) is untouched.
- `PROJECT_CONTEXT.md` gained one Preferred bullet naming the six files; the Avoid entry now names
  the four mutating files. Avoid entries for released LaunchGuardian 0.2.0, client/LOQ files, and
  ledger-in-tree are unchanged in the diff. Constraints, Durable Decisions, and Definition Of Done
  were not touched.
- `scope-contract.yml` gained one `in_scope` entry (file-level allowlist ending "those six files
  only"), and `out_of_scope`/`must_not_do` now name the four mutating files instead of banning
  `conductor/` wholesale. YAML keys, ordering, and list structure are unchanged.
- `git diff main` for the three files shows the client/LOQ bans and the ledger-in-tree bans only as
  unchanged context lines — `scope-contract.yml` lines 33, 36, and 85's client/LOQ and ledger
  clauses were not re-emitted as `-`/`+` pairs.
- `git status --porcelain` lists no path under `sdd-plus/archive/`, so the archived
  `grok-coplan-linux-discover` packet is unmodified.

## Documentation Updates

- [x] README or user-facing docs updated, if needed.
- [x] Project context updated, if needed.
- [ ] Specs updated, if needed. (No behavior change — no delta spec expected for this LITE packet.)
- [ ] No documentation update needed. Reason:

## Result

`implementer-checked` — NOT independently verified.

Narrowed the stale wholesale `conductor/` ban to the four mutating files (`mutate.py`, `coord.py`,
`executors.py`, `handoff.py`) in `README.md`, `PROJECT_CONTEXT.md`, and
`sdd-plus/security/scope-contract.yml`, and recorded the vendored six-file negotiate closure as
allowed read-only coplan runtime on this VM. Docs-only, no behavior change: 51 tests pass,
`start_probe.py` exits 0, the contract still parses as YAML, and the verifier subagent has not yet
reviewed this diff.
