#!/usr/bin/env python3
"""SDD+ change packet helper. Cross-platform replacement for scripts/sdd.ps1.

Commands:
  init                       Create the sdd-plus directory structure.
  new <kebab-change-name>    Create a change packet from templates.
  status                     List active changes and task counts.
  verify <kebab-change-name> Check required artifacts exist and are filled in.
  archive <kebab-change-name> [--force]  Move a completed change to the archive.
"""

import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

REQUIRED_FILES = ["brief.md", "plan.md", "tasks.md", "decision-log.md", "verification.md"]
SDD_DIRS = ["sdd-plus", "sdd-plus/standards", "sdd-plus/specs",
            "sdd-plus/specs/capabilities", "sdd-plus/changes",
            "sdd-plus/archive", "sdd-plus/templates"]
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

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


def find_root(require: bool = True) -> Path:
    """Walk up from cwd looking for an sdd-plus directory. Never falls back silently."""
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "sdd-plus").is_dir():
            return candidate
    if require:
        sys.exit("error: no sdd-plus directory found in this or any parent directory. "
                 "Run 'python3 scripts/sdd.py init' (on Windows: 'python') from the project root first.")
    return current


def assert_kebab(name: str) -> None:
    if not name:
        sys.exit("error: change name is required.")
    if not KEBAB.match(name):
        sys.exit("error: change name must be kebab-case, e.g. improve-search-flow.")


def cmd_init() -> None:
    root = find_root(require=False)
    for d in SDD_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    print(f"Initialized SDD+ directories under {root}")


def render_template(template: Path, target: Path, change_name: str) -> None:
    content = template.read_text(encoding="utf-8-sig")  # tolerate legacy BOMs on read
    content = content.replace("{{CHANGE_NAME}}", change_name)
    content = content.replace("{{DATE}}", datetime.date.today().isoformat())
    target.write_text(content, encoding="utf-8")  # never write a BOM


def cmd_new(name: str) -> None:
    assert_kebab(name)
    root = find_root()
    change_dir = root / "sdd-plus" / "changes" / name
    if change_dir.exists():
        sys.exit(f"error: change already exists: {change_dir.relative_to(root)}")
    change_dir.mkdir(parents=True)
    template_dir = root / "sdd-plus" / "templates"
    for fname in REQUIRED_FILES:
        template = template_dir / fname
        target = change_dir / fname
        if template.is_file():
            render_template(template, target, name)
        else:
            target.write_text(f"# {fname}\n\nChange: {name}\n", encoding="utf-8")
    specs_dir = change_dir / "specs"
    specs_dir.mkdir()
    delta_template = template_dir / "spec-delta.md"
    if delta_template.is_file():
        render_template(delta_template, specs_dir / "EXAMPLE-capability.md.template", name)
    print(f"Created change: {change_dir.relative_to(root)}")
    print("If this change modifies system behavior, add delta specs under "
          f"{specs_dir.relative_to(root)}/<capability>.md")


def task_counts(tasks_path: Path) -> tuple[int, int]:
    if not tasks_path.is_file():
        return 0, 0
    lines = tasks_path.read_text(encoding="utf-8-sig").splitlines()
    complete = sum(1 for l in lines if re.match(r"^\s*-\s*\[[xX]\]\s+", l))
    pending = sum(1 for l in lines if re.match(r"^\s*-\s*\[\s\]\s+", l))
    return complete, pending


def delta_spec_files(change_dir: Path) -> list[Path]:
    specs_dir = change_dir / "specs"
    if not specs_dir.is_dir():
        return []
    return sorted(p for p in specs_dir.glob("*.md") if not p.name.endswith(".template"))


def delta_capabilities_in_file(delta_file: Path) -> list[str]:
    """The capability declared in a single delta file, if it is a valid kebab-case
    name appearing outside any fenced code block. Returns [] when the line is
    missing, still the placeholder, fenced, or not kebab-case — callers fail
    closed on [] rather than skip the sync gate silently."""
    in_code = False
    for line in delta_file.read_text(encoding="utf-8-sig").splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.lower().startswith("capability:"):
            raw = line.split(":", 1)[1].strip()
            if "<" in raw or ">" in raw:  # unfilled angle-bracket placeholder
                return []
            cap = raw.strip("`").strip()
            if KEBAB.match(cap):
                return [cap]
            return []
    return []


def delta_capabilities(change_dir: Path) -> list[str]:
    caps: list[str] = []
    for f in delta_spec_files(change_dir):
        for cap in delta_capabilities_in_file(f):
            if cap not in caps:
                caps.append(cap)
    return caps


def delta_added_requirements(delta_file: Path) -> list[str]:
    """Requirement names the delta ADDS, per the spec-delta template grammar:
    `### Requirement: <name>` headings appearing under a `## ADDED Requirements`
    section. Used to confirm the living spec actually contains them — i.e. the
    delta was synced, not just that the capability file exists. MODIFIED/REMOVED/
    RENAMED are intentionally not checked here (rarer, harder; see decision-log)."""
    reqs = []
    in_added = False
    in_code = False
    for line in delta_file.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^##(?!#)\s", line):  # any level-2 heading closes the ADDED section
            in_added = bool(re.match(r"^##\s+ADDED\s+Requirements\s*$", line, re.IGNORECASE))
            continue
        if in_added:
            m_req = re.match(r"^###\s+Requirement:\s*(.+?)\s*$", line, re.IGNORECASE)
            if m_req:
                name = m_req.group(1).strip().strip("`")
                if name and not name.startswith("<"):
                    reqs.append(name)
    return reqs


def requirement_present(living_spec: Path, requirement: str) -> bool:
    """True if the living spec has a `### Requirement: <name>` heading whose name
    equals this requirement (whitespace/case-normalized). Exact name, not a
    substring — so 'Session' does not match '### Requirement: Session Expiry'."""
    if not living_spec.is_file():
        return False
    target = " ".join(requirement.strip().strip("`").lower().split())
    in_code = False
    for line in living_spec.read_text(encoding="utf-8-sig").splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^#{2,4}\s+Requirement:\s*(.+?)\s*$", line, re.IGNORECASE)
        if m:
            name = " ".join(m.group(1).strip().strip("`").lower().split())
            if name == target:
                return True
    return False


def text_has_placeholder(text: str) -> bool:
    """True if the text still carries template placeholder residue. Fenced blocks
    and inline `code` spans are ignored, so a brief/decision-log that quotes a
    placeholder form as an example is not flagged. Detects {{CHANGE_NAME}}, or TBD
    as a whole line / list item / checkbox / real (non-quoted) table cell."""
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        bare = re.sub(r"`[^`]*`", "", line)  # drop inline code spans (mentions)
        if "{{CHANGE_NAME}}" in bare:
            return True
        if re.match(r"^\s*-?\s*(\[[ xX]?\]\s*)?TBD\s*$", bare):
            return True
        if bare.lstrip().startswith("|") and re.search(r"\|\s*TBD\s*\|", bare):
            return True
    return False


def verification_result_is_pending(text: str) -> bool:
    """True if verification.md's `## Result` section is empty or still 'Pending.'."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^##\s+Result\s*$", line, re.IGNORECASE):
            collected = []
            for nxt in lines[i + 1:]:
                if re.match(r"^#{1,6}\s", nxt):
                    break
                if nxt.strip():
                    collected.append(nxt.strip())
            joined = " ".join(collected).strip().lower().rstrip(".")
            return joined in ("", "pending")
    return False


def delta_heading_issues(delta_file: Path) -> list[str]:
    """Non-canonical requirement headings under `## ADDED Requirements`. The living
    specs use `### Requirement: <name>`; a delta authored as `### R5 — <name>` is
    NOT machine-verifiable — `delta_added_requirements` returns [] for it, so the
    'is this delta synced?' gate passes VACUOUSLY and an unsynced delta can archive
    clean. Surfacing these headings is what lets verify warn and the ready-prompt
    refuse to claim READY on grammar it cannot confirm. Returns the offending lines."""
    issues, in_added, in_code = [], False, False
    for line in delta_file.read_text(encoding="utf-8-sig").splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^##(?!#)\s", line):
            in_added = bool(re.match(r"^##\s+ADDED\s+Requirements\s*$", line, re.IGNORECASE))
            continue
        # a level-3 heading under ADDED that is not the canonical Requirement: form
        if in_added and re.match(r"^###\s", line) and not re.match(
                r"^###\s+Requirement:\s*\S", line, re.IGNORECASE):
            issues.append(line.strip())
    return issues


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


def archive_readiness(change_dir: Path, caps_dir: Path, *,
                      bound: "VerdictBinding | None" = None) -> list[tuple[str, str]]:
    """The single, read-only list of WAIVABLE blockers between a packet and
    archive. cmd_archive enforces it and the ready-prompt reads it, so the prompt
    can NEVER claim ready when archive would block — they consult one function.
    Returns [(category, message), ...]; an empty list means archive-eligible.

    Read-only but NOT side-effect-free: it spawns scripts/check_verdict.py through
    verdict_binding to decide whether an independent verifier verdict is bound to
    bytes in this packet. AT MOST ONE subprocess per call, and ZERO when the packet
    claims nothing (no verifier-report.md and no verifier-report.sha256). The
    keyword-only `bound=` parameter exists solely so a caller that has ALREADY
    computed the binding for THIS SAME change_dir can avoid a second identical
    spawn; passing a binding computed for a different directory is a caller bug.
    Policy, spawn budget and every fail-closed mode: plan.md section F.

    Deliberately does not fabricate confidence: it reports what is provably wrong.
    Grammar it cannot machine-verify is surfaced separately (delta_heading_issues)
    so the ready-prompt fails toward 'needs sync' rather than a vacuous pass."""
    blockers: list[tuple[str, str]] = []
    unattributable = [f.name for f in delta_spec_files(change_dir)
                      if not delta_capabilities_in_file(f)]
    if unattributable:
        blockers.append(("unattributable",
                         "delta spec(s) with no valid 'Capability:' line: "
                         + ", ".join(unattributable)))
    unsynced = [cap for cap in delta_capabilities(change_dir)
                if not (caps_dir / f"{cap}.md").is_file()]
    if unsynced:
        blockers.append(("unsynced-capability",
                         "capabilities with no living spec yet: " + ", ".join(unsynced)))
    missing_reqs = []
    for delta_file in delta_spec_files(change_dir):
        for cap in delta_capabilities_in_file(delta_file):
            living = caps_dir / f"{cap}.md"
            for req in delta_added_requirements(delta_file):
                if not requirement_present(living, req):
                    missing_reqs.append(f"{cap}: {req}")
    if missing_reqs:
        blockers.append(("missing-requirement",
                         "delta requirements not present in the living spec "
                         "(delta not synced?): " + "; ".join(missing_reqs)))
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


def cmd_status() -> None:
    root = find_root()
    changes_root = root / "sdd-plus" / "changes"
    changes = sorted(p for p in changes_root.iterdir() if p.is_dir()) if changes_root.is_dir() else []
    if not changes:
        print("No active SDD+ changes.")
        return
    for change in changes:
        complete, pending = task_counts(change / "tasks.md")
        deltas = delta_spec_files(change)
        suffix = f", {len(deltas)} delta spec(s)" if deltas else ""
        print(f"{change.name}: {complete} complete, {pending} pending{suffix}")


def _classify_packet(change_dir: Path, caps_dir: Path) -> tuple[str, str]:
    """Bucket one packet. Robust by construction: any error becomes UNKNOWN, so a
    single broken packet (a missing REQUIRED_FILE — precisely the messiest backlog
    entries) never aborts the batch. Uses the same predicates as verify/archive."""
    try:
        missing = [f for f in REQUIRED_FILES if not (change_dir / f).is_file()]
        if missing:
            return "IN-PROGRESS", "missing " + ", ".join(missing)
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
        if any(delta_heading_issues(f) for f in delta_spec_files(change_dir)):
            return "NEEDS-SYNC", "non-canonical delta grammar; run /drydock:sync"
        if archive_readiness(change_dir, caps_dir, bound=bound):
            return "NEEDS-SYNC", "delta specs not yet in the living specs"
        return "ARCHIVE-READY", "verified + synced"
    except Exception as e:  # noqa: BLE001 — a triage crash must never abort the sweep
        return "UNKNOWN", str(e)[:70]


_TRIAGE_ORDER = ["ARCHIVE-READY", "NEEDS-SYNC", "CLAIMED-DONE-UNVERIFIED",
                 "IN-PROGRESS", "UNKNOWN"]
_TRIAGE_NEXT = {
    "ARCHIVE-READY": "python3 scripts/sdd.py archive <name>",
    "NEEDS-SYNC": "/drydock:sync <name>, then archive",
    "CLAIMED-DONE-UNVERIFIED": "fill verification.md + /drydock:verify <name>  "
                               "(or archive <name> --abandon --reason \"…\" if truly abandoned)",
    "IN-PROGRESS": "finish the packet, or abandon it",
    "UNKNOWN": "inspect by hand",
}


def cmd_triage() -> None:
    """Read-only. Bucket every active packet and print a per-bucket next action, so
    a backlog can be drained deliberately: archive the ready ones, sync the rest,
    and make an explicit per-packet call on the ones abandoned mid-lifecycle."""
    root = find_root()
    changes = root / "sdd-plus" / "changes"
    caps_dir = root / "sdd-plus" / "specs" / "capabilities"
    dirs = sorted(p for p in changes.iterdir() if p.is_dir()) if changes.is_dir() else []
    dirs = [d for d in dirs if KEBAB.match(d.name)]
    if not dirs:
        print("No active SDD+ changes.")
        return
    buckets: dict[str, list] = {}
    for ch in dirs:
        bucket, detail = _classify_packet(ch, caps_dir)
        buckets.setdefault(bucket, []).append((ch.name, detail))
    print(f"{len(dirs)} active packet(s):")
    for bucket in _TRIAGE_ORDER:
        items = buckets.get(bucket, [])
        if not items:
            continue
        print(f"\n{bucket} ({len(items)}) — next: {_TRIAGE_NEXT[bucket]}")
        for nm, detail in items:
            print(f"  - {nm}: {detail}")


def cmd_verify(name: str, show_ready_prompt: bool = True) -> int:
    assert_kebab(name)
    root = find_root()
    change_dir = root / "sdd-plus" / "changes" / name
    if not change_dir.is_dir():
        sys.exit(f"error: change not found: sdd-plus/changes/{name}")

    standards_dir = root / "sdd-plus" / "standards"
    if not standards_dir.is_dir() or not any(standards_dir.iterdir()):
        sys.exit("error: no standards found under sdd-plus/standards.")

    missing = [f for f in REQUIRED_FILES if not (change_dir / f).is_file()]
    if missing:
        sys.exit(f"error: missing required artifacts: {', '.join(missing)}")

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

    # Delta grammar lint — surfaced every verify. Non-canonical headings make the
    # sync gate unverifiable, so they are worth naming even when the packet is green.
    heading_issues = [iss for f in delta_spec_files(change_dir)
                      for iss in delta_heading_issues(f)]
    if heading_issues:
        print(f"warning: {len(heading_issues)} delta requirement heading(s) are not the "
              "canonical '### Requirement: <name>' form (e.g. "
              f"{heading_issues[0]!r}); sync cannot be machine-verified until they are "
              "normalized. Run /drydock:sync.")

    # Ready-to-archive prompt: the well-timed moment green is learned. It FAILS
    # TOWARD 'needs sync' — READY prints only on positive confirmation, never from a
    # merely empty blocker list, so a non-canonical or unsynced delta cannot read as
    # ready. This closes the pre-existing vacuous-pass hole.
    if show_ready_prompt:
        if heading_issues:
            print("Not archive-ready: delta grammar is not machine-verifiable — "
                  "run /drydock:sync, then verify again.")
        elif blockers:
            sync_only = all(c in ("unsynced-capability", "missing-requirement")
                            for c, _ in blockers)
            if sync_only:
                print("Nearly there: delta specs aren't synced into the living specs "
                      "yet. Run /drydock:sync, then archive.")
            else:
                print("Not archive-ready: " + "; ".join(m for _, m in blockers))
        else:
            print(f"READY TO ARCHIVE — run: python scripts/sdd.py archive {name}")
    return 1 if blocking_unfilled else 0


def record_override(change_dir: Path, waived: list, reason: str) -> None:
    """Append an auditable override record to the change's decision-log.md.

    Overrides travel with the packet into archive/, so a forced archive always
    leaves a paper trail of which gate(s) were waived and why."""
    entry = (f"\n## Override — {datetime.date.today().isoformat()}\n"
             f"- Gates waived: {'; '.join(waived)}\n"
             f"- Reason: {reason}\n")
    with (change_dir / "decision-log.md").open("a", encoding="utf-8") as f:
        f.write(entry)


def _replace_result_section(text: str, new_body: str) -> str:
    """Replace the `## Result` section with a NORMALIZED `## Result` heading + new_body
    (append one if absent). The heading match is liberal (`## Result:`, `## Result PASS`)
    and the heading line is rewritten clean — so a stray verdict written onto a
    malformed heading line cannot survive an abandon."""
    lines = text.splitlines()
    out, i, replaced = [], 0, False
    while i < len(lines):
        if re.match(r"^##\s+Result\b", lines[i], re.IGNORECASE):
            out.extend(["## Result", "", new_body])   # drop any inline text on the heading
            i += 1
            while i < len(lines) and not re.match(r"^#{1,6}\s", lines[i]):
                i += 1
            replaced = True
            continue
        out.append(lines[i])
        i += 1
    if not replaced:
        out.extend(["", "## Result", "", new_body])
    return "\n".join(out) + "\n"


def _unsynced_requirements(change_dir: Path, caps_dir: Path) -> list[str]:
    """Canonical delta requirements not present in a living spec — the spec
    knowledge an abandon would entomb unharvested (non-canonical grammar cannot be
    checked, so it is not counted as safely-synced either)."""
    missing = []
    for f in delta_spec_files(change_dir):
        for cap in delta_capabilities_in_file(f):
            living = caps_dir / f"{cap}.md"
            for req in delta_added_requirements(f):
                if not requirement_present(living, req):
                    missing.append(f"{cap}: {req}")
    return missing


def cmd_abandon(name: str, reason: str) -> None:
    """Archive a packet as ABANDONED — never verified. Distinct from --force: it
    records the ABSENCE of a verification (never a synthesized PASS), warns when it
    buries unsynced spec knowledge, and — like archive — only MOVES, never deletes."""
    if not reason.strip():
        sys.exit('error: --abandon requires a non-empty --reason "<why>" — the honest '
                 "record of why this packet is being buried unverified.")
    assert_kebab(name)
    root = find_root()
    change_dir = root / "sdd-plus" / "changes" / name
    caps_dir = root / "sdd-plus" / "specs" / "capabilities"
    if not change_dir.is_dir():
        sys.exit(f"error: change not found: sdd-plus/changes/{name}")
    archive_root = root / "sdd-plus" / "archive"
    target = archive_root / f"{datetime.date.today().isoformat()}-{name}"
    # Collision check BEFORE any mutation, so a name clash leaves the packet fully
    # intact in changes/ (never a half-abandoned packet, never a duplicate Override).
    if target.exists():
        sys.exit(f"error: archive already exists: {target.relative_to(root)}")

    # Warn about ALL spec knowledge this abandon buries — canonical unsynced
    # requirements AND deltas whose sync cannot even be verified (non-canonical
    # grammar or no Capability line). triage and verify are loud about these; abandon
    # — the permanently-lossy operation, run on precisely these messy packets — must
    # not be the one place that goes quiet.
    entombed = _unsynced_requirements(change_dir, caps_dir)
    unverifiable = sorted(f.name for f in delta_spec_files(change_dir)
                          if delta_heading_issues(f) or not delta_capabilities_in_file(f))
    if entombed or unverifiable:
        print("warning: this abandon buries spec knowledge not in the living specs "
              "(it will not be harvested):")
        if entombed:
            print("  - unsynced requirements: " + "; ".join(entombed))
        if unverifiable:
            print("  - deltas whose sync cannot be verified (non-canonical grammar or "
                  "no Capability line): " + ", ".join(unverifiable))

    verif = change_dir / "verification.md"
    text = verif.read_text(encoding="utf-8-sig") if verif.is_file() \
        else "# Verification\n\n## Result\n\nPending.\n"
    body = (f"Abandoned {datetime.date.today().isoformat()} — never verified. "
            f"Reason: {reason}")
    verif.write_text(_replace_result_section(text, body), encoding="utf-8")

    waived = ["ABANDONED — never verified (archive gates not checked)"]
    if entombed:
        waived.append("entombs unsynced requirements (" + "; ".join(entombed) + ")")
    if unverifiable:
        waived.append("entombs unverifiable deltas (" + ", ".join(unverifiable) + ")")
    record_override(change_dir, waived, reason)

    archive_root.mkdir(parents=True, exist_ok=True)
    shutil.move(str(change_dir), str(target))
    print(f"Abandoned (never verified) and moved to: {target.relative_to(root)}")


def cmd_archive(name: str, force: bool, reason: str = "") -> None:
    if force and not reason:
        sys.exit('error: --force requires --reason "<why>" so the override is auditable '
                 "(it is recorded to the packet's decision-log.md). "
                 f'e.g. archive {name} --force --reason "hotfix; tests tracked in #123".')
    cmd_verify(name, show_ready_prompt=False)  # prints status; hard-exits on missing artifacts
    root = find_root()
    change_dir = root / "sdd-plus" / "changes" / name
    caps_dir = root / "sdd-plus" / "specs" / "capabilities"

    # One shared readiness check — the same list the ready-prompt reads, so the
    # prompt can never disagree with what archive enforces.
    blockers = archive_readiness(change_dir, caps_dir)
    waived = [msg for _, msg in blockers]
    if blockers and not force:
        lines = "\n".join(f"  - {msg}" for _, msg in blockers)
        if any(c == "unbound-verdict" for c, _ in blockers):
            hint = ("Bind the verifier verdict: put the report verbatim in "
                    f"{VERIFIER_REPORT} and the sha256 it was stated with in "
                    f"{VERIFIER_SHA}")
        elif any(c in ("unsynced-capability", "missing-requirement") for c, _ in blockers):
            hint = "Run /drydock:sync first"
        else:
            hint = "Complete the packet"
        sys.exit(f"error: not archive-ready:\n{lines}\n{hint}, or rerun with --force.")
    if force and waived:
        record_override(change_dir, waived, reason)
        print(f"OVERRIDE recorded in decision-log.md: waived {len(waived)} gate(s) — {reason}")
    archive_root = root / "sdd-plus" / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    target = archive_root / f"{datetime.date.today().isoformat()}-{name}"
    if target.exists():
        sys.exit(f"error: archive already exists: {target.relative_to(root)}")
    shutil.move(str(change_dir), str(target))
    print(f"Archived change: {target.relative_to(root)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SDD+ change packet helper.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    p_new = sub.add_parser("new")
    p_new.add_argument("name")
    sub.add_parser("status")
    sub.add_parser("triage")
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("name")
    p_archive = sub.add_parser("archive")
    p_archive.add_argument("name")
    p_archive.add_argument("--force", action="store_true")
    p_archive.add_argument("--abandon", action="store_true",
                           help="archive as ABANDONED — never verified (distinct from "
                                "--force); records the absence of a result, never a PASS")
    p_archive.add_argument("--reason", default="",
                           help="required with --force or --abandon: why "
                                "(recorded to the packet's decision-log.md)")
    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "new":
        cmd_new(args.name)
    elif args.command == "status":
        cmd_status()
    elif args.command == "triage":
        cmd_triage()
    elif args.command == "verify":
        sys.exit(cmd_verify(args.name))
    elif args.command == "archive":
        if args.abandon:
            if args.force:
                sys.exit("error: use either --abandon or --force, not both — they are "
                         "different dispositions (abandon records 'never verified'; "
                         "force waives a specific gate on work you stand behind).")
            cmd_abandon(args.name, args.reason)
        else:
            cmd_archive(args.name, args.force, args.reason)


if __name__ == "__main__":
    main()
