# Brief

## Change

grok-coplan-closure-gate

## Mode

LITE. One production file (`scripts/start_probe.py`), one new test file, one pin value, one
one-line stub addition in an existing test file. No contract change to `scripts/conductor/*`,
no schema, no auth, no migration, no side effects beyond the probe's existing exit code and JSON.

**Round 2 of 2 (final)** of coplan negotiation. Round 1 returned three blocking concerns; the
Pilot's audit of each — accept / reject / partial, with the repo inventory that settles the
factual half — is in `plan.md` §0 and `decision-log.md`. The residual policy calls are OQ-1..OQ-3
below; each has a default matching the Owner's stated intent, so none of them blocks
implementation.

## User Need

The Owner needs the six-file coplan closure to be *mechanically* enforced, not merely described.
Today the boundary that keeps this VM's coplan read-only lives in prose that no process reads.
The Owner wants a failure, in local runs and in CI, the moment the vendored conductor tree grows
a seventh file or the mutating four appear — not a later discovery that something mutating got
vendored and ran.

## Problem

The read-only coplan closure is exactly six files under `scripts/conductor/`
(`negotiate.py`, `review.py`, `codex_bridge.py`, `negotiate_schema.json`, `review_schema.json`,
`__init__.py`), pinned at `drydock-pins.json:26-31`. The mutating four (`mutate.py`, `coord.py`,
`executors.py`, `handoff.py`) must never be vendored or run here.

That ban is **prose only** today:

- `README.md:10-13` — "those six files only … must not be vendored or run here"
- `PROJECT_CONTEXT.md:36-38, 42-43` — same statement, under "Avoid"
- `sdd-plus/security/scope-contract.yml:32, 35, 85` — in_scope six files, out_of_scope mutating
  four, `must_not_do: "…vendor or run mutating conductor…"`

Nothing checks it:

- **`check_pins()` (`scripts/start_probe.py:53-69`) only verifies that pinned files exist and
  that their hashes match.** It iterates `pins["files"]` and never looks at what else is sitting
  in `scripts/conductor/`. A seventh file — including `mutate.py` — passes `check_pins()`
  silently, because an unpinned file is simply not in the map being iterated. That is the hole.
- `hooks/packet_guard.py` does not deny the mutating four. Its deny tier
  (`hooks/packet_guard.py:105-128`) covers exactly three classes: schema migrations, new CI
  workflow/config, and container build/deploy config. There is no conductor class. It also
  silent-allows on any error by design (`hooks/packet_guard.py:16`), and it is a Claude Code
  PreToolUse hook — **Grok Shell is not behind it at all**, so a hook can never be the closure
  gate for this VM.
- `scripts/check_secret_tree.py` walks the tree for secrets only; it has no conductor knowledge.

`scripts/start_probe.py` already runs in both places that matter — locally, and in CI at
`.github/workflows/drydock.yml:24` (`run: python3 scripts/start_probe.py`, exit code consumed) —
and is already the fail-closed gate for pins, hooks, the secret tree, backstop installation, and
Codex discovery. It is the right place for the closure check.

## Scope

In scope:

- A new fail-closed check in `scripts/start_probe.py` asserting two conjoined claims — stated
  this way deliberately, because round 1 called it "closure" while permitting untracked
  accretion, and that overclaimed:
  - **tracked-set closure** — the set of **tracked** files under `scripts/conductor/` is exactly
    the six pinned files; any extra tracked file fails, whatever it is named;
  - **on-disk presence ban** — none of `mutate.py`, `coord.py`, `executors.py`, `handoff.py`
    **exists** anywhere under `scripts/conductor/`, tracked or not, including as bytecode
    (`__pycache__/coord.cpython-313.pyc`) or as an extensionless file (`mutate`);
  - plus, by default, none of those four basenames is **tracked anywhere in the repo** (OQ-3).

  What is *not* asserted, plainly: an untracked, non-mutating extra file under
  `scripts/conductor/` does not fail (OQ-1).
- One additive JSON key on the probe's stdout (`conductor_errors`), with an explicit
  compatibility contract.
- A new test file exercising the check against fake trees under `tmp_path`.
- Re-pinning `scripts/start_probe.py` in `drydock-pins.json` (one value).
- A one-line addition to `_stub_other_checks` in `tests/test_start_probe_discover.py` so the
  existing `main()` tests stay hermetic. No assertion in that file changes.

Out of scope — parked leftover holes, explicitly **not** touched by this packet:

- `.env` write handling / secrets-hook widening.
- `kernel/brief_engine.py` completeness (no rewrite, no edit).
- GitHub fast-forward `--force` work.
- The verifier-checkbox slog.

Out of scope — boundaries for this packet specifically:

- **No mutating file is planted in the live tree.** Not in `scripts/conductor/`, not anywhere
  else, not as a test fixture. Tests build fake conductor trees under `tmp_path` only.
- No change to any of the six vendored conductor files, including `discover_core()`.
- No rewrite of `hooks/packet_guard.py`. This is deliberate, and it is an argument, not an
  omission: the guard is a Claude Code PreToolUse hook that Grok Shell never invokes, it
  silent-allows on error by design, and it governs *writes at authoring time* rather than *the
  state of the tree*. A closure invariant must be checkable after the fact, by CI, on any
  machine — that is `start_probe`, not a hook. The Owner asked for `start_probe`; this packet
  agrees with that call and does not touch the hook.
- No `.github/workflows/drydock.yml` edit. CI already runs the probe and consumes its exit code;
  the probe adapts, the workflow does not.
- No new capability spec. This is a behavior addition to an existing fail-closed gate, matching
  the two prior coplan LITE packets, which kept only `specs/EXAMPLE-capability.md.template`.
- No commit, no push, no archive, no `negotiate.py` run in the planning turn.

## Acceptance Criteria

- [ ] `python3 scripts/start_probe.py` on the clean live tree exits 0 with `"conductor_errors": []`.
- [ ] A tracked seventh file under `scripts/conductor/` makes the probe fail (exit 1) with a
      `conductor_errors` entry naming that file.
- [ ] Each of `mutate.py`, `coord.py`, `executors.py`, `handoff.py` placed under
      `scripts/conductor/` makes the check fail **even when untracked** — including in a
      subdirectory, as bytecode (`__pycache__/coord.cpython-313.pyc`), and as an extensionless
      file (`mutate`).
- [ ] A banned stem with a benign suffix (`coord.json`, `handoff.md`) does **not** fail — the
      check is a stem+suffix rule, not a substring match.
- [ ] A tracked mutating basename **outside** `scripts/conductor/` also fails. *(Drop this
      criterion if the Owner narrows OQ-3 to directory scope.)*
- [ ] A missing pinned conductor file produces a `check_pins()` failure only — the new check does
      not duplicate that failure mode.
- [ ] Untracked non-mutating files under `scripts/conductor/` — ordinary `__pycache__` bytecode of
      an *allowed* module, and a plain `helper.py` — do **not** fail the check (OQ-1 default).
- [ ] `discover_errors` (`list[str]`) and `discover_skipped` (`str`) keep their exact names,
      types, and always-present status; no existing JSON key is removed, renamed, or retyped.
- [ ] No mutating conductor file exists anywhere in the working tree after the change —
      including under `tests/` and `scripts/conductor/`.
- [ ] Full suite green: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`.
- [ ] `scripts/start_probe.py` re-pinned in `drydock-pins.json`, probe green after re-pin.

## Impact Areas

- Backend: `scripts/start_probe.py` only — one new function plus three lines in `main()`.
- Frontend: none.
- Data model: none.
- API: the probe's stdout JSON gains one additive key (`conductor_errors`). Contract in `plan.md`.
- AI/model behavior: none. The check never spawns Codex and never imports `negotiate.py`.
- Documentation: none required — README, PROJECT_CONTEXT, and the scope contract already state
  the rule; this packet makes the existing prose enforced rather than restating it.
- Operations/security: the probe gains a new dependency on `git ls-files` for the tracked-file
  listing. Fails closed if git is unavailable. `.git` is already a hard requirement of the probe
  (`scripts/start_probe.py:140` errors when `.git` is missing), and CI checks out with git, so
  this adds no new environmental assumption in practice.

## Open Questions

Three Owner policy calls, surfaced by the round-1 critique and adjudicated in `plan.md` §0. Full
statements, evidence and deltas are in `plan.md` § "Open Questions — Owner policy calls".

**None of these blocks implementation.** Each has a default that matches the Owner's stated
intent; if the Owner does not answer, the implementer builds the defaults. Any answer is a small
costed edit, not a re-plan.

- **OQ-1 — should the gate also fail on non-ignored *untracked* files under
  `scripts/conductor/`?** Default: **no** — the Owner's intent is that the *tracked* set is
  exactly six. Worth an answer because it is cheaper than it looks:
  `git ls-files --others --exclude-standard scripts/conductor/` is **empty on the current tree**
  (the three `__pycache__` entries are already ignored by `.gitignore`), so adopting it would cost
  ~15 lines and would not fail today. Cost of "yes": local dev scratch under that directory starts
  failing the probe.
- **OQ-2 — is filename-based detection enough, or does the Owner want content-based detection of
  renamed mutating code?** Default: **filename-based is enough for this packet.** The threat
  model is drift and accidental vendoring, not a determined operator; renaming *inside*
  `scripts/conductor/` is already defeated by tracked-set closure plus the sha256 pins on the six.
  Content or AST-based detection would be its own packet, not a LITE addition.
- **OQ-3 — should `mutate` / `coord` / `executors` / `handoff` be reserved basenames
  repo-wide, or only under `scripts/conductor/`?** Default: **repo-wide, tracked-only**, because
  `README.md:12-13` bans vendoring "here" (this repo) and directory-scope alone is evaded by
  committing one level up. Inventory shows **zero collisions today** across 118 tracked files, so
  nothing breaks now; the cost is a future legitimately-named `coord.py` needing an Owner-approved
  `BANNED_STEMS` edit. This is the one place the packet exceeds the literal wording of the Owner's
  intent line, which is why it is asked rather than assumed. Narrowing is three deletions
  (`plan.md` §3).

Residual, accepted and documented: an **untracked, non-mutating** extra file dropped into
`scripts/conductor/` does not fail (this is OQ-1). It is not a `__pycache__` carve-out — the check
never enumerates untracked files except to look for the four banned stems, and bytecode of a
*banned* module does fail.
