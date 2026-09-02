# Plan

## Change

grok-docs-bound-archive

## Round

**Round 2 of 2 (final before implement).** Codex negotiate ran at round 1
(`gpt-5.4-mini`, `ok: true`, `converged: false`) and returned **three blocking concerns**. This
revision addresses all three — see §Codex round-1 blocking concerns, answered. The next turn is the
implement turn; **this turn is still planning only** (no production edit, no commit, no archive).

**Owner (2026-09-02):** accepted the Codex r2 residual by aligning Step 3 to `Daniel runs it` so
the 4e grep matches Steps 1–2. Round 2 content otherwise unchanged.

## Mode

**LITE. Docs only.** No behavior change, no code change, no pin change, no test change, no delta
specs, no archive change.

Two files are edited: `README.md` and `PROJECT_CONTEXT.md`.
`sdd-plus/security/scope-contract.yml` is **deliberately not edited** — F6 (rewritten this round as
a full-file proof, not a grep) and §Decision carry the evidence. That file would be in scope only if
it actually talked about `sdd.py archive` or the verify→archive pipeline; read line by line this
turn, all 88 lines, it does not. It is not skipped for convenience, and this is not a partial
landing: the two files that make claims about archive both get corrected, and the one that makes
none stays as it is.

The LGF contract carve-out from `grok-docs-coplan-runtime` does not apply here. That packet edited
the yaml because the yaml **contained the stale ban** (`out_of_scope:34`, `must_not_do:84` both said
`conductor/`). Here the yaml contains nothing to correct.

## Definition — transport vs archive (durable; answers Codex blocking concern 1)

This is the one semantic that the shipped prose must carry, not just this plan. It is defined by
**which command runs**, not by which directory is written, because that is the distinction the code
actually implements.

> **Archive** is running `python3 scripts/sdd.py archive <name>` — the `cmd_archive` function at
> `scripts/sdd.py:773-807`. Its terminal act is `shutil.move(str(change_dir), str(target))`
> (`:806`), which **moves the packet out of `sdd-plus/changes/<name>` into
> `sdd-plus/archive/<date>-<name>`** (`:780`, `:801-803`). That move is archiving. Daniel runs it.
>
> **Transport** is copying in-channel bytes into the **live** packet directory
> `sdd-plus/changes/<name>/` **without** invoking `cmd_archive` and without moving the packet. Grok
> does it.

**The sidecar write is transport, not archiving**, on three on-disk grounds:

1. It does not call `cmd_archive` (`scripts/sdd.py:773`). Nothing in the producer choreography
   invokes `sdd.py archive`; the archived §D.2 block (`sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/plan.md:906-920`)
   makes `sdd.py archive <name>` a **separate, fifth step** after the sidecar write at step 4.
2. It does not `shutil.move` the packet (`scripts/sdd.py:806`). After the sidecar write the packet
   is still at `sdd-plus/changes/<name>/`; that is exactly why `sdd.py archive` still has something
   to move.
3. It does not write a `## Override` heading. `record_override` (`scripts/sdd.py:669-678`, heading
   written at `:674`) is reached only from the `--force` path in `cmd_archive` (`:798-799`) and from
   `cmd_abandon` (`:766`). The sidecar path touches neither.

Consequences the prose must honour:

- `PROJECT_CONTEXT.md:60`'s `never archives` **stays verbatim** in the line and stays *true*: Grok
  never runs `sdd.py archive`. `:21`'s "Daniel archives" also stays true and unchanged.
- The clarifying clause must **use this definition** (name the command that counts as archiving, and
  name the live packet directory that transport writes into). It must not merely assert "transport
  includes X" — that was the round-1 wording Codex correctly called a semantics bug, because it
  asserts the conclusion instead of giving the reader a rule.
- Both shipped paragraphs must contain the literal phrase **`is transport, not archiving`** and must
  name **`sdd.py archive`** as the archiving act, so neither document can be skim-read as "Grok
  archives". Step 4e greps for exactly that.

## Codex round-1 blocking concerns, answered

Quoted verbatim from `/home/box/drydock-state/drydock-grok-sandbox/negotiate-grok-docs-bound-archive-r1.json`
(`blocking_concerns[0..2]`, `:8-18`). Each is answered with facts re-read on disk this turn.

### Concern 1 (verbatim)

> **issue:** The plan’s own wording creates an unresolved boundary conflict between "Grok never
> archives" and "Grok copies the report and writes the sha256 sidecar".
>
> **why:** Without a crisp definition of what counts as transport versus archive, future readers can
> reasonably read the new docs as self-contradictory. That is a semantics bug, not just a style
> issue, and it should be settled before any edit lands.

**Accepted in full.** Round 1's Step 3 clause ("Transport includes copying the verifier report…;
running `sdd.py archive` is still Daniel's") asserted the answer without supplying a rule, and it
lived only in the plan — the shipped prose would have carried the assertion, not the definition.

Settled by §Definition above, which is now a durable, command-based rule and is written **into the
shipped prose** at Steps 1, 2 and 3, not just into this plan. On-disk facts it rests on:

- `scripts/sdd.py:773-807` — `cmd_archive`; `:806` `shutil.move(str(change_dir), str(target))`;
  `:780` `change_dir = root / "sdd-plus" / "changes" / name`; `:801-803`
  `target = archive_root / f"{date}-{name}"`. Moving the packet **is** the archive act.
- `scripts/sdd.py:669-678` — `record_override` writes `## Override — <date>`; called from `:798-799`
  (`--force`) and `:766` (`cmd_abandon`) only.
- `sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/plan.md:906-920` — the five-step producer
  choreography: (1) verifier posts report + sha256 in channel and **writes nothing**; (2) Grok
  copies the report verbatim to `<packet>/verifier-report.md`; (3) `check_verdict.py` exit 0 is the
  bind; (4) Grok writes the same hex to `<packet>/verifier-report.sha256`; (5) **separately**,
  `python3 scripts/sdd.py archive <name>`.
- `PROJECT_CONTEXT.md:60` — "Grok (choreographer) transports, never audits, never archives, never
  implements." Preserved verbatim inside the edited line (Step 3, checked by Step 4b).
- `PROJECT_CONTEXT.md:21` — "…→ Daniel archives." Left byte-identical (Step 2).

### Concern 2 (verbatim)

> **issue:** Step 4e is over-scoped for a docs-only change.
>
> **why:** Running the full pytest suite plus `start_probe.py` introduces unrelated failure modes and
> side effects, and `start_probe.py` is explicitly called out as mutating hooks. This does not
> directly validate the doc edits and increases the chance of noise or accidental drift.

**Accepted in full.** Round 1's 4e is **deleted**, not softened, and every place it leaked is
updated (§Tests, §Files Expected To Change, must_not_do 7 and 16, §Risks, the `tasks.md` sketch, and
`brief.md`'s two ACs and OQ-4). On-disk facts:

- `scripts/start_probe.py:1-6` — module docstring: *"Choreography start probe: pin drift + hook
  payloads + secret-tree + pre-push install… **Installs backstops/pre-push into .git/hooks if
  missing or drifted**; fails if it cannot."* It is a mutating command. Round 1's own must_not_do 16
  already forbade running it in the planning turn for that reason, then scheduled it as a Step 4e
  implement command — an inconsistency Codex is right to reject.
- F14 (re-proved below) — nothing under `tests/` asserts any sentence in `README.md`,
  `PROJECT_CONTEXT.md`, or `scope-contract.yml`. A green pytest run therefore proves **nothing**
  about this packet's prose; it is unrelated signal that can only produce noise.

Replaced by targeted, **read-only** validation that actually proves the doc edits: 4a (both docs
carry all the claims), 4b (nothing weakened), 4c (advertised strings equal the `sdd.py` constants),
4d (diff touched only the named docs), **new 4e (the transport/archive definition landed in both
files)**, 4f (conditional yaml parse). None of these mutates anything, none needs a clean worktree,
and none can fail for a reason unrelated to this change — which also disposes of Codex's
"no fallback if the workspace is already dirty or `start_probe.py` mutates state" gap: there is no
broad command left to need a fallback for.

### Concern 3 (verbatim)

> **issue:** The decision to leave `sdd-plus/security/scope-contract.yml` untouched is under-argued.
>
> **why:** The plan relies on a word-sense distinction and a grep result, but if that contract is
> authoritative for archive semantics, skipping it could leave the repo with inconsistent
> source-of-truth docs. I want a stronger proof that no relevant pipeline wording lives there before
> accepting the no-edit decision.

**Accepted as a fair objection to the argument, and answered with a stronger proof — F6 below is
rewritten from a six-term grep into a full-file, key-by-key reading of all 88 lines plus a
seventeen-term grep.** The hanging question is answered directly rather than left conditional:
**the scope contract is not authoritative for archive semantics.** The conclusion is unchanged (no
yaml edit) but it now rests on a full-file negative proof, not on one word sense.

## Load-bearing facts, checked on disk this turn

Every fact below was re-read at `HEAD = 93c2959050ac908fd19596a5c7eddfeae95030f2` on `main` in this
planning turn (`git log -1 --format='%H %s'` → `93c2959… Merge pull request #21 from
danizeap/archive/grok-archive-bound-verdict`). Nothing here is quoted from memory or from the task
prompt.

**F1 — `README.md` is 14 lines and says nothing about archive.** Grep for the **seventeen**-term
list (`archive|verifier-report|sidecar|sha256|--force|check_verdict|record_verify|sdd\.py|verdict|bind|bound|READY|Override|packet|pipeline|changes/|cmd_archive`,
case-insensitive) returns **zero hits — exit 1**. Its content is: title `:1`, "Throwaway Grok
choreography sandbox… **Not a client project.**" `:3`, vendored pin `:5`, ledger-outside-tree `:6`,
"Do not copy client or LOQ files here." `:8`, and the coplan closure runtime paragraph `:10-13`
ending "…is not vendored and must not be vendored or run here." The file ends at `:13` plus a
trailing newline.

**F2 — `README.md:10-13` is the precedent for the paragraph shape.** It announces a capability as
runtime on this VM, names the exact files, and states what remains forbidden. That paragraph was
added by `grok-docs-coplan-runtime` (`sdd-plus/archive/2026-09-01-grok-docs-coplan-runtime/plan.md`
Step 1, `:68-89`). The new paragraph is the same shape for a different capability.

**F3 — `PROJECT_CONTEXT.md:21` (Desired Outcome), verbatim:**

```
A VIABLE sandbox packet: new → implement (Claude) → deterministic gates → cross-review (Codex, transport only) → independent verifier (in-channel hash) → check_verdict.py + record_verify → Daniel archives. Fail-cases actually denied with recorded evidence.
```

`check_verdict.py` appears as a step *preceding* archive. Nothing says archive itself binds on it,
and neither artifact filename appears anywhere in the file.

**F4 — `PROJECT_CONTEXT.md:60` (Constraints), verbatim:**

```
- Grok (choreographer) transports, never audits, never archives, never implements.
```

**F5 — `PROJECT_CONTEXT.md`, same seventeen-term grep: hits at `:9`, `:21`, `:25`, `:32`, `:35`,
`:45`, `:57`, `:60`, `:65`.** `:9` and `:25` and `:35` name `check_verdict.py`; `:32` names
`scripts/sdd.py` in the Stack list; `:45` "client code, client **packets**, LOQ files"; `:57`
"missing **verdict** = failed / BLOCKED"; `:21` is F3; `:60` is F4; `:65` "Smoke **packet** and
fail-cases are later work". **No hit anywhere in the file for `verifier-report`, `sidecar`,
`sha256`, `--force`, `Override`, `bound`, `pipeline`, `changes/`, or `cmd_archive`.** The file
names the *script* and the *role boundary* and never the artifacts or the bound path.

**F6 — `sdd-plus/security/scope-contract.yml`: full-file proof that it holds no verify→archive
pipeline wording (rewritten this round; replaces the round-1 six-term grep).** All 88 lines read
line by line this turn.

**F6.1 — What the file is authoritative for, and what it is not.** `:1-2` is its own header
comment: *"Project LGF scope contract for drydock-grok-sandbox. / Throwaway LITE sandbox — NOT a
production launch."* `related_gates` (`:8-11`) names exactly three: *"Gate 0 — Scope & Permission"*,
*"Gate 1 — Product, Asset & Data Inventory"*, *"Gate 11 — Infrastructure, DNS, TLS & Web
Hardening"*. It is therefore authoritative for **LaunchGuardian Gate-0 launch scope and permission,
asset/data inventory, and infra hardening**. There is no lifecycle gate, no packet gate, no
verification gate in that list.

It is **not** authoritative for SDD+ packet lifecycle, `sdd.py archive`, verify→archive readiness,
or bound sidecars. The source of truth for archive semantics is `scripts/sdd.py` — `cmd_archive`
(`:773-807`), `archive_readiness`, `verdict_binding` (`:344-411`), `sidecar_digest` (`:322-329`) —
plus the archived hole-3 packet at `sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/`.
Codex's conditional ("*if* that contract is authoritative for archive semantics") is hereby
answered: **it is not**, on the file's own `related_gates` declaration.

**F6.2 — Full key inventory.** Every top-level and nested key that could conceivably hold pipeline
wording, with the line it lives on and why it is or is not about `sdd.py archive` / bound sidecar /
verify→archive:

| Key | Line(s) | Content | Pipeline wording? |
| --- | --- | --- | --- |
| `project` | `:3` | `"drydock-grok-sandbox"` | No — a name. |
| `change` | `:4` | `"bootstrap-lgf-packet"` | No — the LGF change label this contract was written for. Matches the grep on the word *packet* as part of a slug; makes no claim about how packets archive. |
| `date` / `owner` | `:5-6` | `"2026-09-01"` / `"Daniel Paez"` | No. |
| `related_gates` | `:8-11` | Gate 0 / Gate 1 / Gate 11 | No — LGF launch gates (F6.1). |
| `scope.summary` | `:14` | `"…live-fire of kernel, hooks, CI, check_verdict.py, and LaunchGuardian. Not a client project. Not a production product."` | No — names `check_verdict.py` as a **thing being live-fired** in the sandbox. It asserts nothing about what archive binds on, does not mention `sdd.py`, and would remain true word for word after this packet's docs land. |
| `scope.launch_type` | `:15` | `"not_a_production_launch"` | No. |
| `scope.environments` | `:16-25` | `git-main` (`:17-19`), `github-actions-ubuntu-latest` (`:20-22`), `shared-grok-vm` (`:23-25`, *"Local live-fire of kernel/hooks/scanners; run ledger outside the tree"*) | No — environments and public exposure. No archive wording. |
| `scope.in_scope` | `:27-32` | git tree (`:28`), CI job (`:29`), LG scan (`:30`), local scanner install (`:31`), six-file coplan closure (`:32`) | No. `:28` `"This git tree (kernel, hooks, scripts, tests, sdd-plus, CI workflow)"` is the closest approach — it names `sdd-plus` — but as **tree membership for the LG scan**, not as a lifecycle claim. It says the directory is in launch scope; it says nothing about `sdd.py archive`, readiness, or sidecars. |
| `scope.out_of_scope` | `:33-38` | client/LOQ (`:34`), mutating conductor (`:35`), production deployment (`:36`), run ledger (`:37`), `"The grok-choreography-smoke packet (not this bootstrap)"` (`:38`) | No. `:38` matches the grep on *packet* but scopes **which packet the bootstrap covers**, not how any packet archives. |
| `scope.assumptions` | `:39-42` | throwaway LITE sandbox (`:40`), absence-of-evidence (`:41`), no approved production launch (`:42`) | No. |
| `scope.open_questions` | `:43-44` | `"None blocking sandbox bootstrap. Production launch is intentionally not in play."` | No. |
| `users_and_access` | `:46-55` | intended users (`:47-50`), excluded users (`:51-53`), admin roles (`:54-55`) | No — who may use the sandbox. Names Daniel as Owner-operator (`:55`) but assigns no lifecycle command. |
| `external_boundaries` | `:57-75` | domains (`:58-59`), third parties GitHub/PyPI/GitHub Releases (`:60-69`), inbound (`:70-71`), outbound (`:72-75`) | No — **and this is the sharpest negative proof.** The seventeen-term grep's hits at `:57`, `:70`, `:72` are substring matches on `bound` inside `external_boundaries`, `inbound_integrations`, `outbound_integrations`. Not one is "bound verdict". The bound-sidecar path adds **no** external surface: no domain, no third-party service, no inbound or outbound integration. |
| `launch_constraints.must_have` | `:78-81` | fail-closed CI job `drydock` (`:79`), honest LGF files (`:80`), scanners installed before the LG scan (`:81`) | No — none is an archive-readiness claim, and none becomes false when a packet archives from a bound sidecar. |
| `launch_constraints.must_not_do` | `:82-86` | `"Force-push or delete main"` (`:83`), `"Weaken ci_parse_lg_report.py"` (`:84`), client/LOQ + vendor/run mutating conductor (`:85`), `"Commit ledger files into this tree"` (`:86`) | No. Note `:83` is about **git remote force-push**, not `sdd.py archive --force` — the literal token `--force` gets **zero hits in the whole file**. Nothing here is an archive-pipeline claim that the bound path would make false. |
| `launch_constraints.rollback_or_disable_path` | `:87` | `"Delete or archive the public sandbox repo; disable the drydock workflow; VM ledger stays outside git. There is no production traffic to drain."` | No — **"archive" here means deleting/mothballing the GitHub repository**, an LGF Gate-0 rollback concept. It is not `sdd.py archive` and must not be treated as the same topic. |

**F6.3 — The seventeen-term grep, command and complete hit list.** Broader than round 1's six terms,
run this turn:

```
grep -niE 'archive|verifier-report|sidecar|sha256|--force|check_verdict|record_verify|sdd\.py|verdict|bind|bound|READY|Override|packet|pipeline|changes/|cmd_archive' \
  sdd-plus/security/scope-contract.yml
```

**Seven hits, complete, quoted:**

```
4:change: "bootstrap-lgf-packet"
14:  summary: "Public throwaway Grok choreography sandbox for Drydock-on-Grok v1 live-fire of kernel, hooks, CI, check_verdict.py, and LaunchGuardian. Not a client project. Not a production product."
38:    - "The grok-choreography-smoke packet (not this bootstrap)"
57:external_boundaries:
70:  inbound_integrations:
72:  outbound_integrations:
87:  rollback_or_disable_path: "Delete or archive the public sandbox repo; disable the drydock workflow; VM ledger stays outside git. There is no production traffic to drain."
```

Classified: `:57`, `:70`, `:72` are substring artifacts of `bound` inside boundary/integration key
names. `:4` and `:38` are the word *packet* used as a name. `:14` is `check_verdict.py` as a
live-fire target. `:87` is repo mothballing. **Zero hits for `verifier-report`, `sidecar`, `sha256`,
`--force`, `record_verify`, `sdd.py`, `READY`, `Override`, `pipeline`, `changes/`, or
`cmd_archive`.** Round 1 knew about `:14` and `:87`; the stronger pass confirms the other five hits
are also not pipeline wording under a different term, and that no term in the list finds any.

**F6.4 — Negative proof that matters.** The three keys that *could* have carried an archive claim
carry none: `in_scope` (`:27-32`) enumerates the git tree, the CI job, the LG scan, the local
scanner install and the six-file coplan closure — not `sdd.py archive`. `must_not_do` (`:82-86`) is
force-push/delete main, weakening `ci_parse_lg_report.py`, client/LOQ + mutating conductor, and
ledger-in-tree — none of which the bound path makes false. `must_have` (`:78-81`) is fail-closed CI,
honest LGF files and scanners-before-LG — not archive readiness. There is no verify→archive section
in the file, and no key under which one would belong.

**F6.5 — Conclusion and the bounded reversal.** No line in the file constrains or describes
`sdd.py archive` or the verify→archive pipeline, so **there is nothing to correct and the no-edit
decision stands**. If a later re-read at Step 0 finds such a line, correct **that line only**, do
not invent a new key, do not append to `must_not_do`, and never touch `:87`.

**F7 — the live contract in `scripts/sdd.py` (READ ONLY; not edited by this packet).**

- `:27-29` —
  `VERIFIER_REPORT = "verifier-report.md"`, `VERIFIER_SHA = "verifier-report.sha256"`,
  `BOUND_VERDICTS = ("VERIFIED", "VERIFIED WITH NOTES")`. `:30` —
  `CHECK_VERDICT = Path(__file__).resolve().parent / "check_verdict.py"`.
- `:322-329` — `sidecar_digest` docstring: "exactly one non-empty, non-`#` line. Its first
  whitespace-separated token must be 64 hex chars. A second token is allowed only if it names the
  report, so the sidecar can be produced either by pasting the in-channel hex or by running
  `sha256sum verifier-report.md`… Anything else fails closed."
- `:344-411` — `verdict_binding`: bound means all four, in order — (1) both files exist; (2) the
  sidecar parses to one sha256 hex; (3) the report's `## Verdict` section is exactly one line and is
  exactly `VERIFIED` or `VERIFIED WITH NOTES`; (4)
  `python3 scripts/check_verdict.py <report> <digest> <that exact line>` exits 0. "Fails closed
  everywhere."
- `:499-500` — the `unbound-verdict` blocker: `f"{VERIFIER_REPORT} is present but not bound:
  {bound.reason}"`.
- `:626-632` — on a bound packet `cmd_verify` prints "Bound verifier verdict: … confirmed by
  check_verdict.py" and, if the Result is still Pending, "waived by the bound verdict."
- `:773-807` — `cmd_archive` (see §Definition). `:789-792` — the hint on an unbound packet: "Bind
  the verifier verdict: put the report verbatim in verifier-report.md and the sha256 it was stated
  with in verifier-report.sha256", followed at `:797` by "…, or rerun with `--force`."
- `:774-777` — `--force` requires `--reason "<why>"`; `:798-800` — the `--force` path records the
  override. **`--force` is not removed and is not being removed.**

**F8 — the path is live, proved on disk this turn.**
`sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/` carries both `verifier-report.md` and
`verifier-report.sha256`. `sha256sum -c` against the sidecar's hex, re-run this turn, prints
`verifier-report.md: OK`. The sidecar holds
`52093daa2ad53bddcc686f9b84e1471e69e25a379cef5a83a8d7d71d96d13438`. The sidecar entered git in
`f799ddc` ("Archive grok-archive-bound-verdict after independent VERIFIED WITH NOTES."), merged as
PR #21 → this HEAD `93c2959`.

**F9 — that archive used no `--force`.** `record_override` writes a literal `## Override — <date>`
heading (`scripts/sdd.py:674`). `grep -c '^## Override'` on
`sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/decision-log.md`, re-run this turn, returns
**0**. (The string `## Override` does appear inside a prose table cell at that packet's
`decision-log.md:11`; that is not a heading and the anchored grep correctly returns 0.)

**F10 — precision correction, and it changes the wording we ship.** `grok-archive-bound-verdict` is
**not** the first archive ever done without `--force`. `2026-09-01-grok-coplan-discover-probe`,
`2026-09-01-grok-coplan-linux-discover` and `2026-09-01-grok-docs-coplan-runtime` also have zero
`## Override` headings — they archived cleanly by ticking their boxes and filling their Result.
The honest claim, and the only one the docs may make, is: **the first archive made READY by a bound
verifier sidecar.** Do not write "first archive without `--force`" into any file.

**F10a — citation policy for `f799ddc` / PR #21 (answers a Codex gap).** The commit and PR are a
**historical note** recording the first bound archive. They are **not a pin, not a reference point,
and nothing binds to them**: no test asserts them (F14), `drydock-pins.json` does not contain them,
and no command re-reads them. The shipped prose says so in the sentence itself
("a historical note … not a pin"), so a reader cannot mistake the citation for a contract. If the
commit is ever rewritten out of history the sentence becomes a stale anecdote, not a broken gate —
accepted, and recorded in §Risks.

**F11 — the producer choreography, from the archived plan §D.2**
(`sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/plan.md`, heading at `:892`, the five
numbered steps at `:906-920`): (1) verifier posts report + sha256 of those exact bytes in channel
and **writes nothing**; (2) Grok copies the report verbatim to `<packet>/verifier-report.md`;
(3) Grok/Owner runs
`python3 scripts/check_verdict.py <packet>/verifier-report.md <hex> "VERIFIED WITH NOTES"` — exit 0
is the bind; (4) Grok writes the same hex to `<packet>/verifier-report.sha256`; (5)
`python3 scripts/sdd.py archive <name>` — no `--force`, no `## Override`. Steps 2 and 4 are
transport; step 5 is archiving (§Definition). §D.2 (`:892-901`) also states the producer is outside
this repo and that no repo script, workflow job or conductor stage transports verifier reports;
must_not_do 25 (`:1497-1501`) forbids building one here.

**F12 — sufficient, not necessary.** Archived brief `:52-54`: "A bound report becomes a
**sufficient** path to READY. It does not become a **necessary** one… a forgotten producer step is a
missed benefit, never a false pass." OQ-2 default (archived brief `:302-307`) is "sufficient only";
must_not_do 8 forbids making it mandatory.

**F13 — `agents/verifier.md` was deliberately not edited (OQ-3, archived brief `:309-314`)**, because
it is pinned at `drydock-pins.json:20` and blob-recorded at `:3`. This packet does not edit it either.

**F14 — no test asserts any of this prose (re-proved this turn, and it is why pytest is not a
validation of this packet).** `tests/` holds **13 `.py` modules**. A case-insensitive grep for
`README|PROJECT_CONTEXT|scope-contract|Daniel archives|never archives` across `tests/` returns
exactly two source hits, both in `tests/test_pre_commit_tree.py:32-33`, where a **fixture file named
`readme.txt`** is written into a throwaway git repo — not this repo's `README.md`, and not an
assertion about its contents. **Zero** hits for `PROJECT_CONTEXT`, `scope-contract`,
`Daniel archives`, or `never archives` anywhere.
`tests/test_sdd_archive_bound_verdict.py:283-297` is the only test reading repo files by path; its
corpus inventory globs `sdd-plus/archive/*/tasks.md` and is unaffected by a docs edit and by a live
packet under `sdd-plus/changes/`. So: **no test change**, same as `grok-docs-coplan-runtime`
(which also added none — its plan `:197-201`) — **and a green pytest run would prove nothing about
this packet's prose**, which is the substance of Codex concern 2.

**F15 — guards.** `hooks/packet_guard.py` `is_exempt()` (`:85`) exempts `*.md` basenames, so
`README.md` and `PROJECT_CONTEXT.md` are exempt (established by `grok-docs-coplan-runtime` plan
`:180-184` and unchanged). `protect_secrets.py`'s secret-name regex is
`secrets?\.(json|ya?ml|toml)`, which matches neither file. This packet writes no `.yml` at all under
the OQ-1 default, so the yaml deny question does not arise — but the STOP rule in Step 4f stands in
case the default is reversed.

## Decision — which files get a sentence, and why

Recorded here because it is the one judgment call in this packet. The implementer copies it into
`decision-log.md` at implement time (see Step 5); it is not written to `decision-log.md` in the
planning turn.

| File | Edit? | Evidence |
| --- | --- | --- |
| `README.md` | **Yes** | Zero grep hits across seventeen terms for the whole pipeline (F1). It is the first file a session reads, and silence here is what recreates the stale-refusal defect: a session learns the repo's rules from README and would reach for `--force`, or refuse, never knowing the clean path exists. It already hosts a structurally identical "X is runtime on this VM" paragraph at `:10-13` (F2), so this is not a new topic being shoehorned — it is the same topic (what this VM is permitted to run) for a second capability. |
| `PROJECT_CONTEXT.md` | **Yes, two touches** | `:21` states the pipeline and ends it at "Daniel archives" with `check_verdict.py` as a prior step (F3) — incomplete, not merely silent. `:60` says Grok "never archives" (F4) and is the sentence a careful session would cite to refuse writing the sidecar; it needs the **transport-vs-archive definition** (§Definition) stated in the line, not the ban weakened. |
| `sdd-plus/security/scope-contract.yml` | **No** | **F6 full-file proof, not a grep and not a word sense.** The file declares its own authority as LGF Gate 0 / Gate 1 / Gate 11 (`:8-11`) and is **not authoritative for packet lifecycle or `sdd.py archive`** — that authority is `scripts/sdd.py:773-807` plus the archived hole-3 packet (F6.1). All 88 lines were read key by key (F6.2): no key holds verify→archive wording, and the three keys that could have (`in_scope:27-32`, `must_not_do:82-86`, `must_have:78-81`) hold none (F6.4). A seventeen-term grep finds seven hits (F6.3), of which three (`:57`, `:70`, `:72`) are the substring `bound` inside `external_boundaries`/`inbound_integrations`/`outbound_integrations`, two (`:4`, `:38`) are the word *packet* used as a name, one (`:14`) is `check_verdict.py` as a live-fire target, and one (`:87`) means *deleting the sandbox repo*. Zero hits for `verifier-report`, `sidecar`, `sha256`, `--force`, `sdd.py`, `Override`, `pipeline`, `changes/`, `cmd_archive`. The bound path adds no external surface, no new permission, no scanner obligation, and makes no `must_not_do` false. Adding a line would be shoehorning a governance-lifecycle topic into an LGF launch-scope contract to force a three-file diff. Unlike `grok-docs-coplan-runtime`, where the yaml itself carried the stale ban, there is nothing here to correct. |

**Reversal condition (bounded, not open-ended):** if, at Step 0, the implementer finds a line in
`scope-contract.yml` that actually constrains or describes `sdd.py archive` or the verify→archive
pipeline, correct **that line** and record the finding. Do not invent a new key, do not append to
`must_not_do`, and do not touch `:87`.

## Approach

Two paragraphs of prose plus one line-edit, all stating the same things, so the documents cannot
drift:

1. **The transport/archive boundary, defined by command** (§Definition) — archiving is
   `python3 scripts/sdd.py archive <name>`, the step that moves the packet from `sdd-plus/changes/`
   to `sdd-plus/archive/`, and Daniel runs it; transport is copying in-channel bytes into the live
   packet directory without running that command, and Grok does it. Both documents carry the rule,
   not just the conclusion.
2. **The ordinary bound-sidecar path** — `verifier-report.md` + `verifier-report.sha256`,
   `check_verdict.py` exit 0 as the bind, `## Verdict` exactly `VERIFIED` or `VERIFIED WITH NOTES`,
   then `sdd.py archive <name>` with **no `--force`** and no `## Override`.
3. **Grok still never archives — and the sidecar write is transport, not archiving** (F4, F11,
   §Definition). The prose states which command is the archive act, so `never archives` and "Grok
   writes the sidecar" are visibly about two different actions rather than one contradiction.
4. **Sufficient, never necessary** — ticked boxes plus a filled Result still archive exactly as
   before; a forgotten sidecar is a missed benefit, never a false pass (F12). The phrase appears
   literally in both paste strings (Step 4a greps for it); no third file is added to reinforce it.
5. **`--force --reason "<why>"` remains the Owner override** when the verdict is unbound (F7
   `:774-777`, `:797`).
6. **The producer is choreography, not a repo script** (F11, archived must_not_do 25).

Nothing is claimed beyond what `scripts/sdd.py` actually does. In particular the prose says the
sidecar **binds the report bytes**; it does not call it a signature, an attestation, or proof of
authorship. It is a hash of bytes a trusted party transported — choreography, not cryptography.

### Step 0 — Re-read before editing (BEFORE any write)

The facts above have a shelf life. Re-run and read the output; do not take the strings from this
plan. All read-only:

```
git log -1 --format='%H %s'
sed -n '1,14p' README.md
sed -n '19,22p;55,62p' PROJECT_CONTEXT.md
grep -niE 'archive|verifier-report|sidecar|sha256|--force|check_verdict|record_verify|sdd\.py|verdict|bind|bound|READY|Override|packet|pipeline|changes/|cmd_archive' \
  README.md PROJECT_CONTEXT.md sdd-plus/security/scope-contract.yml
sed -n '27,30p' scripts/sdd.py
sed -n '773,807p' scripts/sdd.py
```

Confirm, all six:

1. HEAD is still `93c2959…` (or, if the Owner has moved it, that the quoted lines still read as F1
   and F3/F4 say).
2. `README.md` still has zero hits among the seventeen terms. **If README has gained an archive
   sentence since plan time, STOP and tell the Owner** — do not write a second, possibly
   contradictory one.
3. `PROJECT_CONTEXT.md:21` and `:60` still read verbatim as F3 and F4.
4. `scope-contract.yml` still returns exactly the seven hits listed in F6.3, and its only `archive`
   hit is still `:87` `rollback_or_disable_path`. **If a new line about `sdd.py archive` has appeared
   there, apply the §Decision reversal condition** — edit that line, and record it.
5. `scripts/sdd.py:27-29` still reads `verifier-report.md` / `verifier-report.sha256` /
   `("VERIFIED", "VERIFIED WITH NOTES")`. **If any of those three constants has changed, STOP** —
   the docs would be advertising a filename or verdict string that no longer exists. Do not adapt
   the prose to a gate that moved without an Owner decision.
6. `cmd_archive` still ends in `shutil.move(str(change_dir), str(target))` (`:806`), moving
   `sdd-plus/changes/<name>` to `sdd-plus/archive/<date>-<name>`. **If that is no longer what
   archiving does, STOP** — §Definition, and therefore both paste strings, would be describing a
   command that changed.

Then re-prove the live claim rather than trusting F8/F9:

```
cd sdd-plus/archive/2026-09-02-grok-archive-bound-verdict && sha256sum -c <(printf '%s  verifier-report.md\n' "$(cat verifier-report.sha256)") ; cd -
grep -c '^## Override' sdd-plus/archive/2026-09-02-grok-archive-bound-verdict/decision-log.md
```

Expect `verifier-report.md: OK` and `0`. If either fails, the README claim in Step 1 is false as
written — **STOP and tell the Owner**; do not soften the sentence to make it survive.

### Step 1 — `README.md`: append one paragraph after line 13

Do not restructure the file, do not touch `:1-13`, and do not restate the ledger, pin, or
client/LOQ sentences. Append a blank line then, **verbatim** (copy, do not paraphrase):

```
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
```

Two wordings are load-bearing and must not be edited while pasting: **"first done live in `f799ddc`
(PR #21), a historical note … rather than a pin"** — not "first archive without `--force`", which
F10 shows is false, and not a claim that anything binds to that commit (F10a) — and **"is transport,
not archiving"**, which is the literal phrase Step 4e greps for in both files.

### Step 2 — `PROJECT_CONTEXT.md`: Desired Outcome (`:21`)

Leave `:21` **byte-identical** — it is an accurate description of the pipeline as far as it goes, it
ends at "Daniel archives" which stays true under §Definition, and rewriting the arrow chain invites
drift. Add a blank line and one paragraph immediately after it, **verbatim**:

```
The last hop can be a bound archive, live since 2026-09-02, and the roles split on the command.
**Archiving** is running `python3 scripts/sdd.py archive <name>` — the step that moves a packet out
of `sdd-plus/changes/` into `sdd-plus/archive/` — and Daniel runs it. **Transport** is copying
in-channel bytes into the live packet directory without running that command: Grok copies the
verifier report verbatim to `<packet>/verifier-report.md`, `python3 scripts/check_verdict.py
<report> <hex> "VERIFIED WITH NOTES"` exits 0, and Grok writes that same hex to
`<packet>/verifier-report.sha256`. Writing the report and the sidecar
**is transport, not archiving**, so Grok does both and still never archives. Then Daniel runs
`python3 scripts/sdd.py archive <name>` with no `--force` and no `## Override` — first done live in
`f799ddc` (PR #21), a historical note rather than a pin. A bound report is
**sufficient, never necessary** — a packet that ticks its boxes and fills its Result archives
exactly as before, and `--force --reason "<why>"` stays the Owner override when the verdict is
unbound.
```

Do not touch Short Description (`:9`), First Useful Version (`:25`), Stack And Tools (`:29-46`),
Data And Integrations (`:50-53`), Definition Of Done (`:65`), or the Durable Decisions table
(`:69-73`) — OQ-3 default is no new row.

### Step 3 — `PROJECT_CONTEXT.md`: Constraints (`:60`)

Replace the single line

```
- Grok (choreographer) transports, never audits, never archives, never implements.
```

with, **verbatim**:

```
- Grok (choreographer) transports, never audits, never archives, never implements. Archiving is
  running `python3 scripts/sdd.py archive` — the step that moves a packet out of `sdd-plus/changes/`
  into `sdd-plus/archive/` — and Daniel runs it. Transport is copying in-channel bytes into the live
  packet directory without running that command, so writing `<packet>/verifier-report.md` and
  `<packet>/verifier-report.sha256` is transport, not archiving, and Grok does it.
```

The clause **narrows nothing and grants nothing new**: it supplies the rule (`§Definition`) that
tells a reader which side of the existing boundary the sidecar write falls on. `never archives`
must survive verbatim in the line; Step 4b greps for it. Leave the other five Constraints bullets
(`:57`, `:58`, `:59`, `:61`) byte-identical.

### Step 4 — Post-edit honesty checks (BEFORE filling `verification.md`)

All six checks are **read-only**. None runs pytest, none runs `start_probe.py`, none writes to
`.git/hooks`, none needs a clean worktree, and none can fail for a reason unrelated to this change
— which is why no fallback is specified (Codex concern 2, and the "no fallback for dirty state"
gap).

**4a — both documents state all the claims.** Every term below must hit in both files:

```
for f in README.md PROJECT_CONTEXT.md; do
  for t in verifier-report.md verifier-report.sha256 check_verdict.py "VERIFIED WITH NOTES" \
           "sdd.py archive" "--force" "sufficient, never necessary"; do
    grep -qF -e "$t" -- "$f" || echo "MISSING [$t] in $f"
  done
done
```

Expect **no output**. Note `grep -qF -e "$t" -- "$f"`: the `-e` and `--` are required, because
without them `grep` parses the `--force` term as an option and the check silently errors instead of
testing. Any `MISSING` line means the two documents disagree about the contract — fix it before
recording a Result.

**4b — nothing was weakened.** All three must return a hit:

```
grep -nF 'never archives' PROJECT_CONTEXT.md
grep -nF 'Do not copy client or LOQ files here.' README.md
grep -nF 'must not be vendored or run here.' README.md
```

**4c — the advertised strings match the code they advertise.** The docs must not name a filename or
verdict the gate does not use:

```
grep -nE 'VERIFIER_REPORT|VERIFIER_SHA|BOUND_VERDICTS' scripts/sdd.py
```

Read `:27-29` and confirm `verifier-report.md`, `verifier-report.sha256`, `VERIFIED`,
`VERIFIED WITH NOTES` are exactly the strings written into the two documents. A mismatch is a
documentation bug, not a code bug — fix the prose, never `scripts/sdd.py`. **Read only.**

**4d — nothing else moved.**

```
git status --short
git diff -- README.md PROJECT_CONTEXT.md
git diff --stat
```

The diff must touch `README.md` and `PROJECT_CONTEXT.md` only. `git status` may additionally show
the untracked packet directory `sdd-plus/changes/grok-docs-bound-archive/`. **Any change under
`scripts/`, `tests/`, `kernel/`, `hooks/`, `.github/`, `sdd-plus/archive/`,
`sdd-plus/security/`, or `drydock-pins.json` means the change has drifted — revert it with
`git checkout -- <path>` and re-check.**

**4e — the transport/archive definition landed in both documents** (replaces round-1's pytest +
`start_probe.py` step; Codex concern 2). This is the check that actually proves the semantics fix:

```
for f in README.md PROJECT_CONTEXT.md; do
  for t in "sdd.py archive" "sdd-plus/changes/" "live packet directory" \
           "is transport, not archiving" "Daniel runs it"; do
    grep -qF -e "$t" -- "$f" || echo "DEF-MISSING [$t] in $f"
  done
done
grep -nF 'is transport, not archiving' README.md PROJECT_CONTEXT.md
grep -nF 'never archives' PROJECT_CONTEXT.md
```

Expect no `DEF-MISSING` line; expect `is transport, not archiving` to hit **twice in
`PROJECT_CONTEXT.md`** (the `:21` paragraph and the `:60` clause) and **once in `README.md`**; expect
`never archives` to still hit. A `DEF-MISSING` line means a document names the sidecar write without
naming the command that counts as archiving — the exact self-contradiction Codex flagged. Fix the
prose before recording a Result.

**4f — only if the §Decision reversal condition fired and the yaml was edited:**

```
python3 -c "import sys,yaml; yaml.safe_load(open('sdd-plus/security/scope-contract.yml')); print('yaml ok')"
git diff -- sdd-plus/security/scope-contract.yml
```

Confirm it parses and that `rollback_or_disable_path` (`:87`) is byte-identical in the diff.
**If `packet_guard` denies the yaml write: STOP and tell the Owner.** Do not skip the file, do not
land a partial change, and do not route around the hook with shell redirection, `python -c`,
`sed -i`, or any other write path.

### Step 5 — Record the packet (still no commit)

Fill in, in this order. Line-level shape is specified so "paste output and set the Result" is not
the whole instruction (Codex gap):

1. `decision-log.md` — replace the single template `TBD` row (`:11`) with **three** rows in the
   existing four-column table (`| Date | Decision | Reason | Alternatives Considered |`), dated
   `2026-09-02`, one line each, no new columns and no new headings:
   (a) *README and PROJECT_CONTEXT edited, `scope-contract.yml` deliberately not* — reason cites
   F6.1 (`related_gates:8-11` = LGF Gate 0/1/11, not packet lifecycle) and F6.3 (seven hits, none
   pipeline wording); alternative considered: add a governance line to the yaml, rejected as
   shoehorning.
   (b) *`PROJECT_CONTEXT.md:60` gains the transport/archive definition rather than staying
   byte-identical* (brief OQ-2) — reason cites §Definition and `scripts/sdd.py:773-807`, `:806`;
   alternative: leave `:60` alone, rejected because the ban and its scope must be readable in one
   place.
   (c) *No pytest and no `start_probe.py` in this packet's validation* — reason cites F14 (no test
   asserts this prose) and `scripts/start_probe.py:1-6` (installs into `.git/hooks`); alternative:
   run the suite for reassurance, rejected as unrelated signal plus mutation risk.
   Add a fourth row **only** if Step 0 turned up something new (e.g. the yaml reversal fired).
2. `tasks.md` — tick the boxes that were actually done. The sketch is below; the implement turn
   replaces the five template lines with those six, keeps the `- [x] ` / `- [ ] ` markdown form and
   the `## Implementation` heading, and ticks a box only after that step's commands have run.
   **Do not tick anything in the planning turn.**
3. `verification.md` — under `## Automated Checks` replace the `- [ ] TBD` line with one ticked
   bullet per Step 4 check (`4a`…`4e`, plus `4f` only if it fired), each followed by an indented
   fenced block holding that command's **actual pasted output** (for the "expect no output" checks,
   paste the empty result and say so). Under `## Manual Checks`, one ticked bullet for the Step 0
   re-read and one for the Step 1–3 paste fidelity. Under `## Documentation Updates`, tick the
   README and project-context lines and leave the "no documentation update needed" line unticked.
   Then replace `Pending.` under `## Result` with the outcome. Do not set a Result while any `4a`
   `MISSING` or `4e` `DEF-MISSING` line is outstanding.

Then **stop**. No commit, no push, no PR, no `sdd.py archive`, no `sdd.py --record-verify`, no
`record_verify_bound.py`, no `negotiate.py`, no Codex. The Owner decides when to commit. The
verifier subagent is the Owner's call, not the implementer's, and the implementer's own report is
evidence, never verification.

### `tasks.md` sketch (for the implement turn — NOT written in this turn)

- [ ] Step 0: re-read README, PROJECT_CONTEXT, scope-contract, `sdd.py:27-29` and `cmd_archive`
      `:773-807`; re-prove the sidecar hash and the zero-`## Override` count.
- [ ] Step 1: append the bound-archive paragraph to `README.md`.
- [ ] Step 2: add the bound-archive paragraph after `PROJECT_CONTEXT.md:21`.
- [ ] Step 3: extend `PROJECT_CONTEXT.md:60` with the transport/archive definition clause.
- [ ] Step 4: run the read-only checks 4a–4e (and 4f only if the yaml was edited); paste output into
      `verification.md`. **No pytest, no `start_probe.py`.**
- [ ] Step 5: fill `decision-log.md`, tick these boxes, record the Result. Stop before commit.

## Tests

**No new pytest, no test file edited, and no pytest run as part of this packet's validation.**
Justification, not assumption:

- F14 — nothing under `tests/` asserts any sentence in `README.md`, `PROJECT_CONTEXT.md`, or
  `scope-contract.yml`. The only case-insensitive hits are a `readme.txt` **fixture** created inside
  a throwaway git repo at `tests/test_pre_commit_tree.py:32-33`. So a green suite is not evidence
  about this change, and a red suite would be evidence about something else — Codex blocking
  concern 2.
- `tests/test_sdd_archive_bound_verdict.py:283-297` is the only test that reads repo files by path.
  It globs `sdd-plus/archive/*/tasks.md`; a docs edit does not change that set, and a live packet
  under `sdd-plus/changes/` is outside its glob. (Its inventory will need a row **when this packet
  is eventually archived** — that is the archive turn's obligation, not this packet's, and archiving
  is out of scope here.)
- Precedent: `grok-docs-coplan-runtime` made the same finding and added no pytest
  (`archive/2026-09-01-grok-docs-coplan-runtime/plan.md:197-201`).
- A pytest asserting prose in `README.md` would freeze editorial wording behind a red test for no
  correctness gain. The honesty this packet needs is *the docs match the code*, and Step 4c checks
  exactly that against `scripts/sdd.py:27-29` — the strings the docs advertise.
- `scripts/start_probe.py` is **not run either**. Its own docstring (`:1-6`) says it *"Installs
  backstops/pre-push into .git/hooks if missing or drifted"* — a mutation, in a docs-only packet,
  that validates nothing about the prose.

How the docs stay honest instead — five read-only checks, no mutation, no unrelated failure modes:
Step 4a (both documents carry all the claims), 4b (nothing weakened — `never archives` survives),
4c (advertised strings equal the constants in `sdd.py`), 4d (no drift outside the named docs), and
4e (the transport/archive definition landed in both files).

**Reversal condition:** if Step 0 or Step 4 turns up a test that *does* assert the old wording,
update **that one test** in the same implement commit and record it in `decision-log.md`. Do not add
a second test, and do not broaden the change.

Explicitly not tested, because it must not be built: there is **no producer-pipeline test**. No test
or verification command plants `verifier-report.md` or `verifier-report.sha256` in the live
`sdd-plus/changes/grok-docs-bound-archive/` "to see the gate fire" — the live packet stays unbound
(archived must_not_do 15).

## Files Expected To Change

| File | Change | Lines |
| --- | --- | --- |
| `README.md` | Append one paragraph carrying the transport/archive definition, the bound-sidecar path, sufficient-not-necessary, the `--force` override, and the choreography producer | +1 blank +~14 after `:13` |
| `PROJECT_CONTEXT.md` | Add one paragraph after Desired Outcome `:21`; extend the Constraints line `:60` with the transport/archive definition clause | +1 blank +~11 after `:21`; `:60` (edit, `never archives` retained) |
| `sdd-plus/changes/grok-docs-bound-archive/tasks.md` | Replace the five template lines with the six sketch lines and tick what was done (implement turn only) | — |
| `sdd-plus/changes/grok-docs-bound-archive/verification.md` | Record the Step 4 read-only evidence per §Step 5.3 and set the Result (implement turn only) | — |
| `sdd-plus/changes/grok-docs-bound-archive/decision-log.md` | Replace the template TBD row `:11` with the three §Step 5.1 rows (implement turn only) | — |

**Explicitly NOT changed** — a diff touching any of these means the change has drifted:

- `sdd-plus/security/scope-contract.yml` — F6 / §Decision; edited only under the stated reversal
  condition, and never `:87`.
- `scripts/sdd.py` — read at `:27-29`, `:322-329`, `:344-411`, `:499-500`, `:626-632`, `:669-678`,
  `:773-807`. **Read only.** The gate shipped; this packet describes it.
- `scripts/check_verdict.py`, `scripts/record_verify_bound.py`, `scripts/conductor/*`.
- `scripts/start_probe.py` — **not edited and not run**, in either turn (F14, its docstring `:1-6`).
- `tests/*` (F14) — not edited **and not executed** as this packet's validation.
- `kernel/*`, `hooks/*`, `.github/workflows/*`, `backstops/*`, `.git/hooks/*`.
- `drydock-pins.json` — no pinned file is edited, so no pin moves.
- `agents/verifier.md` — F13/OQ-3. The verifier still writes nothing to the tree.
- `sdd-plus/archive/**` — history, byte-identical. In particular
  `2026-09-02-grok-archive-bound-verdict/verifier-report.md` and its `.sha256` are the evidence this
  packet cites; altering either would invalidate the citation.
- `sdd-plus/changes/grok-docs-bound-archive/specs/` — no delta specs. This packet changes no
  capability behavior.

## must_not_do

1. **The leftover-hole slog is STOPPED.** Do not open, reopen, or plan work for leftover hole 1
   (`.env` write handling) or hole 4 (GitHub fast-forward `--force`) — accepted residual. Holes 2
   and 3 are archived; do not reopen them. Do not add "future work" prose about any of them to
   README, PROJECT_CONTEXT, the yaml, or this packet.
2. **Do not edit `scripts/sdd.py`.** Not one character, not a comment, not the helper text. If the
   docs and the code disagree, the docs are wrong (Step 4c).
3. **Do not change archive behavior.** No new blocker, no new waiver, no change to
   `verdict_binding`, `sidecar_digest`, `archive_readiness`, or `cmd_archive`. The gate already
   shipped in hole 3.
4. **Do not make a bound report mandatory.** Sufficient, never necessary (F12, archived
   must_not_do 8). Do not write prose that implies a packet without a sidecar can no longer archive.
5. **Do not remove, weaken, or discourage `--force` / `--reason` / `--abandon`.** `--force` remains
   the Owner override when a verdict is unbound, and the docs must say so.
6. **Do not edit `tests/`** — unless Step 0/Step 4 finds a test that asserts the old wording, in
   which case update **that one test only**, in the same implement commit, and record it.
7. **Do not touch `drydock-pins.json`, `kernel/`, `scripts/check_verdict.py`,
   `scripts/record_verify_bound.py`, `scripts/conductor/`, `hooks/`, `.github/workflows/`, or
   `scripts/start_probe.py`.** `start_probe.py` is neither edited **nor run** by this packet, in
   either turn (see must_not_do 16).
8. **Do not edit `agents/verifier.md`.** OQ-3 default is no (F13); it costs two pin records for a
   prose change, and the verifier writes nothing to the tree by design.
9. **Do not invent a producer pipeline in-repo.** No workflow job, no conductor stage, no new
   script, no `agents/verifier.md` edit to emit the sidecar. The producer is Grok choreography
   outside this tree and it already ran live (F8, F11, archived must_not_do 25). Documenting it is
   the whole point; building it is out of bounds.
10. **Do not touch `scope-contract.yml:87` `rollback_or_disable_path`.** Its "archive" means
    deleting the sandbox repo, not `sdd.py archive` (F6.2). Editing it because it matched a grep is
    the specific mistake this plan is written to prevent. And do not add a governance-lifecycle key
    anywhere else in that file to force a three-file diff (F6.5).
11. **Do not weaken `PROJECT_CONTEXT.md:60`.** `never archives` stays verbatim in the line; the
    clause supplies the rule for where the boundary sits, it does not move it (Step 4b, Step 4e).
12. **Do not overclaim.** The sidecar is a hash of transported bytes: choreography, not
    cryptography. No prose calling it a signature, an attestation, tamper-proof, or proof of
    authorship. And no "first archive without `--force`" — F10 shows that is false. The `f799ddc` /
    PR #21 citation is a historical note, never a pin (F10a).
13. **Do not plant `verifier-report.md` or `verifier-report.sha256` in the live packet** at
    `sdd-plus/changes/grok-docs-bound-archive/`, in tests, or in verification commands. This packet
    stays unbound.
14. **Never mint a verify-run or ledger event.** No `--record-verify` in any form, no
    `scripts/record_verify_bound.py`, no `kernel/brief_complete_engine.py` invocation. The run
    ledger stays outside this tree.
15. **Never run `python3 scripts/sdd.py archive`** — nor any other `sdd.py` subcommand — against
    this or any live packet name while planning or implementing. `cmd_archive` **moves** the
    directory (`:806`).
16. **Do not run `python3 scripts/start_probe.py`, and do not run `pytest`, in either turn.**
    `start_probe.py` writes `.git/hooks` (`:1-6`) and carries a known-deny `git reset --hard`
    fixture; the suite asserts nothing about this prose (F14). This replaces round 1's
    "Step 4e implement-turn command only", which Codex correctly rejected as over-scoped.
17. **No commit, no push, no PR, no archive** — not in this planning turn and not as part of the
    implement steps either. The implementer stops after `verification.md`; the Owner decides when to
    commit. Do not `git add` the untracked packet directory.
18. **No `scripts/conductor/negotiate.py` run and no Codex call**, in the planning turn or the
    implement turn. Round 2 is the final planning round; negotiation is closed.
19. **Never `--dangerously-skip-permissions`, never `git config`, never force-push, never
    `git reset --hard`.**
20. **No client trees, no LOQ files, no migration or backfill** of archived packets' sidecars, and
    no completeness-CLI kill. None of it is in this packet.
21. **Do not tick a box or fill a Result in the planning turn.** `tasks.md` stays unchecked,
    `verification.md` Result stays `Pending.` until Step 5 of the implement turn.
22. **Do not mark anything verified on the implementer's own authority.** Implementer evidence is
    evidence, not verification — a docs packet that advertises the verification gate is exactly the
    wrong place to blur that.
23. **Do not opportunistically refactor or reformat** `README.md` or `PROJECT_CONTEXT.md`. Append
    and one line-edit only; no reflowing, no heading changes, no reordering.
24. **Do not paraphrase or re-wrap the Step 1–3 paste strings.** They are copied verbatim; the
    phrases "is transport, not archiving", "sufficient, never necessary" and the `f799ddc`
    historical-note clause are what Step 4a/4e check for and what settles Codex concern 1. **The
    line breaks are load-bearing**: every checked phrase is deliberately kept on a single line
    because `grep -F` does not match across a newline. Re-flowing a paragraph can split a phrase and
    turn a passing check into a false `MISSING` / `DEF-MISSING` — or, worse, hide a real omission.
    If a line must be re-wrapped, re-wrap *around* the checked phrases, never through them.

## Risks

- **Reader still sees a contradiction (Codex concern 1, residual).** A skim of "Grok writes the
  sidecar" next to `never archives` could still read as conflict if the definition is dropped in
  editing. Mitigation: §Definition is written into **both** shipped paragraphs and the `:60` clause,
  each naming `sdd.py archive` as the archiving act and the live packet directory as transport's
  target; Step 4e fails loudly with `DEF-MISSING` if any of that is missing from either file;
  must_not_do 24 forbids paraphrasing the strings.
- **Over-claiming cryptography.** Prose like "cryptographically verified archive" would misdescribe
  what shipped: the sidecar hashes bytes that a trusted choreographer transported, and nothing
  prevents a party who can write the report from also writing a matching sidecar. The gate binds
  *report bytes to a stated digest*; it does not authenticate the author. Mitigation: must_not_do 12;
  the Step 1/Step 2 strings say "binds on the verifier's own bytes" and name the choreography
  explicitly, and the archived plan's own §D.4 ("the sidecar is not a signature") is the standard
  this prose is held to.
- **Editing `scope-contract.yml:87` by accident.** It contains the word "archive" and will match any
  grep run while working. Editing it would corrupt the LGF Gate-0 rollback path — a security
  document — for a governance-workflow reason. Mitigation: F6.2 states the word-sense split within
  the full-file reading; must_not_do 10 names the line; the default is not to open the file for
  writing at all.
- **Over-widening into "bound reports are required".** A crisp new paragraph reads as the *only*
  path, and a later session could refuse to archive an honestly-completed packet that has no
  verifier report. Mitigation: both paragraphs state "sufficient, never necessary" in the same
  sentence as the new path; Step 4a greps for the literal phrase in both files; must_not_do 4. No
  third file is added to reinforce the point — that would trade one skim risk for a drift risk.
- **Stale-claim risk in the historical citation.** "first done live in `f799ddc` (PR #21)" is a fact
  about a specific commit; if someone rewrites that history the sentence goes stale silently, and no
  test guards it (deliberately, per §Tests). Mitigation: F10a makes the citation explicitly a
  historical note rather than a pin, and the shipped sentence says so, so a stale citation degrades
  to a wrong anecdote and never to a broken gate; Step 0 re-proves the sidecar hash and the
  zero-`## Override` count before the sentence is written; F10's precision (first *bound* archive,
  not first without `--force`) keeps it true of the corpus as it grows.
- **Leftover-slog creep.** A docs packet that touches README is a magnet for "while we're here" —
  the `.env` hole, the FF `--force` hole, a Durable Decisions row, a scope-contract tidy.
  Mitigation: must_not_do 1 and 20, OQ-3's no-new-row default, and Step 4d's drift check.
- **Under-fixing by editing only one file.** README alone leaves `PROJECT_CONTEXT.md:21` describing
  a pipeline that stops short and `:60` still readable as a ban on the sidecar write; PROJECT_CONTEXT
  alone leaves the first-read file silent. Mitigation: both or neither (see §Rollback); Steps 4a and
  4e fail loudly if only one document carries the claims or the definition.
- **Prose does not enforce.** This packet moves no mechanism. A session that ignores the docs can
  still reach for `--force`; that is a missed benefit, not a hole, because `--force` requires
  `--reason` and records an `## Override`. Accepted for LITE. If the Owner wants enforcement, that
  is a separate packet.
- **Documenting a gate that moves under the docs.** If `VERIFIER_SHA`, `BOUND_VERDICTS`, or
  `cmd_archive`'s move semantics ever change, these paragraphs become wrong with nothing to catch
  it. Mitigation: Step 0 checks 5 and 6 and Step 4c compare the prose against `scripts/sdd.py:27-29`
  and `:773-807` at edit time; a mismatch STOPs rather than being papered over.

## Rollback

Doc-only and fully reversible. No runtime state, no schema, no pins, no deployed surface, no
behavior — reverting restores docs that are silent/incomplete about the archive path, which is the
current state, not a broken one. Nothing in Steps 0–5 mutates anything outside the two docs and the
packet directory, so there is no hook, `.git/`, or cache state to unwind.

- Before commit: `git checkout -- README.md PROJECT_CONTEXT.md` (add
  `sdd-plus/security/scope-contract.yml` only if the reversal condition fired and it was edited).
- After commit on a packet branch: `git revert <sha>`, or abandon the branch without merging.
  **Never `reset --hard`, never force-push** — the git-safety hook blocks both and the Owner has not
  authorized either.
- **All or none.** Reverting one document and keeping the other is not a valid state: it leaves
  README and PROJECT_CONTEXT making different claims about who may write the sidecar, whether it is
  required, and which command counts as archiving. Roll back both together.
- The packet directory `sdd-plus/changes/grok-docs-bound-archive/` is untracked; removing it is the
  Owner's call and is not part of a code rollback.
