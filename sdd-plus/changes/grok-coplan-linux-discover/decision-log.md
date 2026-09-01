# Decision Log

## Change

grok-coplan-linux-discover

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-09-01 | Search the Windows `LOCALAPPDATA` root first, then `PATH`, then `$HOME/.local/bin`. | On a machine with a real Codex install, that install must win; a stray `codex` shim on `PATH` should never silently displace it. `PATH` order otherwise matches what the Owner's own shell would resolve. | `PATH` first everywhere (risks shims winning on Windows); `shutil.which` only (drops the Windows glob and its newest-by-mtime rule). |
| 2026-09-01 | Make the `.sandbox-bin` exclusion an explicit predicate rather than relying on the glob root. | The old code excluded the stale sandbox copy only by accident of geography — it sat outside `LOCALAPPDATA`. Once `PATH` is searched, that accident stops protecting us, so the safety property has to be stated in code and tested. | Leaving it implicit (silently loses the guarantee); excluding all of `~/.codex` (would wrongly reject the real install, which symlinks into `~/.codex/packages/`). |
| 2026-09-01 | Check both the literal path and its `realpath` for a `.sandbox-bin` component. | A `PATH` symlink pointing at the sandbox copy would otherwise pass the filter and be returned. | Literal-path check only (defeated by one symlink). |
| 2026-09-01 | Return the `PATH` path as found (`/home/box/.local/bin/codex`) instead of resolving the symlink. | That is the canonical entry point Codex's own installer publishes; resolving would pin us to a versioned `packages/standalone/<ver>` path that changes on every upgrade. | Returning `os.path.realpath()` of the hit. |
| 2026-09-01 | Vendor all ten conductor files verbatim first, then edit two. | Makes the packet diff show exactly which bytes this change is responsible for, and puts the whole conductor under `drydock-pins.json` so it is commit-bound and tamper-evident. | Vendoring only `codex_bridge.py` (leaves `negotiate.py` and its imports untracked and unpinned — the fix would not actually be runnable from the repo). |
| 2026-09-01 | Correct the `discover` stage error message in `negotiate.py`. | The message named only the Windows root, which is precisely what made the original live-fire failure read as "Codex is missing" rather than "we looked in one place". A wrong error message is a real defect. | Leaving it (misleading); dropping the Windows root from the text (loses the Windows diagnostic). |
| 2026-09-01 | New optional keyword arguments (`path_env`, `home`) on `discover_core()` rather than monkeypatching `os.environ` in tests. | Keeps the discovery search order testable as a pure-ish function with `tmp_path` fakes, with no ambient-environment coupling. The public contract (path string or `None`) is unchanged. | Environment-only tests (leakier, and cannot express `PATH` ordering as cleanly). |
