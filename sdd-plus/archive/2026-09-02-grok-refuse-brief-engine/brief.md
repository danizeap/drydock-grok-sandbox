# Brief

## Change

grok-refuse-brief-engine

## Mode

LITE. **Round 2 of 2 (final).** Leftover hole 2 only. Three production files in known locations
(`kernel/brief_engine.py`, a new `kernel/brief_complete_engine.py` holding *moved bytes*,
`scripts/record_verify_bound.py`), one existing test file, and three pin values in
`drydock-pins.json`. No auth, no schema, no migration, no workflow edit, no conductor edit,
no hook edit.

**On the contract, stated precisely.** Round 1 described this as "no contract change"; that was
wrong and is withdrawn. Two separate claims replace it:

1. The completeness CLI **at the new path** is unchanged — `kernel/brief_complete_engine.py` is
   byte-identical to today's engine, so `--write-status`, `--lang`, `--record-verify NAME` and the
   bare FACTS JSON behave identically.
2. The **old path** gains a refusal that today does not exist, and under the OQ-1 default that
   refusal is stricter than `kernel/brief.py:28`. Because `kernel/brief.py` and `scripts/brief.py`
   delegate their non-matching modes into that path, this changes their observable behavior —
   including exit codes — without either file being edited. The deltas are enumerated in plan
   §Behavior deltas on unedited files.

Additive refusal at the old path, unchanged completeness at the new one. Not a pure byte
relocation.

## User Need

The Owner must be able to trust that "recorded: true" in the Drydock ledger means a verify-run was
bound to an in-channel report hash — not that someone typed a PASS and ran a completeness command.
Today that trust has a named leak, and the Owner has said the leftover holes are unparked and must
be closed before any real project is migrated onto this framework.

## Problem

Case 5b: bare `--record-verify` records *completeness*, not *provenance*. Three entry points were
hardened in earlier packets — `kernel/brief.py:27-54`, `kernel/brief_complete.py:13-16` (execs the
overlay), and `scripts/brief.py:25-52` all refuse the bare form and route the four-argument bound
form through `scripts/record_verify_bound.py`, which runs `scripts/check_verdict.py` first
(`scripts/record_verify_bound.py:33-53`).

**The hole is the fourth entry point: the completeness engine itself.**

```
python3 kernel/brief_engine.py --record-verify NAME
```

still goes straight to `record_verify()` (`kernel/brief_engine.py:514`, dispatched at
`:548` and `:556-557`) and, on a passing packet gate, calls `append_event(...)`
(`kernel/brief_engine.py:536`) to write a `verify-run` ledger event. No `check_verdict`, no
in-channel hash, no binding. Every wrapper's refusal is one path segment away from being bypassed,
and `kernel/brief_engine.py:11` documents that mode in its own usage text.

The repo's own test suite states the hole as a fact rather than a defect:
`tests/test_kernel_brief_overlay.py:38-42` (`test_completeness_engine_still_has_bare_mode`,
docstring "Honest leftover: the vendored engine can still record completeness").

Two Owner constraints shape the fix. The completeness bytes are pinned at sha256
`aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b`
(`drydock-pins.json:25`), unchanged from Drydock `kernel/brief.py` @ `5f76f67`, and must stay
byte-identical — so the logic cannot be rewritten, only **moved**. And the moved file must stay
directly under `kernel/`, because `_HOOKS = Path(__file__).resolve().parent.parent / "hooks"`
(`kernel/brief_engine.py:42`) resolves `hooks/` from the file's grandparent directory.

## Scope

In scope:

- Move the completeness bytes from `kernel/brief_engine.py` to `kernel/brief_complete_engine.py`,
  unchanged, sha256 still `aa3ba09…`.
- Replace `kernel/brief_engine.py` with a refuse/bound overlay in the shape of
  `kernel/brief.py:27-68`: bare `--record-verify` refused with exit 1 and JSON
  `reason=bare-record-verify-refused`; the exact four-argument bound form `os.execv`s
  `scripts/record_verify_bound.py`; every other mode delegated unchanged to the moved
  completeness file.
- Retarget `scripts/record_verify_bound.py:21` (`BRIEF`) at the moved completeness file, so the
  bound path does not hit the new overlay and refuse itself. Update its docstring
  (`scripts/record_verify_bound.py:7`), which currently names `kernel/brief_engine.py` as the
  thing not to call directly.
- Retarget `tests/test_kernel_brief_overlay.py:10` (`ENGINE`) at the moved file, and add tests
  asserting the *overlay* at `kernel/brief_engine.py` refuses.
- Update `drydock-pins.json`: new hash for `kernel/brief_engine.py` (now the overlay), new key
  `kernel/brief_complete_engine.py` = `aa3ba09…`, new hash for `scripts/record_verify_bound.py`.

Out of scope:

- **Leftover hole 1** — `.env` write handling.
- **Leftover hole 3** — `archive --force` / verifier checkboxes.
- **Leftover hole 4** — GitHub fast-forward `--force`.
- **Any rewrite of the completeness logic.** The bytes move; not one line changes.
- **`hooks/packet_guard.py`** — no rewrite, no extension. `kernel/` is not one of its deny classes
  (`hooks/packet_guard.py:105-128`: schema migrations, new CI config, container config) and this
  packet does not make it one.
- **`.github/workflows/drydock.yml`** — no workflow edit.
- **`scripts/conductor/*`** — no conductor edit; the closure pinned by the previous packet stands.
- **`scripts/start_probe.py`** — no code edit. `check_pins()` iterates `pins["files"].items()`
  (`scripts/start_probe.py:76`), so adding a pin key needs no probe change, and the
  `scripts/start_probe.py` pin (`drydock-pins.json:12`) therefore does not move.
- **`kernel/brief.py`, `kernel/brief_complete.py`, `scripts/brief.py`** — deliberately not edited;
  they may keep pointing at `kernel/brief_engine.py`, which is now the overlay (see plan §2). Their
  pins (`drydock-pins.json:7-8`, `:24`) stay unchanged. **Not edited is not the same as not
  affected:** under the OQ-1 default their equals-form and abbreviation passthroughs are refused
  by the new overlay, which is a behavior change on all three (plan §Behavior deltas on unedited
  files). That is in scope and intended; editing the files is not.

## Acceptance Criteria

- [ ] `python3 kernel/brief_engine.py --record-verify NAME` exits **1** and prints JSON with
      `recorded: false` and `reason: "bare-record-verify-refused"`. No ledger event is written.
- [ ] The exact bound form
      `python3 kernel/brief_engine.py --record-verify <packet> <verdict-file> <sha256> <verdict-string>`
      still reaches `scripts/record_verify_bound.py`: a wrong hash yields
      `reason: "check_verdict-failed"`, and a *correct* hash gets past `check_verdict` into the
      completeness engine (proving the bound path is not self-refusing).
- [ ] `sha256sum kernel/brief_complete_engine.py` is
      `aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b` — byte-identical to the
      pre-change `kernel/brief_engine.py`.
- [ ] `_HOOKS` still resolves from the moved file: `python3 kernel/brief_complete_engine.py`
      (no arguments) exits 0 and prints the FACTS JSON, which is only possible if the
      `hooks/_drydock_common.py` import at `kernel/brief_engine.py:42-46` succeeded.
- [ ] `python3 kernel/brief_engine.py` (no arguments) still exits 0 and prints the FACTS JSON,
      delegated through the overlay.
- [ ] `python3 scripts/brief.py`, `python3 kernel/brief.py` and `python3 kernel/brief_complete.py`
      keep their current behavior — bare refused, bound bound, other modes delegating — with those
      three files unedited.
- [ ] `python3 scripts/start_probe.py` reports `"ok": true` with `pin_errors: []`, including the
      new `kernel/brief_complete_engine.py` pin.
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` is green, including the
      pre-existing `tests/test_brief_wrapper.py` and `tests/test_record_verify_bound.py`.

## Impact Areas

- Backend: `kernel/brief_engine.py` becomes an overlay; completeness moves to
  `kernel/brief_complete_engine.py`; `scripts/record_verify_bound.py` retargeted. No behavior of
  the completeness engine itself changes.
- Frontend: none.
- Data model: none. The ledger event shape written by
  `append_event(...)` (`kernel/brief_engine.py:536`) is untouched; this packet changes *who may
  cause* one, not what one looks like.
- API: no external API. The completeness CLI contract (`--write-status`, `--lang`,
  `--record-verify NAME`, bare FACTS JSON) is unchanged at its new path; the overlay is additive
  refusal at the old path.
- AI/model behavior: none directly; the point is that an agent cannot mint a provenance claim by
  reaching one level below the wrappers.
- Documentation: `scripts/record_verify_bound.py:7`'s docstring is the only prose in the live tree
  that names the completeness path (`grep -rn brief_engine` over tracked `*.py`/`*.md`/`*.json`/
  `*.yml`, excluding `sdd-plus/archive/`, hits only the files listed in scope). `README.md`,
  `AGENTS.md` and `PROJECT_CONTEXT.md` do not name it, so no doc edit is required.
- Operations/security: this is the security change. It removes the last documented direct route to
  an unbound `verify-run` ledger event. Residual limits are stated honestly in plan §Risks.

## Open Questions

One policy call, carried from round 1 with its default unchanged. It is **not** blocking
implementation — the default is stated and buildable — but it is a real Owner decision with a real
cost, and Codex round 1 was correct that round 1's phrasing buried it.

- **OQ-1 — should the overlay's `--record-verify` matcher be stricter than
  `kernel/brief.py:28`'s?** Verified on this VM (Python 3.13.5) against a replica of the engine's
  own parser (`kernel/brief_engine.py:545-549`): argparse also accepts `--record-verify=NAME` and
  unambiguous abbreviations (`--record-ver NAME`, `--record NAME`, `--rec=NAME`, even `--r NAME`),
  and the existing `"--record-verify" in argv` guard matches **none** of them.

  **Default (build this):** the new overlay matches all those spellings and refuses anything that
  is not the canonical bound form. Because `kernel/brief.py:65-68` and `scripts/brief.py:63-66`
  delegate their non-matching modes *to this overlay*, the strict matcher closes the same gap for
  them without editing or re-pinning either file.

  **What it costs, corrected in round 2.** Round 1 claimed "nothing that currently works stops
  working." That is false and is withdrawn: `python3 kernel/brief.py --record-verify=NAME` today
  reaches `record_verify()` and exits 0, and under the default it will be refused with exit 1.
  The accurate, narrower claim — confirmed by a repo-wide grep this round — is that **no caller in
  this repo uses those spellings**; the sole executing caller,
  `scripts/record_verify_bound.py:55`, uses the canonical two-token form. So the tightening breaks
  zero known callers, and every delta moves in the refuse direction, never toward an easier
  `append_event`. The literal-copy fallback and its cost are in plan §OQ-1.

  **Owner decision needed only if you reject that trade.** Silence means build the default.
