# Brief

## Change

grok-coplan-linux-discover

## User Need

The Owner runs Drydock's two-brain co-planning (`scripts/conductor/negotiate.py`) from this
Linux sandbox VM. Today the first live-fire round dies before it can ask Codex anything, so
co-planning is simply unavailable outside Windows. The need is for the conductor to find the
Codex core wherever it is actually installed, so a plan can be negotiated on this machine.

## Problem

`discover_core()` in `scripts/conductor/codex_bridge.py` (Drydock pin
`5f76f67eda90d92b4f0eea1908e66c7f45ca81f7`) only globs the Windows install root:
`%LOCALAPPDATA%\OpenAI\Codex\bin\*\codex.exe`. On this VM `LOCALAPPDATA` is unset, so the
function returns `None` immediately and `negotiate.py` fails closed at stage `discover` with
`no Codex core found under %LOCALAPPDATA%\OpenAI\Codex\bin`. Codex is installed here as
`/home/box/.local/bin/codex` (codex-cli 0.152.0), on `PATH`.

A second problem is that the conductor was never committed to this sandbox repo — it was only
fetched into `/home/box/drydock-state/`. Untracked, unpinned code cannot be reviewed, hashed,
or held to the start probe, so the fix would not be commit-bound.

## Scope

In scope:

- Vendor `scripts/conductor/` (10 files) into this repo from the already-fetched pin copy,
  byte-identical apart from the deliberate edits below.
- Port `discover_core()` to POSIX: `PATH` lookup, then `$HOME/.local/bin/codex`, while keeping
  the existing Windows `LOCALAPPDATA` glob behavior intact.
- Keep the existing safety property: never return the stale `~/.codex/.sandbox-bin` copy.
- Correct the now-inaccurate `discover` failure message in `negotiate.py`.
- Unit tests for all three discovery shapes plus the sandbox-bin rejection.
- Pin every vendored file in `drydock-pins.json`.

Out of scope:

- Anything downstream of `discover` (gauge / route / delegate). Those stages may still fail on
  this VM; that is a separate packet.
- Mutating delegation (`mutate.py`), review flows, or any behavior change to the other nine
  vendored files.
- Leftover-hole work from earlier packets. Archiving this packet.

## Acceptance Criteria

- [ ] `discover_core()` returns `/home/box/.local/bin/codex` on this VM with `LOCALAPPDATA` unset.
- [ ] A Windows-shaped `LOCALAPPDATA/OpenAI/Codex/bin/*/codex.exe` tree still resolves to the
      newest `codex.exe`.
- [ ] A `codex` living under a `.sandbox-bin` directory is never returned, on any platform.
- [ ] `negotiate.py --round 1` with a short non-secret probe plan gets past stage `discover`.
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passes.
- [ ] `python3 scripts/start_probe.py` exits 0 with the new pins.

## Impact Areas

- Backend: `scripts/conductor/codex_bridge.py` discovery; `scripts/conductor/negotiate.py` message.
- Frontend: none.
- Data model: none.
- API: `discover_core()` keeps its signature and return contract (path string or `None`); new
  keyword arguments are optional and test-only.
- AI/model behavior: none — routing, prompts, and schemas are untouched.
- Documentation: packet artifacts only.
- Operations/security: the read-only delegation flags, secret guard, and sandbox-bin exclusion
  are all preserved. `drydock-pins.json` grows by ten entries, which is what makes the vendored
  conductor tamper-evident.

## Open Questions

- None blocking. The `codex` on this VM is a symlink into `~/.codex/packages/standalone/...`;
  we deliberately return the `PATH` path as found rather than its resolved target, because that
  is the entry point the Owner and Codex's own installer treat as canonical.
