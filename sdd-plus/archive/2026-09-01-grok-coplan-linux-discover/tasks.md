# Tasks

## Change

grok-coplan-linux-discover

## Implementation

- [x] Hash the ten fetched conductor files against `/home/box/drydock-state/.../conductor/PIN.json`,
      then vendor them into `scripts/conductor/` (no `__pycache__`).
- [x] Port `discover_core()` in `scripts/conductor/codex_bridge.py`: keep the Windows
      `LOCALAPPDATA` glob first, add `PATH` and `$HOME/.local/bin/codex` fallbacks, and route
      every candidate through an explicit `.sandbox-bin` rejection filter.
- [x] Correct the `discover` stage error message in `scripts/conductor/negotiate.py` so it names
      what is actually searched on each platform.
- [x] Add `tests/test_codex_discover.py`: Windows glob picks newest exe, `PATH` lookup works,
      `$HOME/.local/bin` fallback works, `.sandbox-bin` candidate is rejected, and discovery on
      this machine returns a real executable.
- [x] Add the `scripts/conductor/*` sha256 entries to `drydock-pins.json`.
- [x] Narrow the vendored set from ten files to the six `negotiate.py` actually imports; drop
      `mutate.py` (Gate 7 `shell=True` injection surface, no caller here), `coord.py`,
      `executors.py`, `handoff.py`, and their pin entries.
- [x] Replace the `encoding=`/`errors=` kwargs on the `app-server` `Popen` in `codex_bridge.py`
      with explicit `io.TextIOWrapper` pipes (same protocol, UTF-8 no longer locale-dependent).

## Verification

- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passes.
- [x] `python3 scripts/start_probe.py` exits 0.
- [x] `discover_core()` returns `/home/box/.local/bin/codex` on this VM.
- [x] One live `negotiate.py --round 1` with a short non-secret probe plan gets past stage
      `discover` (later stages may fail; that is out of scope).
- [x] `launchguardian scan --target . --strict-scanners` — **APPROVED**, 0 findings.
