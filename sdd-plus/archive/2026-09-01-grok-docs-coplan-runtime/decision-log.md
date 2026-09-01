# Decision Log

## Change

grok-docs-coplan-runtime

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-09-01 | Narrow the `conductor/` ban in all three documents rather than deleting it: the six vendored files become allowed, the four mutating files stay explicitly forbidden by name. | Deleting the entries would silently permit `mutate.py` and its `shell=True` surface, and would strand the archived Gate 7 acceptance in `grok-coplan-linux-discover`, which cites `README.md` and `scope-contract.yml` as the reason that finding was safe to accept. | Delete the conductor entries outright (rejected: over-widens and breaks the archived rationale). Leave the docs stale and rely on tribal knowledge (rejected: it is the defect this packet exists to fix). |
| 2026-09-01 | State the `in_scope` permission in `scope-contract.yml` as a file-level allowlist naming all six basenames plus "those six files only", not as a directory exception "under `scripts/conductor/`". | A path-prefix grant in the authoritative contract pre-approves whatever is dropped into the directory later, so vendoring `mutate.py` tomorrow would already be permitted by the contract meant to forbid it. Raised by Codex in negotiate round 1 and accepted in round 2. | Keep the round-1 directory wording (rejected: over-widens). Name the directory in the yaml and the six files only in README (rejected: leaves the authoritative file broader than the docs). |
| 2026-09-01 | Gate the edits behind a re-runnable Step 0 that checks the on-disk closure against `drydock-pins.json`, and STOP to the Owner on any mismatch. | The allowlist is only sound if the tree matches the pins; without a re-runnable check an implementer working on a drifted tree could widen the allowlist to match whatever is present. `git ls-files` is authoritative because `ls` also shows the untracked `__pycache__/`. | Trust the plan-time observation of the six files (rejected: has a shelf life, and the permission boundary depends on it). |
