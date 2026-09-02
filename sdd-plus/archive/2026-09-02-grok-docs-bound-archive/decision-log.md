# Decision Log

## Change

grok-docs-bound-archive

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-09-02 | Edit `README.md` and `PROJECT_CONTEXT.md`; deliberately do not edit `sdd-plus/security/scope-contract.yml` | F6.1 — the file declares its own authority as `related_gates:8-11` (LGF Gate 0 / Gate 1 / Gate 11), not packet lifecycle, so it is not authoritative for `sdd.py archive`; F6.3 — the seventeen-term grep returns seven hits (`:4`, `:14`, `:38`, `:57`, `:70`, `:72`, `:87`), none of them verify→archive pipeline wording (`:57`/`:70`/`:72` are the substring `bound` inside boundary/integration key names; `:87` `rollback_or_disable_path` means deleting the sandbox repo). Re-read line by line at Step 0 this turn: nothing to correct, so the reversal condition did not fire | Add a governance line to the yaml so the diff spans three files — rejected as shoehorning a lifecycle topic into an LGF launch-scope contract |
| 2026-09-02 | `PROJECT_CONTEXT.md:60` gains the transport/archive definition clause rather than staying byte-identical (brief OQ-2) | §Definition — archiving is defined by which command runs: `cmd_archive` at `scripts/sdd.py:773-807`, whose terminal act is `shutil.move(str(change_dir), str(target))` at `:806`, moving the packet out of `sdd-plus/changes/`. The sidecar write invokes neither, so it is transport. `never archives` survives verbatim in the line; the clause supplies the rule, it does not move the boundary | Leave `:60` alone and carry the definition only in the Desired Outcome paragraph — rejected because the ban and its scope must be readable in one place, or a careful session cites `:60` to refuse the sidecar write |
| 2026-09-02 | No pytest and no `start_probe.py` in this packet's validation; five read-only checks (4a–4e) instead | F14 — nothing under `tests/` asserts any sentence in these docs (the only hits are a `readme.txt` fixture at `tests/test_pre_commit_tree.py:32-33`), so a green suite proves nothing about this prose; `scripts/start_probe.py:1-6` installs backstops/pre-push into `.git/hooks` if missing or drifted, a mutation in a docs-only packet | Run the suite for reassurance — rejected as unrelated signal plus mutation risk (Codex round-1 blocking concern 2) |
| 2026-09-02 | Owner accepted the Codex r2 residual by aligning plan Step 3 to `Daniel runs it` (from `and it is Daniel's.`) | Step 4e greps the literal phrase `Daniel runs it` in both documents; Steps 1 and 2 already used it, so the unaligned Step 3 wording would have been a needless third phrasing of the same rule | Keep `and it is Daniel's.` in Step 3 and drop the phrase from the 4e term list — rejected because it weakens the check that settles Codex concern 1 |
