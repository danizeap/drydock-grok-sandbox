"""scripts/brief.py refuses bare --record-verify (case 5b hole)."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "brief.py"


def _run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def test_bare_record_verify_refused():
    proc = _run(["--record-verify", "does-not-exist"])
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "bare-record-verify-refused"


def test_bound_form_still_requires_check_verdict(tmp_path: Path):
    verdict = tmp_path / "v.md"
    verdict.write_text("VERIFIED WITH NOTES\n", encoding="utf-8")
    proc = _run(
        ["--record-verify", "does-not-exist", str(verdict), "0" * 64, "VERIFIED WITH NOTES"]
    )
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "check_verdict-failed"


def test_other_modes_still_delegate_to_kernel():
    proc = _run([])
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "drydock" in payload or "engine" in payload or "generated" in payload
