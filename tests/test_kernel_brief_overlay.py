"""kernel/brief.py and kernel/brief_complete.py refuse bare --record-verify."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OVERLAY = ROOT / "kernel" / "brief.py"
ALIAS = ROOT / "kernel" / "brief_complete.py"
ENGINE = ROOT / "kernel" / "brief_engine.py"


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
    """Honest leftover: the vendored engine can still record completeness."""
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
