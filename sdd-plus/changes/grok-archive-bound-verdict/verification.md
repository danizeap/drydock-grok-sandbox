# Verification

## Change

grok-archive-bound-verdict

## Automated Checks

- [x] **Full suite, cache-free** — `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`
      → `171 passed in 2.48s`. 86 pre-existing tests (none modified) plus 85 collected cases
      from the new `tests/test_sdd_archive_bound_verdict.py` (45 test functions, parametrized).
- [x] **Pins + guardrails, run AFTER the re-pin** — `scripts/start_probe.py` →
      `"ok": true`, `"pin_errors": []`, `"conductor_errors": []`, `"hook_errors": []`,
      `"secret_tree_errors": []`, exit 0. Hook evidence: `git_safety_deny` deny,
      `protect_secrets_deny` deny, `git_safety_allow_benign` allow.
- [x] **Pin moved, one value only** — `drydock-pins.json:6` `scripts/sdd.py`
      `202e2fb127caa716788f8866dfdd80f02b49eca937037aee0ecf2c57174c48f1` →
      `edea07c8b1f18bed62312c6617b4f5b5bbc9c4f6db0868cc519fe40099fcff68`. No other pin,
      and none of `drydock_commit` / `verifier_md_git_blob` / `hash_alg`, moved. Re-pin ran
      only after every `scripts/sdd.py` edit was final, and the probe only after the re-pin.
- [x] **Gate positive (command 3, `tempfile` only)** —
      `binding: VerdictBinding(ok=True, verdict='VERIFIED WITH NOTES', digest='7643a351…6cf8b063', reason='')`;
      `readiness: []`.
- [x] **Gate negative / fail-case 3 (command 4, same scratch dir)** — corrupted sidecar
      (`"0"*64`) → `['unbound-verdict', 'incomplete']`; verdict flipped to `NOT VERIFIED` →
      `['unbound-verdict', 'incomplete']`; **no report and no sidecar at all** →
      `['incomplete']` only, i.e. an unclaimed packet is still denied and is NOT given an
      `unbound-verdict` blocker. A bound report is sufficient, never necessary.
- [x] **Producer contract, the plan.md section D.2 sequence by hand (command 5a)** —
      report written verbatim → real `scripts/check_verdict.py` CLI exit `0` → that same hex
      written to `verifier-report.sha256` →
      `VerdictBinding(ok=True, verdict='VERIFIED WITH NOTES', digest='7643a351…6cf8b063', reason='')`.
      The same sequence is performed as test #38 under `_isolated_tree`, ending in an archive
      with no `## Override`.
- [x] **Spawn budget (command 5b, plan.md section F.3)** — with `subprocess.run` wrapped and
      counted: unclaimed packet → `archive_readiness` **0** spawns; bound packet → **1**;
      bound packet with `bound=` supplied → **0**; and
      `archive_readiness(d, c) == archive_readiness(d, c, bound=verdict_binding(d))` → `True`.
- [x] **Inventory still closed (command 5c, Step 9a, read-only)** —
      `grep -n '^## '` and `grep -ni 'verif'` over all eight `tasks.md` (6 archived + live +
      template). Every heading and every hit is already listed in plan.md section E.1: three
      heading shapes, two verifier-owned checkbox wordings, the bare `## Verification` over
      implementer commands, and the four prose mentions. **No new wording**, so
      `_VERIFIER_OWNED` was not widened. Held as a regression by test #19d.

## Manual Checks

- [x] **The live packet is untouched and still blocked (command 6, read-only)** —
      `sdd.py verify grok-archive-bound-verdict` →
      `Tasks: 8 complete, 1 pending.` /
      `warning: unfilled placeholder content (TBD) remains in: verification.md` /
      `Packet incomplete. Archive will require --force.` /
      `Not archive-ready: 1 pending task(s); unfilled placeholders in verification.md`,
      exit `1`. No `READY TO ARCHIVE`. This packet carries no `verifier-report.md`, so it is
      unbound and blocked exactly as it was before the change — and the one pending task is
      the verifier-owned Step 12, which is NOT waived because there is no bound verdict.
- [x] **No live-tree fixtures planted** — no `verifier-report.md` and no
      `verifier-report.sha256` anywhere under `sdd-plus/changes/`; every packet the tests
      build lives under `tmp_path`, and `cmd_archive` is only ever called behind the
      `_isolated_tree` fixture whose `assert sdd.find_root() == tmp_path.resolve()` is the
      mechanical guard against moving a live packet.
- [x] **No ledger event minted** — no `--record-verify` in any form, no
      `kernel/brief_complete_engine.py`, no `kernel/brief_engine.py`, no
      `scripts/record_verify_bound.py`, in tests or in these commands.
- [x] **Nothing outside the stated file set changed (command 7)** — `git status --porcelain`
      shows only `scripts/sdd.py`, `drydock-pins.json`,
      `tests/test_sdd_archive_bound_verdict.py` and this packet's own artifacts. No
      `sdd-plus/archive/` change, no `.env`, no `__pycache__`. `grok-archive-bound-verdict`
      is still present in `sdd-plus/changes/`.
- [ ] *(verifier-owned)* Independently re-run the suite, review the diff against brief scope
      and the `must_not_do` fences, and confirm the evidence claims above.

## Documentation Updates

- [x] No documentation update needed. Reason: the change is a gate re-derivation inside
      `scripts/sdd.py`. No behavior, setup, data, API or workflow surface outside that file
      moves; no living capability is touched, so there is no delta spec to sync. The producer
      step is choreography outside this repo (plan.md section D.2) and is surfaced to the
      operator by `cmd_archive`'s new `Bind the verifier verdict: …` hint.

## Result

Pending.
