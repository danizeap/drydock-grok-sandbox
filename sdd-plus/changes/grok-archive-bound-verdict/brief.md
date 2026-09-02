# Brief

## Change

grok-archive-bound-verdict

## Mode

LITE. **Round 2 of 2 (final before implement).** Codex negotiate round 1 ran and returned three
blocking concerns (producer path, under-specified verifier-owned matcher, no subprocess policy);
this revision answers all three — `plan.md` §D, §E, §F. **This turn is still planning: nothing is
implemented or committed, no Codex call and no `negotiate.py` run happens here, and every
`tasks.md` box stays unchecked.** Next turn is implement. Leftover hole 3 only.

Known files, all named up front: `scripts/sdd.py` (one new helper group plus edits to four
existing call sites), a new `tests/test_sdd_archive_bound_verdict.py`, and **one** value in
`drydock-pins.json` (line 6). No auth, no schema, no migration, no workflow edit, no conductor
edit, no hook edit, no kernel edit. `scripts/check_verdict.py` is deliberately **not** edited, so
its pin (`drydock-pins.json:9`) does not move.

**On the contract, stated precisely.** This is a real behavior change to `sdd.py archive` and
`sdd.py verify`, and it is stated in two halves so they are not conflated:

1. **Additive readiness.** A packet that carries a *bound* `verifier-report.md` — a verifier
   report whose bytes hash to a declared sha256 and whose `## Verdict` is exactly `VERIFIED` or
   `VERIFIED WITH NOTES` — may archive **without `--force`**, even though its verifier-owned
   tasks are unticked and `verification.md` Result is still `Pending.`. Today that packet gets an
   `incomplete` blocker (`scripts/sdd.py:291-299`) and `cmd_archive` exits with
   `error: not archive-ready` unless `--force` is passed (`scripts/sdd.py:551-558`).
2. **Unchanged refusal without a bind.** A packet with no report, a missing or malformed sha256
   sidecar, a mismatched hash, a `NOT VERIFIED` / `BLOCKED` / absent verdict, or *implementation*
   tasks still pending is **still** not archive-ready. `--force` remains the Owner override for
   exactly those cases and is not removed, not renamed, and not weakened.

3. **The producer is choreography that already runs, and the contract is on-disk.** *(Round 2,
   Codex BC1.)* The bound-verdict artifacts are not a new invention waiting on a new pipeline. The
   verifier already posts report + sha256 in channel; Grok already copies the report **verbatim**
   into the packet as `verifier-report.md`; `scripts/check_verdict.py` is already run and **exit 0
   is already the bind**. Proof on disk: three archived packets record that digest in their
   `## Override` reason, and each equals today's whole-file `sha256sum` of the report sitting beside
   it — `sdd-plus/archive/2026-09-01-grok-choreography-smoke/decision-log.md:18` (`88328932…`),
   `…-coplan-closure-gate/decision-log.md:40` (`d25b70b8…`),
   `…-refuse-brief-engine/decision-log.md:42` (`ce4fdba2…`). The **only** new step is that after
   `check_verdict` exits 0, Grok writes that same hex to `verifier-report.sha256` beside the report.
   That is a file write by a party outside this repo, so it is **not** implemented here as a
   `scripts/`, workflow or conductor change — none of those transports the report today either.
   What this packet enforces is the resulting **on-disk contract**: both files present, sidecar hex
   equal to the whole-file sha256 of the report bytes, verdict whitelisted. Tested on `tmp_path`
   packets (`plan.md` §D.3), never by planting fixtures in the live tree.

A bound report becomes a **sufficient** path to READY. It does not become a **necessary** one: a
packet that genuinely ticks every box and fills its Result archives exactly as it does today
(OQ-2). A packet whose sidecar is never written archives exactly as it does today too — a forgotten
producer step is a missed benefit, never a false pass.

Still LITE, not FULL: one production file, one new test file, one pin value, no new dependency
(`subprocess` is stdlib and is the only import added), and no new external surface. The change is
a *gate re-derivation* inside a helper script, not an architecture or auth change.

## User Need

The Owner wants "archive-ready" to mean **independently verified**, and wants that to be the
ordinary path rather than an override.

Today it is neither. The verifier subagent is a read-only reviewer: it writes nothing to the tree.
So after a genuine, independent verification the packet on disk still looks unfinished — Step 12
is unticked, `verification.md` Result still says `Pending.`, the brief's acceptance checkboxes are
still open — and `sdd.py archive` refuses. The Owner's only lever is `--force --reason "…"`, which
records an **override** in `decision-log.md` (`scripts/sdd.py:559-561`). So the repo's permanent
record of a properly verified packet is a waiver, and the ledger cannot distinguish "verified, but
the checkboxes lag" from "we skipped verification and forced it through". Both look identical:
`OVERRIDE recorded in decision-log.md`.

Both archived packets on disk show the shape exactly. `sdd-plus/archive/2026-09-02-grok-refuse-brief-engine/tasks.md:57`
is `- [ ] Step 12 — Invoke the verifier subagent.` left unchecked, and its
`verifier-report.md:56` records `VERIFIED WITH NOTES` — an independent verdict that the archive
gate could not see.

## Problem

`archive_readiness()` (`scripts/sdd.py:259-300`) is the single waivable-blocker list that both
`cmd_archive` and the ready-prompt read. Its last blocker is:

```python
    unfilled = packet_unfilled(change_dir)
    _, pending = task_counts(change_dir / "tasks.md")
    if unfilled or pending > 0:
        ...
        blockers.append(("incomplete", "; ".join(detail)))
```

Two inputs make that fire on a fully verified packet:

- `task_counts` (`scripts/sdd.py:84-90`) counts **every** `- [ ]` line in `tasks.md`. It cannot
  tell "Step 12 — invoke the verifier subagent", which only the verifier can honestly tick, from
  "Implement the smallest coherent change", which the implementer must.
- `packet_unfilled` (`scripts/sdd.py:244-256`) folds two different faults into one filename: a
  real template placeholder (`text_has_placeholder`, `:182-201`) and a Result that is empty or
  `Pending.` (`verification_result_is_pending`, `:204-217`). Only the second is verifier-owned.

Meanwhile the repo already has a working, byte-exact bind that nothing in `sdd.py` consults. The
choreography is: the verifier posts its Verification Report **and** the sha256 of those exact
report bytes in the same in-channel message; Grok transports the report verbatim into the packet
as `verifier-report.md`; `python3 scripts/check_verdict.py <file> <sha256> <verdict-string>`
(`scripts/check_verdict.py:17-44`) exits 0 only if the bytes hash correctly and the verdict string
is present. **Exit 0 is the bind.** Six archived packets already carry a `verifier-report.md`, all
tracked, all ending in a `## Verdict` section reading `VERIFIED WITH NOTES` — but the declared
hash lives only in the chat transcript, so archive has nothing on disk to check.

Three consequences, all of them live today:

1. Every honestly verified packet archives as an override.
2. The `--force` record is therefore uninformative, which erodes the one audit signal it exists
   to provide.
3. `cmd_verify` never even reaches `archive_readiness` for such a packet: its ready-prompt is
   gated on `not unfilled and pending == 0` (`scripts/sdd.py:416`), so a bound packet could never
   print `READY TO ARCHIVE`. That short-circuit contradicts the comment at
   `scripts/sdd.py:259-263`, which states that the prompt and archive consult one function so they
   "can NEVER" disagree.

## Scope

In scope:

- Teach `scripts/sdd.py` to read a **bound verdict** from the packet directory: `verifier-report.md`
  plus a one-line `verifier-report.sha256` sidecar carrying the in-channel digest, bound by
  running the existing pinned `scripts/check_verdict.py` and requiring exit 0.
- Restrict the accepted verdicts to exactly `VERIFIED` and `VERIFIED WITH NOTES`, decided by a
  whole-line rule over the report's `## Verdict` section — never by `check_verdict`'s substring
  test, because `VERIFIED` is a substring of `NOT VERIFIED`
  (`tests/test_check_verdict.py:36-43` already documents that trap).
- In `archive_readiness`, when and only when a verdict is bound, waive (a) pending
  **verifier-owned** tasks and (b) a `Pending.` Result in `verification.md`. Nothing else.
- Define "verifier-owned" as a **closed matcher over a complete corpus audit**, not a heuristic
  (Round 2, Codex BC2). Every `tasks.md` in the repo — six archived, the live packet, the template —
  is inventoried line by line in `plan.md` §E.1, including the four files that contain **zero**
  verifier-owned tasks. The audit found a third heading shape Round 1 had missed: a bare
  `## Verification` over five implementer-run commands
  (`sdd-plus/archive/2026-09-01-grok-coplan-linux-discover/tasks.md:26-33`), which must **not** be
  waived. Every inventoried wording gets a test, including the negatives.
- Give `archive_readiness` a keyword-only `bound=` parameter so a caller that already computed the
  binding does not spawn `check_verdict.py` a second time, and state the subprocess policy —
  when it spawns, how often, timeout, and every fail-closed mode (Round 2, Codex BC3;
  `plan.md` §F). No cache, no retry, no pool.
- Document the producer choreography (the one new step: write the sidecar after `check_verdict`
  exits 0) in this packet and in `sdd.py`'s own `unbound-verdict` error text.
- Add an `unbound-verdict` blocker for a packet that *claims* a verifier report but fails to bind
  it, so a broken bind is a named fault rather than a generic "incomplete".
- Fix the three callers that short-circuit before `archive_readiness` and would otherwise
  contradict it: `cmd_verify:399-400`, `cmd_verify:416`, `_classify_packet:325-327`.
- New `tests/test_sdd_archive_bound_verdict.py`, entirely under `tmp_path`.
- Re-pin `scripts/sdd.py` — one value, `drydock-pins.json:6`.

Out of scope:

- **Leftover hole 1** — `.env` write handling.
- **Leftover hole 2 residual** — `kernel/brief_complete_engine.py` (pinned
  `aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b`) is **not touched, not read,
  not rewritten**. That the completeness engine's own packet gate still sees pending tasks is the
  hole-2 residual and is a different file with a different owner. Archive is `scripts/sdd.py`.
- **Leftover hole 4** — GitHub fast-forward `--force`.
- **`scripts/check_verdict.py`** — not edited. It stays the pinned bind; the design is built
  around its existing whole-file hashing rather than changing it (plan §Approach B).
- **`scripts/record_verify_bound.py`** — not the archive path. Hole 3 is `archive_readiness`, not
  `record_verify`. Not retargeted, not edited.
- **`hooks/packet_guard.py`** — no rewrite, no new deny class. `scripts/sdd.py` and `tests/` are
  not in its deny classes (`hooks/packet_guard.py:105-128`: schema migrations, *new* CI config,
  container config), so nothing here needs it and nothing here extends it.
- **`.github/workflows/drydock.yml`**, **`scripts/conductor/*`**, **`scripts/start_probe.py`**,
  **`hooks/*`**, **`kernel/*`**, **`backstops/*`** — untouched.
- **`agents/verifier.md`** — not edited (OQ-3). It is pinned at `drydock-pins.json:20` *and*
  recorded as a git blob at `drydock-pins.json:3`, so touching it costs two records for a prose
  change. The choreography instruction lands in this packet and in `sdd.py`'s own actionable
  error text instead.
- **Building a producer inside this repo.** No workflow job, no conductor stage, no new script, and
  no `agents/verifier.md` edit to make the verifier emit a sidecar. The producer is choreography
  outside this tree and it already runs (contract claim 3); this packet documents it and enforces
  the on-disk result. Proven not required: every `verifier-report.md` in the repo entered git in an
  archive commit, never as the output of a repo script.
- **Caching the bind.** No module-level cache, no cache file, no `functools.cache`, no mtime key,
  no second `hashlib` call in `sdd.py`. Repeated work is removed by the `bound=` parameter alone
  (`plan.md` §F.3). Caching would be worth it at hundreds of packets; the tree has **one**.
- Making a bound report **mandatory** for archive (OQ-2). This packet adds a path; it does not
  remove the existing one.
- **Backfilling sidecars for in-flight or archived packets.** Nothing is migrated. A packet that
  already carries a report but no sidecar behaves exactly as it does today; its remedy is one
  `sha256sum` line or the `--force` it was already using.
- Retrofitting the six archived `verifier-report.md` files with sidecars. They live under
  `sdd-plus/archive/`, which `cmd_triage`, `cmd_status` and `cmd_verify` never read — they only
  look at `sdd-plus/changes/` (`scripts/sdd.py:305-306`, `:357`, `:381`). No migration, and none
  of them is re-examined by this change.

## Acceptance Criteria

- [ ] A packet whose only pending tasks are verifier-owned and whose `verification.md` Result is
      `Pending.`, carrying `verifier-report.md` + a matching `verifier-report.sha256` with
      `## Verdict` = `VERIFIED WITH NOTES`, returns `archive_readiness(...) == []`.
- [ ] The same packet archives with `python3 scripts/sdd.py archive <name>` — **no `--force`** —
      and **no** `## Override` section is appended to its `decision-log.md`.
- [ ] The same packet prints `READY TO ARCHIVE` from `sdd.py verify <name>` and exits 0, and is
      bucketed `ARCHIVE-READY` by `sdd.py triage`.
- [ ] The same acceptance holds with the verdict `VERIFIED` (no notes).
- [ ] **Fail-case 3 stays denied.** Each of these still yields blockers and still exits
      `error: not archive-ready` without `--force`: no `verifier-report.md` at all; report present
      but no sidecar; sidecar hash mismatched; sidecar malformed; `## Verdict` reading
      `NOT VERIFIED`; `## Verdict` reading `BLOCKED`; no `## Verdict` section; a `## Verdict`
      section carrying more than one line.
- [ ] **A bound report does not waive implementation work.** A packet with a valid bound verdict
      *and* a pending non-verifier task (e.g. `- [ ] Implement the smallest coherent change.`)
      still reports an `incomplete` blocker naming 1 pending task, and still refuses to archive
      without `--force`.
- [ ] **A bound report does not waive placeholders.** A bound packet with a `TBD` line in
      `plan.md` still reports `incomplete` naming `plan.md`.
- [ ] **A bound report does not waive sync.** A bound packet with a delta spec whose capability has
      no living spec still reports `unsynced-capability`.
- [ ] `NOT VERIFIED` is rejected by the packet's own whole-line verdict rule, and
      `scripts/check_verdict.py` is never invoked with `required="VERIFIED"` against a report
      whose verdict line is `NOT VERIFIED`.
- [ ] A packet that ticks every box and fills its Result, with **no** verifier report at all,
      archives exactly as it does today — no new requirement is imposed.
- [ ] `--force --reason "…"` still works, still records the override, and `--abandon` is unchanged.
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` is green, including
      every pre-existing test.
- [ ] `python3 scripts/start_probe.py` reports `"ok": true` with `"pin_errors": []` after
      `drydock-pins.json:6` is updated.
- [ ] No test creates, moves, archives or mutates any packet under the live `sdd-plus/changes/`,
      and no verify-run ledger event is minted.
- [ ] **Producer contract (Codex BC1).** Walking the documented choreography by hand in a scratch
      dir — write report → run `python3 scripts/check_verdict.py <report> <hex> "VERIFIED WITH
      NOTES"` → exit 0 → write that same hex to `verifier-report.sha256` — yields
      `verdict_binding(...).ok is True` and an archive with no `--force` and no `## Override`.
      Missing sidecar or mismatched hex yields unbound. No workflow, conductor or new script is
      added to make this true.
- [ ] **Closed matcher (Codex BC2).** Every wording in the `plan.md` §E.1 inventory classifies as
      the table states, asserted against the real files read-only: `(4,0)` smoke, `(0,0)` for
      discover-probe / linux-discover / docs-coplan-runtime, `(1,0)` closure-gate, `(1,0)`
      refuse-brief-engine, `(0,5)` the live packet, `(0,5)` the template. In particular a bare
      `## Verification` heading waives **nothing**, and prose naming the verifier subagent waives
      **nothing**.
- [ ] **Subprocess policy (Codex BC3).** A packet that claims no verdict spawns **zero**
      subprocesses on every path; `archive_readiness` spawns at most one and never in a loop;
      `archive_readiness(d, c) == archive_readiness(d, c, bound=verdict_binding(d))`; and every
      failure — missing `check_verdict.py`, non-zero exit, timeout, `OSError`,
      `SubprocessError`, decode error — yields `ok=False` with a non-empty `reason` and an
      `unbound-verdict` blocker. None is ever treated as "no claim".

## Impact Areas

- Backend: `scripts/sdd.py` only. New helpers (`verdict_line`, `sidecar_digest`,
  `verdict_binding`, `verifier_owned_pending`, `packet_unfilled_reasons`) plus edits inside
  `archive_readiness`, `cmd_verify`, `cmd_archive`'s hint text, and `_classify_packet`.
  `archive_readiness` gains one **keyword-only, optional** parameter, `bound=`, whose default
  reproduces today's behavior exactly; it exists only so `cmd_verify` and `_classify_packet` do not
  spawn `check_verdict.py` twice for the same packet in one process. `cmd_status` is not edited and
  never spawns (`scripts/sdd.py:303-314`).
- Frontend: none.
- Data model: none. No ledger event is written, read, or reshaped by this packet. The packet
  directory gains one optional file (`verifier-report.sha256`) alongside the `verifier-report.md`
  that six archived packets already carry; both travel into the archive by the existing
  `shutil.move` (`scripts/sdd.py:567`) with no code change.
- API: the CLI contract of `sdd.py` changes in one direction only — some packets that previously
  required `--force` no longer do. No flag is added, removed or renamed; `cmd_archive`'s argparse
  block (`scripts/sdd.py:581-589`) is untouched. Stdout gains two informational lines in
  `cmd_verify` and one new blocker category string.
- AI/model behavior: this is the point. An agent can no longer convert "done" into "archived" by
  ticking its own boxes any more easily than before; and an *honest* verification now has a
  machine-checkable on-disk form, so the Owner's `--force` stops being noise.
- Documentation: no `README.md`, `AGENTS.md`, `PROJECT_CONTEXT.md` or `agents/verifier.md` edit
  (OQ-3). The transport convention — the five-step producer sequence, with the one new step called
  out — is documented in this packet at `plan.md` §D.2, and in the `unbound-verdict` blocker's own
  message, which names the file to create and the grammar it must have at the moment the operator
  needs it.
- Operations/security: this is the security change, and its limit must be said out loud. The
  binding is **choreography, not cryptography**: any agent that can write `verifier-report.md` can
  also write `verifier-report.sha256`. What it buys is that self-certification stops being a
  silent checkbox tick and becomes two named artifacts that travel into the archive, carry the
  verifier's exact bytes, and can be diffed against the in-channel message. It also fails **closed**
  on drift — see plan §Risks.
- Operations/performance: `archive_readiness` stops being a pure in-process check and may spawn
  `scripts/check_verdict.py` — the same subprocess `scripts/record_verify_bound.py:33-38` already
  runs, here with a **stricter** `timeout=30` where that precedent has none. Budget, stated and
  tested: **zero** spawns for a packet that claims no verdict (every packet in `sdd-plus/changes/`
  today); one for `sdd.py verify`; one per *claimed* packet for `sdd.py triage`; two for
  `sdd.py archive`; zero for `sdd.py status`. Measured 26.5 ms per spawn against a 30 s timeout.
  Every failure — timeout, missing binary, non-zero exit, `OSError` — blocks and is named; none is
  silently treated as "no claim". Full policy in `plan.md` §F.

## Open Questions

Four policy calls. Each has a stated default that is buildable today, so **none of them blocks
implementation**. Silence means build the default.

- **OQ-1 — sidecar filename and grammar.** *Default (build this):* `verifier-report.sha256`,
  sitting beside `verifier-report.md` in the packet directory; exactly one non-empty, non-`#`
  line; first whitespace token must be 64 hex characters; a second token is allowed only if it
  names `verifier-report.md` (with or without `sha256sum`'s `*` binary marker). That grammar
  accepts both a pasted in-channel hex and literal `sha256sum verifier-report.md` output.
  *Alternative:* a footer line inside the report itself. Rejected with reasons in plan §Approach B
  — it would change the bytes `check_verdict` hashes, retroactively make all six archived reports
  non-conforming, and self-heal on a careless rewrite instead of failing closed.

- **OQ-2 — is a bound report sufficient, or also required?** *Default (build this):*
  **sufficient only.** A packet that ticks every box and fills its Result still archives with no
  report, exactly as today. *Alternative:* make a bound report mandatory for every archive. That
  is a strictly larger contract change, would block any packet verified by other means, and is a
  separate Owner decision; if wanted it is a two-line follow-up (add an `unverified` blocker when
  `verdict_binding` is not `ok`), not a redesign.

- **OQ-3 — should `agents/verifier.md` be updated to make the verifier emit the sidecar line?**
  *Default (build this):* **no.** It is pinned at `drydock-pins.json:20` and blob-recorded at
  `drydock-pins.json:3`, so a prose edit costs two records and a second pin move in a LITE packet.
  The in-channel footer convention already exists; what changes is only where Grok writes the hex
  on transport, which is packet choreography. The `unbound-verdict` message states the exact
  required grammar at the moment it is needed. *Delta if the Owner says yes:* one paragraph in
  `agents/verifier.md`, one pin value, one blob field — and a re-run of `start_probe`.

- **OQ-4 — how wide is "verifier-owned"?** **Round 2: this is no longer two observed examples. It
  is a closed matcher over a complete corpus audit** (Codex BC2), and it is a contract, not a regex
  detail. *Default (build this):* a pending task is verifier-owned iff the normalized phrase
  `verifier subagent` (also `sub-agent`) appears **either on the task's own checkbox line, or on the
  enclosing level-2 heading**.

  Every `tasks.md` in the repo was read line by line — six archived, the live packet, and the
  template, including the four files containing **zero** verifier-owned tasks. Full table in
  `plan.md` §E.1. The corpus contains exactly:

  - *Line form* (2 instances): `sdd-plus/archive/2026-09-02-grok-refuse-brief-engine/tasks.md:57`
    (`- [ ] Step 12 — Invoke the verifier subagent. Do not self-certify. …`) and
    `sdd-plus/archive/2026-09-02-grok-coplan-closure-gate/tasks.md:47`
    (`- [ ] Invoke the verifier subagent; do not self-certify.`).
  - *Section form* (1 instance): `sdd-plus/archive/2026-09-01-grok-choreography-smoke/tasks.md:18`,
    `## Verification (verifier subagent — not the Implementer)`, over four tasks at `:20-23` none of
    which names the verifier on its own line.
  - *Must NOT match* — **the shape the audit found and Round 1 had missed**: a bare
    `## Verification` heading at `sdd-plus/archive/2026-09-01-grok-coplan-linux-discover/tasks.md:26`
    whose five tasks (`:28-33`) are implementer-run commands (`pytest`, `start_probe.py`,
    `discover_core()`, `negotiate.py --round 1`, `launchguardian scan`). This is exactly the
    "accidentally waive implementation tasks" failure Codex named. The matcher is anchored on the
    token **`verifier`**, never on `verif`, which is what keeps those five blocked.
  - *Must NOT match* — free prose naming the verifier subagent inside a notes block
    (`…docs-coplan-runtime/tasks.md:45-46`, `…coplan-closure-gate/tasks.md:56`,
    `…refuse-brief-engine/tasks.md:18-19`). Only `^##(?!#)\s` lines and `- [ ] ` lines are ever
    inspected, so prose is structurally invisible and cannot set section state.
  - *Must NOT match* — `- [ ] Run verification.` (`sdd-plus/templates/tasks.md:13`, and the live
    packet's `:13`). "Verification" is not "verifier".

  The two scopes cover **6 of 6** verifier-owned pending tasks in the repo and waive **0 of 45**
  implementer-owned tasks. *Cost, stated:* a packet that files implementation work under a heading
  that literally names the verifier subagent would have that work waived — an over-waive recorded in
  `plan.md` §Risks, never used that way in this repo, requiring a bound independent verdict to be
  reachable at all, and visible in the diff. *Alternative:* line-only matching — narrower, but it
  would leave the smoke-packet shape blocked, which is 4 of the repo's 6 verifier-owned tasks.
  *Guardrail:* the matcher may not be widened beyond the §E.1 set; a wording not in that table means
  stop and ask the Owner (`plan.md` must_not_do 23, Step 9a, test #19d).
