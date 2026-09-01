# Brief

## Change

grok-docs-coplan-runtime

## User Need

The sandbox already runs coplan (`scripts/conductor/negotiate.py`, six-file closure on main via PR #10). Humans and implementers still read README, PROJECT_CONTEXT, and the LGF scope contract, which all say `conductor/` is forbidden on this VM. That stale ban is now a defect: it tells the next Claude/Codex session to refuse the loop we just live-fired.

## Problem

Three committed files still encode the v1-before-coplan rule:

- `README.md:8` — "Do not run `conductor/` on this VM in v1."
- `PROJECT_CONTEXT.md:39` — Avoid: `conductor/ on this VM`
- `sdd-plus/security/scope-contract.yml:34` and `:84` — out_of_scope / must_not_do: `conductor/` on this VM

PR #10 vendored the negotiate import closure and PR #12/#13 live-fired it. Design r11 says that closure is runtime. Mutating conductor (`mutate.py`, `coord.py`, `executors.py`, `handoff.py`) stays unvendored and stays forbidden.

## Scope

In scope:

- Rewrite those three files so the six-file negotiate closure (`negotiate.py`, `review.py`, `codex_bridge.py`, two schemas, `__init__.py`) is allowed as read-only coplan on this VM.
- Keep mutating conductor forbidden (not vendored; `subprocess-shell-true` in `mutate.py`).
- Keep client/LOQ copies, ledger-in-tree, and leftover-hole slog out of scope in those docs.
- No code, no pin changes, no workflow edits, no `discover_core` changes.

Out of scope:

- Leftover holes (`.env` writes, `brief_engine.py` completeness-only, GitHub FF `--force`).
- Vendoring more conductor files.
- Changing start_probe or CI.
- Archiving this packet.

Mode: LITE. Docs + one LGF contract correction. No behavior change.

## Acceptance Criteria

- [ ] `README.md` no longer forbids running the vendored negotiate closure on this VM.
- [ ] `PROJECT_CONTEXT.md` Avoid list matches: mutating conductor out; negotiate closure in.
- [ ] `sdd-plus/security/scope-contract.yml` `out_of_scope` and `must_not_do` no longer ban `conductor/` wholesale; they still ban mutating/unvendored conductor and client/LOQ copies.
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` still passes (no test changes required unless a test asserted the old sentence).
- [ ] `python3 scripts/start_probe.py` still exits 0.

## Impact Areas

- Backend: none.
- Frontend: none.
- Data model: none.
- API: none.
- AI/model behavior: none.
- Documentation: README, PROJECT_CONTEXT.
- Operations/security: LGF scope-contract.yml wording only. No scanner, hook, or CI change.

## Open Questions

- None blocking. If `packet_guard` denies the yaml edit, stop and tell the Owner; do not silently skip the contract file.
