# Tasks

## Change

grok-archive-bound-verdict

## Implementation

- [x] Confirm scope and standards. LITE, Round 2 plan converged; re-read
      `scripts/sdd.py:84-90`, `:182-217`, `:244-256`, `:259-300`, `:317-337`, `:378-432`,
      `:539-568` and `scripts/check_verdict.py:17-44`; confirmed `sha256 scripts/sdd.py` was
      `202e2fb1…c48f1` (pin `drydock-pins.json:6`) before any edit.
- [x] Re-run the plan.md section E.1 inventory (Step 9a) before locking the matcher:
      `grep -n '^## '` and `grep -ni 'verif'` over all eight `tasks.md`. Every heading and
      every hit is already in the table — no new wording, so the closed set stands and
      `_VERIFIER_OWNED` is not widened.
- [x] Add tests: new `tests/test_sdd_archive_bound_verdict.py`, one case per row of the
      plan.md Tests table (#1-#41, including #19a-#19d and #38-#41), tiered per section F.7.
      Every packet under `tmp_path`; `cmd_archive` only behind the `_isolated_tree` guard;
      #19d is the one read-only exception that reads the real corpus. No pre-existing test
      file modified.
- [x] Implement the smallest coherent change in `scripts/sdd.py`: `import subprocess` +
      `from typing import NamedTuple`; the six constants of section A.2 (`_VERIFIER_OWNED`
      anchored on `verifier`, never `verif`); the six helpers `_flatten`, `VerdictBinding`,
      `verdict_line`, `sidecar_digest`, `verdict_binding`, `verifier_owned_pending`;
      `packet_unfilled` split into `packet_unfilled_reasons` + a behavior-identical
      `packet_unfilled`.
- [x] Wire the four call sites: `archive_readiness` gains keyword-only `bound=`, the
      `unbound-verdict` blocker and an updated docstring (no longer "pure"); `cmd_verify`
      derives its messages from the blockers, reuses the binding, drops the `:416`
      short-circuit and returns on `blocking_unfilled` (no `sys.exit` added); `cmd_archive`
      gains the `unbound-verdict` hint branch and nothing else; `_classify_packet` splits
      pending/unfilled by owner and passes `bound=`.
- [x] Update docs/specs: none required. No behavior, setup, data, API or workflow change
      outside `scripts/sdd.py`; no living capability touched, so no delta spec. The producer
      is choreography outside this repo (plan.md section D.2) and is documented there and in
      `sdd.py`'s own `Bind the verifier verdict` hint.
- [x] Re-pin last: every `scripts/sdd.py` edit final → hash → that one value into
      `drydock-pins.json:6` → only then `start_probe.py`. No other pin moved.
- [x] Run verification: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`
      and `start_probe.py`; output recorded verbatim in `verification.md`.

## Verification

- [ ] Invoke the verifier subagent; do not self-certify. Only then may this box and
      `verification.md` Result move. Not run this turn: the Implementer does not verify its
      own diff, and this packet changes the archive gate itself — self-binding a report the
      implementer wrote is the exact failure this packet must not normalize
      (plan.md must_not_do 21).
