# Plan

## Change

grok-refuse-brief-engine — close leftover hole 2: direct
`python3 kernel/brief_engine.py --record-verify NAME` still records completeness (case 5b).

## Mode

LITE. **Round 2 of 2 (final).** Round 1 did not converge (2 blocking concerns from Codex,
transport-only; the choreographer did not audit). This revision is the Pilot's own audit of that
critique — see §Round 2 audit. The negotiation cap is 2, so this plan either stands as written or
the named Owner question below blocks.

- **Known files, all four named up front:** `kernel/brief_engine.py` (replaced by an overlay),
  `kernel/brief_complete_engine.py` (new — *moved bytes*, never authored),
  `scripts/record_verify_bound.py` (one constant plus its docstring),
  `tests/test_kernel_brief_overlay.py` (one constant plus new tests), and three values in
  `drydock-pins.json`.
- **Contract change, stated precisely — not "no contract change".** Two separate claims, because
  conflating them is what round 1 got wrong:
  1. *The completeness CLI at the NEW path is unchanged.* `kernel/brief_complete_engine.py`
     accepts `--write-status`, `--lang`, `--record-verify NAME` and bare FACTS JSON and emits the
     same stdout JSON, byte-for-byte, because it **is** the same bytes.
  2. *The OLD path gains a refusal, and under the OQ-1 default that refusal is stricter than
     `kernel/brief.py:28`.* This is **additive refusal**, not a pure byte relocation. Because
     `kernel/brief.py:65-68` and `scripts/brief.py:63-66` delegate their non-matching modes into
     this path, the stricter matcher changes the observable behavior of those two files even
     though neither file is edited. The exact deltas are enumerated in §Behavior deltas on
     unedited files. Do not describe this packet as "no contract change."
- **No auth, no schema, no migration, no side-effect widening.** The one side effect in play —
  `append_event(...)` at `kernel/brief_engine.py:536` — becomes *harder* to reach, never easier.
  Every behavior delta in this packet moves in the refuse direction.
- **No workflow, no conductor, no hook edit.** `.github/workflows/drydock.yml`,
  `scripts/conductor/*` and `hooks/*` are untouched.

Still LITE, not FULL: this is one directory's worth of choreography, in the exact shape three
sibling files already use, with no new dependency and no new external surface. The contract change
is real but is a strict tightening of a bypass with zero known callers (fact 12), which is a
recorded Owner decision (OQ-1), not an unbounded API break.

## Round 2 audit — Codex round-1 critique

Source: `negotiate-grok-refuse-brief-engine-r1.json`, read verbatim from disk. Codex ran as
`gpt-5.4-mini` ("light task -> workhorse model"), transport only. Its critique is **input, not
orders**. Every claim below was re-checked against the tree at HEAD `0b4a475` by the Pilot; the
verification commands used are recorded so a reviewer can re-run them.

### BC1 — "silently broadens behavior by refusing `--record-verify=…` and unambiguous abbreviations" → **PARTIAL ACCEPT**

**The factual core is confirmed, and round 1 understated it.** Verified live (side-effect-free:
`BAD_NAME` fails `record_verify`'s kebab regex at `kernel/brief_engine.py:518-519`, so it returns
before any `sdd.py` subprocess and before `append_event`):

```
$ python3 kernel/brief.py --record-verify=BAD_NAME     -> {"recorded": false, "reason": "bad-name"}  exit=0
$ python3 scripts/brief.py --record-ver BAD_NAME       -> {"recorded": false, "reason": "bad-name"}  exit=0
$ python3 kernel/brief.py --record-verify BAD_NAME     -> bare-record-verify-refused                 exit=1
```

The first two prove Codex's mechanism exactly: the token misses `"--record-verify" in argv` at
`kernel/brief.py:28` / `scripts/brief.py:26`, falls through to the delegating `os.execv`, and is
parsed by the completeness engine. Under the strict overlay those two invocations become exit 1
`bare-record-verify-refused`. So two files listed under "Files Expected To Change → explicitly
**not** changed" *do* change observable behavior, including their **exit codes** (0 → 1). Round 1
called this a "bonus" in §2 while the Mode section simultaneously claimed "no contract change."
Codex is right that those two statements cannot both stand.

**What is accepted:** the framing defect. "No contract change" is deleted from Mode and from
`brief.md`; the deltas are now enumerated explicitly in §Behavior deltas on unedited files; §2 no
longer calls the strict matcher a free bonus; `brief.md`'s claim that "nothing that currently works
stops working" is deleted, because it is false — the equals and abbreviation spellings currently
work and will stop working, which is the entire point.

**What is rejected:** the implied remedy of reverting to the literal `"--record-verify" in argv`
matcher. Three reasons, in order of weight:

1. **The Owner default is already recorded.** OQ-1 was raised in round 1 with a stated default of
   *strict matcher*, and per Owner intent for this packet a recorded default is not silently
   reversed by a peer critique. It stays as OQ-1 with that default, named and visible.
2. **The blast radius is zero known callers** (fact 12, new this round). A repo-wide grep for any
   `--record…` spelling across tracked `*.py`/`*.md`/`*.json`/`*.yml`/`*.sh` finds exactly one
   executing caller — `scripts/record_verify_bound.py:55`, which uses the canonical two-token form
   — plus tests, which also use the canonical form, plus docstrings. Nothing in this repo invokes
   the equals or abbreviated spelling. The only behavior that changes is the bypass itself.
3. **Refusing is the fail-safe direction.** Every delta is `records / exit 0` → `refuses / exit 1`.
   No delta makes `append_event` easier to reach.

Codex proposed no third option and neither does this plan; per Owner intent, no new matcher design
is invented. OQ-1 keeps exactly two branches: the strict default (build this) and the literal-copy
fallback.

### BC2 — "the move/overwrite sequence is too easy to perturb without a mechanical safeguard" → **PARTIAL ACCEPT**

**The premise that no safeguard exists is rejected.** Round 1 already specified move-first,
hash-then-edit as a hard order (§1 and Steps 2-4: `cp`, `sha256sum`, stop unless `aa3ba09…`, only
then overwrite), already forbade `git mv` and any edit to the moved file (must_not_do 1, 5), and
already had `test_completeness_engine_bytes_unmoved` plus `check_pins()` as mechanical nets. Codex
appears not to have credited the choreography that was there.

**What is accepted is that the wording is perturbable**, which is a fair reading of the same text.
Three concrete gaps in the round-1 phrasing, each tightened below with **no new machinery** — no
helper script, no extra pin tool, no new workflow, per Owner intent:

- *"Stop" was undefined.* Step 3 now states the abort semantics: on mismatch, delete the copy,
  change nothing else, stop and report to the Owner. Do not "fix it and continue."
- *The riskiest moment had no check after it.* The hash was confirmed **before** the overlay
  overwrite, but the overwrite is precisely the operation that can hit the wrong path and clobber
  the freshly copied file. New Step 4a re-runs the identical `sha256sum` immediately after the
  overwrite. Same command, zero new tooling, catches exactly the failure Codex names.
- *The pinned value was assumed current rather than proven current.* New Step 8a re-asserts the
  hash immediately before `drydock-pins.json` is written, so `aa3ba09…` is pinned because it was
  observed, not because it was observed forty minutes earlier.

Also tightened: the "never open that file" rule is promoted from prose in must_not_do into a hard
tool-level rule in Steps — after Step 3, no `Edit`/`Write`/formatter/`sed` invocation may name
`kernel/brief_complete_engine.py` at all, for any reason, including fixing its stale docstring.

### Gaps (input, not orders — dispositions)

| Codex gap | Disposition | Where |
| --- | --- | --- |
| Plan does not say whether argparse-abbreviation parity is required or intentionally dropped | **Accepted.** It is intentionally dropped, and now says so in one place with the evidence. | Mode; §Behavior deltas; §OQ-1 |
| No acceptance criterion for the extra `execv` hop beyond "tests pass"; wants one runtime check for the wrapper path and one for the bound path | **Accepted.** Cheap and genuinely load-bearing — the hop is the thing least covered by unit tests. Two named runtime checks with expected output added. | Verification commands 3a, 4a |
| No stated way for a reviewer to tell a successful refactor from a merely relocated residual hole | **Accepted.** A four-line review criterion added; the honest residual was already in §Risks but had no crisp pass/fail test a reviewer could apply. | §Review criterion |

### Risks raised by Codex (dispositions)

Five of the six were already in §Risks (hole relocated not removed; stale docstring left
deliberately; pin/probe ordering; `execv` hop debuggability; byte-change fragility). One is new and
worth answering:

- **"The stricter matcher may become a maintenance trap if future argparse options expand the
  prefix space."** Real, and it resolves in the safe direction. If a future option (say
  `--record-hash`) is added to the completeness engine, argparse makes `--record` ambiguous and
  exits 2; the overlay's prefix matcher still matches `--record` and refuses with exit 1. Both are
  non-zero, neither records. The matcher can become *over*-broad, never under-broad, and
  over-broad here means "refuses a token that argparse would itself have rejected." Recorded in
  §Risks; no design change.
- **"External callers depending on abbreviation semantics."** No external callers exist — this
  repo is the only consumer, and fact 12 enumerates every call site.

## Behavior deltas on unedited files

This table is the honest version of what round 1 called "no contract change." All of it follows
from `kernel/brief.py:65-68` and `scripts/brief.py:63-66` delegating into `kernel/brief_engine.py`,
which becomes the strict overlay. **Neither file is edited and neither pin moves**; the behavior
change is inherited through the delegation edge.

| Invocation | Today | After (OQ-1 default) | Direction |
| --- | --- | --- | --- |
| `kernel/brief.py --record-verify NAME` | refused, exit 1 | unchanged — refused in-process at `:28-54`, before any hop | none |
| `kernel/brief.py --record-verify=NAME` | delegates; **records**; exit 0 | `bare-record-verify-refused`, exit 1 | tightened |
| `kernel/brief.py --record-ver NAME` (and `--record`, `--r`, `--rec=NAME`) | delegates; **records**; exit 0 | `bare-record-verify-refused`, exit 1 | tightened |
| `scripts/brief.py`, same four spellings | identical to the rows above | identical to the rows above | tightened |
| `kernel/brief_complete.py`, same spellings | execs `kernel/brief.py`; identical | identical | tightened |
| `kernel/brief.py --record-verify <4 args>` | execs `record_verify_bound.py` | unchanged | none |
| `kernel/brief.py` / `scripts/brief.py`, all other modes (bare FACTS, `--write-status`, `--lang`) | delegates, exit 0 | unchanged output; one extra `execv` hop | none |

Exit-code note, because it is the part a scripted caller would feel: the tightened rows move from
exit **0** to exit **1**. Fact 12 establishes that no such caller exists in this repo.

## Review criterion — refactor vs. relocated hole

A reviewer should be able to decide this in four checks, without reading the diff line by line.
The packet **passes** only if all four hold:

1. **Every named path refuses.** `kernel/brief_engine.py`, `kernel/brief.py`,
   `kernel/brief_complete.py`, `scripts/brief.py` all return exit 1 /
   `bare-record-verify-refused` on the bare form. Verification commands 1 and 5.
2. **The residual is exactly one path, and it is unadvertised.** After the change,
   `grep -rn "brief_complete_engine" ` over tracked non-archive files returns
   `scripts/record_verify_bound.py` (the gate), `tests/test_kernel_brief_overlay.py`,
   `drydock-pins.json`, and the overlay's own docstring — and **nothing else**. No wrapper, no
   README, no AGENTS.md, no workflow names it as a thing to run. If any *user-facing* doc or
   wrapper acquires that path, the hole has been relocated rather than closed, and the packet
   fails this criterion.
3. **The gated path still works end to end.** The bound form gets *past* `check_verdict` into
   completeness: `test_engine_overlay_bound_form_reaches_completeness` and the untouched
   `tests/test_record_verify_bound.py:44-53`. A packet that refuses everything, including
   provenance, is not a fix.
4. **The residual is written down, not discovered.** `test_completeness_engine_still_has_bare_mode`
   retains its retargeted docstring saying the moved bytes still contain the mode, and §Risks says
   it in prose. The claim of this packet is *"every advertised path refuses,"* never *"the
   capability is gone."*

## Load-bearing facts, checked on disk

1. **The hole is real and is the engine's own documented mode.**
   `kernel/brief_engine.py:11` prints
   `python brief.py --record-verify NAME -> ... record a verify-run` in its module docstring;
   `:548` registers `ap.add_argument("--record-verify", metavar="NAME", default=None)`; `:556-557`
   dispatch straight into `record_verify(root, args.record_verify)` (`:514`), which on a passing
   gate calls `append_event(root, "brief", "verify", "verify-run", …)` (`:536`). Nothing in that
   path consults `scripts/check_verdict.py`.

2. **`_HOOKS` is the constraint on where the bytes may go.**
   `kernel/brief_engine.py:42-43`:
   ```python
   _HOOKS = Path(__file__).resolve().parent.parent / "hooks"
   sys.path.insert(0, str(_HOOKS))
   ```
   followed by `from _drydock_common import (…)` at module scope (`:44-46`). For any
   `kernel/<name>.py`, `parent.parent` is the repo root, so `hooks/` resolves. For
   `kernel/vendor/<name>.py` it would resolve to `kernel/hooks/` and the import would fail at
   module import time — before `main()`'s `try` (`:555`) can convert anything into a JSON error
   block. **The moved file must sit directly under `kernel/`.** (The stale docstring at
   `kernel/brief_complete.py:5` still says "Vendored completeness bytes are at
   `kernel/vendor/brief.py`" — a path that does not exist; this fact is why that layout was
   abandoned. That docstring is *not* corrected by this packet: editing it would move
   `drydock-pins.json:24` for a comment.)

3. **`record_verify`'s own `sdd.py` fallback survives the move.**
   `kernel/brief_engine.py:522-524` prefers `root / "scripts" / "sdd.py"` and falls back to
   `Path(__file__).resolve().parent / "sdd.py"`. `parent` of `kernel/<moved>.py` is still
   `kernel/`, exactly as before — the fallback is equally (non-)existent either way, and the
   primary path is unaffected.

4. **The overlay pattern to copy is `kernel/brief.py:27-68`.** `ROOT` (`:22`), `COMPLETE` (`:23`),
   `BOUND` (`:24`); refuse when `"--record-verify" in argv` and `len(rest) != 4` with JSON
   `{"recorded": false, "reason": "bare-record-verify-refused", "detail": …}` plus a stderr usage
   line, `return 1` (`:28-54`); `os.execv` to `scripts/record_verify_bound.py` on the four-argument
   form (`:55-64`); otherwise `os.execv` the completeness file with `argv[1:]` (`:65-68`).
   `scripts/brief.py:25-67` is the same shape with `KERNEL` (`:21`) instead of `COMPLETE`.
   `kernel/brief_complete.py:13-16` is a two-line alias that `os.execv`s `kernel/brief.py`.

5. **The recursion trap, stated precisely.** Today `kernel/brief.py:23` is
   `COMPLETE = ROOT / "kernel" / "brief_engine.py"` and `scripts/brief.py:21` is
   `KERNEL = ROOT / "kernel" / "brief_engine.py"`. Once `kernel/brief_engine.py` *is* the overlay,
   an overlay whose own `COMPLETE` pointed at `kernel/brief_engine.py` would `execv` itself
   forever. The new overlay's `COMPLETE` therefore points at
   `kernel/brief_complete_engine.py`. See §2 for why the two wrappers are deliberately left
   pointing at the overlay.

6. **`scripts/record_verify_bound.py` would refuse itself if not retargeted.** `:21` is
   `BRIEF = ROOT / "kernel" / "brief_engine.py"`, and `:54-58` runs
   `[sys.executable, str(BRIEF), "--record-verify", packet]` — a **bare, two-token**
   `--record-verify` invocation, issued *after* `check_verdict` exits 0 (`:33-53`). That is
   exactly the shape the new overlay refuses. Without the retarget, the bound path returns
   `bare-record-verify-refused` and provenance recording breaks completely.

7. **The current test suite encodes the hole as expected behavior.**
   `tests/test_kernel_brief_overlay.py:10` is `ENGINE = ROOT / "kernel" / "brief_engine.py"`;
   `:38-42` `test_completeness_engine_still_has_bare_mode` asserts `"--record-verify NAME"` and
   `"record a verify-run"` appear in that file's text. After the move that text lives in
   `kernel/brief_complete_engine.py`, so the constant must be retargeted or the test fails for the
   right reason in the wrong place.

8. **`check_pins()` needs no code change for a new pin key.** `scripts/start_probe.py:68-84`
   loads `drydock-pins.json`, takes `pins.get("files")`, and iterates
   `for rel, expected in files.items()` (`:76`), reporting `missing pinned file` (`:78-80`) or
   `hash drift` (`:82-83`). Adding a key is pure data. **`scripts/start_probe.py` is not edited and
   its pin (`drydock-pins.json:12`) does not move.**

9. **Nothing else in the live tree names the completeness path.**
   `grep -rn "brief_engine"` over tracked `*.py` / `*.md` / `*.json` / `*.yml`, excluding
   `sdd-plus/archive/`, returns only: `scripts/record_verify_bound.py:7,21`;
   `scripts/brief.py:4,11,21,39,64`; `kernel/brief.py:4,12,13,23,41,66`;
   `tests/test_kernel_brief_overlay.py:10`; `drydock-pins.json:25`. (Plus
   `reports/launchguardian/raw/semgrep-results.json`, which is a scanned-paths list in a generated
   report — not edited.) No `README.md`, `AGENTS.md` or `PROJECT_CONTEXT.md` reference, so no doc
   edit is required.

10. **`hooks/packet_guard.py` will not block this work.** Its deny classes are schema migrations,
    *new* CI config, and container config (`hooks/packet_guard.py:105-128`). `kernel/` is not among
    them, and this packet does not extend the hook.

11. **The argparse spellings the existing guard misses (verified on this VM against a replica of
    `kernel/brief_engine.py:545-549`):**

    | argv | engine parses `record_verify` as | `"--record-verify" in argv` |
    | --- | --- | --- |
    | `["--record-verify", "p"]` | `p` | **True** |
    | `["--record-verify=p"]` | `p` | False |
    | `["--record-ver", "p"]` | `p` | False |
    | `["--record", "p"]` | `p` | False |
    | `["--r", "p"]` | `p` | False |
    | `["--record-verify=p", "v", "d", "r"]` | `SystemExit 2` (unrecognized `v d r`) | False |

    Re-verified this round on Python 3.13.5 against a standalone replica of
    `kernel/brief_engine.py:545-549`; the table above is exact. One row to add:
    `["--rec=p"]` also parses to `p` (abbreviation *and* equals together), which the proposed
    `_record_verify_index` catches because it partitions on `=` before prefix-matching.

    So the equals form and every unambiguous abbreviation slip past `kernel/brief.py:28` and
    `scripts/brief.py:26` today, and the equals form can never be a legitimate bound invocation
    (four trailing arguments after `--record-verify=p` are an argparse `SystemExit 2`). This drives
    OQ-1 and the strict matcher in §2.

12. **No caller in this repo uses the equals or abbreviated spelling.** (New this round; the
    evidence BC1 turns on.) `grep -rnE -- '--record[-a-z]*[= ]'` over tracked
    `*.py`/`*.md`/`*.json`/`*.yml`/`*.yaml`/`*.sh`, excluding `sdd-plus/archive/`, this packet dir,
    and `reports/`, returns exactly:

    - `scripts/record_verify_bound.py:55` — the one executing caller, canonical two-token form
      (`[sys.executable, str(BRIEF), "--record-verify", packet]`);
    - `tests/test_kernel_brief_overlay.py`, `tests/test_brief_wrapper.py`,
      `tests/test_record_verify_bound.py` — canonical form only;
    - docstring/usage prose in `kernel/brief.py`, `kernel/brief_complete.py`, `scripts/brief.py`,
      `scripts/record_verify_bound.py`, `kernel/brief_engine.py:11` — not executed.

    So the strict matcher of OQ-1 breaks **zero** known callers. The set of invocations whose
    behavior changes is exactly the set of bypass spellings. This does not make it "no contract
    change" — it bounds the blast radius of a contract change that is real.

13. **A new pin key needs no probe change, and the new file is not caught by any closure check.**
    `check_pins()` (`scripts/start_probe.py:68-84`) iterates `pins["files"].items()` and stats each
    path, so an added key is pure data (fact 8). Separately confirmed this round:
    `check_conductor_closure()` (`scripts/start_probe.py:119-154`) constrains only
    `scripts/conductor/` and the banned mutating stems, so `kernel/brief_complete_engine.py` is not
    flagged by it. **Implementation note, not a plan change:** the new file must be `git add`ed
    before commit, or `check_pins()` passes locally on the working tree while a fresh clone fails
    with `missing pinned file`. Step 11's `git status --porcelain` is where that is caught.

## Approach

### 1. Move the bytes — copy, verify, then overwrite. In that order.

The completeness logic is **not rewritten, not re-typed, not reformatted**. Move it:

```bash
cp kernel/brief_engine.py kernel/brief_complete_engine.py
sha256sum kernel/brief_complete_engine.py
# must print aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b
```

`shutil.copy2` or `Path("kernel/brief_complete_engine.py").write_bytes(Path("kernel/brief_engine.py").read_bytes())`
are equivalent and acceptable. **Do not `git mv`** — `kernel/brief_engine.py` must continue to
exist, as the overlay. Only after the hash is confirmed may `kernel/brief_engine.py` be
overwritten. After that point `kernel/brief_complete_engine.py` is frozen: no edit, ever, in this
packet, not even a docstring path fix (that would break the `aa3ba09…` pin, which is the whole
point of the constraint).

The new path is **`kernel/brief_complete_engine.py`** — directly under `kernel/` per fact 2, and
named so the two roles read off the filename: `brief_complete*` is completeness,
`brief_engine.py`/`brief.py`/`brief_complete.py` are the gated entry points.

### 2. The overlay at `kernel/brief_engine.py`

Structurally `kernel/brief.py:27-68` with three differences: `COMPLETE` points at the moved file
(fact 5), the strings name `kernel/brief_engine.py` as the invoked path, and the matcher covers the
spellings in fact 11 (OQ-1 default).

```python
#!/usr/bin/env python3
"""Choreography overlay at the historical completeness path.

Completeness lives at kernel/brief_complete_engine.py (bytes unchanged from
Drydock kernel/brief.py @ 5f76f67, sha256 aa3ba09...). This file used to BE
those bytes, which meant `python3 kernel/brief_engine.py --record-verify NAME`
recorded a verify-run with no in-channel binding (case 5b, leftover hole 2).
It is now the same gate kernel/brief.py applies. Bound form:

  python3 kernel/brief_engine.py --record-verify <packet> <verdict-file> \\
      <expected-sha256> <required-verdict-string>

which execs scripts/record_verify_bound.py (check_verdict first, then
kernel/brief_complete_engine.py). Other modes are delegated unchanged to
kernel/brief_complete_engine.py.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPLETE = ROOT / "kernel" / "brief_complete_engine.py"   # NEVER this file: execv loop
BOUND = ROOT / "scripts" / "record_verify_bound.py"


def _record_verify_index(argv: list[str]) -> int | None:
    """Index of any token the completeness parser would read as --record-verify.

    argparse accepts `--record-verify NAME`, `--record-verify=NAME`, and any
    unambiguous abbreviation (`--record-ver`, `--record`, `--r`) --- checked
    against kernel/brief_complete_engine.py:545-549. The plain
    `"--record-verify" in argv` guard used by kernel/brief.py:28 sees only the
    first spelling, so this overlay matches all of them and lets the canonical
    spelling alone through to the bound form.
    """
    for i, tok in enumerate(argv[1:], start=1):
        if not tok.startswith("--"):
            continue
        name = tok.partition("=")[0]
        if len(name) > 2 and "--record-verify".startswith(name):
            return i
    return None


def main(argv: list[str]) -> int:
    i = _record_verify_index(argv)
    if i is not None:
        rest = argv[i + 1 :]
        if argv[i] != "--record-verify" or len(rest) != 4:
            print(json.dumps({...}, indent=2))     # reason: bare-record-verify-refused
            print("refused: ...", file=sys.stderr)
            return 1
        if not BOUND.is_file():
            print(json.dumps({"recorded": False,
                              "reason": "missing-record_verify_bound"}, indent=2))
            return 1
        os.execv(sys.executable,
                 [sys.executable, str(BOUND), rest[0], rest[1], rest[2], rest[3]])
    if not COMPLETE.is_file():
        print("missing kernel/brief_complete_engine.py", file=sys.stderr)
        return 1
    os.execv(sys.executable, [sys.executable, str(COMPLETE), *argv[1:]])
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

The refusal payload keeps the *exact* reason string the sibling overlays and the existing tests
use — `"reason": "bare-record-verify-refused"` — with `"recorded": False`, `indent=2`, exit 1, and
a stderr usage line naming `kernel/brief_engine.py`:

```json
{
  "recorded": false,
  "reason": "bare-record-verify-refused",
  "detail": "kernel/brief_engine.py --record-verify requires <packet> <verdict-file> <expected-sha256> <required-verdict-string>, spelled exactly; completeness-only kernel/brief_complete_engine.py is not provenance"
}
```

Note the `indent=2` fix relative to `kernel/brief.py:56-59`, where the
`missing-record_verify_bound` branch passes `indent=2` to `print()` instead of `json.dumps()` —
harmless today (it becomes `print(s, indent=2)`… which would in fact `TypeError`), so the overlay
writes that one branch correctly rather than copying the bug. **This is the only place the overlay
knowingly diverges from `kernel/brief.py`'s bytes**, it is on an unreachable-unless-broken branch,
and `kernel/brief.py` itself is still not edited.

**Why `kernel/brief.py` and `scripts/brief.py` are deliberately left pointing at
`kernel/brief_engine.py`.** They may keep their current `COMPLETE`/`KERNEL` constants: that path
still exists, and it is now the overlay. Their non-`--record-verify` modes then take one extra
`os.execv` hop (`kernel/brief.py` → overlay → completeness). `os.execv` *replaces* the process, so
the hop costs one interpreter start and cannot recurse or stack. In exchange, two files stay
unedited and two pins (`drydock-pins.json:7-8`) stay put. Their *canonical* bare-`--record-verify`
refusals still fire in their own process, before any hop, so no currently-green test changes
outcome.

**This is where the packet's contract change actually lands, and it is not free.** Under the OQ-1
default, the equals-form and abbreviation spellings that today pass *through* these two wrappers
into the engine (fact 11) will instead hit the strict overlay and be refused — so
`kernel/brief.py --record-verify=NAME` and `scripts/brief.py --record-ver NAME` go from
"records, exit 0" to "refused, exit 1" without either file being edited. That is a deliberate
tightening of a bypass, enumerated row by row in §Behavior deltas on unedited files and bounded by
fact 12 (no caller uses those spellings). It is the price of leaving the two wrappers unedited and
un-repinned, and it is the OQ-1 decision, not an implementation detail. Do not describe it as a
bonus or as a no-op.

### 3. Retarget `scripts/record_verify_bound.py`

Two edits, no logic change:

- `:21` — `BRIEF = ROOT / "kernel" / "brief_engine.py"` → `ROOT / "kernel" / "brief_complete_engine.py"`.
  Mandatory per fact 6: the subprocess at `:54-58` issues the bare two-token form, which the
  overlay now refuses; pointed at the overlay, `record_verify_bound.py` would refuse itself and
  provenance recording would be impossible by any route.
- `:7` — the docstring line currently reads "Do not call kernel/brief_engine.py --record-verify
  directly; kernel/brief.py, kernel/brief_complete.py, and scripts/brief.py refuse the bare form."
  Rewrite to: completeness is `kernel/brief_complete_engine.py`, and `kernel/brief.py`,
  `kernel/brief_complete.py`, `scripts/brief.py` **and `kernel/brief_engine.py`** refuse the bare
  form. Leaving the stale sentence would make the repo's only prose about this contract point at
  the wrong file, one packet after fixing it.

Nothing else in that file moves: `CHECK` (`:20`), the `check_verdict` gate (`:33-53`), the
argument count check (`:25-31`), and the stdout/stderr passthrough (`:60-63`) are unchanged.

### 4. Tests — `tests/test_kernel_brief_overlay.py`

Retarget one constant, keep all five existing tests meaningful, add five. Same file, because it
already owns this contract; no new test file is needed.

- `:10` — `ENGINE = ROOT / "kernel" / "brief_engine.py"` → `ROOT / "kernel" / "brief_complete_engine.py"`,
  and add `ENGINE_OVERLAY = ROOT / "kernel" / "brief_engine.py"`.
- `:38-42` `test_completeness_engine_still_has_bare_mode` — assertions unchanged, now reading the
  moved file. Update the docstring: the leftover is no longer that a *documented, wrapper-named*
  path records; it is that the vendored bytes still contain the mode at their new, unadvertised
  path (see §Risks).
- The four other existing tests (`:22-27`, `:30-35`, `:45-55`, `:58-62`) are untouched and must
  stay green — they exercise `kernel/brief.py` and `kernel/brief_complete.py`, whose behavior this
  packet does not change.

New tests (same `_run` helper at `:13-19`):

| Test | Asserts |
| --- | --- |
| `test_engine_overlay_bare_record_verify_refused` | `_run(ENGINE_OVERLAY, ["--record-verify", "does-not-exist"])` → `returncode != 0`, stdout JSON `recorded is False`, `reason == "bare-record-verify-refused"`. **The headline criterion.** |
| `test_engine_overlay_bound_form_still_requires_check_verdict` | four-arg form with a `tmp_path` verdict file and digest `"0"*64` → `reason == "check_verdict-failed"`, i.e. the overlay reached `record_verify_bound.py` rather than refusing. Mirrors `:45-55`. |
| `test_engine_overlay_bound_form_reaches_completeness` | verdict file written, `digest = hashlib.sha256(p.read_bytes()).hexdigest()`, packet `"does-not-exist"` → `recorded is False` with `reason in {"bad-name", "packet-not-found", "gate-failed"}`. Proves the bound path gets **past** `check_verdict` into the moved completeness file — the one assertion that would catch a `record_verify_bound.py` still pointing at the overlay. Mirrors `tests/test_record_verify_bound.py:44-53`. |
| `test_completeness_engine_bytes_unmoved` | `hashlib.sha256(ENGINE.read_bytes()).hexdigest() == "aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b"`, and `ENGINE.parent.name == "kernel"`. Pins both Owner constraints in one test. |
| `test_completeness_engine_hooks_import_resolves` | `(ENGINE.resolve().parent.parent / "hooks" / "_drydock_common.py").is_file()` **and** `_run(ENGINE, [])` → `returncode == 0` with parseable FACTS JSON. The second half is the real proof: `_HOOKS` is consumed by a module-scope import (`:42-46`) that runs before `main()`'s `try`, so a mis-resolved `_HOOKS` is a traceback and a non-zero exit, not a JSON error block. |
| `test_engine_overlay_other_modes_delegate` | `_run(ENGINE_OVERLAY, [])` → exit 0, JSON containing `drydock` / `engine` / `generated`. Empty-argv FACTS still works through the overlay. |

Under the OQ-1 default, add one more:

| Test | Asserts |
| --- | --- |
| `test_engine_overlay_equals_and_abbrev_forms_refused` | `pytest.mark.parametrize` over `["--record-verify=does-not-exist"]`, `["--record-ver", "does-not-exist"]`, `["--record", "does-not-exist"]`, `["--r", "does-not-exist"]`, and `["--record-verify=p", "v", "d", "r"]` → each exits non-zero with `reason == "bare-record-verify-refused"`. Drop this test if the Owner picks the literal-copy fallback. |

Not modified, and expected green unchanged: `tests/test_brief_wrapper.py` (exercises
`scripts/brief.py`, incl. `test_other_modes_still_delegate_to_kernel:41-45`, which now traverses
the extra hop) and `tests/test_record_verify_bound.py` (all three tests call
`record_verify_bound.py` directly; after the retarget they reach completeness exactly as before —
`:44-53` in particular pins that the post-`check_verdict` leg still works).

**No test may create a real packet, a real passing gate, or a real `verify-run` ledger event.**
Every provenance test uses `does-not-exist` as the packet name so `record_verify` (`:518-535`)
bails before `append_event` (`:536`).

### 5. Pins — last, and in this order

`drydock-pins.json`, three values, computed **after** every code edit is final:

| Line | Key | Change |
| --- | --- | --- |
| 25 | `kernel/brief_engine.py` | `aa3ba09…` → sha256 of the **overlay** (new value) |
| new | `kernel/brief_complete_engine.py` | add, `aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b` (unchanged bytes) |
| 11 | `scripts/record_verify_bound.py` | `43bc4dd…` → recompute after the retarget |

Place the new key adjacent to `kernel/brief_engine.py` (after line 25) so the kernel trio reads
together. Unchanged, explicitly: `scripts/brief.py` (`:7`), `kernel/brief.py` (`:8`),
`kernel/brief_complete.py` (`:24`), `scripts/start_probe.py` (`:12`), all `hooks/*`, all
`scripts/conductor/*` (`:26-31`), `backstops/*`, `agents/verifier.md`, `AGENTS.md`,
`scripts/sdd.py`, `scripts/check_verdict.py`, `scripts/check_secret_tree.py`, and the top-level
`drydock_commit` / `verifier_md_git_blob` / `hash_alg` fields.

```bash
python3 - <<'PY'
import hashlib, pathlib
for p in ("kernel/brief_engine.py", "kernel/brief_complete_engine.py",
          "scripts/record_verify_bound.py"):
    print(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(), p)
PY
```

Re-pinning before the files are final leaves the probe failing its own `check_pins()`; running the
probe before re-pinning fails on drift at line 25 and line 11. Pins last, probe after.

## Steps

The byte-freeze choreography is Steps 2 → 3 → 4 → 4a, **in that order, with no step merged into
another**. Round 2 tightening (BC2): each hash gate below is a *stop*, not a warning, and the
`sha256sum` after Step 4 is the one that catches an overwrite aimed at the wrong path.

1. Re-read `kernel/brief_engine.py:11`, `:42-46`, `:514`, `:536`, `:548`, `:556-557` and
   `kernel/brief.py:22-68`; confirm facts 1, 2, 4 still hold at HEAD `0b4a475`. Also run
   `sha256sum kernel/brief_engine.py` **before touching anything** and confirm it is `aa3ba09…`;
   if it is not, the tree is not the tree this plan was written against — stop and report.
2. `cp kernel/brief_engine.py kernel/brief_complete_engine.py`. Copy only. Not `git mv`, not
   `mv`, not an editor "save as", not a retype.
3. `sha256sum kernel/brief_complete_engine.py` — **stop unless it is exactly**
   `aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b`.
   **Abort semantics, explicitly:** on any mismatch, delete `kernel/brief_complete_engine.py`,
   change nothing else, leave `kernel/brief_engine.py` untouched, and report to the Owner. Do not
   diagnose-and-continue, do not re-copy with a "fix", do not proceed to Step 4 with a mismatched
   file on disk. A mismatch here means the source bytes are not what the packet assumes, and every
   downstream pin would be wrong.
   **From this point `kernel/brief_complete_engine.py` is frozen: no `Edit`, no `Write`, no `sed`,
   no formatter, no linter autofix, no editor buffer may name that path again for the rest of the
   packet — including to fix its stale internal `brief.py` docstring reference.** If a tool call
   would name it, that is the signal that something has gone wrong, not a small exception.
4. Overwrite **`kernel/brief_engine.py`** — and only that path — with the overlay of §2
   (`COMPLETE` → `kernel/brief_complete_engine.py`; strings naming `kernel/brief_engine.py`;
   matcher per OQ-1 default). Read the destination path back before writing; this is the single
   step in the packet that can clobber the frozen file.
4a. **Re-run `sha256sum kernel/brief_complete_engine.py`** — still `aa3ba09…`. Same stop rule as
   Step 3. This is the check round 1 was missing: Step 3 proved the copy was right *before* the
   risky write, and only this re-check proves the risky write did not land on it. Then run
   `python3 kernel/brief_engine.py | head -3` once by hand, before pytest, so an `execv` self-loop
   is found in one process rather than under the test runner (§Risks).
5. Retarget `scripts/record_verify_bound.py:21` to the moved file and rewrite the `:7` docstring
   line (§3). Change nothing else in that file.
6. Update `tests/test_kernel_brief_overlay.py`: retarget `:10`, add `ENGINE_OVERLAY`, adjust the
   `:38-42` docstring, add the six (or seven, under the OQ-1 default) tests of §4.
7. `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` — green, including
   `tests/test_brief_wrapper.py` and `tests/test_record_verify_bound.py`. Fix until green.
   **Never by editing `kernel/brief_complete_engine.py`**, and never by weakening a refusal
   (must_not_do 1, 11).
8. **Re-assert the freeze one last time before pinning:** `sha256sum kernel/brief_complete_engine.py`
   is `aa3ba09…`. Same stop rule. Only then compute the other two hashes (§5) and update
   `drydock-pins.json`: line 25 value, new key, line 11 value. The value written for
   `kernel/brief_complete_engine.py` is pinned because it was *just observed*, never because it
   was observed at Step 3. Do not touch any other pin.
9. `python3 scripts/start_probe.py` — expect `"ok": true`, `"pin_errors": []`.
10. Run the verification commands below; paste output verbatim into `verification.md`.
11. `git status --porcelain` — expect only the intended files; no `.env`, no `scripts/conductor/`
    entry, no `__pycache__` noise.
12. Invoke the verifier subagent. Do not self-certify. Only then may `tasks.md` boxes and
    `verification.md` Result move.

### Verification commands (implementer runs; read-only except where noted)

```bash
# 1. the hole, closed
python3 kernel/brief_engine.py --record-verify does-not-exist; echo "exit=$?"
#    expect: {"recorded": false, "reason": "bare-record-verify-refused", ...}  exit=1

# 2. bytes intact, and hooks resolve from the new location
sha256sum kernel/brief_complete_engine.py    # aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b
python3 kernel/brief_complete_engine.py | head -3; echo "exit=${PIPESTATUS[0]}"   # FACTS JSON, exit=0

# 3. delegation through the overlay
python3 kernel/brief_engine.py | head -3; echo "exit=${PIPESTATUS[0]}"            # FACTS JSON, exit=0

# 3a. WRAPPER-PATH runtime check for the extra execv hop (Codex gap 2).
#     Three interpreter starts: scripts/brief.py -> overlay -> completeness.
#     Byte-for-byte identical FACTS to the direct call is the acceptance criterion,
#     not merely "tests pass".
diff <(python3 scripts/brief.py) <(python3 kernel/brief_complete_engine.py) && echo "HOP OK: identical"
#     expect: no diff output, "HOP OK: identical", exit 0.
#     (Both are deterministic FACTS blocks over the same tree; any drift here means the
#      hop is not transparent and the packet has changed completeness output.)

# 4. bound form still reaches check_verdict (wrong hash -> check_verdict-failed)
python3 kernel/brief_engine.py --record-verify does-not-exist /tmp/v.md $(printf '0%.0s' {1..64}) "VERIFIED WITH NOTES"

# 4a. BOUND-PATH runtime check (Codex gap 2): the bound form gets PAST check_verdict
#     into the moved completeness file. This is the check that catches a
#     record_verify_bound.py still pointing at the overlay (self-refusal deadlock).
printf 'VERIFIED WITH NOTES\n' > /tmp/v.md
python3 kernel/brief_engine.py --record-verify does-not-exist \
    /tmp/v.md "$(sha256sum /tmp/v.md | cut -d' ' -f1)" "VERIFIED WITH NOTES"; echo "exit=$?"
#     expect reason in {bad-name, packet-not-found, gate-failed} -- a COMPLETENESS-side
#     reason, proving check_verdict passed and the moved engine was reached.
#     A reason of "bare-record-verify-refused" here is the deadlock failure (§Risks) and
#     must NOT be read as the new gate working.

# 5. siblings unchanged on the canonical spelling
python3 scripts/brief.py --record-verify does-not-exist; echo "exit=$?"
python3 kernel/brief.py  --record-verify does-not-exist; echo "exit=$?"

# 5a. siblings TIGHTENED on the bypass spellings (§Behavior deltas). Under the OQ-1
#     default these now refuse; before this packet they returned exit 0 and recorded.
#     BAD_NAME is used so the pre-change behavior was side-effect-free (bad-name regex).
python3 kernel/brief.py  --record-verify=BAD_NAME; echo "exit=$?"   # expect refused, exit=1
python3 scripts/brief.py --record-ver BAD_NAME;    echo "exit=$?"   # expect refused, exit=1

# 6. residual is exactly one unadvertised path (§Review criterion 2)
grep -rn "brief_complete_engine" --include=*.py --include=*.md --include=*.json \
     --include=*.yml . | grep -v '^./sdd-plus/'
#     expect only: scripts/record_verify_bound.py, tests/test_kernel_brief_overlay.py,
#     drydock-pins.json, kernel/brief_engine.py (overlay docstring). Nothing else.

# 7. suite + probe
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
python3 scripts/start_probe.py; echo "exit=$?"
git status --porcelain
```

Commands 4 and 4a write `/tmp/v.md` (outside the repo) and must use packet name `does-not-exist`
so no ledger event can be minted. Command 5a uses `BAD_NAME`, which fails `record_verify`'s kebab
regex (`kernel/brief_engine.py:518-519`) and so returns before any `sdd.py` subprocess — this is
what made the same probe safe to run *before* the change while auditing BC1.

## Tests

| Test | File | Asserts |
| --- | --- | --- |
| `test_engine_overlay_bare_record_verify_refused` | `tests/test_kernel_brief_overlay.py` | bare form at `kernel/brief_engine.py` → exit 1, `reason == "bare-record-verify-refused"` |
| `test_engine_overlay_bound_form_still_requires_check_verdict` | same | 4-arg form, bad digest → `check_verdict-failed` |
| `test_engine_overlay_bound_form_reaches_completeness` | same | 4-arg form, real digest → `bad-name`/`packet-not-found`/`gate-failed` (past `check_verdict`) |
| `test_engine_overlay_other_modes_delegate` | same | empty argv → exit 0, FACTS JSON |
| `test_engine_overlay_equals_and_abbrev_forms_refused` | same | OQ-1 default only: 5 parametrized spellings → refused |
| `test_completeness_engine_bytes_unmoved` | same | moved file sha256 == `aa3ba09…`, parent dir is `kernel` |
| `test_completeness_engine_hooks_import_resolves` | same | `parent.parent/"hooks"/"_drydock_common.py"` exists **and** the moved file runs bare with exit 0 |
| `test_completeness_engine_still_has_bare_mode` (retargeted) | same | the moved bytes still contain the mode — the honest residual |
| existing `:22-27`, `:30-35`, `:45-55`, `:58-62` | same | unchanged; `kernel/brief.py` + `kernel/brief_complete.py` behavior preserved |
| `tests/test_brief_wrapper.py` (3 tests) | unmodified | `scripts/brief.py` refuse/bound/delegate still green across the extra hop |
| `tests/test_record_verify_bound.py` (3 tests) | unmodified | bound wrapper still reaches completeness after the retarget |

## Files Expected To Change

- `kernel/brief_complete_engine.py` — **new, moved bytes**, sha256 `aa3ba09…`, never edited.
- `kernel/brief_engine.py` — replaced by the ~75-line overlay of §2.
- `scripts/record_verify_bound.py` — one constant (`:21`) and one docstring line (`:7`).
- `tests/test_kernel_brief_overlay.py` — one constant retargeted, one added, one docstring, six or
  seven new tests.
- `drydock-pins.json` — two values updated (lines 25, 11), one key added.
- Packet artifacts: `tasks.md`, `verification.md`, `decision-log.md`.

Explicitly **not edited**, but with behavior inherited through the delegation edge under the OQ-1
default — see §Behavior deltas on unedited files, and do not read "not edited" as "not affected":
`kernel/brief.py`, `kernel/brief_complete.py`, `scripts/brief.py`. Their pins do not move.

Explicitly **not changed and not affected** (no edit, no pin move, no behavior delta):
`scripts/start_probe.py`, `scripts/check_verdict.py`, `scripts/sdd.py`, `hooks/*` (including
`packet_guard.py`), `backstops/*`, `.github/workflows/drydock.yml`, `scripts/conductor/*`,
`README.md`, `AGENTS.md`, `PROJECT_CONTEXT.md`, `tests/test_brief_wrapper.py`,
`tests/test_record_verify_bound.py`, `reports/`.

## must_not_do

1. **Do not rewrite, retype, reformat, or "tidy" the completeness logic** — not one line, not a
   docstring, not the stale `brief.py` self-reference inside it. The bytes move by `cp`, and
   `kernel/brief_complete_engine.py` must hash to `aa3ba09…` when the packet closes.
2. **Do not move the completeness file out of `kernel/`.** `kernel/vendor/…`, `scripts/…`, or any
   nested directory breaks `_HOOKS` (fact 2) and the module fails at import.
3. **Do not point the overlay's `COMPLETE` at `kernel/brief_engine.py`.** That is an `os.execv`
   self-loop. It must be the moved file.
4. **Do not leave `scripts/record_verify_bound.py:21` pointing at `kernel/brief_engine.py`.** The
   bound path would refuse itself and provenance recording would break for every route (fact 6).
5. **Do not `git mv`, `git rm`, or delete `kernel/brief_engine.py`.** That path must survive as the
   overlay; deleting it breaks `kernel/brief.py:23`, `scripts/brief.py:21`, and the line-25 pin.
6. **Do not edit `kernel/brief.py`, `kernel/brief_complete.py`, or `scripts/brief.py`**, and do not
   move their pins. The extra `execv` hop is the accepted cost (§2).
7. **Do not touch leftover holes 1, 3, or 4** — `.env` write handling, `archive --force` /
   verifier checkboxes, GitHub fast-forward `--force`. They are unparked but not this packet.
8. **Do not rewrite or extend `hooks/packet_guard.py`**, and do not add `kernel/` to any deny class.
9. **Do not edit `.github/workflows/drydock.yml`** and do not edit anything under
   `scripts/conductor/`.
10. **Prefer no `scripts/start_probe.py` edit.** A new pin key needs no code change (fact 8); if
    the implementer believes otherwise, that is an Owner decision, not an implementation detail.
11. **Do not weaken any existing refusal** to make a test pass. The overlay's guard may only be
    equal to or stricter than `kernel/brief.py:28`'s.
12. **Never create a real packet, a real passing gate, or a real `verify-run` ledger event in a
    test or a verification command.** Use `does-not-exist` as the packet name; write verdict files
    under `tmp_path` or `/tmp`, never in the repo.
13. **Re-pin last.** Hashes are computed only after every code edit is final, and
    `scripts/start_probe.py` runs only after the pins are updated.
14. **No commit, no push, no PR, no archive in the planning turn**; no
    `scripts/conductor/negotiate.py` run and no Codex call in the planning turn.
15. **Never `--dangerously-skip-permissions`, never `git config`, never force-push, never
    `git reset --hard`.**
16. **Do not mark anything verified without the verifier subagent.** Implementer evidence is
    evidence, not verification.
17. **Do not resolve OQ-1 by implementing something other than the stated default or the stated
    fallback.** No third matcher design.

Added in round 2, from the Pilot's audit of the Codex critique:

18. **Do not reintroduce the phrase "no contract change"** to describe this packet, in code
    comments, commit messages, `verification.md`, or the completion summary. The accurate framing
    is fixed: *the completeness CLI at the new path is unchanged; the old path gains an additive
    refusal that, under the OQ-1 default, is stricter than `kernel/brief.py:28` and therefore
    changes the observable behavior of two unedited wrappers.* Say that, or say nothing.
19. **Do not add machinery to satisfy BC2.** No helper script, no new pin tool, no wrapper around
    `cp`, no `Makefile` target, no pre-commit addition, no new workflow. The safeguard is the
    ordering and the stop-rules in Steps 2/3/4/4a/8 and the existing
    `test_completeness_engine_bytes_unmoved`. Adding tooling here would widen a LITE packet into a
    new product and is out of scope.
20. **Do not skip Step 4a or Step 8's re-assertion** because Step 3 already passed. They cover
    different failure moments (a mis-targeted overwrite, and drift between the last edit and the
    pin write). "It hashed correctly earlier" is not evidence about the bytes being pinned.
21. **Do not treat `bare-record-verify-refused` from `scripts/record_verify_bound.py` as success.**
    It is the self-refusal deadlock (§Risks, verification command 4a). A packet where *every* path
    refuses, including the bound one, has broken provenance recording, not secured it.

## OQ-1 — strict matcher vs literal copy

**Status: open Owner question with a stated default. The default stands unchanged from round 1.**
This is the one genuine policy call in the packet, and Codex BC1 is right that it must be decided
explicitly rather than absorbed into "no contract change" — which is why it is named here, carried
in `brief.md`, and enumerated in §Behavior deltas rather than left implicit.

- **Asks:** should the new overlay match `--record-verify=NAME` and unambiguous abbreviations
  (fact 11), which `kernel/brief.py:28` does not?
- **Default (build this):** yes — the strict matcher. The overlay is new code; matching only the
  canonical spelling would ship a file whose stated job is "this path no longer records" while
  `python3 kernel/brief_engine.py --record-verify=NAME` still records. Because
  `kernel/brief.py:65-68` and `scripts/brief.py:63-66` delegate non-matching modes *to this
  overlay*, the strict matcher closes the same bypass for them with zero edits and zero extra pins
  on those two files.
- **What choosing the default costs, stated honestly (round 2, per BC1):** it is a **contract
  change on two unedited files**. `kernel/brief.py --record-verify=NAME` and
  `scripts/brief.py --record-ver NAME` go from "records, exit 0" to "refused, exit 1". It is *not*
  true that "nothing that currently works stops working" — the bypass spellings currently work and
  will stop. The claim that survives scrutiny is narrower and is the one the packet makes: **no
  caller in this repo uses those spellings** (fact 12: the only executing caller,
  `scripts/record_verify_bound.py:55`, uses the canonical two-token form), and every delta moves in
  the refuse direction, so nothing legitimate breaks and `append_event` never becomes easier to
  reach. If the Owner disagrees with that trade, the fallback below is the lever.
- **Fallback if the Owner wants byte-parity with `kernel/brief.py`:** delete `_record_verify_index`,
  restore `if "--record-verify" in argv: i = argv.index("--record-verify")`, drop the
  `argv[i] != "--record-verify"` clause, and drop
  `test_engine_overlay_equals_and_abbrev_forms_refused`. ~12 lines deleted, no redesign — and the
  equals/abbreviation bypass is then a *documented, unfixed* residual across all four entry points,
  which should be recorded in `sdd-plus/security/accepted-risks.md` rather than left silent. Under
  the fallback, §Behavior deltas collapses to "no deltas on unedited files" and the Mode section's
  contract-change bullet reduces to point 1 only.
- **Not on the table:** any third matcher design. The overlay is either the strict prefix matcher
  of §2 or the literal copy of `kernel/brief.py:28`. Codex proposed no third option and this plan
  invents none (must_not_do 17).

## Risks

- **The hole moves rather than disappears — say so plainly.** `python3 kernel/brief_complete_engine.py --record-verify NAME`
  still records. It has to: the Owner requires the vendored bytes byte-identical, and a Python file
  under `kernel/` is always directly runnable. What this packet buys is that **every path any
  wrapper, docstring, pin, test, or doc names now refuses**, and the one remaining path is an
  unadvertised filename that only `scripts/record_verify_bound.py` — the gate itself — points at.
  This is defense by choreography, not removal of a capability. It should be recorded as an
  accepted residual, and `test_completeness_engine_still_has_bare_mode`'s retargeted docstring is
  where the repo keeps saying it out loud.
- **Renaming as a security control has a shelf life.** The next person to look for "the brief
  engine" will find `kernel/brief_complete_engine.py`. Mitigation: the moved file's neighbours are
  four gated entry points, and `record_verify_bound.py`'s docstring names the contract. Genuinely
  closing this needs the completeness bytes to stop being independently executable — a Drydock
  upstream change, not a sandbox packet.
- **Self-refusal deadlock.** If step 5 is skipped, `record_verify_bound.py` calls the overlay with
  the bare form and gets `bare-record-verify-refused` — provenance recording breaks entirely and
  the failure looks like a *success* of the new gate. `test_engine_overlay_bound_form_reaches_completeness`
  and the existing `tests/test_record_verify_bound.py:44-53` are the tripwires.
- **`execv` loop.** If the overlay's `COMPLETE` points at itself, `python3 kernel/brief_engine.py`
  spawns interpreters until the machine complains. Caught immediately by
  `test_engine_overlay_other_modes_delegate` — but the implementer should run
  `python3 kernel/brief_engine.py` once by hand right after step 4, before pytest, so a loop is
  found in one process rather than under the test runner.
- **`_HOOKS` breakage if the file lands in a subdirectory.** Fails loudly at import
  (traceback, non-zero exit) rather than silently, and
  `test_completeness_engine_hooks_import_resolves` pins it.
- **Pin/probe ordering.** Editing before re-pinning makes `check_pins()` fail on lines 25 and 11;
  re-pinning before the files are final pins the wrong bytes. §5 fixes the order.
- **Accidental byte change to the moved file.** An editor auto-formatting on save, a trailing
  newline normalization, or a helpful "fix the docstring path" would break `aa3ba09…`.
  `test_completeness_engine_bytes_unmoved` plus `check_pins()` catch it after the fact; Steps 3,
  4a and 8 catch it at the three moments it can happen; the rule is simply never to open that file
  for editing. This is Codex BC2's concern and it is answered by ordering and stop-rules, not by
  new tooling.
- **The strict matcher as a future maintenance trap** (raised by Codex; new to this section). If a
  later option is added to the completeness engine that shrinks argparse's unambiguous prefix
  space — say `--record-hash` — then `--record` becomes ambiguous and argparse itself exits 2,
  while the overlay's prefix matcher still matches `--record` and refuses with exit 1. Both are
  non-zero and neither records. The failure mode is that the matcher becomes *over*-broad, and
  over-broad here means refusing a token the parser would have rejected anyway. It cannot become
  under-broad without someone editing `_record_verify_index`. Accepted without design change; a
  future packet that adds engine options should re-read fact 11's table.
- **The contract change on unedited wrappers.** `kernel/brief.py` and `scripts/brief.py` change
  observable behavior — including exit codes — without being edited or re-pinned, which is
  surprising to a reader who greps the diff for their names and finds nothing. Mitigated by
  §Behavior deltas on unedited files, verification command 5a, and the parametrized refusal test;
  bounded by fact 12. This is a real cost of the OQ-1 default, not a neutral one.
- **Extra `execv` hop.** `scripts/brief.py` → overlay → completeness is now three interpreter
  starts for a FACTS run. Measurable, irrelevant at this scale, and the alternative is editing and
  re-pinning two more files. `tests/test_brief_wrapper.py:41-45` proves the hop works.
- **Scope creep.** Leftover holes 1/3/4, `packet_guard`, workflow and conductor edits are all
  fenced in `must_not_do`.

## Rollback

Single-commit revert. `git revert <sha>` restores `kernel/brief_engine.py` to the `aa3ba09…`
completeness bytes, deletes `kernel/brief_complete_engine.py`, restores
`scripts/record_verify_bound.py:21` to `kernel/brief_engine.py`, restores
`tests/test_kernel_brief_overlay.py`, and restores all three pin values together — so there is no
intermediate state where `check_pins()` fails on its own hashes or where the bound path refuses
itself. Nothing outside the repo changes: no migration, no data, no config, no `.git/hooks` change,
no external state, and no ledger event is written by this packet.

Manual fallback if the revert is awkward mid-stack, in this order: (1) copy
`kernel/brief_complete_engine.py` back over `kernel/brief_engine.py` and confirm `aa3ba09…`;
(2) delete `kernel/brief_complete_engine.py`; (3) set `scripts/record_verify_bound.py:21` back to
`ROOT / "kernel" / "brief_engine.py"` and restore its `:7` docstring line; (4) restore
`drydock-pins.json` line 25 to `aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b`,
line 11 to
`43bc4ddae631fc2c0726d93dc053028aa767b232fc58da96811e365b5d3eda89`, and remove the
`kernel/brief_complete_engine.py` key; (5) revert `tests/test_kernel_brief_overlay.py`;
(6) `python3 scripts/start_probe.py` to confirm `ok: true`.
