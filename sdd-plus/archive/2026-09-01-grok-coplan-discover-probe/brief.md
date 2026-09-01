# Brief

## Change

grok-coplan-discover-probe

## User Need

Coplan on this Linux VM should fail at the start probe when Codex is not findable, not minutes later at `negotiate.py` stage `discover`. The Owner runs `python3 scripts/start_probe.py` before spending a Codex round; that probe must tell the truth about discovery.

## Problem

Packet `grok-coplan-linux-discover` (archived, main via PR #10 / `9952106`) ported `discover_core()` so it finds `/home/box/.local/bin/codex` and vendored `scripts/conductor/`. The first live-fire still taught a second lesson: `start_probe.py` can print `ok: true` while `negotiate.py` is about to fail closed at `discover`. That happened on this VM when discovery was Windows-only. Start probe does not call `discover_core()` at all.

A clean start probe that cannot see a missing Codex core is a silent hole in the coplan loop.

## Scope

In scope:

- Make `python3 scripts/start_probe.py` fail closed when `scripts.conductor.codex_bridge.discover_core()` returns `None`, except on GitHub Actions.
- Owner 2026-09-01: if `GITHUB_ACTIONS` is set, skip the discover check; keep fail-closed on this VM; JSON must record `discover_skipped` (a non-empty reason string). Do not edit `.github/workflows/`.
- Keep the check token-free: import and call `discover_core()` only. Do not spawn the Codex CLI, do not gauge, do not route, do not delegate, do not run `negotiate.py`.
- Surface the miss in the existing JSON (`ok: false` plus a named error list), same shape as pin/hook/secret errors. When skipped, `discover_errors` is `[]` and `discover_skipped` is set.
- Unit tests for: core found (injected), core missing (injected), and `.sandbox-bin` must not count as found. Prefer the existing `path_env` / `home` kwargs on `discover_core()`.
- Update `drydock-pins.json` if `scripts/start_probe.py` (or any other pinned file) changes.

Out of scope:

- Gauge / route / delegate / negotiate live-fire (this packet is the probe, not a Codex round).
- Leftover-hole work (`.env` writes, `brief_engine.py` completeness-only, GitHub FF `--force`).
- Vendoring more conductor files (`mutate.py` and friends stay out).
- Changing `discover_core()` search order or the `.sandbox-bin` exclusion.
- Archiving this packet.

Mode: LITE.

## Acceptance Criteria

- [ ] `python3 scripts/start_probe.py` on this VM still exits 0 (Codex is at `/home/box/.local/bin/codex`).
- [ ] The same probe exits 1 and reports a discover error when `discover_core()` is made to return `None` and `GITHUB_ACTIONS` is unset.
- [ ] When `GITHUB_ACTIONS` is set, the discover check is skipped even if no core is findable; `ok` is not flipped by discover; JSON records a non-empty `discover_skipped` and `discover_errors: []`.
- [ ] The probe never invokes the Codex CLI (no `Popen`/`run` of `codex`, no `negotiate.py`).
- [ ] Tests cover found / missing / sandbox-bin-rejected without requiring a live Codex binary in the test process.
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passes.
- [ ] Pins match if a pinned file changed.

## Impact Areas

- Backend: `scripts/start_probe.py` (and tests). May add a tiny helper next to it if that keeps start_probe readable; do not put this in `kernel/`.
- Frontend: none.
- Data model: none.
- API: `discover_core()` signature unchanged; start_probe JSON gains a discover-error field or list.
- AI/model behavior: none. No tokens.
- Documentation: packet artifacts only.
- Operations/security: fail-closed on missing core. Do not weaken pin/hook/secret/pre-push checks.

## Open Questions

- None blocking. Owner resolved the CI hole on 2026-09-01: skip discover when `GITHUB_ACTIONS` is set; JSON records `discover_skipped`. Prefer `discover_errors` (list of strings) matching `pin_errors` / `hook_errors`.
