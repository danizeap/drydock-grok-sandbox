# drydock-grok-sandbox

Throwaway Grok choreography sandbox for Drydock-on-Grok v1. **Not a client project.**

Vendored Drydock kernel/hooks from `danizeap/drydock@5f76f67eda90d92b4f0eea1908e66c7f45ca81f7`.
Run ledger lives **outside** this tree: `~/drydock-state/drydock-grok-sandbox/`.

Do not copy client or LOQ files here.

The vendored read-only coplan closure is runtime on this VM: `scripts/conductor/negotiate.py`,
`review.py`, `codex_bridge.py`, `negotiate_schema.json`, `review_schema.json`, `__init__.py` —
those six files only, pinned in `drydock-pins.json`. Mutating conductor (`mutate.py`, `coord.py`,
`executors.py`, `handoff.py`) is not vendored and must not be vendored or run here.

Archive can bind on the verifier's own bytes, and the role boundary is the command. **Archiving** is
running `python3 scripts/sdd.py archive <name>` — the step that moves a packet out of
`sdd-plus/changes/` into `sdd-plus/archive/` — and Daniel runs it. **Transport** is copying
in-channel bytes into the live packet directory without running that command: Grok copies the
verifier's report verbatim to `<packet>/verifier-report.md` and writes the sha256 that
`python3 scripts/check_verdict.py` already accepted for those exact bytes to
`<packet>/verifier-report.sha256`. Writing the report and the sidecar
**is transport, not archiving**, so Grok does it and still never archives; the verifier writes
nothing to this tree, and the producer is choreography, not a repo script. When both files are
present and the report's `## Verdict` section is exactly `VERIFIED` or `VERIFIED WITH NOTES`,
`python3 scripts/sdd.py archive <name>` is ready with **no `--force`** and no `## Override` record —
first done live in `f799ddc` (PR #21), a historical note of the first bound archive rather than a
pin. A bound report is **sufficient, never necessary**: a packet that ticks its boxes and fills its
Result still archives the old way, a forgotten sidecar is a missed benefit rather than a false pass,
and `--force --reason "<why>"` remains the Owner override when the verdict is unbound.
