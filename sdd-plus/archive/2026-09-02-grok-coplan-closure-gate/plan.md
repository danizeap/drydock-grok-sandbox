# Plan

## Change

grok-coplan-closure-gate

## Mode

LITE. One production file (`scripts/start_probe.py`), one new test file
(`tests/test_start_probe_conductor_closure.py`), one pin value in `drydock-pins.json`, and one
added stub line in `tests/test_start_probe_discover.py`. No contract change to the vendored
conductor, no schema, no auth, no migration, no workflow edit.

**Round 2 of 2 (final)** of coplan negotiation. Round 1 did not converge (three blocking
concerns). This revision is the Pilot's own audit of those concerns — §0 — not an acceptance of
them. Two were partially accepted with code changes, one was partially accepted with a scope
change; the residual judgment calls are Owner policy, recorded as OQ-1..OQ-3 below and in
`brief.md`. Each Open Question has a **stated default consistent with Owner intent**, so none of
them blocks implementation: round 2 can converge on the defaults, and any Owner answer is a
costed delta, not a redesign.

## 0. Round-2 audit of the Codex round-1 critique

Codex's round-1 critique is input, not instruction. Each blocking concern was checked against the
repo. Verdicts are recorded as rows in `decision-log.md`; the reasoning and the evidence are here.

### Inventory run for this audit (answers BC-2 and gap 1 with facts)

Run on `main` at `b421962`, this VM, before any edit:

```
$ git ls-files | wc -l
118

$ git ls-files | awk -F/ '{n=$NF; split(n,a,"."); \
    if (a[1]=="mutate"||a[1]=="coord"||a[1]=="executors"||a[1]=="handoff") print}'
(no output)

$ git ls-files | grep -Ei 'mutate|coord|executor|handoff'
(no output)                 # not even as a substring anywhere in any tracked path

$ find . -path ./.git -prune -o -type f -print | awk -F/ '{n=$NF; split(n,a,"."); \
    if (a[1]=="mutate"||a[1]=="coord"||a[1]=="executors"||a[1]=="handoff") print}'
(no output)                 # untracked included; whole worktree except .git

$ git ls-files --others --exclude-standard scripts/conductor/
(no output)                 # no *non-ignored* untracked file under the conductor dir

$ git ls-files --others scripts/conductor/
scripts/conductor/__pycache__/__init__.cpython-313.pyc
scripts/conductor/__pycache__/codex_bridge.cpython-313.pyc
scripts/conductor/__pycache__/review.cpython-313.pyc
                            # ...and all three are ignored by .gitignore (`__pycache__/`, `*.pyc`)
```

All 32 distinct tracked `*.py` basenames were also listed; none is a banned stem, and none is a
near-miss. **Conclusion: the repo-wide tracked-basename ban has zero collisions today**, and the
stricter "no non-ignored untracked file under `scripts/conductor/`" rule would also pass today at
zero cost. Both facts change the shape of the answers below.

### BC-1 — "The plan does not actually implement a closure gate." → **PARTIAL**

Accepted as a *naming and framing* defect, rejected as a *design* defect.

Codex is right that round 1 used the word "closure" for something that permits untracked
accretion. That was overclaiming, and it is fixed: §2 now states the predicate as
**tracked-set closure plus on-disk presence ban**, and says in one line what is not closed.

Rejected: the implied remedy of failing on *every* untracked file. The Owner's intent is
"the `scripts/conductor` **tracked** set is exactly the six pinned files, and none of the four
**exist** under `scripts/conductor/`". Failing on every untracked file is a different, wider
requirement, and round 1 was right that a naive version fights `__pycache__`.

What the audit *did* find is that Codex's objection has a cheap, git-native answer that round 1
missed: `git ls-files --others --exclude-standard` returns exactly the untracked files git is not
already told to ignore — and it returns **nothing** under `scripts/conductor/` today. That turns
the ad hoc `__pycache__` carve-out (gap 2) into a declarative rule the repo already owns. It is
still a widening of the Owner's stated predicate, so it is **OQ-1**, not a silent adoption.

### BC-2 — "Repo-wide banned-stem matching is not proven safe." → **ACCEPTED (evidence now supplied)**

The complaint was procedural and correct: round 1 asserted safety without showing the scan. The
scan is above. Result: **0 collisions** across 118 tracked files, and 0 across the entire worktree
excluding `.git` — not one file whose name even *contains* `mutate`, `coord`, `executor`, or
`handoff`. Repo-wide tracked-only matching is therefore viable today, and the check cannot
false-fail on the current tree.

What the scan cannot settle is whether the Owner wants four basenames reserved repo-wide
*forever*. That is policy, not fact → **OQ-3**. The default keeps repo-wide matching (the docs'
ban is "not vendored or run **here**", i.e. this repo), and §3 states the exact one-branch
deletion that narrows it to directory-scope if the Owner says otherwise.

### BC-3 — "Filename-only detection is too easy to evade." → **PARTIAL**

Accepted for the one sub-case that is real and cheap to close; rejected for the rest, on threat
model.

- **Accepted:** the extensionless-file gap. An untracked `scripts/conductor/mutate` (no suffix)
  passed round 1's presence scan because of the `.py`/`.pyc` suffix filter. Fixed in §1:
  the presence scan now also matches a banned stem with **no extension at all**. Three lines. The
  repo-wide *tracked* branch deliberately keeps the suffix filter (see §3).
- **Rejected for this packet:** content hashing / semantic detection of "mutating code under a
  different name". Two reasons, and neither is laziness. First, **the rename-inside-the-directory
  case is already closed by other means**: any tracked file under `scripts/conductor/` that is not
  one of the six fails the closure branch *whatever it is named*, and the six themselves are
  sha256-pinned by `check_pins()` (`scripts/start_probe.py:64-68`), so mutating code cannot be
  smuggled *into* `negotiate.py` either. The only tracked-code path Codex's argument really leaves
  open is a renamed module committed **outside** `scripts/conductor/` — e.g. `scripts/orchestrate.py`
  — and no filename rule, hash pin, or heuristic can catch arbitrary future code by content. That
  is a code-review and packet-governance problem, not a probe problem.
- **Threat model, stated so it stops being implicit:** this gate defends against *drift and
  accidental vendoring* — a seventh conductor file landing during a future packet, or the mutating
  four being copied in "just to look at them". It does **not** claim to defeat a determined
  operator with write access to the worktree, who can already run anything. A gate that is honest
  about its scope is worth more than one that pretends to be an anti-exfiltration control.

Content-based or capability-based detection is recorded as **OQ-2** — deliberately out of this
LITE packet.

### Gaps and risks (input, not orders — dispositions)

| Codex item | Disposition |
| --- | --- |
| gap 1 — unshown inventory | **Accepted.** Scan above; recorded in `decision-log.md`. |
| gap 2 — `__pycache__` carve-out is ad hoc | **Accepted as a framing fix.** There is in fact *no* `__pycache__` carve-out in the code: the check simply never enumerates untracked files except to look for the four banned stems — and it *does* fail on `__pycache__/coord.cpython-313.pyc`. §2 now says that as a rule instead of an exception, and the misleadingly-named test is renamed. |
| gap 3 / risk 3 — live-tree canary flakiness | **Partial.** Kept, because under the default policy it can only fire if someone actually vendors a seventh *tracked* file or plants a banned stem — neither is developer noise. `PYTHONDONTWRITEBYTECODE=1` is belt-and-braces, not the mechanism. Under OQ-1's strict variant the canary *would* become sensitive to dev scratch; that cost is stated in OQ-1. |
| risk 1 — git subprocess in the probe | **Rejected as blocking, mitigation kept.** The probe already hard-requires `.git` (`scripts/start_probe.py:139`) and `subprocess` is already imported (`scripts/start_probe.py:11`). `_tracked_files` fails closed, and `test_git_failure_fails_closed` holds that. A git hiccup blocking the probe is the *correct* direction for a fail-closed gate. |
| risk 2 — test matrix large and partly redundant | **Accepted.** §5 is consolidated from 16 test functions to 13, by merging the four separate banned-name tests into one parametrized presence test. Coverage is not reduced — it grows, via the new extensionless and benign-suffix cases. |

### Codex's decomposition

Not adopted as a work split. This is a LITE packet in one file plus one test file; the five-way
owner/tier assignment is heavier than the change. Its first item — "decide the exact policy" — is
the one that mattered, and it is answered above and in OQ-1..OQ-3.

## Load-bearing facts, checked on disk

1. **`check_pins()` cannot see extra files.** `scripts/start_probe.py:53-69` loads
   `drydock-pins.json`, takes `pins["files"]`, and iterates `for rel, expected in files.items()`.
   Every branch inside that loop is about a *pinned* path: missing file (line 63-65) or hash
   drift (line 66-68). Nothing enumerates the contents of any directory. Therefore an unpinned
   `scripts/conductor/mutate.py` is invisible to `check_pins()` by construction — not by
   oversight in the data, but because the pins map is the loop's only input. This is the hole.

2. **The pinned six, verbatim** (`drydock-pins.json:26-31`):
   `scripts/conductor/__init__.py`, `scripts/conductor/codex_bridge.py`,
   `scripts/conductor/negotiate.py`, `scripts/conductor/negotiate_schema.json`,
   `scripts/conductor/review.py`, `scripts/conductor/review_schema.json`.
   `git ls-files scripts/conductor/` returns exactly those six today. `ls scripts/conductor/`
   returns those six **plus `__pycache__/`** (holding `__init__.cpython-313.pyc`,
   `codex_bridge.cpython-313.pyc`, `review.cpython-313.pyc`) — untracked noise that any
   filesystem-only closure check would false-positive on. That asymmetry is the whole reason the
   design uses two instruments (see Approach §2). Note for OQ-1: all three are **ignored** by
   `.gitignore` (`__pycache__/`, `*.pyc`), so `git ls-files --others --exclude-standard
   scripts/conductor/` is empty — git already knows which of them is noise.

3. **`start_probe` already requires `.git`.** `scripts/start_probe.py:139-140` returns
   `missing .git; cannot install {name}` from `ensure_backstop_hook`. So the probe already fails
   closed without a git checkout; depending on `git ls-files` adds no new environmental
   assumption. CI checks out with `actions/checkout` before `.github/workflows/drydock.yml:24`
   runs the probe. `git version 2.47.3` on this VM.

4. **There is a kwargs-seam precedent.** `check_discover(**kwargs)`
   (`scripts/start_probe.py:191-215`) exists so tests can substitute the entire search input
   without touching the live tree. The new check follows that shape with explicit parameters
   (`root`, `tracked`) rather than inventing a new idiom.

5. **`main()`'s shape** (`scripts/start_probe.py:218-242`): each check contributes one term to
   the `errors` sum (lines 225-226) and one key to `result` (lines 227-237), in check order.
   `ok` is `not errors` (line 228). `hook_evidence` is last.

6. **Nothing else is a machine consumer of this JSON.** `.github/workflows/drydock.yml:24`
   consumes the **exit code** only. `scripts/check_secret_tree.py` does not use git and knows
   nothing about the conductor. So an additive key is safe.

7. **`hooks/packet_guard.py` is not, and cannot be, this gate.** Its deny classes are exactly
   schema migrations / new CI config / container config (`hooks/packet_guard.py:105-128`); its
   documented fail direction is silent-allow on any error (`hooks/packet_guard.py:16`); it is a
   Claude Code PreToolUse hook, and Grok Shell does not run it. It governs write attempts, not
   tree state. Not edited by this packet.

## Approach

### 1. New function `check_conductor_closure()` in `scripts/start_probe.py`

Placed after `check_pins()` (the check it completes), before `check_hooks()`.

```python
CONDUCTOR_DIR = "scripts/conductor"

# The read-only coplan closure: exactly these files may be tracked under scripts/conductor/.
# Hardcoded on purpose -- see decision-log. test_allowlist_matches_pins keeps it in step with
# drydock-pins.json, so drift between the two is a test failure, not a silent widening.
CONDUCTOR_ALLOWED = frozenset({
    "__init__.py", "codex_bridge.py", "negotiate.py",
    "negotiate_schema.json", "review.py", "review_schema.json",
})

# Mutating conductor: must not be vendored or run here (README.md:10-13,
# PROJECT_CONTEXT.md:42-43, sdd-plus/security/scope-contract.yml:35,85).
BANNED_STEMS = frozenset({"mutate", "coord", "executors", "handoff"})
BANNED_SUFFIXES = (".py", ".pyc")


def _tracked_files(root: Path) -> tuple[list[str], list[str]]:
    """(repo-relative tracked paths, errors). Fails closed: git problems are errors."""
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(root), capture_output=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return [], [f"cannot list tracked files: {e}"]
    if proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", errors="replace").strip().splitlines()
        return [], [f"cannot list tracked files: git ls-files exit {proc.returncode}"
                    f"{': ' + tail[-1] if tail else ''}"]
    out = proc.stdout.decode("utf-8", errors="replace")
    return [p for p in out.split("\0") if p], []


def _is_banned_name(name: str, *, allow_extensionless: bool = False) -> bool:
    """mutate.py / coord.pyc / handoff.cpython-313.pyc -- stem before the first dot.

    allow_extensionless also matches a bare `mutate` (no suffix at all). Used only by the
    on-disk scan inside scripts/conductor/, where an extensionless file is already anomalous;
    the repo-wide tracked scan keeps the suffix filter. See plan.md section 3.
    """
    stem, dot, _ = name.partition(".")
    if stem not in BANNED_STEMS:
        return False
    if not dot:
        return allow_extensionless
    return name.endswith(BANNED_SUFFIXES)


def check_conductor_closure(root: Path = ROOT, tracked: list[str] | None = None) -> list[str]:
    """The vendored coplan closure is exactly six files, and mutating conductor is absent.

    Two instruments on purpose:
      * tracked-set closure  -- git is authoritative for "what this repo vendors"
      * filesystem presence  -- an untracked mutate.py is still runnable
    """
    errors: list[str] = []
    if tracked is None:
        tracked, git_errors = _tracked_files(root)
        if git_errors:
            return git_errors                     # fail closed; do not half-check

    prefix = CONDUCTOR_DIR + "/"
    for rel in sorted(tracked):
        norm = rel.replace("\\", "/")
        name = norm.rsplit("/", 1)[-1]
        if _is_banned_name(name):
            if not norm.startswith(prefix):
                errors.append(f"mutating conductor tracked: {norm}")
            continue                              # in-dir hits belong to the presence scan
        if norm.startswith(prefix) and norm[len(prefix):] not in CONDUCTOR_ALLOWED:
            errors.append(f"unpinned file tracked under {CONDUCTOR_DIR}/: {norm}")

    conductor = root / "scripts" / "conductor"
    if conductor.is_dir():
        try:
            present = sorted(p for p in conductor.rglob("*")
                             if p.is_file()
                             and _is_banned_name(p.name, allow_extensionless=True))
        except OSError as e:
            return errors + [f"cannot scan {CONDUCTOR_DIR}/: {e}"]
        for p in present:
            errors.append("mutating conductor present: "
                          f"{p.relative_to(root).as_posix()}")
    return errors
```

Notes the implementer must not "simplify" away:

- **`continue` after a banned tracked name is the dedupe.** A tracked
  `scripts/conductor/mutate.py` would otherwise be reported three times (unpinned-extra,
  tracked-elsewhere, present-on-disk). It is reported **once**, by the presence scan, with the
  most specific message. A banned name tracked *outside* the directory is reported by the
  tracked branch, because the presence scan does not look there.
- **Missing pinned files are deliberately not reported here.** The tracked loop only ever adds
  errors for files it *sees*. A conductor file that has been deleted produces exactly one
  failure, from `check_pins()` (`scripts/start_probe.py:63-65`). Duplicating it would make one
  fault print two errors with two different vocabularies. `test_missing_pinned_file_is_not_
  reported_here` pins this.
- **The stem-before-the-first-dot rule** catches `mutate.py`, the sourceless-import vector
  `mutate.pyc` (PEP 3147 allows importing `conductor.mutate` from a bare
  `scripts/conductor/mutate.pyc`), and bytecode leftovers like `__pycache__/coord.cpython-313.pyc`
  (any interpreter tag — the match is version-agnostic). It cannot fire on `coord.json` or
  `handoff.md`, because of the suffix filter, and `test_benign_suffix_is_not_banned` pins that.
- **`allow_extensionless=True` on the on-disk scan only** (round-2 change, BC-3). A bare
  `scripts/conductor/mutate` with no suffix is runnable via `python3 scripts/conductor/mutate`
  and was missed in round 1. Inside a Python package directory an extensionless file is already
  anomalous, so the false-positive cost there is ~0. The repo-wide *tracked* branch keeps the
  suffix filter, because repo-wide an extensionless `handoff` is a plausible ordinary file
  (`backstops/pre-commit` and `backstops/pre-push` are the repo's two tracked extensionless files
  today, so the category is in use).
- **`rglob("*")`** covers hiding in a subdirectory (`scripts/conductor/sub/mutate.py`).

### 2. What exactly is asserted — the predicate, stated without overclaiming

Round 1 called this "the closure gate" while permitting untracked accretion. Codex was right that
those two things do not match (BC-1). The predicate, said precisely, is **two conjoined claims**:

> **(a) tracked-set closure** — the set of files this repo *vendors* under `scripts/conductor/`
> is exactly the six pinned ones; **and (b) an on-disk presence ban** — none of the four mutating
> names exists there at all, tracked or not.

| Question | Answer | Why |
| --- | --- | --- |
| Extra **tracked** file under `scripts/conductor/` | **fail** | "This repo vendors exactly six files" is a statement about committed contents. `git ls-files` is the authoritative answer; the filesystem is not. This also means an extra tracked file fails **whatever it is named** — the rename-evasion of BC-3 does not work inside this directory. |
| Extra **untracked**, non-mutating file there | **pass** (default; see OQ-1) | Not an exception carved out for `__pycache__` — a consequence of (a) being a claim about *vendored* contents. The check never enumerates untracked files at all except to look for the four banned stems. |
| Any of the four **on disk**, tracked or not | **fail** | The Owner's words are "none of the four may **exist** under `scripts/conductor/`". An untracked `mutate.py` is fully importable and runnable; tracking has nothing to do with the danger. Presence is the right predicate — and it *does* fire on `__pycache__/coord.cpython-313.pyc`, so bytecode is not blanket-exempt. |
| The four **tracked anywhere else** in the repo | **fail** (default; see OQ-3) | See §3. Proven collision-free by the §0 inventory. |

**The `__pycache__` rule, crisply (gap 2).** There is no `__pycache__` special case in the code.
Bytecode under `scripts/conductor/` is invisible to claim (a) because it is untracked, and is
*fully in scope* for claim (b) because the presence scan matches `coord.cpython-313.pyc`. One
rule, two consequences — not an ad hoc carve-out.

**The residual, stated plainly:** an untracked, non-mutating extra file under `scripts/conductor/`
does not fail — e.g. a hand-written `helper.py` that a developer never commits. It is invisible to
the vendoring claim and is not one of the four named dangers. Closing this is **OQ-1**; it would
cost one more `git ls-files` invocation and would pass on the current tree unchanged.

### 3. Repo-wide vs directory-scoped for the mutating four — repo-wide, tracked-only

**Chosen: repo-wide over the `git ls-files` listing, matched on basename; the *filesystem*
scan stays scoped to `scripts/conductor/`.**

Justification. The prose ban is "not vendored … here" (`README.md:12-13`), not "not vendored in
one directory". A directory-scoped-only check is evaded by committing `scripts/mutate.py` or
`kernel/coord.py` and importing it — same capability, same repo, gate silent. Making the check
repo-wide costs one string comparison per tracked file over a listing already in hand.

The filesystem half deliberately does **not** go repo-wide: an `rglob("*")` over the whole
worktree would walk `.git/`, virtualenvs, and any future `node_modules`, would be slow on every
probe run, and would fire on unrelated vendored third-party files. Scoped to
`scripts/conductor/` it is a handful of `stat` calls.

**Proven safe, not assumed safe (BC-2, round-2 change).** The §0 inventory scanned all 118 tracked
files and the whole worktree outside `.git`: **zero** files whose basename stem is one of the four,
and zero paths that even contain those substrings. The repo's 32 distinct tracked `*.py` basenames
were listed and checked by hand. So this check cannot false-fail on the tree as it stands, and
Codex's "immediate false failures" risk is disproven for today.

Accepted false-positive, *going forward*: a future *legitimate* file named `coord.py` or
`handoff.py` anywhere in this repo would fail the probe. In this sandbox those four names are
treated as a reserved namespace, and the escape hatch is an Owner decision plus an edit to
`BANNED_STEMS` — visible, not silent. Whether the Owner wants that reservation to be repo-wide at
all is **OQ-3**; it is the one place this packet exceeds the literal wording of the Owner's intent
line, and it is flagged rather than smuggled.

**Narrowing delta if the Owner answers OQ-3 "directory-scoped only":** delete the
`if not norm.startswith(prefix): errors.append(...)` branch inside the tracked loop (the `continue`
stays, as the dedupe), delete `test_tracked_mutating_file_outside_conductor_fails`, and drop the
matching acceptance-criterion line in `brief.md`. Three deletions, no redesign. No feature flag is
added to production code for this — a dead config switch is worse than a three-line edit.

### 4. Wire into `main()`

Three lines, in check order (fact 5), immediately after the `check_pins()` call:

```python
pin_errors = check_pins()
conductor_errors = check_conductor_closure()
hook_errors, evidence = check_hooks()
...
errors = (pin_errors + conductor_errors + hook_errors + secret_tree_errors
          + pre_push_errors + pre_commit_errors + discover_errors)
```

`main()` calls with no arguments — real `ROOT`, real `git ls-files`. `ok` is already
`not errors` (`scripts/start_probe.py:228`), so it flips automatically, and the existing
`START PROBE FAILED: …` stderr line (line 240) picks the message up for free.

### 5. Tests — new file `tests/test_start_probe_conductor_closure.py`

Preamble copies `tests/test_start_probe_discover.py:15-17` (`ROOT`,
`sys.path.insert(0, str(ROOT / "scripts"))`, `import start_probe`).

**Fixture-tree helper — never writes into the live tree:**

```python
SIX = ("__init__.py", "codex_bridge.py", "negotiate.py",
       "negotiate_schema.json", "review.py", "review_schema.json")


def _tree(tmp_path: Path, names=SIX) -> Path:
    """Fake conductor tree under tmp_path. Nothing here touches the real repo."""
    d = tmp_path / "scripts" / "conductor"
    d.mkdir(parents=True, exist_ok=True)
    for n in names:
        p = d / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# fixture\n", encoding="utf-8")
    return tmp_path


def _tracked(names=SIX):
    return [f"scripts/conductor/{n}" for n in names]
```

Every test passes `root=tmp_path` and an explicit `tracked=[...]` list, except the two that
exercise the git plumbing and the one live-tree canary. **No test ever creates a file named
`mutate.py`, `coord.py`, `executors.py`, or `handoff.py` inside the real
`scripts/conductor/`, or anywhere in the real repo** — every such name is written under
`tmp_path`, which pytest places outside the worktree.

Test cases. **Round-2 change (risk 2):** the four separate banned-name tests of round 1
(`test_untracked_mutating_file_on_disk_fails`, `test_each_banned_stem_is_detected`,
`test_banned_bytecode_is_detected`, `test_banned_file_in_subdirectory_fails`) are merged into one
parametrized `test_banned_name_present_on_disk_fails`. 16 test functions become 13; the number of
*cases* goes up, because the merge is where the two new BC-3 cases land.

- `test_exact_six_tracked_files_pass` — `_tree(tmp_path)`, `tracked=_tracked()`; asserts `== []`.
- `test_extra_tracked_file_fails` — `tracked=_tracked() + ["scripts/conductor/extra.py"]`;
  asserts exactly one error, containing `extra.py` and `unpinned`. Note this also covers the
  BC-3 rename case *inside* the directory: the name is irrelevant, closure is by set membership.
- `test_untracked_non_mutating_file_does_not_fail` — parametrized over
  `__pycache__/negotiate.cpython-313.pyc` (ordinary bytecode of an *allowed* module) and a plain
  `helper.py`; each written on disk with `tracked=_tracked()`; asserts `== []`. Pins the residual
  of §2 as deliberate. *(Renamed from round 1's `test_untracked_pycache_is_not_an_extra_file`,
  which implied a `__pycache__` special case that does not exist — gap 2.)*
- `test_missing_pinned_file_is_not_reported_here` — tree and `tracked` both hold five of six;
  asserts `== []`. `check_pins()` owns missing files; no duplicated failure mode.
- `test_banned_name_present_on_disk_fails` — `pytest.mark.parametrize` over relative paths, each
  written under the fake conductor dir with `tracked=_tracked()` (i.e. **untracked**); each asserts
  exactly one error naming the file. This is the "presence, not tracking" contract plus every
  banned-name variant in one place:
  `mutate.py`, `coord.py`, `executors.py`, `handoff.py` (the four stems);
  `mutate.pyc` (sourceless-import vector, directly in the dir);
  `__pycache__/coord.cpython-313.pyc` (bytecode leftover, version tag arbitrary);
  `sub/mutate.py` (pins `rglob` over `iterdir`);
  **`mutate` (extensionless — the round-2 BC-3 addition; fails without
  `allow_extensionless=True`)**.
- `test_benign_suffix_is_not_banned` — parametrized over `coord.json` and `handoff.md` written
  untracked in the fake dir; asserts `== []`. Pins the suffix filter, so the check is not a blunt
  substring match. *(New in round 2 — the negative half BC-3 made worth stating.)*
- `test_tracked_mutating_file_outside_conductor_fails` — `tracked=_tracked() +
  ["scripts/mutate.py"]`, nothing extra on disk; asserts one error containing `scripts/mutate.py`
  and `tracked`. Pins the repo-wide scope decision of §3.
- `test_banned_file_reported_once` — `mutate.py` both on disk **and** in `tracked`; asserts
  `len(errors) == 1`. Pins the dedupe.
- `test_git_failure_fails_closed` — `monkeypatch.setattr(start_probe.subprocess, "run", …)`
  returning a `returncode=128` stub (and a second case raising `OSError("no git")`); call with
  `tracked=None`; asserts a single error mentioning `git`/`cannot list tracked files`, and that
  nothing raises. A probe that cannot list tracked files must not report closure.
- `test_real_git_repo_listing_detects_an_extra_file` — integration over the git plumbing:
  `pytest.skipif(shutil.which("git") is None)`, `git init` in `tmp_path` with `-c` identity
  flags (never `git config` on the machine), write the six plus `extra.py`, `git add -A`, then
  `check_conductor_closure(root=tmp_path)` with `tracked=None`; asserts the `extra.py` error.
  Proves `-z` parsing and `cwd=root` actually work — the injected-`tracked` tests cannot.
- `test_live_tree_is_closed` — `assert start_probe.check_conductor_closure() == []` against the
  real `ROOT`. Read-only regression canary: if anyone vendors a seventh conductor file, this
  fails in CI even before the probe step is read. **Kept despite Codex risk 3**, because under the
  default policy it cannot fire on developer noise: untracked non-mutating files are out of scope
  by construction (§2), and the only bytecode that can trip it is bytecode of a *banned* module,
  which cannot exist unless a banned module did. Verified green against the live tree in the §0
  inventory. If the Owner adopts OQ-1, revisit — the strict variant does make this canary
  sensitive to uncommitted scratch.
- `test_allowlist_matches_pins` — loads `drydock-pins.json`, derives
  `{k.split("/")[-1] for k in pins["files"] if k.startswith("scripts/conductor/")}`, asserts
  equality with `start_probe.CONDUCTOR_ALLOWED`. Keeps the hardcoded constant honest without
  making the gate derive from the thing it is gating.
- `test_main_reports_conductor_errors_and_exits_1` — stub the other checks (same pattern as
  `tests/test_start_probe_discover.py:122-128`), `monkeypatch.setattr(start_probe,
  "check_conductor_closure", lambda: ["boom"])`; asserts `result["conductor_errors"] == ["boom"]`,
  `result["ok"] is False`, exit code 1.
- `test_main_json_contract` — all checks stubbed green; asserts `conductor_errors == []` and
  `isinstance(..., list)`, **and** that `discover_errors` is still a `list` and
  `discover_skipped` still a `str`, both present. The additive-only contract, as a test.

**One-line change to `tests/test_start_probe_discover.py`:** add
`monkeypatch.setattr(start_probe, "check_conductor_closure", lambda: [])` to `_stub_other_checks`
(`tests/test_start_probe_discover.py:122-128`). Without it, that file's two `main()` tests would
silently start depending on the live conductor tree and on git being present — they would still
pass today, for a reason they never asked about. No assertion in that file changes; nothing else
in it is touched.

### 6. Re-pin — last, in this order

`scripts/start_probe.py` is pinned at `drydock-pins.json:12`, currently
`ffcd8ec3ca42b2f7e03d9de612a8182218342cbe1147fdf0bc6f02a9815e46b1`. Strictly:

1. Finish **every** edit to `scripts/start_probe.py`.
2. `python3 -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('scripts/start_probe.py').read_bytes()).hexdigest())"`
3. Replace **that one value** on `drydock-pins.json:12`. Nothing else in the pins map changes —
   the six conductor pins (lines 26-31) are untouched, and the new test file is not pinned.
4. **Only then** run `python3 scripts/start_probe.py`.

Re-pinning before the file is final leaves the probe failing its own `check_pins()`.

### 7. Verification commands the implementer runs

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` — full suite green.
2. `python3 scripts/start_probe.py; echo $?` — expect exit 0, `"conductor_errors": []`,
   `"discover_errors": []`, `"discover_skipped": ""`, `"ok": true`.
3. Negative, without planting anything in the live tree:
   ```
   python3 -c "import sys,pathlib; sys.path.insert(0,'scripts'); import start_probe; \
   print(start_probe.check_conductor_closure(tracked=['scripts/conductor/mutate.py']))"
   ```
   expect one `mutating conductor tracked:`-class error. (`tracked=` injection is the correct
   instrument; a live-tree plant is forbidden.)
4. `git status --porcelain` — expect only the intended files; **no** `scripts/conductor/`
   entry of any kind.
5. `git ls-files scripts/conductor/ | wc -l` — expect `6`.
6. Capture 1, 2, 4, 5 verbatim in `verification.md`, then run the verifier subagent.

## Steps

1. Read `scripts/start_probe.py:53-69` and `:218-242` and confirm the two facts this plan rests
   on (pins loop cannot see extra files; `main()` sums per-check error lists).
2. Add `CONDUCTOR_DIR`, `CONDUCTOR_ALLOWED`, `BANNED_STEMS`, `BANNED_SUFFIXES` module constants
   below `PINS_PATH` (`scripts/start_probe.py:17`).
3. Add `_tracked_files()` and `_is_banned_name(name, *, allow_extensionless=False)` helpers.
4. Add `check_conductor_closure(root=ROOT, tracked=None)` after `check_pins()`. The on-disk scan
   passes `allow_extensionless=True`; the tracked scan does not.
5. Wire it into `main()`: one call after `check_pins()`, one term in the `errors` sum, one
   `conductor_errors` key immediately after `pin_errors` in `result`.
6. Write `tests/test_start_probe_conductor_closure.py` with the 13 test functions in §5, all fake
   trees under `tmp_path`.
7. Add the single `check_conductor_closure` stub line to `_stub_other_checks` in
   `tests/test_start_probe_discover.py`.
8. Run the suite (verification command 1); fix until green.
9. Re-pin `scripts/start_probe.py` per §6, in that order.
10. Run verification commands 2-5 and paste the output into `verification.md`.
11. Invoke the verifier subagent. Do not self-certify.

## Tests

13 test functions, all in `tests/test_start_probe_conductor_closure.py`, all fake trees under
`tmp_path` / injected `tracked` lists — full assertions in §5:

| Test | Asserts |
| --- | --- |
| `test_exact_six_tracked_files_pass` | clean six → `[]` |
| `test_extra_tracked_file_fails` | tracked `extra.py` → one `unpinned…` error (any name) |
| `test_untracked_non_mutating_file_does_not_fail` | untracked `__pycache__/negotiate.cpython-313.pyc`, `helper.py` → `[]` |
| `test_missing_pinned_file_is_not_reported_here` | five of six → `[]` (no duplicate of `check_pins`) |
| `test_banned_name_present_on_disk_fails` | 8 parametrized cases, all untracked on disk: four stems, `mutate.pyc`, `__pycache__/coord.cpython-313.pyc`, `sub/mutate.py`, extensionless `mutate` |
| `test_benign_suffix_is_not_banned` | untracked `coord.json`, `handoff.md` → `[]` |
| `test_tracked_mutating_file_outside_conductor_fails` | tracked `scripts/mutate.py` → fails (drop with OQ-3 narrowing) |
| `test_banned_file_reported_once` | tracked **and** on disk → exactly one error |
| `test_git_failure_fails_closed` | `rc=128` and `OSError` → error mentioning git, no raise |
| `test_real_git_repo_listing_detects_an_extra_file` | real `git init` under `tmp_path`, `-z` parsing |
| `test_live_tree_is_closed` | real `ROOT` → `[]` (read-only canary) |
| `test_allowlist_matches_pins` | constant == conductor entries in `drydock-pins.json` |
| `test_main_reports_conductor_errors_and_exits_1` | key present, `ok` false, exit 1 |
| `test_main_json_contract` | `conductor_errors` list; `discover_errors` list, `discover_skipped` str |

Plus the one-line `_stub_other_checks` addition in `tests/test_start_probe_discover.py` (§5).

## Files Expected To Change

- `scripts/start_probe.py` — four module constants, two helpers, `check_conductor_closure()`
  (~45 lines total), and three lines in `main()`. No existing check is modified or weakened.
- `tests/test_start_probe_conductor_closure.py` — new, ~150 lines, 13 test functions plus helpers.
- `tests/test_start_probe_discover.py` — **one added line** inside `_stub_other_checks`. No
  assertion changes.
- `drydock-pins.json` — one value updated: `scripts/start_probe.py` (line 12).
- Packet artifacts: `tasks.md`, `verification.md`, `decision-log.md`.

Explicitly **not** changed: `scripts/conductor/*` (all six), `drydock-pins.json:26-31`,
`kernel/`, `hooks/` (including `packet_guard.py`), `backstops/`,
`.github/workflows/drydock.yml`, `README.md`, `PROJECT_CONTEXT.md`,
`sdd-plus/security/scope-contract.yml`, `scripts/check_secret_tree.py`.

## must_not_do

1. **Never create `mutate.py`, `coord.py`, `executors.py`, or `handoff.py` in the live tree** —
   not in `scripts/conductor/`, not under `tests/`, not as a fixture, not "temporarily to see
   the check fire". Every such name lives under `tmp_path` only. The negative path is proven by
   injected `tracked=[…]` lists and `tmp_path` trees.
2. **Do not vendor any further conductor file**, mutating or not. The closure is six.
3. **Do not touch the parked leftover holes**: `.env` write handling, `kernel/brief_engine.py`
   completeness, the verifier-checkbox slog, GitHub fast-forward `--force`.
4. **Do not rewrite `kernel/brief_engine.py`** — not even a line.
5. **Do not rewrite or extend `hooks/packet_guard.py`.** The Owner asked for `start_probe`;
   the argument for why the hook is the wrong instrument is in `brief.md` and fact 7 above.
6. **Prefer no workflow edit** — do not touch `.github/workflows/drydock.yml`. CI already runs
   the probe at line 24 and consumes the exit code. If a future round genuinely needs a
   workflow change, that is a new Owner decision, not an implementation detail.
7. **Do not weaken `check_pins()`** or fold the closure check into it. Two checks, two messages.
8. **Do not derive `CONDUCTOR_ALLOWED` from `drydock-pins.json` at runtime** — a gate that reads
   its allowlist from the file being gated widens itself the moment someone pins a seventh file.
   The consistency *test* is the link, not the code path.
9. **No commit, no push, no archive, no PR** in the planning turn; no `scripts/conductor/
   negotiate.py` run in the planning turn; no Codex call in the planning turn.
10. **Never `--dangerously-skip-permissions`, never `git config`, never force-push,
    never `git reset --hard`.** The git-init integration test uses `git -c user.email=… -c
    user.name=… init/add` inside `tmp_path`, never machine-level config.
11. **Do not mark anything verified without the verifier subagent.** Implementer evidence is
    evidence, not verification.
12. **Do not "fix" the untracked-extra residual** on the implementer's own authority. It is
    **OQ-1**, an Owner call. Build the default (do not fail on untracked non-mutating files). If
    a future round adopts the strict variant, it uses
    `git ls-files --others --exclude-standard` — never a hardcoded `__pycache__` string, and
    never a blanket "fail on every untracked file", which does break on bytecode.
13. **Do not resolve OQ-1, OQ-2 or OQ-3 by implementing the non-default answer.** The defaults are
    the buildable plan; the alternatives are costed but unauthorized.

## JSON contract — start_probe stdout

The result dict (`scripts/start_probe.py:227-237`) gains **one additive key and loses none**:

| Key | Type | Always present? | Value |
| --- | --- | --- | --- |
| `conductor_errors` | `list[str]` | yes | `[]` when the closure holds; one string per violation otherwise |

**Placement:** immediately after `pin_errors`, before `hook_errors` — the file's convention is
that `*_errors` keys appear in check order (fact 5), and the closure check runs right after
`check_pins()`. Same position in the `errors` concatenation.

**Unchanged, explicitly:** `ok` (`bool`, still exactly `not errors`), `pin_errors`,
`hook_errors`, `secret_tree_errors`, `pre_push_errors`, `pre_commit_errors`,
**`discover_errors` (`list[str]`, always present, `[]` when the core is found *and* when
skipped)**, **`discover_skipped` (`str`, always present, `""` when the check ran)**, and
`hook_evidence` (still last). No key is removed, renamed, retyped, or made conditional.
`discover_errors` / `discover_skipped` keep their exact current semantics; this packet does not
read, move, or reinterpret them.

**Always-present, `[]`-for-clean** matches every existing `*_errors` list, so the JSON has one
shape in every run and `if result["conductor_errors"]:` is the natural predicate. No
absent-vs-present signalling.

**Compatibility:** the only machine consumer is CI, which reads the exit code
(`.github/workflows/drydock.yml:24`); an additive key cannot break it. No workflow edit is
needed, and none is made — this is unlike `discover_skipped`, which also needed none.

## Open Questions — Owner policy calls

These are the three residual judgments the round-1 critique surfaced that the Pilot cannot settle
by looking at the repo, because they are policy rather than fact. **None of them blocks
implementation.** Each has a default that matches the Owner's stated intent, and each answer is a
small, pre-costed delta. If the Owner does not answer, build the defaults.

### OQ-1 — Should the gate also fail on *non-ignored untracked* files under `scripts/conductor/`?

- **Asks:** true closure over the directory's on-disk contents, not just its vendored contents.
- **Default (build this):** **No.** The Owner's intent line says the **tracked** set is exactly
  six; failing on untracked files is a wider requirement than was asked for.
- **Evidence that "yes" is cheap:** `git ls-files --others --exclude-standard scripts/conductor/`
  is **empty on the current tree** (§0). The three `__pycache__` entries are excluded by
  `.gitignore`, which the repo already maintains — so the exemption would be declarative, not an
  ad hoc `__pycache__` string in the gate.
- **Delta if the Owner says yes:** add `_untracked_files(root)` calling
  `git ls-files -z --others --exclude-standard scripts/conductor/` (same fail-closed error
  handling as `_tracked_files`), append one error per result, add one test, and change the §2
  table row plus the `brief.md` residual paragraph. ~15 lines. **Cost:** developer scratch files
  under `scripts/conductor/` then fail the probe locally, and `test_live_tree_is_closed` becomes
  sensitive to uncommitted work.

### OQ-2 — Is filename-based detection sufficient, or does the Owner want content-based detection?

- **Asks:** whether the gate should try to recognise mutating conductor code *renamed* to an
  innocuous name.
- **Default (build this):** **Filename-based is sufficient for this packet.** The Owner's intent
  names the four filenames explicitly, and the threat model is drift/accidental vendoring (§0,
  BC-3), not a determined operator. Inside `scripts/conductor/` renaming is already defeated by
  tracked-set closure plus the sha256 pins on the six.
- **Delta if the Owner says no:** this is not a LITE change and should be its own packet. Options
  would be a content-hash denylist of known upstream mutating modules (brittle — one whitespace
  edit defeats it), or an import/AST heuristic (false positives, real maintenance). The honest
  answer is that the remaining hole — mutating code committed under a new name *outside*
  `scripts/conductor/* ` — is caught by code review and packet governance, not by a probe.

### OQ-3 — Should the four basenames be reserved **repo-wide**, or only under `scripts/conductor/`?

- **Asks:** whether `kernel/coord.py` or `scripts/handoff.py` should be un-committable in this
  repo forever.
- **Default (build this):** **Repo-wide, tracked-only** — as in §3. `README.md:12-13` bans
  vendoring the mutating conductor "here", meaning this repo, and directory-scope alone is evaded
  by committing one level up. This is the single place the packet goes beyond the literal wording
  of the Owner's intent line, which is why it is asked rather than assumed.
- **Evidence:** zero collisions today across 118 tracked files and the whole worktree (§0), so
  nothing breaks now. The cost is purely a future one: a legitimately-named `coord.py` would need
  an Owner-approved `BANNED_STEMS` edit.
- **Delta if the Owner says directory-scoped:** three deletions, spelled out at the end of §3.

## Risks

- **New git dependency inside the probe.** `check_secret_tree` walks the filesystem and never
  shells to git, so this is the probe's first `git` subprocess. Mitigated: the probe already
  hard-requires `.git` (`scripts/start_probe.py:139-140`), CI checks out with git, and
  `_tracked_files` fails closed on missing/erroring git rather than reporting a clean closure.
  `test_git_failure_fails_closed` holds that.
- **Repo-wide basename matching can false-positive *in future*.** A future legitimate `coord.py`
  or `handoff.py` anywhere in this repo fails the probe. **Not a present risk** — the §0 inventory
  found zero collisions across 118 tracked files and the entire worktree. Accepted deliberately
  (§3); the override is an explicit `BANNED_STEMS` edit under Owner sign-off — loud, not silent.
  Open as **OQ-3**.
- **The untracked non-mutating residual.** An untracked `helper.py` in `scripts/conductor/` does
  not fail. Documented in `brief.md` and §2; the four named runtime dangers are still caught by
  presence. Open as **OQ-1**, where the git-native fix and its cost are costed out.
- **Threat-model limit, stated rather than papered over.** This gate catches drift and accidental
  vendoring. It does not catch mutating code committed under an innocuous name outside
  `scripts/conductor/`, and it does not claim to stop an operator who can already run arbitrary
  code on this VM. Open as **OQ-2**.
- **Symlink evasion.** A symlink *named* `mutate.py` is caught (name match, `is_file()` follows
  it). A symlinked *directory* under `scripts/conductor/` pointing at a tree containing
  `mutate.py` may or may not be walked by `Path.rglob` depending on interpreter version. Not
  closed by this packet; noted for Codex. Anyone able to plant a symlink there can already run
  the file directly — the gate's job is catching vendoring, not defeating a local operator.
- **Bytecode-only leftovers.** `__pycache__/mutate.cpython-313.pyc` fails the check even though
  the source is gone. Intentional: it is evidence the module was here, and clearing it is one
  `rm -rf`. Slight risk of a confusing failure; the message names the exact path.
- **Coupling the existing discover tests to the live tree.** Addressed by the one-line
  `_stub_other_checks` addition (§5); without it those tests would pass for an unexamined reason.
- **Pin/edit ordering.** Editing `start_probe.py` without re-pinning makes the probe fail its own
  `check_pins()`. Mitigated by §6's strict ordering.
- **Scope creep.** The parked leftover holes and any hook rewrite stay out, per `must_not_do`.

## Rollback

Single-commit revert. The change is additive across four files and moves as one unit:
`git revert <sha>` restores the prior `scripts/start_probe.py`, drops
`tests/test_start_probe_conductor_closure.py`, restores the `_stub_other_checks` line, and
restores the `ffcd8ec3…` pin value together — so there is no half-reverted state where the probe
fails on its own hash. No migration, no data, no config, no external state, nothing to undo on
the VM or in `.git/hooks`; the check only reads.

Manual fallback if the revert is awkward mid-stack: delete `check_conductor_closure()`, its two
helpers and four constants, remove the three `main()` lines (call, `errors` term,
`conductor_errors` key), delete the new test file, drop the added stub line, and restore the
`ffcd8ec3ca42b2f7e03d9de612a8182218342cbe1147fdf0bc6f02a9815e46b1` pin value on
`drydock-pins.json:12`.
