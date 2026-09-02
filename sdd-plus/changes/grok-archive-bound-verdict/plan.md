# Plan

## Change

grok-archive-bound-verdict — close leftover hole 3: `scripts/sdd.py archive` is READY from a
**bound verifier verdict on disk**, not from ticked verifier checkboxes. `--force` stops being
required after every honest independent verification, and stays required for everything else.

## Mode

LITE. **Round 2 of 2 (final before implement).** Codex negotiate round 1 ran
(`negotiate-grok-archive-bound-verdict-r1.json`, model `gpt-5.4-mini`, `ok: true`,
`converged: false`, `loop.continue: true`) and returned **three blocking concerns**. This revision
answers all three with on-disk facts (§D, §E, §F). **This turn is still planning: nothing is
implemented, nothing is committed, no Codex call and no `negotiate.py` run happens here, and no
`tasks.md` box is ticked.** The next turn is implement.

- **Known files, named up front:** `scripts/sdd.py` (one new constant block, five new helpers,
  edits inside four existing functions), `tests/test_sdd_archive_bound_verdict.py` (new), and
  **one** value in `drydock-pins.json` (line 6).
- **Contract change, stated precisely.** Two claims, kept separate on purpose:
  1. *Additive readiness.* A packet carrying a **bound** `verifier-report.md` archives without
     `--force` even though its verifier-owned tasks are unticked and `verification.md` Result is
     `Pending.`. Today that packet hits the `incomplete` blocker (`scripts/sdd.py:291-299`) and
     `cmd_archive` exits `error: not archive-ready` (`:551-558`).
  2. *Unchanged refusal without a bind.* No report, no sidecar, wrong hash, malformed sidecar,
     `NOT VERIFIED`/`BLOCKED`/absent verdict, or pending **implementation** tasks — all still
     block, and `--force` is still the Owner override for them. `--force` is not removed, not
     renamed, not weakened, and `--abandon` is untouched.
  A bound report is **sufficient**, never **necessary** (OQ-2 in `brief.md`).
- **No auth, no schema, no migration, no new dependency.** One stdlib import is added to
  `scripts/sdd.py`: `subprocess`.
- **No workflow, no conductor, no hook, no kernel edit.** `.github/workflows/drydock.yml`,
  `scripts/conductor/*`, `hooks/*`, `kernel/*`, `backstops/*`, `scripts/start_probe.py`,
  `scripts/check_verdict.py`, `scripts/record_verify_bound.py` and `agents/verifier.md` are all
  untouched, and only `drydock-pins.json:6` moves.

Still LITE, not FULL: one production file, one new test file, one pin value, no new external
surface. It is a gate re-derivation inside a helper script — not architecture, not auth, not data.

## Codex negotiate round 1 — blocking concerns, verbatim

Quoted exactly as returned. None is dropped, softened, or ruled wrong. Each is answered below
with file:line evidence; the answers are §D, §E and §F respectively.

> **1. issue:** No real producer path for the bound-verdict artifacts
> **why:** The plan deliberately avoids workflow/conductor changes, but the new gate depends on
> `verifier-report.md` and `verifier-report.sha256` existing in live packets. As written, nothing
> guarantees those files will ever be created through the real verification flow, so the feature is
> not end-to-end and will only work when someone manually drops files into a packet.

> **2. issue:** Verifier-owned task detection is under-specified
> **why:** The waiver hinges on `_VERIFIER_OWNED` matching all real verifier-owned task shapes, but
> the plan only proves two examples. If the repository contains any other wording, the gate will
> either fail to waive legitimate verifier tasks or accidentally waive implementation tasks. That is
> a contract problem, not just a regex detail.

> **3. issue:** `archive_readiness` is being turned into an I/O/subprocess path without an
> operational policy
> **why:** The plan has `archive_readiness` shell out to `check_verdict.py`, and then reuses that
> path from `verify` and `triage`. That changes a formerly cheap, deterministic check into a
> subprocess-heavy one with new failure modes and repeated work per packet. The plan does not say
> whether the added latency and brittleness are acceptable or how repeated calls should be
> controlled.

Codex's overall note (context, not a fourth concern):

> The shape is directionally right, but I would not start building it as written. The main problem
> is that the plan invents a new bind artifact pair (`verifier-report.md` plus
> `verifier-report.sha256`) without any guaranteed producer path or workflow integration, so the new
> "archive without --force" state is only reachable by ad hoc manual file edits. The second problem
> is that the verifier-owned-task matcher is still a heuristic with only two observed shapes; if that
> classifier is even slightly wrong, you either waive implementation work or keep legitimate
> verifier-owned tasks blocked. I also think the plan is too ambitious in one shot: it mixes the core
> gate change, CLI output changes, triage semantics, and a very large test matrix, which makes the
> blast radius hard to reason about.

**Round-2 dispositions, one line each** (full reasoning in §D/§E/§F; recorded durably in
`decision-log.md`):

| Concern | Disposition | Where answered |
| --- | --- | --- |
| BC1 producer path | **Accepted, and the premise is corrected by evidence.** The producer is not new: the report bytes and the in-channel digest already both reach the packet on every archive, the digest into `--force --reason` prose. Fact 21 proves it hash-for-hash on three packets. The change is *where the hex is written*, not *whether it is produced*. Made testable as an on-disk contract; no workflow, no conductor, no Grok-code change. | §D |
| BC2 under-specified matcher | **Accepted in full.** A complete inventory of every `tasks.md` in the repo (6 archived + 1 live + 1 template, fact 22) now backs a **closed** matcher. The audit found a third shape Round 1 had not seen — a bare `## Verification` heading over implementer-run commands (fact 23) — which the matcher must **not** waive. Every wording gets a test. | §E |
| BC3 no subprocess policy | **Accepted in full.** §F states when the subprocess runs, how many times, the timeout and its justification, every fail-closed mode, and the exact spawn budget per CLI command with a measured per-spawn cost. Repeated work is removed by an explicit `bound=` parameter rather than a global cache; the rejection of the cache is argued, not assumed. | §F |
| Codex "too ambitious in one shot" | **Noted, scope unchanged.** The CLI output change and the triage change are not extras: fact 5 and fact 7 are *existing contradictions* that this gate would otherwise make visible and wrong (the ready-prompt would claim `--force` is needed for a packet archive accepts). Splitting them would ship a knowingly self-contradictory CLI. The test matrix is large because the fail-closed matrix is large; §F.7 groups it into unit/contract/end-to-end tiers so failures localize. | §F.7 |

## Load-bearing facts, checked on disk

Every citation below was re-read this turn against HEAD `1da7781` on `main`.

1. **The blocker to be relaxed.** `archive_readiness(change_dir, caps_dir)`
   (`scripts/sdd.py:259-300`) ends with:

   ```python
   unfilled = packet_unfilled(change_dir)                 # :291
   _, pending = task_counts(change_dir / "tasks.md")      # :292
   if unfilled or pending > 0:                            # :293
       detail = []
       if pending > 0:
           detail.append(f"{pending} pending task(s)")
       if unfilled:
           detail.append("unfilled placeholders in " + ", ".join(unfilled))
       blockers.append(("incomplete", "; ".join(detail))) # :299
   ```

   The three earlier blockers — `unattributable` (`:269-274`), `unsynced-capability` (`:275-279`),
   `missing-requirement` (`:280-290`) — are about delta specs and are **not** touched by this
   packet.

2. **`task_counts` cannot distinguish task owners.** `scripts/sdd.py:84-90` counts every line
   matching `^\s*-\s*\[\s\]\s+` in `tasks.md`. It has no notion of who owns a task. Note it matches
   only the checkbox line itself — indented continuation lines of a multi-line task are not
   counted, which is why a line-level owner matcher only ever has to read the checkbox line.

3. **`packet_unfilled` folds two different faults into one filename.** `scripts/sdd.py:244-256`
   appends `fname` when `text_has_placeholder(text)` **or** (`fname == "verification.md"` and
   `verification_result_is_pending(text)`). Only the second is verifier-owned. The two predicates
   live at `:182-201` and `:204-217` respectively.

4. **Unchecked `- [ ]` boxes in `brief.md` are not "unfilled".** `text_has_placeholder`
   (`:182-201`) flags only `{{CHANGE_NAME}}` and `TBD` (as a whole line, list item, checkbox, or
   an unquoted table cell), ignoring fenced blocks and inline code spans. So the Owner's
   requirement that `brief.md` acceptance checkboxes stay open costs nothing here — they were
   never a blocker. The pending-Result rule (`:204-217`) treats `## Result` as pending when the
   collected non-empty lines up to the next heading join to `""` or `"pending"` after
   `.rstrip(".")`.

5. **`cmd_verify` short-circuits before ever consulting `archive_readiness`.**
   `scripts/sdd.py:416` reads `if show_ready_prompt and not unfilled and pending == 0:`. A bound
   packet has `pending > 0` and `unfilled == ["verification.md"]`, so it can **never** reach
   `archive_readiness` at `:418` and can never print `READY TO ARCHIVE` at `:431`. This directly
   contradicts the docstring at `:259-263`, which states that `cmd_archive` and the ready-prompt
   "consult one function" so the prompt "can NEVER claim ready when archive would block". The
   short-circuit is the violation and it is fixed by this packet.

6. **`cmd_verify` also hard-codes the `--force` claim.** `:399-400`:
   `if pending > 0: print("Pending tasks remain. Archive will require --force.")`. After this
   packet that sentence is false for a bound packet, so it must be derived from
   `archive_readiness` rather than from the raw count.

7. **`_classify_packet` returns `IN-PROGRESS` before reaching `archive_readiness`.**
   `scripts/sdd.py:325-327` returns on `pending > 0`; `:328-330` returns
   `CLAIMED-DONE-UNVERIFIED` on any `unfilled`; `archive_readiness` is only reached at `:333`. So
   `sdd.py triage` would bucket a bound, archivable packet as `IN-PROGRESS` and print "finish the
   packet, or abandon it" (`:347`) while `sdd.py archive` accepted it. Keeping triage from
   contradicting archive is in scope; a triage rewrite is not.

8. **`cmd_archive` is gated on `archive_readiness`, not on `cmd_verify`'s return value.**
   `:544` calls `cmd_verify(name, show_ready_prompt=False)` and **discards** its return; that call
   only `sys.exit`s on a missing change dir (`:383`), missing/empty `sdd-plus/standards/`
   (`:387`), or missing required artifacts (`:391`). The `return 1 if unfilled else 0` at `:432`
   is not read by archive. The real block is `:551-558`. Therefore changing `cmd_verify`'s return
   value cannot block a bound archive — but nothing in this packet may add a `sys.exit` to
   `cmd_verify` on a pending Result, or `cmd_archive` would die at `:544` before
   `archive_readiness` is even consulted.

9. **`--force` mechanics.** `:539-543` requires `--reason` with `--force`; `:551-552` computes
   `blockers` and `waived`; `:553-558` exits when `blockers and not force`, with a hint that
   branches on the blocker category; `:559-561` records the override to `decision-log.md` via
   `record_override` (`:435-444`) **only when `force and waived`**. So when `archive_readiness`
   returns `[]`, no override is recorded even if `--force` was passed — the "no Override section"
   acceptance criterion follows from existing code, not from a new one.

10. **`check_verdict` hashes the whole file and is pinned.** `scripts/check_verdict.py:29-33`:
    `data = path.read_bytes()`, `actual = hashlib.sha256(data).hexdigest()`, compared
    case-insensitively against the argument. There is **no footer stripping**. Its verdict test
    (`:40-43`) is `if required not in text and required not in lines` — a **substring OR whole
    line** test, deliberately loose. Pin: `drydock-pins.json:9` =
    `79075ea8089598260a749c8b20d0f672bdf0670f4e891fdf8c5b82e87b20f735`; on-disk sha256 confirmed
    equal this turn. **Not edited by this packet.**

11. **The substring trap is already documented.** `tests/test_check_verdict.py:36-43`
    (`test_missing_verdict_string`) notes in a comment that `"VERIFIED"` is a substring of
    `"NOT VERIFIED"` and deliberately requires an absent string instead. Any design that hands
    `required="VERIFIED"` to `check_verdict` against an arbitrary report is broken by
    construction. §Approach A.3 is built to make that call impossible.

12. **Every archived verifier report is footerless and ends the same way.** Six tracked files:
    `sdd-plus/archive/2026-09-01-grok-choreography-smoke/verifier-report.md:66-67`,
    `…-coplan-discover-probe/verifier-report.md:72-73`,
    `…-coplan-linux-discover/verifier-report.md:76-77`,
    `…-docs-coplan-runtime/verifier-report.md:60-61`,
    `2026-09-02-grok-coplan-closure-gate/verifier-report.md:57-58`,
    `2026-09-02-grok-refuse-brief-engine/verifier-report.md:55-56`. Each ends with `## Verdict`
    followed by exactly one line, `VERIFIED WITH NOTES`, and **none** carries a
    `sha256 of those exact report bytes:` footer. A repo-wide grep for that footer string across
    `*.md`/`*.py`/`*.json` returns **nothing** — the footer is an in-channel convention only, and
    the bytes that reach disk exclude it. Consequence: for every artifact that exists today, the
    in-channel digest is the **whole-file** sha256 of `verifier-report.md`, which is exactly what
    `check_verdict` computes. §Approach B turns on this fact.

13. **Both verifier-owned task shapes exist on disk, and they differ.** *(Round 2: this fact is now
    the summary of a complete inventory, not two examples — see fact 22, fact 23 and §E. Codex BC2
    was right that two examples is not a contract.)*
    - *Line form:* `sdd-plus/archive/2026-09-02-grok-refuse-brief-engine/tasks.md:57` —
      `- [ ] Step 12 — Invoke the verifier subagent. Do not self-certify. …`; and
      `sdd-plus/archive/2026-09-02-grok-coplan-closure-gate/tasks.md:47` —
      `- [ ] Invoke the verifier subagent; do not self-certify.`
    - *Section form:* `sdd-plus/archive/2026-09-01-grok-choreography-smoke/tasks.md:18` —
      `## Verification (verifier subagent — not the Implementer)` — followed at `:20-23` by four
      pending tasks (`Independently re-run the test suite.`, `Review the diff against brief scope
      and protected-path constraints.`, `Confirm evidence claims in verification.md.`, `Set the
      verification Result.`) **none of which names the verifier on its own line**.
    A line-only matcher would leave the smoke-packet shape blocked. The matcher must handle both.

14. **The task template contains no verifier task.** `sdd-plus/templates/tasks.md` has five
    generic implementation tasks (`Confirm scope and standards.` … `Run verification.`) and no
    occurrence of "verifier". So a freshly-created packet gets **zero** waived tasks — a report
    alone can never archive an untouched packet. `sdd-plus/changes/grok-archive-bound-verdict/tasks.md`
    is currently that template verbatim, five pending, none verifier-owned.

15. **`verifier-report.md` is invisible to every existing predicate.** It is not in
    `REQUIRED_FILES` (`scripts/sdd.py:19`), so `packet_unfilled` (`:246`) and `_classify_packet`'s
    missing-artifact check (`:322`) never look at it; `delta_spec_files` (`:93-97`) only globs
    `specs/*.md`. Extra files in a packet directory are simply carried along by
    `shutil.move(str(change_dir), str(target))` (`:567`) — which is how six reports already
    reached `sdd-plus/archive/`. A second file (`verifier-report.sha256`) needs no plumbing to
    travel with the packet.

16. **Archived packets are never re-examined.** `cmd_status` (`:305-306`), `cmd_triage` (`:357`)
    and `cmd_verify` (`:381`) all resolve `root / "sdd-plus" / "changes"`. Nothing walks
    `sdd-plus/archive/`. So the six sidecar-less archived reports cannot be retroactively
    reclassified by this change, and no migration is needed.

17. **`hooks/packet_guard.py` will not block this work.** `is_high_risk`
    (`hooks/packet_guard.py:105-128`) returns a label only for `migrations`/`db/migrate` paths, a
    **newly created** CI config, or a Dockerfile/compose family name. `scripts/sdd.py`,
    `tests/*.py` and `drydock-pins.json` match none of those, and this packet does not extend the
    hook.

18. **`check_pins()` needs no change for a value update.** `scripts/start_probe.py:68-84` loads
    `drydock-pins.json`, takes `pins.get("files")`, and iterates `files.items()` (`:76`), stat-ing
    each path (`:78-80`) and comparing `sha256_file` case-insensitively (`:81-83`). Editing one
    value is pure data; `scripts/start_probe.py` is not edited and its pin
    (`drydock-pins.json:12`) does not move.

19. **`scripts/sdd.py` is pinned and currently clean.** `drydock-pins.json:6` =
    `202e2fb127caa716788f8866dfdd80f02b49eca937037aee0ecf2c57174c48f1`, and
    `sha256sum scripts/sdd.py` printed exactly that this turn. Its current imports are `argparse`,
    `datetime`, `re`, `shutil`, `sys`, `pathlib.Path` (`:12-17`) — **no `subprocess`**, so adding
    it is a visible new line in the diff.

20. **No `tests/test_sdd*.py` exists.** `tests/` holds `test_bootstrap.py`,
    `test_brief_wrapper.py`, `test_check_secret_tree.py`, `test_check_verdict.py`,
    `test_codex_discover.py`, `test_ensure_pre_push.py`, `test_kernel_brief_overlay.py`,
    `test_pre_commit_tree.py`, `test_record_verify_bound.py`, `test_smoke.py`,
    `test_start_probe_conductor_closure.py`, `test_start_probe_discover.py`. `scripts/sdd.py` has
    **no test coverage at all** today. `tests/test_check_verdict.py` is the pattern for
    `tmp_path` + hashing; `tests/test_start_probe_conductor_closure.py` is the pattern for
    `sys.path.insert(0, str(ROOT / "scripts"))` + direct import. `conftest.py` only inserts `src`
    on `sys.path` and does nothing that affects this work.

### Facts added in Round 2 (the evidence Codex asked for)

21. **The producer already produces both halves today — the hex just lands in prose.** Three
    archived packets record, inside the `## Override` reason that `record_override`
    (`scripts/sdd.py:435-444`) wrote at archive time, the sha256 of their own
    `verifier-report.md`:

    | Packet | Recorded digest (decision-log.md) | `sha256sum verifier-report.md` this turn | Match |
    | --- | --- | --- | --- |
    | `2026-09-01-grok-choreography-smoke` (`decision-log.md:18`) | `88328932376b748a5e3cfc573d727393ee0c3baefa15233bc05f89828b19a323` | `88328932…b19a323` | **yes** |
    | `2026-09-02-grok-coplan-closure-gate` (`decision-log.md:40`) | `d25b70b84db5a46dc4de072de18ba532b1da85052804340cd132007b415a8f5b` | `d25b70b8…415a8f5b` | **yes** |
    | `2026-09-02-grok-refuse-brief-engine` (`decision-log.md:42`) | `ce4fdba20cf5f2827b430e3218c614423d89383607b40c1f972620c4bfc6e184` | `ce4fdba2…bfc6e184` | **yes** |

    The smoke packet's reason states it outright: *"VERIFIED WITH NOTES is bound by check_verdict.py
    sha256 88328932… at commit 174f04a…"* (`sdd-plus/archive/2026-09-01-grok-choreography-smoke/decision-log.md:18`).
    So on every one of those archives the choreographer already (a) transported the report bytes into
    the packet **byte-exactly**, (b) held the in-channel hex in hand, and (c) had already run
    `check_verdict.py` to exit 0 on it. This is the single most load-bearing fact added in Round 2:
    the artifacts are not hypothetical and the producer is not new. What is new is only **which file
    the hex is written into** — a `--force --reason` string today, a one-line sidecar tomorrow. §D.

22. **Complete inventory of every `tasks.md` in the repo.** Eight files exist —
    `sdd-plus/archive/*/tasks.md` (six), the live packet, and the template. Every level-2 heading
    and every checkbox line was read this turn. Full table in §E.1. Summary: **three** distinct
    heading shapes and **two** distinct verifier-owned checkbox wordings exist, and four of the
    eight files contain **zero** verifier-owned tasks.

23. **The audit found a third heading shape that Round 1 had not seen, and it must NOT be waived.**
    `sdd-plus/archive/2026-09-01-grok-coplan-linux-discover/tasks.md:26` is a bare `## Verification`
    heading, and its five tasks (`:28-33`) are **implementer-run commands** — `pytest`,
    `start_probe.py`, `discover_core()`, a live `negotiate.py --round 1`, and a `launchguardian scan`.
    Nothing there is verifier-owned. Had the matcher keyed on the *heading word* "Verification"
    instead of the phrase "verifier subagent", it would have waived five implementation tasks. The
    phrase anchor is what makes the difference: `Verification` does not contain `verifier`
    (`V-e-r-i-f-i-c…` vs `v-e-r-i-f-i-e-r`), so `_VERIFIER_OWNED` already excludes it — but only
    because it is anchored on `verifier`, never on `verif`. §E.3 pins this with a negative test.

24. **"verifier subagent" also appears in `tasks.md` as free prose, and the matcher must ignore it.**
    Three archived packets say it in a note that is neither a checkbox nor a heading:
    `2026-09-01-grok-docs-coplan-runtime/tasks.md:45-46` ("The verifier subagent was not invoked…"),
    `2026-09-02-grok-coplan-closure-gate/tasks.md:56` ("no verifier subagent was invoked in this
    turn"), and `2026-09-02-grok-refuse-brief-engine/tasks.md:18-19` ("the Owner deferred the
    verifier subagent this turn"). The matcher reads **only** lines matching `^##(?!#)\s` or
    `^\s*-\s*\[\s\]\s+`, so all three are structurally invisible. Worth stating because the naive
    "does the file mention the verifier?" design would have waived whole packets on a note.
    Critically, the enclosing heading for all three is `## Implementation` /
    `## Implementer notes` — never a verifier heading — so section state is unaffected too.

25. **`cmd_status` does not call `archive_readiness` and never will spawn.** `cmd_status`
    (`scripts/sdd.py:303-314`) calls only `task_counts` (`:311`) and `delta_spec_files` (`:312`).
    It is not edited by this packet and its spawn budget is **zero**. Checked on disk this turn,
    because §F has to bound spawns per command and a wrong assumption there would be a wrong policy.
    The three real `archive_readiness` call sites are `_classify_packet:333`, `cmd_verify:418` and
    `cmd_archive:551` — grep-confirmed as the complete set.

26. **Shelling out to `check_verdict.py` is already this repo's pattern, and the plan is stricter
    than the precedent.** `scripts/record_verify_bound.py:33-38` runs
    `[sys.executable, str(CHECK), verdict, digest, required]` with `cwd=str(ROOT)`,
    `capture_output=True`, `text=True` — and **no timeout at all**. Repo timeout conventions:
    `scripts/conductor/review.py:67` uses `timeout=30`; `scripts/start_probe.py:92` and
    `kernel/brief_complete_engine.py:527` use `timeout=60`; `hooks/session_orient.py:142` uses a
    named constant. Measured cost this turn, five consecutive spawns against the largest archived
    report (`2026-09-02-grok-refuse-brief-engine/verifier-report.md`, 5 397 bytes; the six reports
    span 5 197-6 363 bytes): `[0.0252, 0.0267, 0.0269, 0.0285, 0.0253]` s, **mean 26.5 ms**, all
    exit 0. Against `timeout=30` that is ~1 130× headroom. §F.2.

## Approach

### A. What `archive_readiness` does with a bound report

Three pieces: how a binding is decided (A.1-A.3), what a binding waives (A.4), and what it does
not (A.5).

#### A.1 The two artifacts

A packet **claims** a verdict by carrying either of:

| File | Role |
| --- | --- |
| `verifier-report.md` | the verifier's report, **byte-identical** to the in-channel message |
| `verifier-report.sha256` | one line: the sha256 the verifier stated in-channel for those bytes |

Neither is added to `REQUIRED_FILES`. A packet with **neither** file makes no claim and is treated
exactly as it is today (fact 15).

#### A.2 New constants and helpers in `scripts/sdd.py`

Placed immediately **before** `archive_readiness` (`:259`), after `packet_unfilled` (`:256`), so
the readiness function still reads top-down with its inputs defined above it.

```python
VERIFIER_REPORT = "verifier-report.md"
VERIFIER_SHA = "verifier-report.sha256"
BOUND_VERDICTS = ("VERIFIED", "VERIFIED WITH NOTES")
CHECK_VERDICT = Path(__file__).resolve().parent / "check_verdict.py"

_SHA256_HEX = re.compile(r"^[0-9a-fA-F]{64}$")
# CLOSED over every tasks.md in this repo -- 6 archived + 1 live + the template,
# audited line by line (plan.md section E.1). Two scopes, one phrase:
#   line form    archive/2026-09-02-grok-refuse-brief-engine/tasks.md:57
#                archive/2026-09-02-grok-coplan-closure-gate/tasks.md:47
#   section form archive/2026-09-01-grok-choreography-smoke/tasks.md:18
# Anchored on "verifier", NEVER on "verif": a bare `## Verification` heading over
# implementer-run commands exists at
# archive/2026-09-01-grok-coplan-linux-discover/tasks.md:26 and must NOT waive its
# five tasks. See plan.md sections A.3/E and brief.md OQ-4.
_VERIFIER_OWNED = re.compile(r"\bverifier\s+sub-?agent\b", re.IGNORECASE)


def _flatten(text: str) -> str:
    """Markdown emphasis stripped and whitespace collapsed, so `verifier` subagent,
    **verifier subagent** and 'verifier\n      subagent' all normalize the same."""
    return " ".join(text.replace("`", "").replace("*", "").replace("_", " ").split())


class VerdictBinding(NamedTuple):
    ok: bool          # a bound VERIFIED / VERIFIED WITH NOTES verdict is on disk
    verdict: str      # the exact verdict line, "" unless ok
    digest: str       # the expected sha256 from the sidecar, "" unless ok
    reason: str       # "" when NOTHING was claimed; else why the claim did not bind


def verdict_line(text: str) -> str:
    """The single non-empty line under `## Verdict`, or "" if absent or ambiguous.

    Deliberately strict: exactly one non-empty line before the next heading. A
    Verdict section carrying prose beside the verdict is not machine-decidable, so
    it returns "" and the packet fails closed to --force. Mirrors the shape of
    verification_result_is_pending (scripts/sdd.py:204-217)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^##\s+Verdict\s*$", line, re.IGNORECASE):
            collected = []
            for nxt in lines[i + 1:]:
                if re.match(r"^#{1,6}\s", nxt):
                    break
                if nxt.strip():
                    collected.append(nxt.strip())
            return collected[0] if len(collected) == 1 else ""
    return ""


def sidecar_digest(text: str) -> str:
    """The expected sha256 from verifier-report.sha256, or "" if malformed.

    Grammar: exactly one non-empty, non-'#' line. Its first whitespace-separated
    token must be 64 hex chars. A second token is allowed only if it names the
    report, so the sidecar can be produced either by pasting the in-channel hex or
    by running `sha256sum verifier-report.md` (whose output is `<hex>  <name>`, or
    `<hex> *<name>` in binary mode). Anything else fails closed."""
    body = [l.strip() for l in text.splitlines()
            if l.strip() and not l.strip().startswith("#")]
    if len(body) != 1:
        return ""
    parts = body[0].split()
    if not _SHA256_HEX.match(parts[0]):
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2 and parts[1].lstrip("*") == VERIFIER_REPORT:
        return parts[0]
    return ""


def verdict_binding(change_dir: Path) -> VerdictBinding:
    """Is an independent verifier verdict BOUND to bytes in this packet?

    Bound means all four, in this order:
      1. verifier-report.md and verifier-report.sha256 both exist;
      2. the sidecar parses to one sha256 hex digest;
      3. the report's `## Verdict` section is exactly one line, and that line is
         exactly "VERIFIED" or "VERIFIED WITH NOTES";
      4. `python3 scripts/check_verdict.py <report> <digest> <that exact line>`
         exits 0 --- the existing pinned hasher is the bind, run as the CLI, so
         archive runs the same command the Owner ran in channel.

    Step 3 is what decides the verdict, NOT step 4: check_verdict's string test is
    a substring OR whole-line test (scripts/check_verdict.py:40-43), and "VERIFIED"
    is a substring of "NOT VERIFIED" (tests/test_check_verdict.py:40). Because the
    string handed to check_verdict is the line this function already extracted and
    whitelisted, that test is a tautology here by construction and can never widen
    what is accepted. NOT VERIFIED is rejected at step 3 and check_verdict is never
    reached with required="VERIFIED".

    Fails closed everywhere: any OSError, decode error, timeout, missing
    check_verdict.py, or non-zero exit yields ok=False with a stated reason.
    reason == "" means nothing was claimed, which is not a fault.

    Spawns AT MOST ONE subprocess, never in a loop, and only after steps 1-3 have
    already passed on cheap file reads -- so an unclaimed packet costs zero
    spawns. Operational policy, spawn budget per CLI command and the measured
    per-spawn cost: plan.md section F."""
    report = change_dir / VERIFIER_REPORT
    sidecar = change_dir / VERIFIER_SHA
    if not report.is_file() and not sidecar.is_file():
        return VerdictBinding(False, "", "", "")
    if not report.is_file():
        return VerdictBinding(False, "", "", f"{VERIFIER_SHA} present but "
                                             f"{VERIFIER_REPORT} is missing")
    if not sidecar.is_file():
        return VerdictBinding(False, "", "", f"no {VERIFIER_SHA} sidecar: write the "
                                             "sha256 the verifier stated in channel "
                                             "for these exact report bytes")
    try:
        expected = sidecar_digest(sidecar.read_text(encoding="utf-8-sig"))
        verdict = verdict_line(report.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError) as e:
        return VerdictBinding(False, "", "", f"cannot read verdict artifacts: {e}")
    if not expected:
        return VerdictBinding(False, "", "", f"{VERIFIER_SHA} must hold one line of "
                                             "64 hex characters (optionally followed "
                                             f"by {VERIFIER_REPORT})")
    if verdict not in BOUND_VERDICTS:
        shown = verdict or "no single-line '## Verdict' section"
        return VerdictBinding(False, "", "", f"verdict is {shown!r}; archive binds only "
                                             + " or ".join(repr(v) for v in BOUND_VERDICTS))
    if not CHECK_VERDICT.is_file():
        return VerdictBinding(False, "", "", f"missing {CHECK_VERDICT.name}")
    try:
        proc = subprocess.run([sys.executable, str(CHECK_VERDICT),
                               str(report.resolve()), expected, verdict],
                              capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return VerdictBinding(False, "", "", f"{CHECK_VERDICT.name} timed out after 30s")
    except (OSError, subprocess.SubprocessError) as e:
        return VerdictBinding(False, "", "", f"cannot run {CHECK_VERDICT.name}: {e}")
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        return VerdictBinding(False, "", "", f"{CHECK_VERDICT.name} exit "
                                             f"{proc.returncode}"
                                             + (f": {tail[-1]}" if tail else ""))
    return VerdictBinding(True, verdict, expected, "")
```

Notes the implementer must not "simplify" away:

- **`CHECK_VERDICT` is anchored on `Path(__file__)`, not on `find_root()` or `cwd`.** Tests build
  fake packets under `tmp_path` and must still exercise the **real pinned** hasher; anchoring on
  the module file makes that automatic and makes the helper immune to `chdir`.
- **The subprocess is the point, not an implementation detail.** The choreography's bind is
  `check_verdict`'s exit code, so archive runs that exact CLI rather than re-implementing
  `hashlib.sha256`. Re-implementing it inside `sdd.py` would mean two hashers to keep in step and
  would silently unpin the bind.
- **Read with `utf-8-sig`** for the *text* parses only, matching every other read in the file
  (`:53`, `:87`, `:106`, …). The **hash** is always over raw bytes, because that is
  `check_verdict`'s job (`scripts/check_verdict.py:29`); a BOM therefore changes the digest, which
  is correct — the report must be byte-identical to what was hashed in channel.
- **`reason == ""` is load-bearing.** It is how "no claim" is distinguished from "failed claim",
  which is what keeps the `unbound-verdict` blocker off packets that simply have not been verified
  yet (A.5).
- **`report.resolve()` in the argv, and no `cwd=`.** `check_verdict.py` opens whatever path it is
  handed (`scripts/check_verdict.py:25-27`), so a relative `change_dir` would make the bind depend
  on the caller's working directory. `record_verify_bound.py:35` solves the same problem the other
  way, with `cwd=str(ROOT)`; an absolute argv is stricter, because it makes `cwd` irrelevant rather
  than merely fixed. **Round 2 addition** (BC3): removes one failure mode outright.
- **`except subprocess.TimeoutExpired` must come BEFORE `except (OSError,
  subprocess.SubprocessError)`.** `TimeoutExpired` is a subclass of `SubprocessError`; ordered the
  other way the timeout branch is dead code and the operator gets a generic "cannot run" for what is
  actually a hang. Both branches fail closed, so this is a message-quality bug, not a security bug —
  but §F.4 names timeout as a distinct policy outcome, so it must be distinctly reported.

#### A.3 Which pending tasks are waived — the matcher, closed over the inventory

The matcher below is **closed over §E.1**: every `tasks.md` in the repo was read line by line, and
every heading and checkbox wording it contains is classified there with a test. It is no longer
"two examples plus a heuristic" (Codex BC2).

```python
def verifier_owned_pending(tasks_path: Path) -> tuple[int, int]:
    """(pending tasks the verifier owns, pending tasks anyone else owns).

    Verifier-owned means the normalized phrase 'verifier subagent' (or
    'sub-agent') appears EITHER on the task's own checkbox line OR on the level-2
    heading that encloses it. CLOSED over every tasks.md in this repo -- six
    archived, one live, one template (plan.md section E.1):
      * line form     -- archive/2026-09-02-grok-refuse-brief-engine/tasks.md:57
                         archive/2026-09-02-grok-coplan-closure-gate/tasks.md:47
      * section form  -- archive/2026-09-01-grok-choreography-smoke/tasks.md:18,
                         whose four pending tasks at :20-23 never name the verifier.
      * NOT a match   -- archive/2026-09-01-grok-coplan-linux-discover/tasks.md:26,
                         a bare `## Verification` heading whose five tasks at :28-33
                         are implementer-run commands (pytest, start_probe,
                         negotiate, launchguardian). Anchoring on 'verifier' and
                         never on 'verif' is what keeps those five blocked.
      * NOT a match   -- free prose naming the verifier subagent inside a notes
                         block: docs-coplan-runtime/tasks.md:45-46,
                         coplan-closure-gate/tasks.md:56,
                         refuse-brief-engine/tasks.md:18-19. Only `^##(?!#) ` lines
                         and `- [ ] ` lines are ever inspected, so prose is
                         structurally invisible.
    Anything else is implementation work and still blocks. The template
    (sdd-plus/templates/tasks.md:9-13) contains no verifier task, so a fresh packet
    gets zero waivers and cannot archive on a report alone."""
    if not tasks_path.is_file():
        return 0, 0
    owned = other = 0
    in_verifier_section = False
    for line in tasks_path.read_text(encoding="utf-8-sig").splitlines():
        if re.match(r"^##(?!#)\s", line):
            in_verifier_section = bool(_VERIFIER_OWNED.search(_flatten(line)))
            continue
        if re.match(r"^\s*-\s*\[\s\]\s+", line):
            if in_verifier_section or _VERIFIER_OWNED.search(_flatten(line)):
                owned += 1
            else:
                other += 1
    return owned, other
```

- The checkbox regex is **character-for-character** the one at `scripts/sdd.py:89`, so
  `owned + other == pending` from `task_counts` for every file. `test_owner_split_totals_match_task_counts`
  pins that invariant, which is what stops the two functions drifting apart.
- Only level-2 headings open or close a verifier section (`^##(?!#)\s`, the same guard used at
  `:148` and `:234`). A `###` sub-heading does not reset it.
- `_flatten` is what makes `## Verification (verifier subagent — not the Implementer)` match
  despite the em dash and parentheses, and makes ``- [ ] Invoke the `verifier` subagent`` match
  despite backticks.

#### A.4 What a binding waives

`archive_readiness` gains one keyword-only optional parameter — the whole of the "repeated work"
answer to Codex BC3, argued in §F.3:

```python
def archive_readiness(change_dir: Path, caps_dir: Path, *,
                      bound: "VerdictBinding | None" = None) -> list[tuple[str, str]]:
```

`bound=None` (every existing call site, unchanged in meaning) means *compute it here*. A caller
that has **already** computed the binding for **this same `change_dir` in this same process** may
pass it, which is the only way the function ever does less work. It is keyword-only so no
positional call can drift into it, and `test_archive_readiness_bound_param_is_equivalent` pins
`archive_readiness(d, c) == archive_readiness(d, c, bound=verdict_binding(d))`.

Its final block becomes:

```python
    bound = verdict_binding(change_dir) if bound is None else bound
    if bound.reason:
        blockers.append(("unbound-verdict",
                         f"{VERIFIER_REPORT} is present but not bound: {bound.reason}"))
    placeholders, result_pending = packet_unfilled_reasons(change_dir)
    verifier_pending, other_pending = verifier_owned_pending(change_dir / "tasks.md")
    if bound.ok:
        unfilled, pending = placeholders, other_pending
    else:
        unfilled = sorted(set(placeholders) | set(result_pending),
                          key=REQUIRED_FILES.index)
        pending = verifier_pending + other_pending
    if unfilled or pending > 0:
        detail = []
        if pending > 0:
            detail.append(f"{pending} pending task(s)")
        if unfilled:
            detail.append("unfilled placeholders in " + ", ".join(unfilled))
        blockers.append(("incomplete", "; ".join(detail)))
    return blockers
```

with `packet_unfilled` split so that the two faults it conflates (fact 3) become separable
**without changing what `packet_unfilled` itself returns**:

```python
def packet_unfilled_reasons(change_dir: Path) -> tuple[list[str], list[str]]:
    """(files with template placeholders, files whose Result is still pending).

    packet_unfilled() is the union of the two and keeps its exact current
    behavior; this split exists because only the SECOND is verifier-owned and so
    only the second is waivable by a bound verdict."""
    placeholders, result_pending = [], []
    for fname in REQUIRED_FILES:
        f = change_dir / fname
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8-sig")
        if text_has_placeholder(text):
            placeholders.append(fname)
        if fname == "verification.md" and verification_result_is_pending(text):
            result_pending.append(fname)
    return placeholders, result_pending


def packet_unfilled(change_dir: Path) -> list[str]:
    """Required files still carrying template placeholders or a pending Result."""
    placeholders, result_pending = packet_unfilled_reasons(change_dir)
    return [f for f in REQUIRED_FILES
            if f in placeholders or f in result_pending]
```

The rewritten `packet_unfilled` returns the same list, in the same `REQUIRED_FILES` order, with
each name at most once — `test_packet_unfilled_behavior_unchanged` pins that against a fixture
covering placeholder-only, pending-Result-only, and both-at-once.

Waived, precisely:

| Fault | Waived by a bound verdict? |
| --- | --- |
| Pending task whose line or enclosing `##` heading names the verifier subagent | **yes** |
| Any other pending task | no |
| `verification.md` Result empty or `Pending.` | **yes** |
| `TBD` / `{{CHANGE_NAME}}` in **any** required file, including `verification.md` | no |
| Missing required artifact | no — `cmd_verify:389-391` still hard-exits |
| `unattributable` / `unsynced-capability` / `missing-requirement` delta blockers | no |

`archive_readiness`'s docstring (`:259-267`) must be updated in the same edit: it is still the
single read-only blocker list, but it is no longer side-effect-free — it spawns
`scripts/check_verdict.py`. Say so there, because that comment is the thing a future reader trusts.
The docstring must state all three: (1) **at most one** subprocess per call, zero when the packet
claims nothing; (2) `bound=` exists solely to let a caller that already has the binding avoid a
second identical spawn, and passing a binding computed for a *different* directory is a caller bug;
(3) the word "pure" comes out of `:260`, because it is no longer true.

#### A.5 Fail-case 3 — how archive without a bound verdict still fails

`unbound-verdict` fires **only** when something was claimed and failed to bind
(`bound.reason != ""`). A packet with no report at all produces no `unbound-verdict` blocker and
behaves byte-for-byte as it does today. Full matrix:

| Packet state | `unbound-verdict` | `incomplete` | Archive without `--force` |
| --- | --- | --- | --- |
| No report, no sidecar, tasks pending | no | yes | **denied** (unchanged) |
| No report, no sidecar, everything ticked and filled | no | no | allowed (unchanged) |
| Report, **no sidecar** | yes | yes | **denied** |
| Sidecar, **no report** | yes | yes | **denied** |
| Report + sidecar, **hash mismatch** | yes | yes | **denied** |
| Report + sidecar, **malformed sidecar** | yes | yes | **denied** |
| Report + sidecar, verdict `NOT VERIFIED` / `BLOCKED` | yes | yes | **denied** |
| Report + sidecar, **no `## Verdict` section** or >1 line in it | yes | yes | **denied** |
| Bound, but a non-verifier task pending | no | yes | **denied** |
| Bound, but `TBD` in `plan.md` | no | yes | **denied** |
| Bound, but delta spec unsynced | no | no | **denied** (`unsynced-capability`) |
| **Bound**, only verifier tasks pending, Result `Pending.` | no | no | **allowed** — the change |

`--force` still waives every row, and still requires `--reason` (`:540-543`) and still writes the
`## Override` record (`:559-561`). `--abandon` is not touched.

`cmd_archive`'s hint (`:555-557`) gains a third branch so the error tells the operator what to do:

```python
        if any(c == "unbound-verdict" for c, _ in blockers):
            hint = ("Bind the verifier verdict: put the report verbatim in "
                    f"{VERIFIER_REPORT} and the sha256 it was stated with in "
                    f"{VERIFIER_SHA}")
        elif any(c in ("unsynced-capability", "missing-requirement") for c, _ in blockers):
            hint = "Run /drydock:sync first"
        else:
            hint = "Complete the packet"
```

`unbound-verdict` first, because it is the most specific and most actionable of the three.

### B. How the sha256 is supplied — **sidecar file**, chosen over footer and argv

**Chosen: a sidecar, `verifier-report.sha256`, beside the report in the packet directory.**

Justification, strongest first:

1. **It preserves the invariant every artifact on disk already satisfies.** All six archived
   reports are footerless (fact 12), so today `sha256(verifier-report.md)` over the **whole file**
   *is* the digest the verifier stated — which is exactly what `check_verdict` computes
   (fact 10). The sidecar keeps that true and keeps the pinned hasher as the literal bind. The
   footer option **breaks** it: once the hex lives inside the file, the file's own hash is no
   longer the stated hash, and something must strip the footer before hashing. That means either
   editing `scripts/check_verdict.py` (a second pin move on the one file whose stability is the
   whole choreography) or building strip-then-tempfile machinery inside `sdd.py` so the existing
   hasher sees body-only bytes. Both are more code and more surface for the same result.
2. **It fails closed on drift; the footer self-heals.** If anything rewrites the report after the
   fact — a reformat, a "helpful" typo fix, a regeneration — the sidecar goes stale and the bind
   fails. With a footer, the natural way to regenerate a report is to recompute its own footer, so
   the gate stays green over bytes no verifier ever saw. Fail-closed on tamper is the direction
   this gate exists to move in. `test_report_edited_after_sidecar_written_is_not_bound` pins it.
3. **The strip rule is a bug farm.** "The bytes without the footer" needs an exact definition:
   which line, first or last occurrence, is the preceding newline included, what if there are two
   footers, what if the footer is not last. Every one of those is a way for the same file to hash
   two different ways in two different tools. A whole-file hash has none of those questions.
4. **Transport does not change.** Grok keeps copying the report **verbatim**; the report bytes on
   disk stay identical to the in-channel report bytes. The only new step is writing the hex the
   verifier already states in channel into a one-line file — `sha256sum verifier-report.md >
   verifier-report.sha256` produces an accepted form, and so does pasting the hex. Under the footer
   option, Grok's transport would have to start **appending** a line that the verifier's message
   deliberately keeps outside the hashed bytes, and all six archived reports would become
   retroactively non-conforming.
5. **Separation of claims.** The report is what the verifier said. The sidecar is the transported
   attestation of which bytes were meant. Putting a file's own hash inside the file is a
   self-referential construction that is not even well-defined without an extra rule.

**Why not argv** (a `--verdict-sha256` flag on `sdd.py archive`):

- `archive_readiness(change_dir, caps_dir)` is a pure function of on-disk packet state
  (`:259-267`), and it has three callers — `cmd_archive:551`, `cmd_verify:418`,
  `_classify_packet:333`. Only the first has argv at all. `cmd_verify` and `cmd_triage` would
  still never see a bound packet, so the `:416` contradiction (fact 5) would survive and the
  ready-prompt would stay wrong.
- **The Owner archives, not Grok.** Requiring a 64-character hex on every archive invocation is
  the same toil as `--force --reason "…"`, so it fails the stated goal that `--force` should not
  be needed every time.
- It leaves **no artifact**. The archived packet would carry no record of which digest was bound,
  which is precisely the audit trail this packet exists to create.

**Consequences of the choice, stated rather than assumed:**

- Transporting a verifier report now means **two files**, and the packet is not bound until both
  are present. A report without a sidecar is a *named* fault (`unbound-verdict`), not a silent
  pass — so the failure is loud.
- The sidecar is not a signature. Anything that can write the report can write the sidecar. See
  §Risks: this is choreography, not cryptography, and it must not be sold as more.

**Rejected failure modes are tested, not just asserted:** missing sidecar, missing report,
mismatched hash, malformed sidecar (five shapes), report mutated after the sidecar was written,
and — the case that would silently pass if the footer scheme were half-implemented — a report
carrying a `sha256 of those exact report bytes:` line whose hex is the digest of the body only,
which under whole-file hashing must **fail**. That last test is what pins the chosen scheme
against a future implementer "helpfully" adding the footer.

### C. The three callers that currently short-circuit

The comment at `scripts/sdd.py:259-263` says `archive_readiness` is the single list that both
`cmd_archive` and the ready-prompt read, so they cannot disagree. Fact 5 shows `:416` violates
that today. Fixed as follows.

**C.1 `cmd_verify` (`:393-432`).** Compute the blocker list once, then derive every message from
it. The block from `:393` to `:400` is replaced by:

```python
    placeholders, result_pending = packet_unfilled_reasons(change_dir)
    unfilled = packet_unfilled(change_dir)
    complete, pending = task_counts(change_dir / "tasks.md")
    caps_dir = root / "sdd-plus" / "specs" / "capabilities"
    bound = verdict_binding(change_dir)
    blockers = archive_readiness(change_dir, caps_dir, bound=bound)   # reuses the binding: 1 spawn, not 2
    blocking_unfilled = placeholders if bound.ok else unfilled

    print(f"Verified artifacts for {name}.")
    print(f"Tasks: {complete} complete, {pending} pending.")
    if blocking_unfilled:
        print("warning: unfilled placeholder content (TBD) remains in: "
              + ", ".join(blocking_unfilled))
    if bound.ok:
        print(f"Bound verifier verdict: {bound.verdict} "
              f"({VERIFIER_REPORT} sha256 {bound.digest[:12]}… confirmed by "
              f"{CHECK_VERDICT.name}).")
        if result_pending:
            print("note: verification.md Result is still Pending — waived by the "
                  "bound verdict.")
    elif bound.reason:
        print(f"warning: {VERIFIER_REPORT} is present but NOT bound: {bound.reason}")
    if any(c == "incomplete" for c, _ in blockers):
        print("Packet incomplete. Archive will require --force.")
```

- `:399-400`'s hard-coded `if pending > 0:` sentence is **replaced** by the blocker-derived line,
  so it can no longer claim `--force` is needed for a bound packet (fact 6).
- The `Tasks: N complete, M pending.` line still prints the **true** raw counts. Honesty about
  what is on disk is not traded for the waiver; the waiver is reported separately.

**C.2 The ready-prompt short-circuit (`:416`).** `if show_ready_prompt and not unfilled and
pending == 0:` becomes `if show_ready_prompt:`, and the branch reuses the `blockers` already
computed. Everything inside (`:419-431`) is unchanged: heading-issue branch first, then
`sync_only`, then `Not archive-ready: …`, then `READY TO ARCHIVE`. `unbound-verdict` is not in the
`sync_only` tuple at `:423`, so a failed bind can never print "Nearly there".

Behavior delta worth naming: an ordinary incomplete packet that today prints nothing after the
warnings will now print `Not archive-ready: 3 pending task(s)`. That is strictly more informative
and is what the `:259-263` comment already promised. It is a stdout change, and
`test_verify_prints_not_archive_ready_for_plain_incomplete_packet` pins it.

**C.3 `cmd_verify`'s return value (`:432`).** `return 1 if unfilled else 0` becomes
`return 1 if blocking_unfilled else 0`. So a bound packet whose only "unfilled" reason is the
waived pending Result exits 0, which is required for `READY TO ARCHIVE` and exit 1 not to
contradict each other. Per fact 8 this cannot affect `cmd_archive`, which discards the value —
and **no `sys.exit` is added to `cmd_verify`**, so `cmd_archive:544` still cannot die before
`archive_readiness` runs.

**C.4 `_classify_packet` (`:325-330`).** Minimal change, in scope only so far as keeping triage
from contradicting archive:

```python
        bound = verdict_binding(change_dir)
        verifier_pending, other_pending = verifier_owned_pending(change_dir / "tasks.md")
        pending = other_pending if bound.ok else verifier_pending + other_pending
        if pending > 0:
            return "IN-PROGRESS", f"{pending} pending task(s)"
        placeholders, result_pending = packet_unfilled_reasons(change_dir)
        unfilled = placeholders if bound.ok else sorted(
            set(placeholders) | set(result_pending), key=REQUIRED_FILES.index)
        if unfilled:
            return "CLAIMED-DONE-UNVERIFIED", "tasks done; unfilled: " + ", ".join(unfilled)
```

and the one call at `:333` becomes `if archive_readiness(change_dir, caps_dir, bound=bound):` —
the same binding already computed five lines up, so triage spends **one** spawn per claimed packet
rather than two (§F.3).

The rest of `_classify_packet` (`:331-337`: heading issues, `archive_readiness`, `ARCHIVE-READY`,
the `except` that turns any error into `UNKNOWN`) is untouched. **No triage rewrite:** the buckets,
`_TRIAGE_ORDER` (`:340-341`), `_TRIAGE_NEXT` (`:342-349`) and `cmd_triage` (`:352-375`) are not
changed. A packet that claims a report and fails to bind is still bucketed by the existing rules —
it reaches `archive_readiness` at `:333` only if its non-verifier tasks are done, and then lands in
`NEEDS-SYNC` with the message "delta specs not yet in the living specs", which is **wrong for that
case**. That mislabel is pre-existing behavior for any non-sync blocker at `:334` and is explicitly
**not** fixed here — recorded in §Risks so it is a known, not a discovered, limit.

### D. The producer path — answer to Codex blocking concern 1

> *"nothing guarantees those files will ever be created through the real verification flow, so the
> feature is not end-to-end and will only work when someone manually drops files into a packet."*

Accepted as a real gap in what Round 1 **wrote down**. But the premise that the producer does not
exist is contradicted by the tree, and the correction matters because it changes what has to be
built — from "invent a producer" to "redirect a hex that is already in hand".

#### D.1 The producer already runs, and fact 21 proves it hash-for-hash

The verification flow in this repo is choreography between four parties, and it already exists:

1. The **verifier subagent** writes nothing to the tree (`agents/verifier.md`, unedited by this
   packet; `AGENTS.md:84`; `sdd-plus/protocols/framework-usage.md:126`). It posts its report **and**
   the sha256 of those exact report bytes in one in-channel message.
2. **Grok (the choreographer)** copies that report **verbatim** into the packet directory as
   `verifier-report.md`. Six packets on disk prove the copy is byte-exact — see step 4.
3. The **Owner/choreographer** runs
   `python3 scripts/check_verdict.py <report> <sha256> <verdict>` (`scripts/check_verdict.py:17-44`).
   **Exit 0 is the bind.** This is not aspirational: the smoke packet's own archive record says
   *"VERIFIED WITH NOTES is bound by check_verdict.py sha256 88328932… at commit 174f04a…"*
   (`sdd-plus/archive/2026-09-01-grok-choreography-smoke/decision-log.md:18`).
4. **`sdd.py archive --force --reason "…"`** then writes that same hex into `decision-log.md` via
   `record_override` (`scripts/sdd.py:435-444`). Fact 21: for all three packets that recorded a
   digest, the recorded hex **equals** today's `sha256sum` of the report in the same directory
   (`88328932…`, `d25b70b8…`, `ce4fdba2…`). Byte-exact transport, verified this turn, three for
   three.

So at the exact moment `sdd.py archive` runs today, the choreographer is holding a 64-character hex
that `check_verdict.py` has **already** accepted against the exact bytes now sitting at
`<packet>/verifier-report.md`. It writes that hex into a `--reason` string. The only thing this
packet changes about the producer is that the hex is **also** written to
`<packet>/verifier-report.sha256` — one extra file write, at a step that already happens, by a party
that already has the value.

#### D.2 The producer is outside this repo, and that is why it is not code here

Grok is the choreographer, not a file in this tree. There is no `scripts/` module, no workflow job
and no conductor stage that transports verifier reports — confirmed on disk: every
`verifier-report.md` in the repo entered git in an **archive commit**
(`git log --diff-filter=A`: `4bacb6a`, `5622a75`, `7d0e31d`, `5bc5a91`, `472fe09`, `7b4200e`), never
as output of a repo script. So "add the producer to this repo" would mean inventing a workflow or
conductor stage that does not exist for the report either — strictly more surface than the feature
needs, and explicitly out of bounds under the Owner's constraints. **No `.github/workflows/`
change, no `scripts/conductor/` change, no new script, no Grok-code change is planned or required.**

The producer step is therefore documented **as choreography**, in this packet and in `sdd.py`'s own
error text, in exactly the place an operator hits it:

> **The ordinary archive-without-`--force` path (new):**
> 1. Verifier posts report + sha256 of those exact bytes in channel. Writes nothing.
> 2. Grok copies the report verbatim to `<packet>/verifier-report.md`. *(already happens)*
> 3. Grok/Owner runs `python3 scripts/check_verdict.py <packet>/verifier-report.md <hex>
>    "VERIFIED WITH NOTES"`. *(already happens; exit 0 is the bind)*
> 4. **New, one line:** after that exit 0, Grok writes the same hex to
>    `<packet>/verifier-report.sha256` — `printf '%s\n' "<hex>" > <packet>/verifier-report.sha256`,
>    or equivalently `sha256sum verifier-report.md > verifier-report.sha256` run in the packet dir
>    (§OQ-1 accepts both forms).
> 5. `python3 scripts/sdd.py archive <name>` — no `--force`, no `## Override` record.
>
> If step 4 is skipped, nothing breaks and nothing silently passes: the packet archives exactly as
> it does today, by ticking the boxes or with `--force --reason`. That is OQ-2 — a bound report is
> **sufficient, never necessary** — and it is the reason this is safe to ship without touching the
> producer's code.

#### D.3 Testable as an on-disk contract, not as a promise about Grok

The contract this packet actually enforces is a property of the packet **directory**, and it is
fully testable without Grok:

| Contract clause | How `sdd.py` decides it | Test |
| --- | --- | --- |
| both files present | `report.is_file() and sidecar.is_file()` | #9, #10 |
| sidecar holds one 64-hex digest | `sidecar_digest` grammar (§A.2) | #4, #5 |
| that hex is the **whole-file** sha256 of the report bytes | `check_verdict.py` exit 0 — the existing pinned bind (`scripts/check_verdict.py:29-33`) | #6, #11 |
| the report's verdict is `VERIFIED` / `VERIFIED WITH NOTES` | `verdict_line` whole-line rule (§A.2) | #1, #14, #15 |

All four are asserted on `tmp_path` packets built by the `_packet` / `_bound` fixtures: both files
present with matching hex → **bind**; missing sidecar, missing report, or mismatched hex →
**unbound**. New test #38 (§Tests) walks the §D.2 sequence end to end in a scratch tree — copy
report, run the real `check_verdict.py` CLI, write the sidecar from that same hex, then archive
without `--force` — so the *documented* producer step is what the test performs, and a drift between
the documented choreography and the gate is a red test.

**No test plants a `verifier-report.md` or `verifier-report.sha256` in the live
`sdd-plus/changes/`** (must_not_do 15). The live packet stays unbound and stays blocked, which
verification command 6 checks.

#### D.4 What is honestly *not* guaranteed

Stated plainly, because "end to end" should not be overclaimed:

- Nothing in this repo can **force** Grok to write the sidecar. The gate is fail-closed, not
  fail-loud: a forgotten step 4 means "archives the old way", not "archives wrongly".
- The six archived reports have **no** sidecar and never will (must_not_do 16, fact 16). They are
  unreachable by every predicate — `cmd_status:305-306`, `cmd_triage:357`, `cmd_verify:381` all
  resolve `sdd-plus/changes/` only. **No migration, no backfill** (Codex gap 2): a packet that
  already carries a report but no sidecar behaves exactly as it does today, and the operator's
  remedy is one `sha256sum` line or the `--force` they were already using.
- The sidecar is not a signature. §Risks says this in full; it is choreography, not cryptography.

### E. The verifier-owned matcher, closed over a complete inventory — answer to Codex blocking concern 2

> *"the plan only proves two examples … That is a contract problem, not just a regex detail."*

Accepted in full. Round 2 audits **every** `tasks.md` in the repo — six archived, the live packet,
and the template — reading every level-2 heading and every checkbox line. The audit found a shape
Round 1 had not seen (fact 23), which is exactly the failure Codex predicted.

#### E.1 The complete inventory — all eight `tasks.md` files

Packets with **zero** verifier-owned tasks are listed too; that is what makes the set closed.

| # | `tasks.md` | Level-2 headings (line) | Verifier-owned wording | Verifier-owned pending | Other pending |
| --- | --- | --- | --- | --- | --- |
| 1 | `archive/2026-09-01-grok-choreography-smoke` | `## Change`:3, `## Implementation`:7, **`## Verification (verifier subagent — not the Implementer)`:18** | **section form**, heading only — the four tasks at `:20-23` never name the verifier | **4** (`:20`, `:21`, `:22`, `:23`) | 0 |
| 2 | `archive/2026-09-01-grok-coplan-discover-probe` | `## Change`:3, `## Implementation`:7 | **none** — the string "verifier" does not occur in the file | 0 | 0 (13 tasks, all `- [x]`) |
| 3 | `archive/2026-09-01-grok-coplan-linux-discover` | `## Change`:3, `## Implementation`:7, **`## Verification`:26** | **none** — bare heading, no "verifier" anywhere; `:28-33` are implementer commands | **0 — must stay 0** | 0 (12 tasks, all `- [x]`) |
| 4 | `archive/2026-09-01-grok-docs-coplan-runtime` | `## Change`:3, `## Implementation`:7 | prose only, `:45-46` (not a checkbox, not a heading) | 0 | 0 (10 tasks, all `- [x]`) |
| 5 | `archive/2026-09-02-grok-coplan-closure-gate` | `## Change`:3, `## Status`:7, `## Implementation`:15, `## Implementer notes`:49 | **line form** `:47`; prose at `:56` | **1** (`:47`) | 0 |
| 6 | `archive/2026-09-02-grok-refuse-brief-engine` | `## Change`:3, `## Planning (Round 2 of 2, final — complete)`:7, `## Implementation`:14, `## Blocked on Owner`:61 | **line form** `:57`; prose at `:18-19` | **1** (`:57`) | 0 |
| 7 | `changes/grok-archive-bound-verdict` (live) | `## Change`:3, `## Implementation`:7 | **none** — template verbatim | 0 | **5** (`:9-13`) |
| 8 | `templates/tasks.md` (fresh-packet baseline) | `## Change`:3, `## Implementation`:7 | **none** | 0 | **5** (`:9-13`) |

Every distinct verifier-owned wording in the repo, quoted verbatim — this is the whole set:

- **Line form, two instances, both `- [ ]`:**
  - `sdd-plus/archive/2026-09-02-grok-refuse-brief-engine/tasks.md:57` —
    `- [ ] Step 12 — Invoke the verifier subagent. Do not self-certify. Only then may these boxes and`
    (continuation `:58-59`, not itself a checkbox; fact 2 — only the checkbox line is read)
  - `sdd-plus/archive/2026-09-02-grok-coplan-closure-gate/tasks.md:47` —
    `- [ ] Invoke the verifier subagent; do not self-certify.`
- **Section form, one instance:**
  - `sdd-plus/archive/2026-09-01-grok-choreography-smoke/tasks.md:18` —
    `## Verification (verifier subagent — not the Implementer)`, enclosing
    `- [ ] Independently re-run the test suite.` (`:20`),
    `- [ ] Review the diff against brief scope and protected-path constraints.` (`:21`),
    `- [ ] Confirm evidence claims in ` + "`verification.md`." (`:22`),
    `- [ ] Set the verification Result.` (`:23`) — **none of which names the verifier**.

Every wording that names the verifier but must **not** waive — also the whole set:

- `sdd-plus/archive/2026-09-01-grok-coplan-linux-discover/tasks.md:26` — `## Verification`
  (bare heading; `:28-33` are `pytest`, `start_probe.py`, `discover_core()`,
  `negotiate.py --round 1`, `launchguardian scan`). **Implementer-owned.**
- `sdd-plus/archive/2026-09-01-grok-docs-coplan-runtime/tasks.md:45-46` — prose note,
  `- Verification is implementer-checked only. The verifier subagent was not invoked …`. Note the
  leading `- `: it is a **bullet**, not a checkbox, so `^\s*-\s*\[\s\]\s+` does not match it.
- `sdd-plus/archive/2026-09-02-grok-coplan-closure-gate/tasks.md:56` — prose,
  `run, and no verifier subagent was invoked in this turn.`
- `sdd-plus/archive/2026-09-02-grok-refuse-brief-engine/tasks.md:18-19` — prose,
  `… the Owner deferred the verifier` / `subagent this turn …`. Note it is **line-wrapped across the
  phrase**; `_flatten` operates per line, so neither half matches, and it is prose either way.
- `sdd-plus/templates/tasks.md:13` and `changes/grok-archive-bound-verdict/tasks.md:13` —
  `- [ ] Run verification.` The word is "verification", not "verifier". **Implementer-owned.**

#### E.2 The matcher is closed over that set, unchanged in shape

The inventory revealed **no third positive shape**. The two scopes of §A.3 — checkbox line, or
enclosing level-2 heading — cover 6 of 6 verifier-owned pending tasks in the repo (4 + 1 + 1) and
waive **zero** of the 45 implementer-owned tasks. So `_VERIFIER_OWNED` stays one regex plus one
heading rule; it is now closed rather than heuristic, and §Risks records what would break it.

What the audit **did** change is the matcher's stated anchor, and this is a real contract fix, not
wording: it is anchored on the token **`verifier`**, never on `verif`. Fact 23 shows why — a
`verif`-anchored or "heading named Verification" design would waive
`archive/2026-09-01-grok-coplan-linux-discover/tasks.md:28-33`, five implementer commands including
a live `negotiate.py` run and a LaunchGuardian scan. That is precisely the "accidentally waive
implementation tasks" outcome Codex named.

#### E.3 One test per inventoried wording, plus the negatives

Tests #17-#19 are replaced by a parametrized closed-set suite (§Tests #17-#19d). Every row of §E.1
is a case:

| Inventoried wording | Expected `verifier_owned_pending` | Test |
| --- | --- | --- |
| refuse-brief-engine `:57` line form (with the `Step 12 —` prefix) | `(1, 0)` | #17 |
| closure-gate `:47` line form (bare imperative) | `(1, 0)` | #17 |
| the same line with backticks/emphasis around `verifier` | `(1, 0)` | #17 |
| `sub-agent` spelling | `(1, 0)` | #17 |
| smoke `:18-23` section form, 4 tasks | `(4, 0)` | #18 |
| smoke section closed by a following `## Notes` heading | tasks after it → `other` | #18 |
| **linux-discover `:26-33` bare `## Verification` + 5 tasks** | **`(0, 5)`** | **#19a** |
| **prose notes naming the verifier subagent (all four instances of §E.1)** | **`(0, n)`** | **#19b** |
| **`- [ ] Run verification.` (template `:13`)** | **`(0, 1)`** | **#19c** |
| template `:9-13`, all five lines verbatim | `(0, 5)` | #19 |
| **`- [ ] Implement the smallest coherent change.` under any heading** | **`(0, 1)`** | **#19c** |
| the live packet's own `tasks.md` bytes | `(0, 5)` | #19d |
| every archived `tasks.md`, `sum(...) == task_counts(...)[1]` | invariant holds | #16 |

#19d reads `sdd-plus/changes/grok-archive-bound-verdict/tasks.md` and every
`sdd-plus/archive/*/tasks.md` **read-only** and asserts the §E.1 column values. It is the
regression that fails if a future packet introduces a wording the closed set does not cover — the
inventory stops being a one-time audit and becomes an enforced contract. (It reads real files
rather than `tmp_path`; that is allowed because it only reads. It writes nothing, and it is the one
exception to the `tmp_path`-only rule, called out here so it is deliberate.)

### F. Operational policy for the subprocess — answer to Codex blocking concern 3

> *"That changes a formerly cheap, deterministic check into a subprocess-heavy one with new failure
> modes and repeated work per packet. The plan does not say whether the added latency and
> brittleness are acceptable or how repeated calls should be controlled."*

Accepted in full. Policy, in six parts. It is a policy, not a redesign: no worker pool, no async, no
threads, no daemon, no persistent cache file. Mode stays LITE.

#### F.1 When a subprocess may be spawned — the gate before the gate

`verdict_binding` spawns `check_verdict.py` **only** after all of these have already passed on
cheap, pure file operations (§A.2, in this order):

1. `verifier-report.md` **and** `verifier-report.sha256` both `is_file()`;
2. the sidecar text parses to exactly one 64-hex digest (`sidecar_digest`);
3. the report's `## Verdict` section is exactly one line **and** that line is in `BOUND_VERDICTS`;
4. `CHECK_VERDICT.is_file()`.

Consequence, stated as the operational rule: **a packet that claims nothing never spawns anything.**
Every packet in `sdd-plus/changes/` today (count: **1**, `grok-archive-bound-verdict`, which carries
no `verifier-report.md`) costs **zero** subprocesses, so `sdd.py triage`, `verify` and `archive`
have the same subprocess cost after this change as before it — zero — for the entire current tree.
The cost is paid only by packets that have actually been verified.

`archive_readiness` itself never spawns directly; it spawns only via one `verdict_binding` call, and
only when `bound is None`.

#### F.2 Timeout: `timeout=30`, kept, with a measured justification

Kept at 30 s, and the number is now defended rather than assumed:

- Measured cost on this VM (fact 26), five consecutive real spawns against the largest archived
  report: `[0.0252, 0.0267, 0.0269, 0.0285, 0.0253]` s, **mean 26.5 ms**, all exit 0. 30 s is
  ~**1 130×** headroom.
- The work is bounded and small: read one file (5-6 KB across all six archived reports), one
  `hashlib.sha256`, one substring test (`scripts/check_verdict.py:29-43`). There is no network, no
  git, no lock, and no input whose size an attacker controls beyond the report the operator put in
  the packet.
- It sits inside the repo's existing convention: `scripts/conductor/review.py:67` uses `timeout=30`;
  `scripts/start_probe.py:92` and `kernel/brief_complete_engine.py:527` use `timeout=60`. And it is
  **stricter than the precedent it copies**: `scripts/record_verify_bound.py:33-38` runs the very
  same `check_verdict.py` with **no timeout at all**, so this packet tightens rather than loosens
  the repo's posture on this exact subprocess.
- **Timeout is a block, never a pass.** `subprocess.TimeoutExpired` → `ok=False`,
  `reason="check_verdict.py timed out after 30s"` → `unbound-verdict`. The operator's remedy is
  `--force --reason`, which is an audited, recorded decision — the correct place for a judgement
  call about a hung machine.

#### F.3 How many spawns — exactly one or zero per call, never a loop

**`verdict_binding`: at most one `subprocess.run`. No loop, no retry, no fallback command.** A
non-zero exit is a verdict about the packet, not a transient to retry; retrying would only turn a
deterministic refusal into a slower deterministic refusal.

**`archive_readiness`: exactly one `verdict_binding` call, or zero when `bound=` was supplied.** It
is not called inside the delta-spec loops (`:281-286`), and it is not called per required file.

**Repeated work across one process — the `bound=` parameter (§A.4).** Codex is right that the naive
version does the same work two or three times in one CLI invocation. Exact budget, per command,
with the `bound=` plumbing in place:

| Command | Path | Spawns per *claimed* packet | Per *unclaimed* packet |
| --- | --- | --- | --- |
| `sdd.py status` | `cmd_status:303-314` — never calls `archive_readiness` or `verdict_binding` (fact 25); **not edited** | **0** | 0 |
| `sdd.py verify <n>` | `cmd_verify` computes `bound` once (§C.1) and passes it to `archive_readiness:418` | **1** | 0 |
| `sdd.py triage` | `_classify_packet` computes `bound` once (§C.4) and passes it to `archive_readiness:333` | **1** | 0 |
| `sdd.py archive <n>` | `cmd_archive:544` → `cmd_verify` (1) + `cmd_archive:551` → `archive_readiness` (1) | **2** | 0 |
| `sdd.py new` / `init` / `abandon` | no readiness call | 0 | 0 |

Without `bound=` those columns would read 2 / 2 / 3. **`sdd.py triage` therefore costs one spawn per
claimed packet — bounded today by 1 active packet, 0 of them claimed, i.e. 0 spawns.** At a
plausible ceiling of ~10 simultaneously-claimed packets that is ~265 ms of subprocess time for a
command that already walks every packet's `tasks.md`, five required files and every delta spec.
Accepted. **Hundreds of packets would justify a real cache; that is explicitly future work and out
of scope** — and it would be a change to `verdict_binding` alone, since `bound=` already routes every
caller through one place.

**Why `sdd.py archive` keeps two spawns instead of one, stated rather than hidden:** collapsing it
would require `cmd_verify` to hand its binding back to `cmd_archive`, but `cmd_verify` returns an
`int` that `main()` uses as the process exit status, and `cmd_archive:544` deliberately discards it
(fact 8). Changing that return type to carry a binding is a wider blast radius than the ~26 ms it
saves. Two spawns per archive is the accepted bound.

**Why not a module-level cache** (the alternative considered, and rejected):

- A `dict` keyed on `(resolved path, mtime_ns, size)` is stale-prone in exactly this codebase's
  tests: test #12 mutates a report inside one process, and a same-size mutation inside one mtime
  tick would return a cached `ok=True` for bytes that no longer hash to the sidecar. A gate that can
  answer from a stale key is a worse failure than a duplicated 26 ms.
- Keying on the report's **content** hash would put a second `hashlib.sha256` call inside `sdd.py` —
  the precise thing §B and must_not_do 10 exist to prevent, because a future reader cannot tell a
  cache hash from a bind hash.
- Module-level mutable state in a **pinned governance script** is a durable readability cost for a
  transient benefit, and it makes test isolation depend on remembering to clear it.
- `bound=` achieves the identical spawn reduction with no state, no staleness window, no second
  hasher, and a one-line equivalence test (#39).

#### F.4 Failure modes — every one of them blocks (fail closed)

No failure mode is ignored, and none is ever silently converted to "no claim". `reason == ""`
(no claim) is reachable **only** from the both-files-absent branch (§A.2, first `return`).

| Failure | Detected at | `VerdictBinding` | Blocker |
| --- | --- | --- | --- |
| `check_verdict.py` file missing/deleted | `CHECK_VERDICT.is_file()` | `ok=False`, `reason="missing check_verdict.py"` | `unbound-verdict` |
| interpreter/exec failure, `OSError` | `except OSError` | `ok=False`, `reason="cannot run …"` | `unbound-verdict` |
| any other `SubprocessError` | `except subprocess.SubprocessError` | `ok=False`, `reason="cannot run …"` | `unbound-verdict` |
| **timeout at 30 s** | `except subprocess.TimeoutExpired` (**listed first** — it subclasses `SubprocessError`) | `ok=False`, `reason="… timed out after 30s"` | `unbound-verdict` |
| non-zero exit (hash mismatch, missing file, bad UTF-8, verdict absent) | `proc.returncode != 0` | `ok=False`, `reason="check_verdict.py exit N: <stderr tail>"` | `unbound-verdict` |
| report or sidecar unreadable / not UTF-8 | `except (OSError, UnicodeDecodeError)` around the reads | `ok=False`, `reason="cannot read verdict artifacts: …"` | `unbound-verdict` |
| sidecar malformed | `sidecar_digest` → `""` | `ok=False`, grammar stated in `reason` | `unbound-verdict` |
| verdict not whitelisted / absent / multi-line | `verdict_line` + `BOUND_VERDICTS` | `ok=False`, `reason` quotes what was found | `unbound-verdict` |
| **neither file present** | first `return` | `ok=False`, **`reason=""`** | **none** — not a fault |

`unbound-verdict` never removes the `incomplete` blocker; both fire together (§A.5 matrix), so a
failed bind can never make a packet *more* archivable than it was. And `_classify_packet`'s
`except Exception` (`:336`) still turns anything unforeseen into `UNKNOWN` rather than a crashed
sweep — a bug in `verdict_binding` degrades triage to "UNKNOWN", never to "ARCHIVE-READY".

#### F.5 Latency and brittleness: accepted, with the bound written down

- **Latency.** Accepted. Worst case for the current tree is `sdd.py archive` on a bound packet:
  2 × 26.5 ms ≈ **53 ms** added to a command that already reads ~8 files and moves a directory.
- **Brittleness.** Two new dependencies enter the readiness path: a Python interpreter that can
  spawn (`sys.executable`), and `scripts/check_verdict.py` existing on disk. Both are already
  required by `scripts/record_verify_bound.py:33-38` and by `start_probe.py:92`, and both are pinned
  (`drydock-pins.json:9` for `check_verdict.py`). If either is broken the packet blocks and the
  operator sees a named reason — the failure is loud and recoverable via `--force`.
- **Non-determinism.** The subprocess is deterministic given the bytes: same report + same sidecar →
  same exit code. The only non-deterministic outcome is the timeout, which fails closed. Codex's
  "flaky failures" risk is therefore bounded to "a machine so loaded that a 26 ms process takes
  30 s", whose remedy is an audited `--force`.

#### F.6 Triage output changes — the explicit statement Codex asked for (gap 3)

**Yes, `sdd.py triage` output changes for packets that now have a bound report, and that is
intended.** A bound packet whose only pending tasks are verifier-owned moves from `IN-PROGRESS`
("finish the packet, or abandon it", `:347`) to `ARCHIVE-READY`. Leaving it in `IN-PROGRESS` would
reproduce the exact `:259-263` contradiction this packet exists to remove, in triage instead of
verify. Pinned by tests #32/#33. No bucket is added or removed, `_TRIAGE_ORDER` (`:340-341`) and
`_TRIAGE_NEXT` (`:342-349`) are untouched, and packets with no report are bucketed
byte-for-byte as they are today. The one thing that stays wrong — a failed bind reading as
`NEEDS-SYNC` — is pre-existing for every non-sync blocker at `:334` and is recorded in §Risks.

#### F.7 Test tiers (Codex gap 4)

The matrix is large because the fail-closed matrix is large, but it is not undifferentiated. The
§Tests table is read in three tiers, and a failure's tier says where to look:

- **Tier 1 — pure unit, no subprocess, no tree** (#1-#5, #16-#19d, #20): `verdict_line`,
  `sidecar_digest`, `verifier_owned_pending`, `packet_unfilled_reasons`. Fast, no I/O beyond
  `tmp_path` reads. A failure here is a parser/matcher bug.
- **Tier 2 — binding + readiness contract, real `check_verdict.py`, no CLI** (#6-#15, #21-#27,
  #38-#41): `verdict_binding` and `archive_readiness` called directly. A failure here is a gate-logic
  or subprocess-policy bug.
- **Tier 3 — end-to-end CLI under `_isolated_tree`, stdout- and filesystem-asserting** (#28-#37):
  `cmd_verify`, `cmd_archive`, `_classify_packet`. A failure here is a wiring or message bug, and it
  is the only tier that scrapes stdout.

Tier 3 asserts on **substrings** (`"READY TO ARCHIVE" in out`), never on whole-line equality, so
incidental wording changes elsewhere do not cascade.

## Steps

1. Re-read `scripts/sdd.py:84-90`, `:182-217`, `:244-256`, `:259-300`, `:317-337`, `:378-432`,
   `:539-568` and `scripts/check_verdict.py:17-44`; confirm facts 1-11 still hold at HEAD
   `1da7781`. Run `sha256sum scripts/sdd.py` **before touching anything** and confirm it is
   `202e2fb127caa716788f8866dfdd80f02b49eca937037aee0ecf2c57174c48f1`. If it is not, the tree is
   not the tree this plan was written against — stop and report to the Owner.
2. Add `import subprocess` to `scripts/sdd.py` (alphabetical among `shutil` and `sys`, `:15-16`)
   and `from typing import NamedTuple`. No other import moves.
3. Add the constants of §A.2 (`VERIFIER_REPORT`, `VERIFIER_SHA`, `BOUND_VERDICTS`,
   `CHECK_VERDICT`, `_SHA256_HEX`, `_VERIFIER_OWNED`) beside `REQUIRED_FILES`/`KEBAB`
   (`:19-23`), except `CHECK_VERDICT`, which goes with them and is anchored on
   `Path(__file__).resolve().parent`.
4. Add `_flatten`, `VerdictBinding`, `verdict_line`, `sidecar_digest`, `verdict_binding` and
   `verifier_owned_pending` between `packet_unfilled` (`:256`) and `archive_readiness` (`:259`).
5. Split `packet_unfilled` into `packet_unfilled_reasons` + a `packet_unfilled` that returns the
   identical list (§A.4). Do **not** change what `packet_unfilled` returns.
6. Edit `archive_readiness` per §A.4: add the keyword-only `bound: VerdictBinding | None = None`
   parameter, rewrite the final block, add the `unbound-verdict` blocker, and update its docstring
   (`:259-267`) to say it now spawns `check_verdict` (at most once, zero for an unclaimed packet),
   is read-only but **not** side-effect-free, and what `bound=` is for. Drop the word "pure" from
   `:260`.
7. Edit `cmd_verify` per §C.1-C.3: derive the messages from `blockers`, pass `bound=bound` into
   `archive_readiness` (§F.3), drop the `:416` short-circuit, return on `blocking_unfilled`. Add no
   `sys.exit`.
8. Edit `cmd_archive`'s hint (`:555-557`) to add the `unbound-verdict` branch first. Change
   nothing else in `cmd_archive` — `--force`, `--reason`, `record_override`, the collision check
   and `shutil.move` all stay as they are.
9. Edit `_classify_packet:325-330` per §C.4, and pass `bound=bound` at `:333`. Touch nothing else
   in triage.
9a. **Re-run the §E.1 inventory before locking the matcher.** `grep -n '^## ' sdd-plus/archive/*/tasks.md
   sdd-plus/changes/*/tasks.md sdd-plus/templates/tasks.md` and `grep -ni 'verif'` over the same
   set. If any wording appears that §E.1 does not list, **stop and tell the Owner** — the matcher is
   closed over that table, and a new shape is a contract change, not a regex tweak.
10. Write `tests/test_sdd_archive_bound_verdict.py` (§Tests). Every fixture under `tmp_path`;
    the `_isolated_tree` guard fixture is mandatory for any test that calls `cmd_archive`,
    `cmd_verify` or `find_root`.
11. `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` — green, including all
    pre-existing tests. Fix until green; never by weakening a refusal, never by widening the
    waiver, never by editing `scripts/check_verdict.py`.
12. **Re-pin last, in this exact order** (§Pin update ordering). Finish every edit to
    `scripts/sdd.py` → hash it → write that one value to `drydock-pins.json:6` → only then run
    `python3 scripts/start_probe.py`.
13. `python3 scripts/start_probe.py` — expect `"ok": true`, `"pin_errors": []`.
14. Run the verification commands below; paste output verbatim into `verification.md`.
15. `git status --porcelain` — expect only `scripts/sdd.py`, `drydock-pins.json`,
    `tests/test_sdd_archive_bound_verdict.py` and the packet artifacts. No `.env`, no
    `sdd-plus/archive/` change, no `__pycache__` noise, and **no packet moved out of
    `sdd-plus/changes/`**.
16. Fill `tasks.md`, `verification.md` (evidence sections) and `decision-log.md`, replacing the
    template `TBD` rows. Leave the Result and the verifier task per Step 17.
17. Invoke the verifier subagent. Do not self-certify. Only then may `verification.md` Result move.

### Pin update ordering

1. Finish **every** edit to `scripts/sdd.py`.
2. `python3 -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('scripts/sdd.py').read_bytes()).hexdigest())"`
3. Write **that one value** into `drydock-pins.json:6`. Nothing else in the pins map changes — in
   particular `scripts/check_verdict.py` (`:9`), `scripts/start_probe.py` (`:12`),
   `kernel/brief_complete_engine.py` (`:26`) and the six conductor pins (`:27-32`) do not move,
   and neither do `drydock_commit` / `verifier_md_git_blob` / `hash_alg`.
4. **Only then** run `python3 scripts/start_probe.py`.

Re-pinning before the file is final leaves the probe failing its own `check_pins()` (fact 18);
running the probe before re-pinning fails with `hash drift scripts/sdd.py`.

## Tests

New file `tests/test_sdd_archive_bound_verdict.py`. Preamble follows
`tests/test_start_probe_conductor_closure.py`: `ROOT = Path(__file__).resolve().parent.parent`,
`sys.path.insert(0, str(ROOT / "scripts"))`, `import sdd`.

**Fixtures — nothing ever touches the live tree:**

```python
CLEAN = {                                   # no TBD, no {{CHANGE_NAME}}
    "brief.md":        "# Brief\n\n## Acceptance Criteria\n\n- [ ] Something real.\n",
    "plan.md":         "# Plan\n\n## Approach\n\nDo the thing.\n",
    "tasks.md":        "# Tasks\n\n- [x] Implement the smallest coherent change.\n",
    "decision-log.md": "# Decision Log\n\nNo decisions needed.\n",
    "verification.md": "# Verification\n\n## Result\n\nPending.\n",
}
REPORT = "# Verification Report\n\n## Isolation\n\nMutation: zero.\n\n## Verdict\n{v}\n"


def _packet(tmp_path, *, tasks=None, result="Pending.", report=None,
            sidecar=None, files=None) -> Path:
    """A fake packet under tmp_path/sdd-plus/changes/<name>. Never the live tree."""


def _bound(tmp_path, verdict="VERIFIED WITH NOTES", **kw) -> Path:
    """_packet(...) whose sidecar holds the true sha256 of the report bytes."""


@pytest.fixture
def _isolated_tree(tmp_path, monkeypatch):
    """chdir into a complete fake sdd-plus tree and REFUSE to proceed unless
    sdd.find_root() resolves to tmp_path. Mandatory for every test that calls
    cmd_verify / cmd_archive / _classify_packet through find_root: cmd_archive
    MOVES the packet, so a find_root that escaped to the real repo would archive a
    live packet."""
    (tmp_path / "sdd-plus" / "standards").mkdir(parents=True)
    (tmp_path / "sdd-plus" / "standards" / "s.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "sdd-plus" / "specs" / "capabilities").mkdir(parents=True)
    (tmp_path / "sdd-plus" / "changes").mkdir(parents=True)
    (tmp_path / "sdd-plus" / "archive").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    assert sdd.find_root() == tmp_path.resolve()
    return tmp_path
```

| # | Test | Asserts |
| --- | --- | --- |
| 1 | `test_verdict_line_extracts_single_line` | `## Verdict` + one line → that line; parametrized over `VERIFIED`, `VERIFIED WITH NOTES`, `NOT VERIFIED` |
| 2 | `test_verdict_line_rejects_multi_line_section` | verdict plus a prose line → `""` |
| 3 | `test_verdict_line_rejects_missing_section` | no `## Verdict` → `""` |
| 4 | `test_sidecar_digest_accepts_bare_hex_and_sha256sum_form` | `<hex>`, `<hex>  verifier-report.md`, `<hex> *verifier-report.md`, and a leading `# comment` line → the hex |
| 5 | `test_sidecar_digest_rejects_malformed` | parametrized: empty, `not-a-hash`, 63 hex chars, 65 hex chars, two hex lines, `<hex>  other.md` → `""` |
| 6 | `test_bound_report_binds` | `_bound(...)` → `ok is True`, `verdict == "VERIFIED WITH NOTES"`, `digest` == real sha256, `reason == ""` |
| 7 | `test_bound_accepts_plain_verified` | verdict `VERIFIED` → `ok is True` |
| 8 | `test_no_artifacts_is_not_a_claim` | neither file → `ok is False` **and `reason == ""`** |
| 9 | `test_missing_sidecar_is_not_bound` | report only → `ok is False`, `reason` names `verifier-report.sha256` |
| 10 | `test_missing_report_is_not_bound` | sidecar only → `ok is False`, `reason` names `verifier-report.md` |
| 11 | `test_hash_mismatch_is_not_bound` | sidecar `"0"*64` → `reason` contains `check_verdict.py exit` and `sha256 mismatch` |
| 12 | `test_report_edited_after_sidecar_written_is_not_bound` | build bound, then append `\nstray\n` to the report → not bound. **The fail-closed-on-drift property that justifies the sidecar over a footer.** |
| 13 | `test_footer_in_report_does_not_bind_body_only_hash` | report carrying `sha256 of those exact report bytes: <hex-of-body>` with the sidecar holding that same body-only hex → **not bound** (whole-file hashing is the contract; pins §B against a half-added footer) |
| 14 | `test_not_verified_is_rejected_before_check_verdict` | correct whole-file hash, verdict `NOT VERIFIED` → not bound; `reason` contains `'NOT VERIFIED'` and does **not** mention `check_verdict`. Pins the substring trap (fact 11) |
| 15 | `test_blocked_and_unknown_verdicts_rejected` | parametrized `BLOCKED`, `VERIFIED WITH NOTES.` (trailing period), `verified with notes` (lowercase), `` → not bound |
| 16 | `test_owner_split_totals_match_task_counts` | for four fixture `tasks.md` shapes, `sum(verifier_owned_pending(p)) == task_counts(p)[1]` |
| 17 | `test_verifier_owned_line_form` | **closed set, parametrized over every line-form wording in §E.1**: refuse-brief-engine `:57` verbatim (`- [ ] Step 12 — Invoke the verifier subagent. Do not self-certify. Only then may these boxes and`), closure-gate `:47` verbatim (`- [ ] Invoke the verifier subagent; do not self-certify.`), the same with backticks/`**` around `verifier`, and the `sub-agent` spelling → each `(1, 0)` |
| 18 | `test_verifier_owned_section_form` | smoke-packet shape verbatim: `## Verification (verifier subagent — not the Implementer)` + the four tasks at `:20-23` → `(4, 0)`; a following `## Notes` heading closes the section; a `###` sub-heading inside it does **not** |
| 19 | `test_template_tasks_are_never_verifier_owned` | the five literal lines of `sdd-plus/templates/tasks.md:9-13` → `(0, 5)` |
| 19a | `test_bare_verification_heading_is_not_verifier_owned` | **fact 23** — linux-discover `:26-33` shape: `## Verification` + the five implementer commands (`pytest`, `start_probe.py`, `discover_core()`, `negotiate.py --round 1`, `launchguardian scan`), rendered as `- [ ]` → **`(0, 5)`**. The regression that keeps a `verif`-anchored matcher out |
| 19b | `test_prose_naming_the_verifier_is_not_a_task` | all four prose instances of §E.1 (docs-coplan-runtime `:45-46`, closure-gate `:56`, refuse-brief-engine `:18-19`, incl. the line-wrapped `verifier` / `subagent` split) placed under `## Implementation` with one pending implementation task → `(0, 1)`. Neither a checkbox nor a heading; must not set section state either |
| 19c | `test_implementation_tasks_are_never_waived` | **the negative Codex asked for**, parametrized: `- [ ] Implement the smallest coherent change.`, `- [ ] Run verification.`, `- [ ] Confirm scope and standards.`, `- [ ] Add or update tests/checks where useful.`, `- [ ] Update docs/specs for behavior, setup, data, API, or workflow changes.` — each under `## Implementation` **and** repeated under a bare `## Verification` heading → `(0, 1)` in every case |
| 19d | `test_repo_tasks_corpus_matches_the_inventory` | **read-only over the real tree** — for each of `sdd-plus/archive/*/tasks.md` (6), `sdd-plus/changes/grok-archive-bound-verdict/tasks.md` and `sdd-plus/templates/tasks.md`, assert `verifier_owned_pending` equals the §E.1 row exactly: `(4,0)`, `(0,0)`, `(0,0)`, `(0,0)`, `(1,0)`, `(1,0)`, `(0,5)`, `(0,5)`. Fails the day a new wording enters the repo, so the inventory stays a contract rather than a one-time audit. Writes nothing |
| 20 | `test_packet_unfilled_behavior_unchanged` | placeholder-only, pending-Result-only, both → identical list to today's semantics, `REQUIRED_FILES` order, no duplicates |
| 21 | `test_bound_waives_verifier_task_and_pending_result` | bound packet, only verifier tasks pending, Result `Pending.` → `archive_readiness(...) == []` |
| 22 | `test_bound_does_not_waive_implementation_tasks` | bound + `- [ ] Implement the smallest coherent change.` → exactly one `incomplete` blocker whose message says `1 pending task(s)` |
| 23 | `test_bound_does_not_waive_placeholders` | bound + `TBD` line in `plan.md` → `incomplete` naming `plan.md` |
| 24 | `test_bound_does_not_waive_unsynced_capability` | bound + delta spec with a capability that has no living spec → `unsynced-capability` still present |
| 25 | `test_unbound_claim_yields_both_blockers` | parametrized over no-sidecar / bad-hash / `NOT VERIFIED` / malformed sidecar → categories include **both** `unbound-verdict` and `incomplete` |
| 26 | `test_no_claim_yields_no_unbound_blocker` | pending tasks, no report → exactly one blocker, category `incomplete` (**fail-case 3 baseline, unchanged**) |
| 27 | `test_clean_packet_without_report_is_ready` | all ticked, Result filled, no report → `[]` (**a report is not made mandatory**) |
| 28 | `test_verify_prints_ready_for_bound_packet` | `_isolated_tree`, `cmd_verify(name)` → stdout has `READY TO ARCHIVE` and `Bound verifier verdict: VERIFIED WITH NOTES`; return value `0` |
| 29 | `test_verify_does_not_print_ready_for_unbound_packet` | stdout has `Not archive-ready`, no `READY TO ARCHIVE`, and `NOT bound` warning |
| 30 | `test_verify_prints_not_archive_ready_for_plain_incomplete_packet` | no report, pending tasks → `Not archive-ready: … pending task(s)` (the `:416` short-circuit removal) |
| 31 | `test_verify_does_not_claim_force_for_bound_packet` | `Archive will require --force.` **absent** from stdout for a bound packet, present for an unbound one |
| 32 | `test_classify_bound_packet_is_archive_ready` | `_classify_packet` → `("ARCHIVE-READY", …)` |
| 33 | `test_classify_unbound_packet_is_in_progress` | same packet without the sidecar → `IN-PROGRESS` |
| 34 | `test_archive_moves_bound_packet_without_force` | `_isolated_tree`, `cmd_archive(name, force=False)` → dir now at `sdd-plus/archive/<today>-<name>`, gone from `changes/`, and `decision-log.md` contains **no** `## Override` |
| 35 | `test_archive_refuses_unbound_packet_without_force` | `pytest.raises(SystemExit)`, message contains `not archive-ready` and the `Bind the verifier verdict` hint; packet still in `changes/` |
| 36 | `test_archive_force_still_works_and_records_override` | unbound packet, `force=True, reason="x"` → moved **and** `## Override` appended (`--force` not weakened) |
| 37 | `test_archive_force_on_bound_packet_records_no_override` | bound packet + `--force` → moved, no `## Override` (follows fact 9; pins that a bound archive is not an override even when forced) |
| 38 | `test_producer_choreography_end_to_end` | **§D.3, the producer contract as a test.** In `_isolated_tree`: write a report, run the **real** `scripts/check_verdict.py` CLI via `subprocess` with the digest from `sha256sum`-equivalent bytes and `"VERIFIED WITH NOTES"` → assert exit 0; **then** write that same hex to `verifier-report.sha256`; then `cmd_archive(name, force=False)` succeeds with no `## Override`. Performs the §D.2 step sequence, so documented choreography and gate cannot drift |
| 39 | `test_archive_readiness_bound_param_is_equivalent` | for a bound packet, an unbound-claim packet and a no-claim packet: `archive_readiness(d, c) == archive_readiness(d, c, bound=verdict_binding(d))`. Pins that `bound=` is an optimization, never a semantic |
| 40 | `test_unclaimed_packet_spawns_no_subprocess` | **§F.1 spawn budget.** `monkeypatch.setattr(sdd.subprocess, "run", boom)` where `boom` raises; `archive_readiness` on a packet with no report, with a report but no sidecar, with a malformed sidecar, and with verdict `NOT VERIFIED` → returns normally in every case, proving the cheap gates short-circuit before any spawn |
| 41 | `test_subprocess_failures_all_fail_closed` | **§F.4 matrix**, parametrized by monkeypatching `sdd.subprocess.run` to raise `TimeoutExpired`, `OSError`, `SubprocessError`, and to return `returncode=1` — plus `monkeypatch.setattr(sdd, "CHECK_VERDICT", tmp_path / "gone.py")` for the missing-binary case. Each → `ok is False`, `reason != ""` (never the no-claim `""`), and `archive_readiness` reporting **both** `unbound-verdict` and `incomplete`. Timeout's reason must say `timed out`, not `cannot run` (exception-ordering regression) |

Hard test rules:

- **`tmp_path` only.** No test writes into `sdd-plus/changes/`, `sdd-plus/archive/`, `scripts/`,
  `kernel/` or `tests/` at runtime. **One deliberate exception, read-only:** #19d *reads*
  `sdd-plus/archive/*/tasks.md`, the live packet's `tasks.md` and `sdd-plus/templates/tasks.md` to
  assert the §E.1 inventory. It opens them for reading and nothing else — no write, no move, no
  fixture planted (must_not_do 15 still holds in full).
- **Tiered (§F.7).** Tier 1 pure unit, Tier 2 binding/readiness with the real `check_verdict.py`,
  Tier 3 end-to-end CLI. Tier 3 asserts stdout **substrings**, never whole lines.
- **`cmd_archive` is only ever called under `_isolated_tree`**, whose `assert sdd.find_root() ==
  tmp_path.resolve()` is the mechanical guard against archiving a live packet.
- **No verify-run ledger event.** No test invokes `kernel/brief_complete_engine.py`,
  `kernel/brief_engine.py`, `scripts/record_verify_bound.py`, or any `--record-verify` form.
- Tests exercise the **real** `scripts/check_verdict.py` through `verdict_binding` — that is the
  point, and it is safe because `check_verdict` only reads.
- Pre-existing tests are not modified. `tests/test_check_verdict.py` in particular stays exactly
  as it is.

## Files Expected To Change

- `scripts/sdd.py` — two imports; six module constants; six new helpers (`_flatten`,
  `VerdictBinding`, `verdict_line`, `sidecar_digest`, `verdict_binding`,
  `verifier_owned_pending`); `packet_unfilled` split into `packet_unfilled_reasons` + a
  behavior-identical `packet_unfilled`; `archive_readiness` gains a keyword-only `bound=` parameter
  (§A.4/§F.3) plus a new final block and docstring; message derivation, the `bound=` hand-off, the
  `:416` short-circuit and the return value in `cmd_verify`; the hint in `cmd_archive`; six lines in
  `_classify_packet`. ~135 lines added, ~22 changed.
- `tests/test_sdd_archive_bound_verdict.py` — new, **45** test functions plus fixtures (37 from
  Round 1, plus #19a-#19d for the closed matcher and #38-#41 for the producer contract and the
  subprocess policy).
- `drydock-pins.json` — **one** value updated: `scripts/sdd.py` (line 6).
- Packet artifacts: `tasks.md`, `verification.md`, `decision-log.md`.

Explicitly **not changed** (no edit, no pin move, no behavior delta):
`scripts/check_verdict.py`, `scripts/record_verify_bound.py`, `scripts/start_probe.py`,
`scripts/check_secret_tree.py`, `scripts/ci_parse_lg_report.py`, `scripts/conductor/*`,
`kernel/*` (including `kernel/brief_complete_engine.py`, pinned `aa3ba09…`), `hooks/*` (including
`packet_guard.py`), `backstops/*`, `agents/verifier.md`, `.github/workflows/drydock.yml`,
`AGENTS.md`, `CLAUDE.md`, `README.md`, `PROJECT_CONTEXT.md`, `sdd-plus/templates/*`,
`sdd-plus/archive/*` (the six existing `verifier-report.md` files are **not** given sidecars —
fact 16), every existing file under `tests/`, and `conftest.py`.

Changed behavior on **unedited** callers, so "not edited" is not read as "not affected": none.
Every behavior delta in this packet lands inside `scripts/sdd.py`. `sdd.py verify` and
`sdd.py triage` change what they print for some packets, but they are edited functions in the
edited file, not inherited effects.

## must_not_do

1. **Do not edit `scripts/check_verdict.py`.** It stays the pinned bind at
   `drydock-pins.json:9` = `79075ea8…`. If the design ever seems to need a footer-stripping
   hasher, that is the signal that §B was abandoned, not that the pin should move.
2. **Do not touch `kernel/brief_complete_engine.py`** (pinned `aa3ba09…`), `kernel/brief_engine.py`,
   `kernel/brief.py`, `kernel/brief_complete.py` or `scripts/brief.py`. That the completeness
   engine's own gate still sees pending tasks is the hole-2 residual and is **out of scope**;
   archive is `scripts/sdd.py`.
3. **Do not touch `scripts/record_verify_bound.py`.** Hole 3 is `archive_readiness`, not
   `record_verify`. Do not retarget it, do not route archive through it.
4. **Do not touch leftover holes 1 or 4** — `.env` write handling, GitHub fast-forward `--force`.
5. **Do not rewrite or extend `hooks/packet_guard.py`**, and do not add any path to a deny class.
6. **Do not edit `.github/workflows/drydock.yml`** and do not edit anything under
   `scripts/conductor/`.
7. **Do not remove, rename, or weaken `--force`**, `--reason`, `--abandon`, or `record_override`.
   `--force` remains the Owner override for every row of the §A.5 matrix.
8. **Do not make a bound report mandatory for archive.** That is OQ-2 with a default of
   *sufficient, not necessary*; a packet that ticks its boxes honestly must still archive.
9. **Do not widen the waiver.** Only (a) pending tasks matched by `_VERIFIER_OWNED` on their own
   line or their enclosing `##` heading and (b) a `Pending.`/empty Result in `verification.md` may
   be waived. Placeholders, missing artifacts, non-verifier tasks and all three delta blockers
   still block.
10. **Do not decide the verdict with `check_verdict`'s string test.** Never call it with
    `required="VERIFIED"` against a report whose verdict line was not already whitelisted by
    `verdict_line` — `"VERIFIED"` is a substring of `"NOT VERIFIED"`
    (`tests/test_check_verdict.py:40`).
11. **Do not add a `sys.exit` to `cmd_verify`** for a pending Result or a pending task.
    `cmd_archive:544` calls it first and would die before `archive_readiness` ever runs (fact 8).
12. **Do not change what `packet_unfilled` returns.** The split is internal; its output list, order
    and de-duplication are pinned by `test_packet_unfilled_behavior_unchanged`.
13. **Never run `python3 scripts/sdd.py archive grok-archive-bound-verdict`** — or any live packet
    name — while implementing or verifying. `cmd_archive` **moves** the directory. Every
    `cmd_archive` call happens under `tmp_path` behind the `_isolated_tree` guard.
14. **Never mint a real verify-run or ledger event.** No `--record-verify` in any form, no
    `kernel/brief_complete_engine.py` invocation, no `scripts/record_verify_bound.py` invocation,
    in tests or in verification commands.
15. **Never plant fixture files in the live `sdd-plus/changes/`** — no `verifier-report.md`, no
    `verifier-report.sha256`, no edited `tasks.md` — to "see the gate fire". Negative paths are
    proven by `tmp_path` packets and direct helper calls.
16. **Do not retrofit the six archived `verifier-report.md` files with sidecars.** They are out of
    reach of every predicate (fact 16); adding artifacts to `sdd-plus/archive/` rewrites history
    for no gain.
17. **Re-pin last.** `drydock-pins.json:6` is written only after every `scripts/sdd.py` edit is
    final, and `start_probe.py` runs only after that. One value moves; no other pin, and none of
    `drydock_commit` / `verifier_md_git_blob` / `hash_alg`.
18. **Do not edit `agents/verifier.md`** on the implementer's own authority — it is OQ-3, and it
    costs a second pin plus the `verifier_md_git_blob` field.
19. **No commit, no push, no PR, no archive in the planning turn**; no
    `scripts/conductor/negotiate.py` run and no Codex call in the planning turn.
20. **Never `--dangerously-skip-permissions`, never `git config`, never force-push, never
    `git reset --hard`.**
21. **Do not mark anything verified without the verifier subagent.** Implementer evidence is
    evidence, not verification — and it is now especially tempting, because this packet's own
    archive gate is the thing being changed. Self-binding a report you wrote is the exact failure
    this packet must not normalize.
22. **Do not resolve OQ-1..OQ-4 by implementing something other than the stated default.** No
    third sha256 scheme, no third matcher design.
23. **Do not widen `_VERIFIER_OWNED` beyond the §E.1 closed set.** In particular: never anchor on
    `verif`, never treat a bare `## Verification` heading as verifier-owned, and never match prose.
    Doing any of those waives the five implementer commands at
    `sdd-plus/archive/2026-09-01-grok-coplan-linux-discover/tasks.md:28-33` (fact 23). If Step 9a's
    re-run of the inventory finds a wording §E.1 does not list, **stop and tell the Owner** — that
    is a contract change, not a regex tweak.
24. **Do not add a module-level or on-disk cache for `verdict_binding`.** The repeated-work answer
    is the keyword-only `bound=` parameter (§F.3). No `dict` at module scope, no `functools.cache`,
    no mtime key, no second `hashlib` call in `sdd.py`, no cache file. And do not "optimize"
    `sdd.py archive` from two spawns to one by changing `cmd_verify`'s return type — `main()` uses
    it as the process exit status (fact 8).
25. **Do not build a producer.** No `.github/workflows/` job, no `scripts/conductor/` stage, no new
    script, and no edit to `agents/verifier.md` to make the verifier emit the sidecar. The producer
    is choreography (§D.2) and it already exists (fact 21); this packet documents it and enforces
    the resulting on-disk contract. **Do not retry a failed bind, and do not "helpfully" write a
    missing sidecar from `sdd.py`** — a gate that can manufacture its own evidence is not a gate.
26. **Do not add a retry loop, worker pool, thread, async path or daemon around
    `check_verdict.py`.** At most one spawn per `verdict_binding` call (§F.3). A non-zero exit is a
    verdict about the packet, not a transient.

## Risks

- **This is choreography, not cryptography — say it plainly.** Anything that can write
  `verifier-report.md` can also write `verifier-report.sha256`. A self-certifying agent is not
  cryptographically stopped by this gate, and no filename-based scheme can stop it. What changes:
  self-certification stops being a silent checkbox tick and becomes two named artifacts that carry
  the verifier's exact bytes, travel into the archive, and can be diffed against the in-channel
  message the Owner already has. The residual belongs in
  `sdd-plus/security/accepted-risks.md` if the Owner wants it recorded there; this packet does not
  write that file on its own authority.
- **Over-waive through a mislabeled section (OQ-4).** A packet that files implementation tasks
  under a heading that literally names the **verifier subagent** has them waived. Bounded by three
  things now: a bound, independent verdict must exist for any waiver to apply at all; the heading is
  visible in the diff; and the §E.1 audit shows the shape has **never** been used that way in this
  repo — the one heading that could plausibly have been abused (`## Verification`,
  `archive/2026-09-01-grok-coplan-linux-discover/tasks.md:26`) does not name the verifier and is
  correctly **not** waived (fact 23, test #19a). Accepted; a narrower line-only matcher would leave
  the smoke-packet shape (fact 13, 4 of the repo's 6 verifier-owned tasks) permanently blocked.
- **Strictness papercuts.** `VERIFIED WITH NOTES.` with a trailing period, a lowercase verdict, or
  a `## Verdict` section carrying an explanatory sentence all fail to bind. That is deliberate —
  the whole-line rule is what keeps `NOT VERIFIED` out — and the cost is that the Owner either
  fixes the report or uses `--force`. Tested (#15) so it is a known behavior, not a surprise.
- **Triage mislabels a failed bind as `NEEDS-SYNC`.** `_classify_packet:333-334` maps *any*
  non-empty `archive_readiness` result to "delta specs not yet in the living specs". A packet whose
  only blocker is `unbound-verdict` and whose implementation tasks are done will read as
  `NEEDS-SYNC`. This is **pre-existing** behavior for every non-sync blocker at that line, it is
  not made worse here, and fixing it is a triage-message change deliberately left out of a LITE
  packet (§C.4). `sdd.py verify` prints the accurate reason.
- **A subprocess in the readiness path.** `verdict_binding` spawns `check_verdict.py`. **Policy,
  budget and every fail-closed mode are now §F**, which is the Round-2 answer to Codex BC3. Summary:
  at most one spawn per call and zero for a packet that claims nothing; `status` 0, `verify` 1,
  `triage` 1 per *claimed* packet, `archive` 2; measured 26.5 ms per spawn against `timeout=30`
  (~1 130× headroom); the current tree has 1 active packet, 0 claimed, so 0 spawns. Hundreds of
  packets would justify a real cache — future work, out of scope, and localized to
  `verdict_binding` because `bound=` already funnels every caller through one place.
- **The producer step can simply be forgotten.** The gate depends on a human/choreographer writing
  `verifier-report.sha256` after `check_verdict` exits 0 (§D.2), and nothing in this repo can compel
  it. The failure mode is benign by construction — a forgotten sidecar means the packet archives the
  way it does today, by ticked boxes or `--force`, because a bound report is sufficient and never
  necessary (OQ-2). It is a *missed benefit*, not a *false pass*. Bounded further by the fact that
  the hex is already in the choreographer's hand at that exact moment (fact 21: three archived
  packets recorded it in prose), so the new step adds no new information-gathering, only a file
  write.
- **The closed matcher can be reopened by a future packet.** §E.1 is closed over the repo *as of
  HEAD `1da7781`*. A packet that invents a fourth wording — "independent reviewer", "Verification
  (external)", a `###` verifier sub-heading — gets its verifier tasks **blocked**, not waived, which
  is the safe direction; the operator falls back to `--force`. Test #19d turns that into a red test
  the moment the wording lands, rather than a silent misclassification. The unsafe direction
  (waiving implementation work) is guarded by must_not_do 23 and tests #19a/#19c.
- **First `subprocess` import in `scripts/sdd.py`** (fact 19). Stdlib, no new dependency, but it
  widens what a pinned governance script can do and is visible in the diff for exactly that reason.
  Mitigated: the only command constructed is `[sys.executable, CHECK_VERDICT, report, expected,
  verdict]` with `CHECK_VERDICT` anchored on `Path(__file__)` — no shell, no `cwd`, no user string
  reaching a shell, and all four arguments are `str()`-wrapped paths or values already validated
  by regex/whitelist.
- **stdout changes for packets nobody was thinking about.** Removing the `:416` short-circuit means
  ordinary incomplete packets now print `Not archive-ready: …`. Strictly more informative, matches
  the `:259-263` comment, pinned by test #30 — but anything scraping `sdd.py verify` output would
  see a new line. Nothing in this repo scrapes it (`.github/workflows/drydock.yml` runs the probe,
  not `sdd.py verify`).
- **A future implementer adds the footer anyway.** The two schemes are silently incompatible: a
  footer whose hex is the body-only digest fails whole-file hashing. Test #13 exists specifically
  to make that a red test rather than a mysterious `sha256 mismatch` in production.
- **`cmd_archive` moves directories.** The single most dangerous thing in this packet is a test
  that archives a live packet. Mitigated by must_not_do 13 and the `_isolated_tree` fixture's
  `assert sdd.find_root() == tmp_path.resolve()`, which fails the test rather than moving anything
  if `TMPDIR` were ever inside the repo.
- **Pin/probe ordering.** Editing `scripts/sdd.py` without re-pinning makes the probe fail its own
  `check_pins()` with `hash drift scripts/sdd.py`; re-pinning before the file is final pins bytes
  that then change. §Pin update ordering fixes the order.
- **Scope creep.** Leftover holes 1/2-residual/4, `packet_guard`, workflow, conductor, kernel and
  `agents/verifier.md` are all fenced in `must_not_do`.

## Rollback

Single-commit revert. `git revert <sha>` restores `scripts/sdd.py` **and** the
`202e2fb127caa716788f8866dfdd80f02b49eca937037aee0ecf2c57174c48f1` value on
`drydock-pins.json:6` together, and drops `tests/test_sdd_archive_bound_verdict.py` — so there is
no intermediate state where `check_pins()` fails on its own hash. Nothing outside the repo changes:
no migration, no data, no config, no `.git/hooks` change, no external state, and no ledger event is
written by this packet.

The one durable side effect a revert does **not** undo is any packet already archived without
`--force` under the new rule. Those directories stay in `sdd-plus/archive/` with their
`verifier-report.md` and `verifier-report.sha256` intact — which is the correct outcome, since the
verdict that admitted them is still on disk and still checkable by hand:
`sha256sum sdd-plus/archive/<packet>/verifier-report.md` against the sidecar.

Manual fallback if the revert is awkward mid-stack, in this order: (1) restore the final block and
docstring of `archive_readiness` to the `:291-299` form; (2) restore `packet_unfilled` to its
`:244-256` body and delete `packet_unfilled_reasons`; (3) restore `cmd_verify:399-400`, `:416` and
`:432`; (4) restore `cmd_archive`'s two-branch hint at `:555-557`; (5) restore
`_classify_packet:325-330`; (6) delete the six helpers, the six constants and the two imports;
(7) delete `tests/test_sdd_archive_bound_verdict.py`; (8) restore `drydock-pins.json:6` to
`202e2fb127caa716788f8866dfdd80f02b49eca937037aee0ecf2c57174c48f1`; (9) `python3
scripts/start_probe.py` to confirm `"ok": true`.

## Verification commands

Run by the implementer; read-only except where noted. Paste output verbatim into
`verification.md`.

```bash
# 1. full suite, cache-free
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
#    expect: green, including every pre-existing test and the 37 new ones

# 2. pins + guardrails, AFTER the re-pin (never before)
python3 scripts/start_probe.py; echo "exit=$?"
#    expect: "ok": true, "pin_errors": [], exit 0

# 3. the new gate, positive — tmp_path only, via the imported helper.
#    Builds a bound packet in a scratch dir, never in sdd-plus/changes/.
python3 - <<'PY'
import hashlib, pathlib, sys, tempfile
sys.path.insert(0, "scripts"); import sdd
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d) / "pkt"; p.mkdir()
    for f, t in {"brief.md": "# Brief\n", "plan.md": "# Plan\n",
                 "tasks.md": "# Tasks\n\n- [ ] Invoke the verifier subagent.\n",
                 "decision-log.md": "# Decision Log\n",
                 "verification.md": "# Verification\n\n## Result\n\nPending.\n"}.items():
        (p / f).write_text(t, encoding="utf-8")
    r = p / "verifier-report.md"
    r.write_text("# Verification Report\n\n## Verdict\nVERIFIED WITH NOTES\n", encoding="utf-8")
    (p / "verifier-report.sha256").write_text(
        hashlib.sha256(r.read_bytes()).hexdigest() + "\n", encoding="utf-8")
    print("binding:", sdd.verdict_binding(p))
    print("readiness:", sdd.archive_readiness(p, pathlib.Path(d) / "caps"))
PY
#    expect: binding ok=True verdict='VERIFIED WITH NOTES'; readiness []

# 4. the new gate, negative (fail-case 3) — same scratch dir, sidecar corrupted
#    and verdict flipped. Expect unbound-verdict + incomplete, never [].
#    (Same script as 3 with sidecar="0"*64, then with verdict "NOT VERIFIED".)

# 5. end to end under a scratch sdd-plus tree — the ONLY place cmd_archive runs.
#    Build tmp/sdd-plus/{standards,specs/capabilities,changes,archive}, cd into it,
#    then: python3 <repo>/scripts/sdd.py verify demo   -> READY TO ARCHIVE, exit 0
#          python3 <repo>/scripts/sdd.py archive demo  -> archived, NO override
#    Confirm `grep -c '## Override' <archived>/decision-log.md` is 0.
#    NEVER run either command against a name under the real sdd-plus/changes/.

# 5a. PRODUCER CONTRACT (Codex BC1) — the §D.2 sequence, by hand, in a scratch dir.
#     Proves the documented choreography is the thing the gate accepts.
python3 - <<'PY'
import hashlib, pathlib, subprocess, sys, tempfile
sys.path.insert(0, "scripts"); import sdd
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d) / "pkt"; p.mkdir()
    r = p / "verifier-report.md"
    # step 2: choreographer copies the in-channel report verbatim
    r.write_text("# Verification Report\n\n## Verdict\nVERIFIED WITH NOTES\n", encoding="utf-8")
    hexd = hashlib.sha256(r.read_bytes()).hexdigest()          # the in-channel digest
    # step 3: the existing pinned bind, run as the CLI, exactly as in channel
    c = subprocess.run([sys.executable, "scripts/check_verdict.py", str(r), hexd,
                        "VERIFIED WITH NOTES"], capture_output=True, text=True)
    print("check_verdict exit:", c.returncode)                  # expect 0
    # step 4: THE ONE NEW STEP — same hex, one line, beside the report
    (p / "verifier-report.sha256").write_text(hexd + "\n", encoding="utf-8")
    print("binding:", sdd.verdict_binding(p))                   # expect ok=True
PY
#    expect: check_verdict exit 0; binding ok=True verdict='VERIFIED WITH NOTES'

# 5b. SPAWN BUDGET (Codex BC3, §F.3) — count real spawns per command shape.
#     Wrap subprocess.run, then call each entry point once on a scratch packet.
#     expect: unclaimed packet 0 spawns; bound packet -> archive_readiness 1,
#            archive_readiness(..., bound=already) 0; cmd_verify 1; cmd_archive 2.
#     Also assert archive_readiness(d,c) == archive_readiness(d,c,bound=verdict_binding(d)).

# 5c. INVENTORY IS STILL CLOSED (Codex BC2, §E.1) — read-only over the real tree.
grep -n '^## ' sdd-plus/archive/*/tasks.md sdd-plus/changes/*/tasks.md sdd-plus/templates/tasks.md
grep -ni 'verif'  sdd-plus/archive/*/tasks.md sdd-plus/changes/*/tasks.md sdd-plus/templates/tasks.md
#    expect: every heading and every hit already listed in plan §E.1. A wording that
#    is not in that table means STOP and tell the Owner (Step 9a).

# 6. the live packet is untouched and still blocked (read-only, no archive)
python3 scripts/sdd.py verify grok-archive-bound-verdict; echo "exit=$?"
#    expect: pending tasks reported, "Not archive-ready: …", NO "READY TO ARCHIVE"
#    (this packet carries no verifier-report.md at plan time, so it is unbound)

# 7. nothing moved, nothing planted
git status --porcelain
git status --porcelain sdd-plus/changes/ sdd-plus/archive/
ls sdd-plus/changes/
#    expect: only scripts/sdd.py, drydock-pins.json, tests/test_sdd_archive_bound_verdict.py
#    and this packet's artifacts; grok-archive-bound-verdict still present in changes/
```

Commands 5c, 6 and 7 are read-only (`cmd_verify` never writes or moves; 5c only greps). Commands
3-5b write only under `tempfile`/`tmp_path`. No command in this list runs `--record-verify`, touches
`kernel/brief_complete_engine.py`, plants a fixture in `sdd-plus/changes/`, or archives a live
packet.
