# drydock-grok-sandbox

Throwaway Grok choreography sandbox for Drydock-on-Grok v1. **Not a client project.**

Vendored Drydock kernel/hooks from `danizeap/drydock@5f76f67eda90d92b4f0eea1908e66c7f45ca81f7`.
Run ledger lives **outside** this tree: `~/drydock-state/drydock-grok-sandbox/`.

Do not copy client or LOQ files here.

The vendored read-only coplan closure is runtime on this VM: `scripts/conductor/negotiate.py`,
`review.py`, `codex_bridge.py`, `negotiate_schema.json`, `review_schema.json`, `__init__.py` —
those six files only, pinned in `drydock-pins.json`. Mutating conductor (`mutate.py`, `coord.py`,
`executors.py`, `handoff.py`) is not vendored and must not be vendored or run here.
