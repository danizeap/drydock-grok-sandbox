# Plan

## Change

grok-coplan-linux-discover

## Approach

1. **Vendor the conductor, unchanged first.** Copy the ten pinned files from
   `/home/box/drydock-state/drydock-grok-sandbox/conductor/` into `scripts/conductor/` after
   confirming each one's sha256 against that directory's `PIN.json`. `__pycache__` is not
   copied. Vendoring before editing means the diff shows exactly which bytes this packet
   changes, and `_repo_root()` (three `dirname` hops from `codex_bridge.py`) still lands on the
   repo root under `scripts/conductor/`, so the secret-path matcher import keeps working.

2. **Make discovery platform-aware, Windows path first.** Rewrite `discover_core()` as an
   ordered candidate search:
   - If a `LOCALAPPDATA` root is available (argument or environment), glob
     `OpenAI/Codex/bin/*/codex.exe` and return the newest by mtime. This is the existing
     behavior, byte-for-byte in effect.
   - Otherwise walk `PATH` entries in order, looking for an executable `codex` (or `codex.exe`).
   - Otherwise try `$HOME/.local/bin/codex`.
   - Return `None` if nothing matches.

   Every candidate, from every branch, passes through one rejection filter before it can be
   returned. Windows keeps priority so a machine with a real Codex install is never silently
   routed to some other `codex` on `PATH`.

3. **Keep the sandbox-bin exclusion explicit.** The old code excluded `~/.codex/.sandbox-bin`
   only implicitly — it lived outside the glob root. Once we search `PATH`, that accident no
   longer protects us, so the rule becomes a real predicate: reject any candidate with a
   `.sandbox-bin` path component, checked on both the literal path and its `realpath` so a
   symlink into the sandbox copy cannot smuggle it back in.

4. **Fix the failure message.** `negotiate.py`'s `discover` stage error names only the Windows
   root. Update it to name what is actually searched, so the next live-fire failure is
   diagnosable instead of misleading.

5. **Test all four shapes** in `tests/test_codex_discover.py` with `tmp_path` fakes and a
   monkeypatched environment: Windows glob picks the newest exe; `PATH` finds a Linux `codex`;
   `$HOME/.local/bin/codex` is found with an empty `PATH`; a `.sandbox-bin` candidate is
   rejected in favor of `None`. Plus one real-machine assertion that discovery resolves to an
   existing executable file here.

6. **Re-pin and verify.** Add all ten `scripts/conductor/*` sha256 entries to
   `drydock-pins.json`, run the test suite, run `start_probe.py`, and run one live
   `negotiate.py --round 1` with a short non-secret probe plan to confirm the `discover` stage
   is passed.

## Files Expected To Change

- `scripts/conductor/__init__.py` (new, vendored verbatim)
- `scripts/conductor/coord.py`, `executors.py`, `handoff.py`, `mutate.py`, `review.py`,
  `negotiate_schema.json`, `review_schema.json` (new, vendored verbatim)
- `scripts/conductor/codex_bridge.py` (new, vendored + `discover_core` ported)
- `scripts/conductor/negotiate.py` (new, vendored + `discover` error message corrected)
- `tests/test_codex_discover.py` (new)
- `drydock-pins.json` (ten new entries)
- `sdd-plus/changes/grok-coplan-linux-discover/{brief,plan,tasks,decision-log,verification}.md`

## Risks

- **Picking the wrong `codex` on a multi-install machine.** Mitigated by search order: the
  Windows install root wins when present, and `PATH` order is respected otherwise, which is the
  same resolution the Owner's own shell would perform.
- **Reintroducing the stale sandbox copy.** This is the security-relevant risk, since that copy
  can behave differently from the installed core. Mitigated by the explicit `.sandbox-bin`
  predicate plus a dedicated rejection test, and by checking the resolved path too.
- **Vendoring drift.** If a vendored file differed from the pin, the fix would sit on unknown
  code. Mitigated by hashing all ten against `PIN.json` before the copy and pinning them after.
- **Live-fire cost.** One `negotiate.py` round spends real Codex tokens. Bounded to a single
  round with a short probe plan; the packet does not require later stages to succeed.

## Rollback

Every change is additive and confined to this branch (`hole/linux-codex-discover`). Reverting
the commit removes `scripts/conductor/`, the new test, and the ten pin entries together, which
returns the repo to a state the start probe accepts. No migration, no state, no deployed
surface — nothing to unwind beyond `git revert`.
