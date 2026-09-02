# Verification

## Change

grok-docs-bound-archive

## Automated Checks

All five checks are read-only. No pytest, no `scripts/start_probe.py`, no `sdd.py`, no
`record_verify` — see `decision-log.md` row 3 (F14, `scripts/start_probe.py:1-6`). Check 4f did not
run: the §Decision reversal condition did not fire and `sdd-plus/security/scope-contract.yml` was
not edited.

- [x] 4a — both documents state all the claims (`verifier-report.md`, `verifier-report.sha256`,
      `check_verdict.py`, `VERIFIED WITH NOTES`, `sdd.py archive`, `--force`,
      `sufficient, never necessary`). Expect no output; **actual output was empty** — no `MISSING`
      line, so the two documents agree about the contract.

      ```
      $ for f in README.md PROJECT_CONTEXT.md; do
          for t in verifier-report.md verifier-report.sha256 check_verdict.py "VERIFIED WITH NOTES" \
                   "sdd.py archive" "--force" "sufficient, never necessary"; do
            grep -qF -e "$t" -- "$f" || echo "MISSING [$t] in $f"
          done
        done
      (no output)
      ```

- [x] 4b — nothing was weakened; all three greps returned a hit.

      ```
      $ grep -nF 'never archives' PROJECT_CONTEXT.md
      30:**is transport, not archiving**, so Grok does both and still never archives. Then Daniel runs
      74:- Grok (choreographer) transports, never audits, never archives, never implements. Archiving is

      $ grep -nF 'Do not copy client or LOQ files here.' README.md
      8:Do not copy client or LOQ files here.

      $ grep -nF 'must not be vendored or run here.' README.md
      13:`executors.py`, `handoff.py`) is not vendored and must not be vendored or run here.
      ```

- [x] 4c — the advertised strings match the code they advertise. `scripts/sdd.py:27-29` reads
      `verifier-report.md`, `verifier-report.sha256`, `("VERIFIED", "VERIFIED WITH NOTES")` —
      exactly the strings written into the two documents. Read only; `scripts/sdd.py` not edited.

      ```
      $ grep -nE 'VERIFIER_REPORT|VERIFIER_SHA|BOUND_VERDICTS' scripts/sdd.py
      27:VERIFIER_REPORT = "verifier-report.md"
      28:VERIFIER_SHA = "verifier-report.sha256"
      29:BOUND_VERDICTS = ("VERIFIED", "VERIFIED WITH NOTES")
      339:    if len(parts) == 2 and parts[1].lstrip("*") == VERIFIER_REPORT:
      372:    report = change_dir / VERIFIER_REPORT
      373:    sidecar = change_dir / VERIFIER_SHA
      377:        return VerdictBinding(False, "", "", f"{VERIFIER_SHA} present but "
      378:                                             f"{VERIFIER_REPORT} is missing")
      380:        return VerdictBinding(False, "", "", f"no {VERIFIER_SHA} sidecar: write the "
      389:        return VerdictBinding(False, "", "", f"{VERIFIER_SHA} must hold one line of "
      391:                                             f"by {VERIFIER_REPORT})")
      392:    if verdict not in BOUND_VERDICTS:
      395:                                             + " or ".join(repr(v) for v in BOUND_VERDICTS))
      500:                         f"{VERIFIER_REPORT} is present but not bound: {bound.reason}"))
      628:              f"({VERIFIER_REPORT} sha256 {bound.digest[:12]}… confirmed by "
      634:        print(f"warning: {VERIFIER_REPORT} is present but NOT bound: {bound.reason}")
      791:                    f"{VERIFIER_REPORT} and the sha256 it was stated with in "
      792:                    f"{VERIFIER_SHA}")
      ```

- [x] 4d — nothing else moved. The diff touches `README.md` and `PROJECT_CONTEXT.md` only, plus the
      untracked packet directory. No change under `scripts/`, `tests/`, `kernel/`, `hooks/`,
      `.github/`, `sdd-plus/archive/`, `sdd-plus/security/`, or `drydock-pins.json`.

      ```
      $ git status --short
       M PROJECT_CONTEXT.md
       M README.md
      ?? sdd-plus/changes/grok-docs-bound-archive/

      $ git diff --stat
       PROJECT_CONTEXT.md | 20 +++++++++++++++++++-
       README.md          | 16 ++++++++++++++++
       2 files changed, 35 insertions(+), 1 deletion(-)
      ```

      `git diff -- README.md PROJECT_CONTEXT.md` shows three hunks: `README.md` +1 blank +15 lines
      after `:13`; `PROJECT_CONTEXT.md` +1 blank +13 lines after the Desired Outcome line; and the
      Constraints bullet replaced 1 line with 5, `never archives` retained verbatim in the first
      sentence. No other hunk.

- [x] 4e — the transport/archive definition landed in both documents (`sdd.py archive`,
      `sdd-plus/changes/`, `live packet directory`, `is transport, not archiving`,
      `Daniel runs it`). Expect no output from the loop; **actual loop output was empty** — no
      `DEF-MISSING` line. `is transport, not archiving` hits twice in `PROJECT_CONTEXT.md` (the
      Desired Outcome paragraph and the Constraints clause) and once in `README.md`;
      `never archives` still hits.

      ```
      $ for f in README.md PROJECT_CONTEXT.md; do
          for t in "sdd.py archive" "sdd-plus/changes/" "live packet directory" \
                   "is transport, not archiving" "Daniel runs it"; do
            grep -qF -e "$t" -- "$f" || echo "DEF-MISSING [$t] in $f"
          done
        done
      (no output)

      $ grep -nF 'is transport, not archiving' README.md PROJECT_CONTEXT.md
      README.md:22:**is transport, not archiving**, so Grok does it and still never archives; the verifier writes
      PROJECT_CONTEXT.md:30:**is transport, not archiving**, so Grok does both and still never archives. Then Daniel runs
      PROJECT_CONTEXT.md:78:  `<packet>/verifier-report.sha256` is transport, not archiving, and Grok does it.

      $ grep -nF 'never archives' PROJECT_CONTEXT.md
      30:**is transport, not archiving**, so Grok does both and still never archives. Then Daniel runs
      74:- Grok (choreographer) transports, never audits, never archives, never implements. Archiving is
      ```

## Manual Checks

- [x] Step 0 re-read, before any write. All six confirmations hold at
      `HEAD = 93c2959050ac908fd19596a5c7eddfeae95030f2`: (1) HEAD unchanged; (2) `README.md` still
      has zero hits among the seventeen terms; (3) `PROJECT_CONTEXT.md:21` and `:60` read verbatim as
      F3/F4; (4) `scope-contract.yml` returns exactly the seven F6.3 hits and its only `archive` hit
      is still `:87` `rollback_or_disable_path`, so the reversal condition did not fire and the yaml
      was not opened for writing; (5) `scripts/sdd.py:27-29` still holds the three constants;
      (6) `cmd_archive` still ends in `shutil.move(str(change_dir), str(target))` at `:806`. The two
      live proofs were re-run rather than trusted from F8/F9:

      ```
      $ cd sdd-plus/archive/2026-09-02-grok-archive-bound-verdict && sha256sum -c <(printf '%s  verifier-report.md\n' "$(cat verifier-report.sha256)") ; cd -
      verifier-report.md: OK
      /workspace/drydock-grok-sandbox

      $ grep -c '^## Override' sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/decision-log.md
      0

      $ cat sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/verifier-report.sha256
      52093daa2ad53bddcc686f9b84e1471e69e25a379cef5a83a8d7d71d96d13438
      ```

- [x] Step 1–3 paste fidelity. The three strings were copied verbatim from the plan's Steps 1, 2 and
      3, not paraphrased and not re-wrapped, so every checked phrase stays on a single line
      (`grep -F` does not match across a newline): `is transport, not archiving`,
      `sufficient, never necessary`, `Daniel runs it`, `never archives`, and the
      `first done live in \`f799ddc\`` historical-note clause. Step 3 used the Owner-aligned wording
      `and Daniel runs it.` (not `and it is Daniel's.`). No overclaim: the prose says "first bound
      archive", never "first archive without `--force`" (F10), and calls `f799ddc` / PR #21 a
      historical note rather than a pin (F10a). Nothing was planted in the live packet — this packet
      has no `verifier-report.md` and no `verifier-report.sha256` and stays unbound.

## Documentation Updates

- [x] README or user-facing docs updated, if needed.
- [x] Project context updated, if needed.
- [ ] Specs updated, if needed.
- [ ] No documentation update needed. Reason:

## Result

Implemented as planned; docs only. `README.md` gained one paragraph after `:13`;
`PROJECT_CONTEXT.md` gained one paragraph after the Desired Outcome line and its Constraints bullet
was extended with the transport/archive definition clause. Both documents now define archiving as
running `python3 scripts/sdd.py archive <name>` — the command that moves a packet out of
`sdd-plus/changes/` — state that writing `<packet>/verifier-report.md` and
`<packet>/verifier-report.sha256` is transport, not archiving, and keep `never archives` verbatim.
`sdd-plus/security/scope-contract.yml` was deliberately not edited (F6; the Step 0 re-read confirmed
no line there describes `sdd.py archive` or the verify→archive pipeline). No behavior change, no
code change, no pin change, no test change, no delta specs, no archive change.

Checks 4a–4e all passed: 4a and 4e produced no output (no `MISSING`, no `DEF-MISSING`), 4b's three
greps all hit, 4c matched the prose against `scripts/sdd.py:27-29`, and 4d showed the diff confined
to the two documents plus the untracked packet directory. 4f did not run — no yaml edit. No pytest
and no `start_probe.py` were run, by design.

This is the implementer's own evidence, not verification. Nothing is committed: no `git add`, no
commit, no push, no PR, no `sdd.py archive`, no `record_verify`. The Owner decides what happens
next, and whether to invoke the verifier subagent.
