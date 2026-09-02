# Tasks

## Change

grok-refuse-brief-engine

## Planning (Round 2 of 2, final — complete)

- [x] Read `negotiate-grok-refuse-brief-engine-r1.json` verbatim from disk.
- [x] Independently audit both blocking concerns against the tree at HEAD `0b4a475`.
- [x] Record a disposition row per blocking concern, gap, and risk in `decision-log.md`.
- [x] Revise `plan.md` and `brief.md` for internal consistency; withdraw "no contract change".

## Implementation

Implemented on branch `packet/grok-refuse-brief-engine` under the Owner decision of 2026-09-02
(see `decision-log.md`). Boxes below are ticked by the **implementer** and record what was actually
run; they are evidence, not verification. Step 12 stays unchecked — the Owner deferred the verifier
subagent this turn and `verification.md` Result stays **Pending**.

Order matters in the first block: the byte-freeze choreography (plan Steps 2/3/4/4a) is the part
that cannot be resequenced, and each hash gate is a **stop**, not a warning.

- [x] Step 1 — Re-confirm facts 1, 2, 4 at HEAD; `sha256sum kernel/brief_engine.py` is `aa3ba09…`
      before anything is touched. *Confirmed at HEAD `0b4a475`; hash matched before any edit.*
- [x] Step 2 — `cp kernel/brief_engine.py kernel/brief_complete_engine.py` (copy only; never
      `git mv`, never `mv`, never a retype).
- [x] Step 3 — `sha256sum kernel/brief_complete_engine.py` is `aa3ba09…`. On mismatch: delete the
      copy, change nothing else, stop, report to Owner. File is frozen from here — no `Edit`,
      `Write`, `sed`, or formatter may name that path again. *Matched; the path was never named by
      an edit tool afterwards.*
- [x] Step 4 — Overwrite `kernel/brief_engine.py`, and only that path, with the §2 overlay
      (`COMPLETE` → the moved file; strings naming `kernel/brief_engine.py`; matcher per the OQ-1
      default). *Destination read back first; `indent=2` moved onto `json.dumps` in the
      `missing-record_verify_bound` branch, the one known divergence from `kernel/brief.py`.*
- [x] Step 4a — Re-run `sha256sum kernel/brief_complete_engine.py`; still `aa3ba09…`. Then run
      `python3 kernel/brief_engine.py | head -3` by hand, before pytest, to catch an `execv`
      self-loop in one process. *Both done; FACTS JSON, exit 0, no loop.*
- [x] Step 5 — Retarget `scripts/record_verify_bound.py:21` to the moved file and rewrite its `:7`
      docstring line. Nothing else in that file moves.
- [x] Step 6 — Update `tests/test_kernel_brief_overlay.py`: retarget `:10`, add `ENGINE_OVERLAY`,
      adjust the `:38-42` docstring, add the six new tests (seven under the OQ-1 default). *All
      seven added, including the parametrized OQ-1 test; the four unrelated existing tests are
      untouched.*
- [x] Step 7 — `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` green,
      including the unmodified `tests/test_brief_wrapper.py` and `tests/test_record_verify_bound.py`.
      Never green it by editing the frozen file or weakening a refusal. *86 passed, first run, no
      fixes needed.*
- [x] Step 8 — Re-assert `aa3ba09…` one final time, then update the three `drydock-pins.json`
      values (line 25, new key, line 11). No other pin moves. *Re-asserted immediately before the
      pin write; `scripts/start_probe.py` not edited.*
- [x] Step 9 — `python3 scripts/start_probe.py` reports `"ok": true`, `"pin_errors": []`.
- [x] Step 10 — Run the verification commands (including new 3a, 4a, 5a and the residual grep);
      paste output verbatim into `verification.md`.
- [x] Step 11 — `git status --porcelain` shows only the intended files; `kernel/brief_complete_engine.py`
      is `git add`ed so a fresh clone does not fail `check_pins()` with `missing pinned file`.
- [ ] Step 12 — Invoke the verifier subagent. Do not self-certify. Only then may these boxes and
      `verification.md` Result move. *Not run: Owner override this turn deferred verification;
      Result stays Pending.*

## Blocked on Owner

- [x] **OQ-1 — resolved by Owner decision 2026-09-02: the STRICT matcher (the stated default).**
      The overlay refuses `--record-verify=NAME` and unambiguous abbreviations as well as the bare
      two-token form; the literal-copy fallback was not taken. Recorded in `decision-log.md` and
      pinned by `test_engine_overlay_equals_and_abbrev_forms_refused`.
