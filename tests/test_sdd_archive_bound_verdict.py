"""archive is READY from a BOUND verifier verdict on disk, not from ticked boxes.

Three tiers (plan.md section F.7):
  Tier 1  pure unit -- verdict_line, sidecar_digest, verifier_owned_pending,
          packet_unfilled_reasons. No subprocess, no tree.
  Tier 2  binding + readiness contract against the REAL scripts/check_verdict.py.
  Tier 3  end-to-end CLI under _isolated_tree; stdout asserted as SUBSTRINGS only.

Every packet is built under tmp_path. cmd_archive MOVES a directory, so it is only
ever called behind _isolated_tree, whose `assert sdd.find_root() == tmp_path` is
the mechanical guard against archiving a live packet. The single deliberate
exception to tmp_path-only is test #19d, which READS the real tasks.md corpus to
hold the plan.md section E.1 inventory as a contract. It writes nothing.

No test mints a verify-run or ledger event: no --record-verify, no
kernel/brief_complete_engine.py, no scripts/record_verify_bound.py.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import sdd  # noqa: E402


CLEAN = {                                   # no TBD, no {{CHANGE_NAME}}
    "brief.md":        "# Brief\n\n## Acceptance Criteria\n\n- [ ] Something real.\n",
    "plan.md":         "# Plan\n\n## Approach\n\nDo the thing.\n",
    "tasks.md":        "# Tasks\n\n- [x] Implement the smallest coherent change.\n",
    "decision-log.md": "# Decision Log\n\nNo decisions needed.\n",
    "verification.md": "# Verification\n\n## Result\n\nPending.\n",
}
REPORT = "# Verification Report\n\n## Isolation\n\nMutation: zero.\n\n## Verdict\n{v}\n"

# One implementer task done, one verifier-owned task pending -- the exact shape a
# bound verdict is meant to waive (archive/2026-09-02-grok-coplan-closure-gate:47).
VERIFIER_TASKS = ("# Tasks\n\n## Implementation\n\n"
                  "- [x] Implement the smallest coherent change.\n"
                  "- [ ] Invoke the verifier subagent; do not self-certify.\n")

HEX0 = "0" * 64


def _packet(tmp_path, *, name="demo", tasks=None, result="Pending.", report=None,
            sidecar=None, files=None) -> Path:
    """A fake packet under tmp_path/sdd-plus/changes/<name>. Never the live tree."""
    d = tmp_path / "sdd-plus" / "changes" / name
    d.mkdir(parents=True, exist_ok=True)
    content = dict(CLEAN)
    if tasks is not None:
        content["tasks.md"] = tasks
    content["verification.md"] = f"# Verification\n\n## Result\n\n{result}\n"
    content.update(files or {})
    for fname, text in content.items():
        (d / fname).write_text(text, encoding="utf-8")
    if report is not None:
        (d / sdd.VERIFIER_REPORT).write_text(report, encoding="utf-8")
    if sidecar is not None:
        (d / sdd.VERIFIER_SHA).write_text(sidecar, encoding="utf-8")
    return d


def _bound(tmp_path, verdict="VERIFIED WITH NOTES", **kw) -> Path:
    """_packet(...) whose sidecar holds the true sha256 of the report bytes."""
    kw.setdefault("report", REPORT.format(v=verdict))
    kw.setdefault("tasks", VERIFIER_TASKS)
    d = _packet(tmp_path, **kw)
    r = d / sdd.VERIFIER_REPORT
    (d / sdd.VERIFIER_SHA).write_text(
        hashlib.sha256(r.read_bytes()).hexdigest() + "\n", encoding="utf-8")
    return d


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


def _caps(tmp_path) -> Path:
    return tmp_path / "sdd-plus" / "specs" / "capabilities"


def _cats(blockers) -> list:
    return [c for c, _ in blockers]


# --------------------------------------------------------------------------
# Tier 1 -- pure unit
# --------------------------------------------------------------------------

@pytest.mark.parametrize("verdict", ["VERIFIED", "VERIFIED WITH NOTES", "NOT VERIFIED"])
def test_verdict_line_extracts_single_line(verdict):
    """#1"""
    assert sdd.verdict_line(REPORT.format(v=verdict)) == verdict


def test_verdict_line_rejects_multi_line_section():
    """#2 -- a Verdict section carrying prose beside the verdict is not decidable."""
    text = "# R\n\n## Verdict\nVERIFIED WITH NOTES\nwith one caveat about scope.\n"
    assert sdd.verdict_line(text) == ""


def test_verdict_line_rejects_missing_section():
    """#3"""
    assert sdd.verdict_line("# R\n\n## Isolation\n\nMutation: zero.\n") == ""


@pytest.mark.parametrize("body", [
    "{h}\n",
    "{h}  verifier-report.md\n",
    "{h} *verifier-report.md\n",
    "# sha256 of the report the verifier stated in channel\n{h}\n",
])
def test_sidecar_digest_accepts_bare_hex_and_sha256sum_form(body):
    """#4 -- pasted hex and both `sha256sum` output forms are accepted."""
    h = "a" * 64
    assert sdd.sidecar_digest(body.format(h=h)) == h


@pytest.mark.parametrize("text", [
    "",
    "not-a-hash\n",
    "b" * 63 + "\n",
    "b" * 65 + "\n",
    "c" * 64 + "\n" + "d" * 64 + "\n",
    "e" * 64 + "  other.md\n",
])
def test_sidecar_digest_rejects_malformed(text):
    """#5 -- anything outside the stated grammar fails closed."""
    assert sdd.sidecar_digest(text) == ""


@pytest.mark.parametrize("tasks", [
    "# Tasks\n\n- [ ] a\n- [ ] b\n",
    VERIFIER_TASKS,
    ("# Tasks\n\n## Verification (verifier subagent — not the Implementer)\n\n"
     "- [ ] Independently re-run the test suite.\n- [ ] Set the verification Result.\n"),
    "# Tasks\n\n## Implementation\n\n- [x] all done\n",
])
def test_owner_split_totals_match_task_counts(tmp_path, tasks):
    """#16 -- the split can never drift from task_counts: owned + other == pending."""
    p = tmp_path / "tasks.md"
    p.write_text(tasks, encoding="utf-8")
    owned, other = sdd.verifier_owned_pending(p)
    assert owned + other == sdd.task_counts(p)[1]


@pytest.mark.parametrize("line", [
    # archive/2026-09-02-grok-refuse-brief-engine/tasks.md:57, verbatim
    "- [ ] Step 12 — Invoke the verifier subagent. Do not self-certify. Only then may these boxes and",
    # archive/2026-09-02-grok-coplan-closure-gate/tasks.md:47, verbatim
    "- [ ] Invoke the verifier subagent; do not self-certify.",
    "- [ ] Invoke the `verifier` subagent; do not self-certify.",
    "- [ ] Invoke the **verifier subagent**; do not self-certify.",
    "- [ ] Invoke the verifier sub-agent; do not self-certify.",
])
def test_verifier_owned_line_form(tmp_path, line):
    """#17 -- closed set: every line-form wording in plan.md section E.1."""
    p = tmp_path / "tasks.md"
    p.write_text(f"# Tasks\n\n## Implementation\n\n{line}\n", encoding="utf-8")
    assert sdd.verifier_owned_pending(p) == (1, 0)


def test_verifier_owned_section_form(tmp_path):
    """#18 -- archive/2026-09-01-grok-choreography-smoke/tasks.md:18-23, verbatim."""
    p = tmp_path / "tasks.md"
    p.write_text(
        "# Tasks\n\n## Implementation\n\n"
        "- [x] Run tests locally and record actual output in `verification.md`.\n\n"
        "## Verification (verifier subagent — not the Implementer)\n\n"
        "- [ ] Independently re-run the test suite.\n"
        "- [ ] Review the diff against brief scope and protected-path constraints.\n"
        "- [ ] Confirm evidence claims in `verification.md`.\n"
        "- [ ] Set the verification Result.\n", encoding="utf-8")
    assert sdd.verifier_owned_pending(p) == (4, 0)


def test_verifier_section_closes_on_next_level_two_heading(tmp_path):
    """#18 -- a following `## Notes` closes the section; a `###` inside does not."""
    p = tmp_path / "tasks.md"
    p.write_text(
        "# Tasks\n\n## Verification (verifier subagent — not the Implementer)\n\n"
        "- [ ] Independently re-run the test suite.\n\n"
        "### Sub-heading that must NOT reset the section\n\n"
        "- [ ] Set the verification Result.\n\n"
        "## Notes\n\n"
        "- [ ] Implement the smallest coherent change.\n", encoding="utf-8")
    assert sdd.verifier_owned_pending(p) == (2, 1)


def test_template_tasks_are_never_verifier_owned(tmp_path):
    """#19 -- sdd-plus/templates/tasks.md:9-13, all five lines verbatim."""
    p = tmp_path / "tasks.md"
    p.write_text(
        "# Tasks\n\n## Implementation\n\n"
        "- [ ] Confirm scope and standards.\n"
        "- [ ] Add or update tests/checks where useful.\n"
        "- [ ] Implement the smallest coherent change.\n"
        "- [ ] Update docs/specs for behavior, setup, data, API, or workflow changes.\n"
        "- [ ] Run verification.\n", encoding="utf-8")
    assert sdd.verifier_owned_pending(p) == (0, 5)


def test_bare_verification_heading_is_not_verifier_owned(tmp_path):
    """#19a -- fact 23. archive/2026-09-01-grok-coplan-linux-discover/tasks.md:26-33:
    a bare `## Verification` over five IMPLEMENTER-run commands. Anchoring on
    'verif' instead of 'verifier' would waive all five."""
    p = tmp_path / "tasks.md"
    p.write_text(
        "# Tasks\n\n## Verification\n\n"
        "- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passes.\n"
        "- [ ] `python3 scripts/start_probe.py` exits 0.\n"
        "- [ ] `discover_core()` returns `/home/box/.local/bin/codex` on this VM.\n"
        "- [ ] One live `negotiate.py --round 1` with a short non-secret probe plan gets past\n"
        "- [ ] `launchguardian scan --target . --strict-scanners` — **APPROVED**, 0 findings.\n",
        encoding="utf-8")
    assert sdd.verifier_owned_pending(p) == (0, 5)


def test_prose_naming_the_verifier_is_not_a_task(tmp_path):
    """#19b -- all four prose instances of plan.md section E.1. Neither a checkbox
    nor a heading, so they are structurally invisible and set no section state."""
    p = tmp_path / "tasks.md"
    p.write_text(
        "# Tasks\n\n## Implementation\n\n"
        "run; they are evidence, not verification. Step 12 stays unchecked — the Owner "
        "deferred the verifier\nsubagent this turn and `verification.md` Result stays "
        "**Pending**.\n\n"
        "- Verification is implementer-checked only. The verifier subagent was not invoked "
        "(per assignment);\n"
        "  verifier-owned Manual Checks in `verification.md` are left unchecked.\n"
        "- run, and no verifier subagent was invoked in this turn.\n\n"
        "- [ ] Implement the smallest coherent change.\n", encoding="utf-8")
    assert sdd.verifier_owned_pending(p) == (0, 1)


@pytest.mark.parametrize("task", [
    "- [ ] Implement the smallest coherent change.",
    "- [ ] Run verification.",
    "- [ ] Confirm scope and standards.",
    "- [ ] Add or update tests/checks where useful.",
    "- [ ] Update docs/specs for behavior, setup, data, API, or workflow changes.",
])
@pytest.mark.parametrize("heading", ["## Implementation", "## Verification"])
def test_implementation_tasks_are_never_waived(tmp_path, task, heading):
    """#19c -- the negative: implementation work is never waived, under either
    heading. A bare `## Verification` heading is not a verifier heading."""
    p = tmp_path / "tasks.md"
    p.write_text(f"# Tasks\n\n{heading}\n\n{task}\n", encoding="utf-8")
    assert sdd.verifier_owned_pending(p) == (0, 1)


def test_repo_tasks_corpus_matches_the_inventory():
    """#19d -- READ-ONLY over the real tree. Holds plan.md section E.1 as a
    contract: the day a wording the closed set does not cover enters the repo,
    this goes red instead of silently misclassifying. Writes nothing.

    The live packet's row reads (1, 0) rather than the template's (0, 5) because
    this packet's own tasks.md is now filled: its implementer boxes are ticked and
    its one pending task is the inventoried LINE FORM (the same wording as
    archive/2026-09-02-grok-coplan-closure-gate/tasks.md:47). No new wording was
    introduced, so the closed set of plan.md section E.1 is unchanged."""
    expected = {
        "sdd-plus/archive/2026-09-01-grok-choreography-smoke/tasks.md": (4, 0),
        "sdd-plus/archive/2026-09-01-grok-coplan-discover-probe/tasks.md": (0, 0),
        "sdd-plus/archive/2026-09-01-grok-coplan-linux-discover/tasks.md": (0, 0),
        "sdd-plus/archive/2026-09-01-grok-docs-coplan-runtime/tasks.md": (0, 0),
        "sdd-plus/archive/2026-09-02-grok-coplan-closure-gate/tasks.md": (1, 0),
        "sdd-plus/archive/2026-09-02-grok-refuse-brief-engine/tasks.md": (1, 0),
        "sdd-plus/changes/grok-archive-bound-verdict/tasks.md": (1, 0),
        "sdd-plus/templates/tasks.md": (0, 5),
    }
    found = sorted(str(p.relative_to(ROOT).as_posix())
                   for p in (ROOT / "sdd-plus" / "archive").glob("*/tasks.md"))
    assert found == sorted(k for k in expected if "/archive/" in k), (
        "a new archived packet entered the corpus; re-run the plan.md section E.1 "
        "inventory before touching the matcher")
    for rel, want in expected.items():
        assert sdd.verifier_owned_pending(ROOT / rel) == want, rel


def test_packet_unfilled_behavior_unchanged(tmp_path):
    """#20 -- the split is internal: same list, REQUIRED_FILES order, no dupes."""
    tbd_plan = "# Plan\n\n## Approach\n\nTBD\n"
    both_verif = ("# Verification\n\n## Automated Checks\n\n- [ ] TBD\n\n"
                  "## Result\n\nPending.\n")

    placeholder_only = _packet(tmp_path, name="ph", result="All checks passed.",
                               files={"plan.md": tbd_plan})
    assert sdd.packet_unfilled(placeholder_only) == ["plan.md"]
    assert sdd.packet_unfilled_reasons(placeholder_only) == (["plan.md"], [])

    pending_only = _packet(tmp_path, name="pend")
    assert sdd.packet_unfilled(pending_only) == ["verification.md"]
    assert sdd.packet_unfilled_reasons(pending_only) == ([], ["verification.md"])

    both = _packet(tmp_path, name="both", files={"plan.md": tbd_plan,
                                                 "verification.md": both_verif})
    assert sdd.packet_unfilled(both) == ["plan.md", "verification.md"]
    assert sdd.packet_unfilled_reasons(both) == (["plan.md", "verification.md"],
                                                 ["verification.md"])


# --------------------------------------------------------------------------
# Tier 2 -- binding + readiness against the REAL scripts/check_verdict.py
# --------------------------------------------------------------------------

def test_bound_report_binds(tmp_path):
    """#6"""
    d = _bound(tmp_path)
    b = sdd.verdict_binding(d)
    assert b.ok is True
    assert b.verdict == "VERIFIED WITH NOTES"
    assert b.digest == hashlib.sha256((d / sdd.VERIFIER_REPORT).read_bytes()).hexdigest()
    assert b.reason == ""


def test_bound_accepts_plain_verified(tmp_path):
    """#7"""
    assert sdd.verdict_binding(_bound(tmp_path, verdict="VERIFIED")).ok is True


def test_no_artifacts_is_not_a_claim(tmp_path):
    """#8 -- reason == "" is load-bearing: no claim is not a fault."""
    b = sdd.verdict_binding(_packet(tmp_path))
    assert b.ok is False
    assert b.reason == ""


def test_missing_sidecar_is_not_bound(tmp_path):
    """#9"""
    b = sdd.verdict_binding(_packet(tmp_path, report=REPORT.format(v="VERIFIED")))
    assert b.ok is False
    assert sdd.VERIFIER_SHA in b.reason


def test_missing_report_is_not_bound(tmp_path):
    """#10"""
    b = sdd.verdict_binding(_packet(tmp_path, sidecar="a" * 64 + "\n"))
    assert b.ok is False
    assert sdd.VERIFIER_REPORT in b.reason


def test_hash_mismatch_is_not_bound(tmp_path):
    """#11 -- the bind IS check_verdict.py's exit code."""
    d = _packet(tmp_path, report=REPORT.format(v="VERIFIED"), sidecar=HEX0 + "\n")
    b = sdd.verdict_binding(d)
    assert b.ok is False
    assert "check_verdict.py exit" in b.reason
    assert "sha256 mismatch" in b.reason


def test_report_edited_after_sidecar_written_is_not_bound(tmp_path):
    """#12 -- fail closed on drift. This is what justifies a sidecar over a footer:
    a footer would self-heal on regeneration and keep the gate green over bytes no
    verifier ever saw."""
    d = _bound(tmp_path)
    assert sdd.verdict_binding(d).ok is True
    # Appended as its own section, so the `## Verdict` section still parses to the
    # same single line: the ONLY thing that changed is the bytes, and the bind must
    # fail on the hash rather than on verdict extraction.
    with (d / sdd.VERIFIER_REPORT).open("a", encoding="utf-8") as f:
        f.write("\n## Addendum\n\nstray\n")
    report = (d / sdd.VERIFIER_REPORT).read_text(encoding="utf-8")
    assert sdd.verdict_line(report) == "VERIFIED WITH NOTES"
    b = sdd.verdict_binding(d)
    assert b.ok is False
    assert "sha256 mismatch" in b.reason


def test_footer_in_report_does_not_bind_body_only_hash(tmp_path):
    """#13 -- whole-file hashing is the contract. A half-added footer scheme, whose
    hex is the digest of the body only, must be a RED test rather than a mysterious
    production mismatch."""
    body = "# Verification Report\n\n## Verdict\nVERIFIED WITH NOTES\n\n## Footer\n"
    body_hex = hashlib.sha256(body.encode("utf-8")).hexdigest()
    report = body + f"sha256 of those exact report bytes: {body_hex}\n"
    d = _packet(tmp_path, report=report, sidecar=body_hex + "\n")
    assert sdd.verdict_line(report) == "VERIFIED WITH NOTES"   # extraction is fine
    b = sdd.verdict_binding(d)
    assert b.ok is False
    assert "sha256 mismatch" in b.reason


def test_not_verified_is_rejected_before_check_verdict(tmp_path):
    """#14 -- the substring trap (tests/test_check_verdict.py:36-43). 'VERIFIED' is
    a substring of 'NOT VERIFIED', so the verdict is decided by verdict_line's
    whole-line whitelist and check_verdict is never reached for this report."""
    d = _bound(tmp_path, verdict="NOT VERIFIED")
    b = sdd.verdict_binding(d)
    assert b.ok is False
    assert "NOT VERIFIED" in b.reason
    assert "check_verdict" not in b.reason


@pytest.mark.parametrize("verdict", [
    "BLOCKED", "VERIFIED WITH NOTES.", "verified with notes", "",
])
def test_blocked_and_unknown_verdicts_rejected(tmp_path, verdict):
    """#15 -- strictness papercuts are deliberate and are known behavior."""
    b = sdd.verdict_binding(_bound(tmp_path, verdict=verdict))
    assert b.ok is False
    assert b.reason != ""


def test_bound_waives_verifier_task_and_pending_result(tmp_path):
    """#21 -- THE change: bound report + only verifier tasks pending + Result
    'Pending.' archives without --force."""
    d = _bound(tmp_path)
    assert sdd.archive_readiness(d, _caps(tmp_path)) == []


def test_bound_does_not_waive_implementation_tasks(tmp_path):
    """#22"""
    tasks = ("# Tasks\n\n## Implementation\n\n"
             "- [ ] Implement the smallest coherent change.\n"
             "- [ ] Invoke the verifier subagent; do not self-certify.\n")
    blockers = sdd.archive_readiness(_bound(tmp_path, tasks=tasks), _caps(tmp_path))
    assert _cats(blockers) == ["incomplete"]
    assert "1 pending task(s)" in blockers[0][1]


def test_bound_does_not_waive_placeholders(tmp_path):
    """#23"""
    d = _bound(tmp_path, files={"plan.md": "# Plan\n\n## Approach\n\nTBD\n"})
    blockers = sdd.archive_readiness(d, _caps(tmp_path))
    assert _cats(blockers) == ["incomplete"]
    assert "plan.md" in blockers[0][1]


def test_bound_does_not_waive_unsynced_capability(tmp_path):
    """#24 -- the three delta blockers are untouched by this packet."""
    d = _bound(tmp_path)
    (d / "specs").mkdir()
    (d / "specs" / "cap.md").write_text("Capability: my-cap\n", encoding="utf-8")
    assert "unsynced-capability" in _cats(sdd.archive_readiness(d, _caps(tmp_path)))


@pytest.mark.parametrize("kw", [
    {"report": REPORT.format(v="VERIFIED WITH NOTES")},                  # no sidecar
    {"report": REPORT.format(v="VERIFIED WITH NOTES"), "sidecar": HEX0 + "\n"},
    {"report": REPORT.format(v="NOT VERIFIED"), "sidecar": HEX0 + "\n"},
    {"report": REPORT.format(v="VERIFIED"), "sidecar": "not-a-hash\n"},
])
def test_unbound_claim_yields_both_blockers(tmp_path, kw):
    """#25 -- a failed bind can never make a packet MORE archivable: both blockers
    fire together."""
    d = _packet(tmp_path, tasks=VERIFIER_TASKS, **kw)
    cats = _cats(sdd.archive_readiness(d, _caps(tmp_path)))
    assert "unbound-verdict" in cats
    assert "incomplete" in cats


def test_no_claim_yields_no_unbound_blocker(tmp_path):
    """#26 -- fail-case 3 baseline: no report, no sidecar, still denied, and NOT
    with an unbound-verdict blocker. Unchanged from today."""
    d = _packet(tmp_path, tasks="# Tasks\n\n- [ ] Implement the change.\n")
    assert _cats(sdd.archive_readiness(d, _caps(tmp_path))) == ["incomplete"]


def test_clean_packet_without_report_is_ready(tmp_path):
    """#27 -- a bound report is SUFFICIENT, never NECESSARY."""
    d = _packet(tmp_path, result="All checks passed.")
    assert sdd.archive_readiness(d, _caps(tmp_path)) == []


def test_archive_readiness_bound_param_is_equivalent(tmp_path):
    """#39 -- bound= is an optimization, never a semantic."""
    caps = _caps(tmp_path)
    bound = _bound(tmp_path, name="a")
    unbound = _packet(tmp_path, name="b", tasks=VERIFIER_TASKS,
                      report=REPORT.format(v="VERIFIED"), sidecar=HEX0 + "\n")
    no_claim = _packet(tmp_path, name="c", tasks=VERIFIER_TASKS)
    for d in (bound, unbound, no_claim):
        assert sdd.archive_readiness(d, caps) == \
            sdd.archive_readiness(d, caps, bound=sdd.verdict_binding(d))


def _boom(*a, **k):
    raise AssertionError("subprocess spawned for a packet that claims nothing")


@pytest.mark.parametrize("kw", [
    {},                                                                   # no report
    {"report": REPORT.format(v="VERIFIED")},                              # no sidecar
    {"report": REPORT.format(v="VERIFIED"), "sidecar": "not-a-hash\n"},   # malformed
    {"report": REPORT.format(v="NOT VERIFIED"), "sidecar": HEX0 + "\n"},  # bad verdict
])
def test_unclaimed_packet_spawns_no_subprocess(tmp_path, monkeypatch, kw):
    """#40 -- plan.md section F.1 spawn budget: the cheap gates 1-3 short-circuit
    before any spawn, so a packet that claims nothing costs zero subprocesses."""
    monkeypatch.setattr(sdd.subprocess, "run", _boom)
    d = _packet(tmp_path, tasks=VERIFIER_TASKS, **kw)
    sdd.archive_readiness(d, _caps(tmp_path))       # must not raise


def _raiser(exc):
    def _run(*a, **k):
        raise exc
    return _run


def _fake_nonzero(*a, **k):
    return subprocess.CompletedProcess(a[0] if a else [], 1, "", "sha256 mismatch\n")


@pytest.mark.parametrize("install, expect, forbid", [
    (lambda mp, tp: mp.setattr(sdd.subprocess, "run",
                               _raiser(subprocess.TimeoutExpired(cmd="check_verdict.py",
                                                                 timeout=30))),
     "timed out", "cannot run"),
    (lambda mp, tp: mp.setattr(sdd.subprocess, "run", _raiser(OSError("no interpreter"))),
     "cannot run", None),
    (lambda mp, tp: mp.setattr(sdd.subprocess, "run",
                               _raiser(subprocess.SubprocessError("weird"))),
     "cannot run", None),
    (lambda mp, tp: mp.setattr(sdd.subprocess, "run", _fake_nonzero),
     "exit 1", None),
    (lambda mp, tp: mp.setattr(sdd, "CHECK_VERDICT", tp / "gone.py"),
     "missing gone.py", None),
])
def test_subprocess_failures_all_fail_closed(tmp_path, monkeypatch, install, expect, forbid):
    """#41 -- plan.md section F.4: every subprocess failure mode blocks, none is
    ever silently converted to the no-claim reason "". Timeout must report
    'timed out', not 'cannot run' -- TimeoutExpired subclasses SubprocessError, so
    the except-ordering is a real regression risk."""
    install(monkeypatch, tmp_path)
    d = _bound(tmp_path)
    b = sdd.verdict_binding(d)
    assert b.ok is False
    assert b.reason != ""
    assert expect in b.reason
    if forbid:
        assert forbid not in b.reason
    cats = _cats(sdd.archive_readiness(d, _caps(tmp_path), bound=b))
    assert "unbound-verdict" in cats
    assert "incomplete" in cats


# --------------------------------------------------------------------------
# Tier 3 -- end-to-end CLI under _isolated_tree. Substring assertions only.
# --------------------------------------------------------------------------

def test_verify_prints_ready_for_bound_packet(_isolated_tree, capsys):
    """#28"""
    _bound(_isolated_tree)
    rc = sdd.cmd_verify("demo")
    out = capsys.readouterr().out
    assert "READY TO ARCHIVE" in out
    assert "Bound verifier verdict: VERIFIED WITH NOTES" in out
    assert rc == 0


def test_verify_does_not_print_ready_for_unbound_packet(_isolated_tree, capsys):
    """#29"""
    _packet(_isolated_tree, tasks=VERIFIER_TASKS,
            report=REPORT.format(v="VERIFIED WITH NOTES"))
    sdd.cmd_verify("demo")
    out = capsys.readouterr().out
    assert "Not archive-ready" in out
    assert "READY TO ARCHIVE" not in out
    assert "NOT bound" in out


def test_verify_prints_not_archive_ready_for_plain_incomplete_packet(_isolated_tree, capsys):
    """#30 -- the :416 short-circuit removal. An ordinary incomplete packet now
    says why, instead of falling silent."""
    _packet(_isolated_tree, tasks="# Tasks\n\n- [ ] Implement the change.\n")
    sdd.cmd_verify("demo")
    out = capsys.readouterr().out
    assert "Not archive-ready" in out
    assert "pending task(s)" in out


def test_verify_does_not_claim_force_for_bound_packet(_isolated_tree, capsys):
    """#31 -- the hard-coded --force sentence is now derived from the blockers."""
    _bound(_isolated_tree, name="bound")
    sdd.cmd_verify("bound")
    assert "Archive will require --force." not in capsys.readouterr().out

    _packet(_isolated_tree, name="plain", tasks=VERIFIER_TASKS)
    sdd.cmd_verify("plain")
    assert "Archive will require --force." in capsys.readouterr().out


def test_classify_bound_packet_is_archive_ready(_isolated_tree):
    """#32 -- triage must not contradict archive."""
    d = _bound(_isolated_tree)
    assert sdd._classify_packet(d, _caps(_isolated_tree))[0] == "ARCHIVE-READY"


def test_classify_unbound_packet_is_in_progress(_isolated_tree):
    """#33 -- the same packet without its sidecar is bucketed exactly as today."""
    d = _bound(_isolated_tree)
    (d / sdd.VERIFIER_SHA).unlink()
    assert sdd._classify_packet(d, _caps(_isolated_tree))[0] == "IN-PROGRESS"


def test_archive_moves_bound_packet_without_force(_isolated_tree):
    """#34 -- no --force, and therefore no ## Override record (fact 9)."""
    d = _bound(_isolated_tree)
    sdd.cmd_archive("demo", force=False)
    assert not d.exists()
    archived = list((_isolated_tree / "sdd-plus" / "archive").glob("*-demo"))
    assert len(archived) == 1
    assert "## Override" not in (archived[0] / "decision-log.md").read_text(encoding="utf-8")


def test_archive_refuses_unbound_packet_without_force(_isolated_tree):
    """#35 -- fail-case 3 at the CLI, with the actionable hint."""
    d = _packet(_isolated_tree, tasks=VERIFIER_TASKS,
                report=REPORT.format(v="VERIFIED WITH NOTES"))
    with pytest.raises(SystemExit) as excinfo:
        sdd.cmd_archive("demo", force=False)
    msg = str(excinfo.value)
    assert "not archive-ready" in msg
    assert "Bind the verifier verdict" in msg
    assert d.is_dir()


def test_archive_force_still_works_and_records_override(_isolated_tree):
    """#36 -- --force is not removed, not renamed, not weakened."""
    _packet(_isolated_tree, tasks=VERIFIER_TASKS)
    sdd.cmd_archive("demo", force=True, reason="x")
    archived = list((_isolated_tree / "sdd-plus" / "archive").glob("*-demo"))
    assert len(archived) == 1
    assert "## Override" in (archived[0] / "decision-log.md").read_text(encoding="utf-8")


def test_archive_force_on_bound_packet_records_no_override(_isolated_tree):
    """#37 -- a bound archive is not an override, even when --force is passed:
    archive_readiness returns [] so there is nothing to waive (fact 9)."""
    _bound(_isolated_tree)
    sdd.cmd_archive("demo", force=True, reason="belt and braces")
    archived = list((_isolated_tree / "sdd-plus" / "archive").glob("*-demo"))
    assert len(archived) == 1
    assert "## Override" not in (archived[0] / "decision-log.md").read_text(encoding="utf-8")


def test_producer_choreography_end_to_end(_isolated_tree):
    """#38 -- plan.md section D.2, performed rather than asserted. The documented
    choreography IS what the gate accepts, so the two cannot drift:
      2. copy the report verbatim into the packet,
      3. run the real check_verdict.py CLI -> exit 0 is the bind,
      4. write that same hex to the sidecar,
      5. archive with no --force and no ## Override."""
    d = _packet(_isolated_tree, tasks=VERIFIER_TASKS)
    report = d / sdd.VERIFIER_REPORT
    report.write_text("# Verification Report\n\n## Verdict\nVERIFIED WITH NOTES\n",
                      encoding="utf-8")
    hexd = hashlib.sha256(report.read_bytes()).hexdigest()

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_verdict.py"), str(report),
         hexd, "VERIFIED WITH NOTES"], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr

    (d / sdd.VERIFIER_SHA).write_text(hexd + "\n", encoding="utf-8")
    sdd.cmd_archive("demo", force=False)

    archived = list((_isolated_tree / "sdd-plus" / "archive").glob("*-demo"))
    assert len(archived) == 1
    assert (archived[0] / sdd.VERIFIER_SHA).is_file()
    assert "## Override" not in (archived[0] / "decision-log.md").read_text(encoding="utf-8")
