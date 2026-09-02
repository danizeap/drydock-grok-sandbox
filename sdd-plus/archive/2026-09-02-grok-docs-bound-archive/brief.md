# Brief

## Change

grok-docs-bound-archive

Mode: **LITE. Docs only.** No behavior change, no code change, no pin change, no test change,
no delta specs.

**Round 2 of 2 (final before implement).** Codex negotiate ran at round 1 (`gpt-5.4-mini`,
`ok: true`, `converged: false`) and returned **three blocking concerns**: (1) the transport-vs-archive
boundary was asserted rather than defined; (2) the validation step was over-scoped (full `pytest`
plus the hook-mutating `start_probe.py`); (3) the "don't edit `scope-contract.yml`" decision was
under-argued. This revision addresses all three — the contract claims that changed are marked below,
and the evidence lives in `plan.md` §Definition, §Codex round-1 blocking concerns answered, F6, and
Step 4. The next turn is the implement turn.

## User Need

The sandbox can now archive a packet from a **bound verifier sidecar** — `verifier-report.md` plus
`verifier-report.sha256`, confirmed by the pinned `scripts/check_verdict.py` — with **no `--force`**
and no `## Override` record. Hole 3 (`grok-archive-bound-verdict`, archived at
`sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/`) shipped that gate, and it has been used
live exactly once: that packet's own archive, commit `f799ddc`, merged as PR #21 at this HEAD
`93c2959`. Its directory carries both artifacts, its `decision-log.md` carries **zero** `## Override`
headings (`grep -c '^## Override'` → `0`, re-run this turn), and `sha256sum -c` against the sidecar
hex `52093daa2ad53bddcc686f9b84e1471e69e25a379cef5a83a8d7d71d96d13438` prints
`verifier-report.md: OK` (also re-run this turn). The `f799ddc` / PR #21 citation is a **historical
note** of the first bound archive — not a pin, nothing binds to it, no test asserts it.

The three files a session actually reads to learn what this repo permits — `README.md`,
`PROJECT_CONTEXT.md`, `sdd-plus/security/scope-contract.yml` — do not say any of this. A session
that reads them learns a pipeline that ends "`check_verdict.py` + `record_verify` → Daniel archives"
(`PROJECT_CONTEXT.md:21`) and has no way to know that the ordinary archive-without-`--force` path
exists, what produces the sidecar, or who is allowed to write it. The predictable failure is the
same stale-refusal defect `grok-docs-coplan-runtime` fixed for coplan: the next session reaches for
`--force` (or refuses) because the docs never told it there is a clean path.

### The transport vs archive definition (round-2 addition; Codex blocking concern 1)

Saying "Grok writes the sidecar" next to `PROJECT_CONTEXT.md:60`'s "never archives" is a semantics
bug unless the boundary is defined by a rule a reader can apply. The rule is **which command runs**:

> **Archiving** is running `python3 scripts/sdd.py archive <name>` — `cmd_archive`
> (`scripts/sdd.py:773-807`), whose terminal act is `shutil.move(str(change_dir), str(target))`
> (`:806`), moving the packet out of `sdd-plus/changes/<name>` into
> `sdd-plus/archive/<date>-<name>`. Daniel runs it.
>
> **Transport** is copying in-channel bytes into the **live** packet directory
> `sdd-plus/changes/<name>/` **without** invoking `cmd_archive` and without moving the packet. Grok
> does it.

The sidecar write is transport under that rule: it calls no `cmd_archive`, moves no packet, and
writes no `## Override` heading (`record_override`, `scripts/sdd.py:669-678`, is reached only from
the `--force` path at `:798-799` and from `cmd_abandon` at `:766`). The archived producer
choreography agrees — the sidecar write is step 4 and `sdd.py archive` is a **separate** step 5
(`sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/plan.md:906-920`).

`never archives` therefore stays verbatim at `:60` and stays true, and "Daniel archives" stays true
at `:21`. This packet ships the **rule**, not just the conclusion: both edited documents must state
which command counts as archiving and which writes are transport.

## Problem

The bound-sidecar contract exists in exactly two places today, and neither is a document anyone
reads first:

1. **The archived packet plan** — `sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/plan.md`
   §D.2 (heading `:892`, the five producer steps `:906-920`) holds the choreography verbatim.
   Archive directories are history; nothing points a new session at them.
2. **`scripts/sdd.py` helper and error text** — `VERIFIER_REPORT` / `VERIFIER_SHA` /
   `BOUND_VERDICTS` at `:27-29`, the `sidecar_digest` grammar docstring at `:322-329`, the
   `verdict_binding` four-step contract at `:344-411`, the `unbound-verdict` blocker at `:499-500`,
   and the `cmd_archive` hint at `:789-792` ("Bind the verifier verdict: put the report verbatim in
   verifier-report.md and the sha256 it was stated with in verifier-report.sha256"). All of it is
   reachable only by reading the source, or by hitting the error after archive already refused.

What the three read-first files say today (checked this turn with a **seventeen**-term grep —
`archive|verifier-report|sidecar|sha256|--force|check_verdict|record_verify|sdd\.py|verdict|bind|bound|READY|Override|packet|pipeline|changes/|cmd_archive`):

- **`README.md`** — 14 lines, **zero hits, exit 1**. It is completely silent on the verify→archive
  pipeline. It does already carry the precedent for this kind of paragraph — the coplan closure
  runtime announcement at `:10-13`.
- **`PROJECT_CONTEXT.md:21`** (Desired Outcome) — "…→ independent verifier (in-channel hash) →
  check_verdict.py + record_verify → Daniel archives." The chain names `check_verdict.py` as a step
  *before* archive, not as the thing archive binds on. Nothing names the two artifacts. The file has
  **no hit at all** for `verifier-report`, `sidecar`, `sha256`, `--force`, `Override`, `bound`,
  `pipeline`, `changes/`, or `cmd_archive`.
- **`PROJECT_CONTEXT.md:60`** (Constraints) — "Grok (choreographer) transports, never audits, never
  archives, never implements." True and staying true, but it supplies no rule for *where the line
  sits*, so a careful session could read `:60` as forbidding the one new producer step.
- **`sdd-plus/security/scope-contract.yml`** — read line by line this turn, all 88 lines, plus the
  seventeen-term grep. See the strengthened argument below and `plan.md` F6.

### Why the scope contract still gets no edit (round-2 strengthening; Codex blocking concern 3)

Round 1 rested this on a six-term grep and a word-sense note. That was under-argued. The full
argument now (complete version in `plan.md` F6.1–F6.5, mirrored in OQ-1):

- **Authority.** The file's own header (`:1-2`) calls it a *"Project LGF scope contract"*, and
  `related_gates` (`:8-11`) names exactly *"Gate 0 — Scope & Permission"*, *"Gate 1 — Product, Asset
  & Data Inventory"*, *"Gate 11 — Infrastructure, DNS, TLS & Web Hardening"*. It is authoritative for
  LaunchGuardian launch scope, permission, inventory and infra hardening. It is **not** authoritative
  for packet lifecycle, `sdd.py archive`, verify→archive readiness, or bound sidecars — that
  authority is `scripts/sdd.py` (`cmd_archive:773-807`, `verdict_binding:344-411`,
  `sidecar_digest:322-329`) plus the archived hole-3 packet. Codex's conditional ("*if* that contract
  is authoritative for archive semantics") is answered: **it is not.**
- **Every key read, none holds pipeline wording.** `scope.summary:14`, `environments:16-25`,
  `in_scope:27-32`, `out_of_scope:33-38`, `assumptions:39-42`, `open_questions:43-44`,
  `users_and_access:46-55`, `external_boundaries:57-75`, `must_have:78-81`, `must_not_do:82-86`,
  `rollback_or_disable_path:87`. The closest approach is `in_scope:28` — *"This git tree (kernel,
  hooks, scripts, tests, sdd-plus, CI workflow)"* — which is a **tree-membership** claim for the LG
  scan, not a lifecycle claim.
- **Seven grep hits, none pipeline wording.** `:57`, `:70`, `:72` are the substring `bound` inside
  `external_boundaries` / `inbound_integrations` / `outbound_integrations`. `:4`
  (`change: "bootstrap-lgf-packet"`) and `:38` (*"The grok-choreography-smoke packet"*) are the word
  *packet* used as a name. `:14` names `check_verdict.py` as a thing being **live-fired**. `:87`
  *"Delete or archive the public sandbox repo"* means mothballing the GitHub repository. **Zero**
  hits for `verifier-report`, `sidecar`, `sha256`, `--force`, `record_verify`, `sdd.py`, `READY`,
  `Override`, `pipeline`, `changes/`, `cmd_archive`.
- **Negative proof.** `must_not_do:82-86` is force-push/delete main (`:83` — git remote force, not
  `sdd.py archive --force`), weakening `ci_parse_lg_report.py`, client/LOQ + mutating conductor, and
  ledger-in-tree; none becomes false when a packet archives from a bound sidecar. `must_have:78-81`
  is fail-closed CI, honest LGF files, scanners-before-LG — not archive readiness. The bound path
  adds no domain, no third-party service, no inbound or outbound integration (`:57-75`), so it
  changes nothing this contract governs.

Conclusion: there is nothing in the file to correct, so editing it would mean **adding** a
governance-lifecycle topic to an LGF launch-scope contract to force a three-file diff. Default stays
**no yaml edit**, now on a full-file proof rather than a word sense.

### Why no pytest and no start_probe (round-2 change; Codex blocking concern 2)

`tests/` holds 13 `.py` modules. A case-insensitive grep for
`README|PROJECT_CONTEXT|scope-contract|Daniel archives|never archives` across `tests/` returns
exactly two source hits, both at `tests/test_pre_commit_tree.py:32-33`, where a **fixture file named
`readme.txt`** is written into a throwaway git repo — not this repo's `README.md`, and not an
assertion about its contents. Zero hits for `PROJECT_CONTEXT`, `scope-contract`, `Daniel archives`,
or `never archives`. `tests/test_sdd_archive_bound_verdict.py:283-297` is the only test that reads
repo files by path, and its corpus inventory globs `sdd-plus/archive/*/tasks.md` only — untouched by
a docs edit and untouched by a live packet under `sdd-plus/changes/`.

So a green suite proves nothing about this packet's prose, and a red one would be about something
else. `scripts/start_probe.py` is worse than merely irrelevant: its own docstring (`:1-6`) says it
*"Installs backstops/pre-push into .git/hooks if missing or drifted"* — a mutation, in a docs-only
packet. Both are dropped from this packet's validation (contract change: two acceptance criteria
removed below), replaced by five read-only checks that prove the prose against the code.

## Scope

In scope:

- Advertise the bound-sidecar archive path in the read-first docs: name the two artifacts, the
  `check_verdict.py` exit-0 bind, the whitelisted verdicts, and `sdd.py archive` without `--force`.
- **Ship the transport-vs-archive definition itself**, not just its conclusion: both edited
  documents must name `python3 scripts/sdd.py archive <name>` as the archiving act (Daniel's) and
  the write into the live packet directory as transport (Grok's).
- Say plainly that a bound report is **sufficient, never necessary** — ticked boxes plus a filled
  Result still archive, and a forgotten sidecar is a missed benefit, never a false pass.
- Say plainly that `--force --reason "<why>"` remains the Owner override when the verdict is unbound.
- Say plainly that the producer is **Grok choreography, not a repo script**, and reconcile it with
  `PROJECT_CONTEXT.md:60` using the definition above: Grok still never archives; Daniel does.
- Decide, from the current wording rather than a quota, which of the three files gets a sentence,
  and record that decision with citations.

Out of scope:

- **Any archive behavior change.** The gate shipped in hole 3 and is not being touched, widened,
  narrowed, or made mandatory.
- **`scripts/sdd.py`**, `scripts/check_verdict.py`, `scripts/record_verify_bound.py`,
  `scripts/conductor/`, `scripts/start_probe.py`, `kernel/`, `hooks/`, `.github/workflows/`,
  `tests/`, `drydock-pins.json`, `agents/verifier.md`.
- **Running `pytest` or `scripts/start_probe.py`** as this packet's validation, in either turn — see
  the section above.
- **Building a producer in-repo.** No workflow job, no conductor stage, no new script, no
  `agents/verifier.md` edit to emit the sidecar. The producer is choreography outside this tree and
  it already ran live (archived plan §D.2, must_not_do 25).
- **The leftover-hole slog, which is STOPPED.** Hole 1 (`.env` write) and hole 4 (GitHub FF
  `--force`) are accepted residual and are not reopened, not planned for, not mentioned as future
  work. Holes 2 and 3 are archived and are not reopened.
- No client trees, no LOQ files, no migration or backfill of archived packets, no completeness-CLI
  kill.
- No commit, no push, no PR, no archive of this packet — the Owner decides when to commit.

## Acceptance Criteria

- [x] `README.md` names the bound-sidecar archive path: both artifact filenames, the
      `check_verdict.py` bind, `VERIFIED` / `VERIFIED WITH NOTES`, and `sdd.py archive` with no
      `--force`.
- [x] `README.md` states that a bound report is sufficient but not necessary, and that
      `--force --reason` remains the Owner override when unbound.
- [x] `README.md` states that the producer is Grok choreography, not a repo script.
- [x] `PROJECT_CONTEXT.md` Desired Outcome no longer ends the pipeline at a bare "Daniel archives"
      with `check_verdict.py` as a prior step; it names the bound artifacts and the no-`--force`
      archive.
- [x] `PROJECT_CONTEXT.md:60` still contains "never archives" (Grok's ban is not weakened) while
      making clear that writing `verifier-report.sha256` is transport, not archiving.
- [x] **(round 2, new)** Both `README.md` and `PROJECT_CONTEXT.md` ship the definition, not just the
      conclusion: each names `sdd.py archive` as the archiving act that moves a packet from
      `sdd-plus/changes/` to `sdd-plus/archive/` and Daniel runs it, and each contains the literal
      phrase `is transport, not archiving` for the write into the live packet directory — so `:60`
      cannot be read as banning the sidecar write and neither document can be skim-read as "Grok
      archives".
- [x] Every claim in the new prose is true of the tree at this HEAD: the two artifact names, the
      whitelisted verdict strings, and the no-`--force`/no-`## Override` outcome all match
      `scripts/sdd.py` and the archived packet on disk.
- [x] The `f799ddc` / PR #21 citation is shipped as a **historical note**, not as a pin or reference
      point, and the prose says so.
- [x] The decision about `sdd-plus/security/scope-contract.yml` (edit or not) is recorded in
      `decision-log.md` with the `file:line` evidence it rests on.
- [x] `git diff` touches only the doc files named in `plan.md` — no `scripts/`, `tests/`,
      `kernel/`, `hooks/`, `.github/`, `.git/hooks/`, `drydock-pins.json`, or `sdd-plus/archive/`.
- [ ] If `sdd-plus/security/scope-contract.yml` is edited at all, it still parses as YAML and
      `rollback_or_disable_path` (`:87`) is byte-identical.

*(Round 2 removed two round-1 criteria — "`pytest` still passes" and "`start_probe.py` still exits
0" — as a deliberate contract change, not an oversight. Neither validates the prose, and
`start_probe.py` mutates `.git/hooks`. They are replaced by the definition criterion above and by
`plan.md` Step 4's five read-only checks. They are **not** replaced by a weaker "pytest still
passes" wish.)*

## Impact Areas

- Backend: none.
- Frontend: none.
- Data model: none.
- API: none.
- AI/model behavior: none. The verifier role blob (`agents/verifier.md`) is not edited; the verifier
  still writes nothing to the tree.
- Documentation: `README.md`, `PROJECT_CONTEXT.md`.
- Operations/security: wording only, and only if `scope-contract.yml` is edited — see Open
  Questions. No scanner, hook, CI, or pin change; nothing is written to `.git/`. No permission is
  widened: the bound path is already shipped and already exercised.

## Open Questions

None blocking. Each has a stated default the implementer builds without asking.

- **OQ-1 — which of the three files get a sentence?** *Default (build this):* **`README.md` and
  `PROJECT_CONTEXT.md` yes; `sdd-plus/security/scope-contract.yml` no.** README is the first file a
  session reads and is currently silent on the entire pipeline (zero hits across seventeen terms),
  which is exactly the silence that recreates the stale-refusal defect; it already hosts a parallel
  "X is runtime on this VM" paragraph at `:10-13`. PROJECT_CONTEXT `:21` and `:60` both make claims
  about archive that are now incomplete. **The yaml argument is the round-2 strengthened one** (see
  "Why the scope contract still gets no edit" above and `plan.md` F6.1–F6.5), not round 1's
  grep-plus-word-sense: the file declares its own authority as LGF Gate 0 / 1 / 11 (`:8-11`) and is
  therefore **not authoritative for archive semantics**; all 88 lines were read key by key and none
  holds verify→archive wording; a seventeen-term grep returns seven hits, of which three are the
  substring `bound` inside `external_boundaries`/`inbound_integrations`/`outbound_integrations`
  (`:57`, `:70`, `:72`), two are the word *packet* as a name (`:4`, `:38`), one is `check_verdict.py`
  as a live-fire target (`:14`), and one is repo mothballing (`:87`); and the three keys that could
  have carried an archive claim (`in_scope:27-32`, `must_have:78-81`, `must_not_do:82-86`) carry
  none. Adding a governance-lifecycle line there would be shoehorning a new topic to force a
  three-file diff — the thing the Owner explicitly warned against. *Reversal condition:* if the
  implementer finds, on re-reading at edit time, a line in the yaml that actually constrains or
  describes `sdd.py archive`, edit **that line only** and record it; do not invent a new key, do not
  append to `must_not_do`, and never touch `:87`.
- **OQ-2 — does `PROJECT_CONTEXT.md:60` stay byte-identical?** *Default (build this):* **no — it
  gains the transport/archive definition, and "never archives" survives verbatim inside the line.**
  Left alone, `:60` is the sentence a careful session would cite to refuse writing the sidecar,
  because writing a file into a packet directory looks like more than transport. The added clause
  must state the **rule** — archiving is running `python3 scripts/sdd.py archive`, the step that
  moves a packet out of `sdd-plus/changes/` into `sdd-plus/archive/`, and it is Daniel's; transport
  is copying in-channel bytes into the live packet directory without running that command — and then
  apply it to the two artifact writes. It must **not** merely say "transport includes X"; that was
  round 1's wording and it asserts the conclusion instead of giving the reader a rule (Codex blocking
  concern 1). *Alternative:* leave `:60` untouched and carry the reconciliation in the Desired
  Outcome paragraph only — rejected because the ban and its scope should be readable in one place.
- **OQ-3 — does this add a Durable Decisions row to `PROJECT_CONTEXT.md:69-73`?** *Default (build
  this):* **no.** The durable decision is hole 3's, already recorded in its archived packet; this
  packet advertises it rather than making it. A LITE docs packet does not rewrite the durable-decision
  table.
- **OQ-4 — does this add a test?** *Default (build this):* **no pytest — and no pytest run, and no
  `start_probe.py` run, either.** Mirrors `grok-docs-coplan-runtime`, which added none. Honesty is
  held entirely by the five **read-only** checks in `plan.md` Step 4: 4a (both documents carry every
  claim), 4b (nothing weakened — `never archives` survives), 4c (the advertised filenames and verdict
  strings equal the constants at `scripts/sdd.py:27-29`), 4d (the diff touches only the two named
  docs), 4e (the transport/archive definition landed in both files). Justified by the grep above:
  nothing under `tests/` asserts these sentences, so a suite run is unrelated signal, and
  `start_probe.py` additionally writes `.git/hooks` (`:1-6`). None of the five checks mutates
  anything or depends on a clean worktree, so no fallback is needed. *Reversal condition:* if the
  implementer finds a test that does assert the old wording, update that one test in the same
  implement commit and record it.
- **Guard note (not a question):** if `packet_guard` denies a write this plan calls for, **stop and
  tell the Owner**. Do not skip the file, do not land a partial change, do not route around the hook.
