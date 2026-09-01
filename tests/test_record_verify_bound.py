"""Bound record_verify: check_verdict must pass first (case 5b hole)."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "record_verify_bound.py"


def _run(packet, verdict: Path, digest: str, required: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), packet, str(verdict), digest, required],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def test_refuses_without_matching_hash(tmp_path: Path):
    p = tmp_path / "verdict.md"
    p.write_text("VERIFIED WITH NOTES\n", encoding="utf-8")
    proc = _run("grok-choreography-smoke", p, "0" * 64, "VERIFIED WITH NOTES")
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "check_verdict-failed"


def test_refuses_missing_file():
    proc = _run(
        "grok-choreography-smoke",
        ROOT / "no-such-verdict.md",
        "abc",
        "VERIFIED WITH NOTES",
    )
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["recorded"] is False
    assert payload["reason"] == "check_verdict-failed"


def test_check_verdict_pass_then_unknown_packet(tmp_path: Path):
    p = tmp_path / "verdict.md"
    body = "VERIFIED WITH NOTES\n"
    p.write_text(body, encoding="utf-8")
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    proc = _run("does-not-exist", p, digest, "VERIFIED WITH NOTES")
    # check_verdict passed, kernel then refused the bad packet name/path.
    payload = json.loads(proc.stdout)
    assert payload.get("recorded") is False
    assert payload.get("reason") in {"bad-name", "packet-not-found", "gate-failed"}
