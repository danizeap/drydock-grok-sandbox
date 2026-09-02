"""kernel/brief.py, kernel/brief_complete.py and kernel/brief_engine.py refuse
bare --record-verify."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
OVERLAY = ROOT / "kernel" / "brief.py"
ALIAS = ROOT / "kernel" / "brief_complete.py"
ENGINE = ROOT / "kernel" / "brief_complete_engine.py"
ENGINE_OVERLAY = ROOT / "kernel" / "brief_engine.py"


def _run(script: Path, args):
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def test_kernel_overlay_bare_record_verify_refused():
    proc = _run(OVERLAY, ["--record-verify", "does-not-exist"])
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "bare-record-verify-refused"


def test_brief_complete_alias_also_refuses_bare():
    proc = _run(ALIAS, ["--record-verify", "does-not-exist"])
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "bare-record-verify-refused"


def test_completeness_engine_still_has_bare_mode():
    """Honest leftover: the vendored bytes still contain the bare mode, now at
    the new unadvertised path kernel/brief_complete_engine.py. The claim this
    packet makes is "every advertised path refuses", never "the capability is
    gone"."""
    text = ENGINE.read_text(encoding="utf-8")
    assert "--record-verify NAME" in text
    assert "record a verify-run" in text


def test_kernel_overlay_bound_form_still_requires_check_verdict(tmp_path: Path):
    verdict = tmp_path / "v.md"
    verdict.write_text("VERIFIED WITH NOTES\n", encoding="utf-8")
    proc = _run(
        OVERLAY,
        ["--record-verify", "does-not-exist", str(verdict), "0" * 64, "VERIFIED WITH NOTES"],
    )
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "check_verdict-failed"


def test_kernel_overlay_other_modes_delegate():
    proc = _run(OVERLAY, [])
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "drydock" in payload or "engine" in payload or "generated" in payload


def test_engine_overlay_bare_record_verify_refused():
    """The headline criterion: the historical completeness path now refuses."""
    proc = _run(ENGINE_OVERLAY, ["--record-verify", "does-not-exist"])
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "bare-record-verify-refused"


def test_engine_overlay_bound_form_still_requires_check_verdict(tmp_path: Path):
    verdict = tmp_path / "v.md"
    verdict.write_text("VERIFIED WITH NOTES\n", encoding="utf-8")
    proc = _run(
        ENGINE_OVERLAY,
        ["--record-verify", "does-not-exist", str(verdict), "0" * 64, "VERIFIED WITH NOTES"],
    )
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "check_verdict-failed"


def test_engine_overlay_bound_form_reaches_completeness(tmp_path: Path):
    """The bound path must get PAST check_verdict into the moved completeness
    file. A bare-record-verify-refused here is the self-refusal deadlock, not a
    success of the new gate."""
    verdict = tmp_path / "v.md"
    verdict.write_text("VERIFIED WITH NOTES\n", encoding="utf-8")
    digest = hashlib.sha256(verdict.read_bytes()).hexdigest()
    proc = _run(
        ENGINE_OVERLAY,
        ["--record-verify", "does-not-exist", str(verdict), digest, "VERIFIED WITH NOTES"],
    )
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] in {"bad-name", "packet-not-found", "gate-failed"}


def test_completeness_engine_bytes_unmoved():
    digest = hashlib.sha256(ENGINE.read_bytes()).hexdigest()
    assert digest == "aa3ba09fa5b8bd3a861d3ac3a58990a06251d0204c5632f93b6658ad85368a2b"
    assert ENGINE.parent.name == "kernel"


def test_completeness_engine_hooks_import_resolves():
    """_HOOKS is consumed by a module-scope import, so a mis-resolved path is a
    traceback and a non-zero exit, not a JSON error block."""
    assert (ENGINE.resolve().parent.parent / "hooks" / "_drydock_common.py").is_file()
    proc = _run(ENGINE, [])
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "drydock" in payload or "engine" in payload or "generated" in payload


def test_engine_overlay_other_modes_delegate():
    proc = _run(ENGINE_OVERLAY, [])
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "drydock" in payload or "engine" in payload or "generated" in payload


@pytest.mark.parametrize(
    "args",
    [
        ["--record-verify=does-not-exist"],
        ["--record-ver", "does-not-exist"],
        ["--record", "does-not-exist"],
        ["--r", "does-not-exist"],
        ["--record-verify=p", "v", "d", "r"],
    ],
)
def test_engine_overlay_equals_and_abbrev_forms_refused(args):
    """OQ-1 default: the strict matcher covers every spelling argparse would
    read as --record-verify, not just the canonical two-token form."""
    proc = _run(ENGINE_OVERLAY, args)
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "bare-record-verify-refused"
