"""Bootstrap tests for hashed check_verdict.py (not the smoke packet)."""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_verdict.py"


def _run(path: Path, digest: str, required: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), digest, required],
        capture_output=True,
        text=True,
    )


def test_match_and_substring(tmp_path: Path):
    p = tmp_path / "verdict.md"
    body = "Result\n\nVERIFIED WITH NOTES\n"
    p.write_text(body, encoding="utf-8")
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    proc = _run(p, digest, "VERIFIED WITH NOTES")
    assert proc.returncode == 0, proc.stderr


def test_hash_mismatch(tmp_path: Path):
    p = tmp_path / "verdict.md"
    p.write_text("VERIFIED\n", encoding="utf-8")
    proc = _run(p, "0" * 64, "VERIFIED")
    assert proc.returncode != 0
    assert "sha256 mismatch" in proc.stderr


def test_missing_verdict_string(tmp_path: Path):
    p = tmp_path / "verdict.md"
    p.write_text("NOT VERIFIED\n", encoding="utf-8")
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    # "VERIFIED" is a substring of "NOT VERIFIED"; require a string that is absent.
    proc = _run(p, digest, "VERIFIED WITH NOTES")
    assert proc.returncode != 0
    assert "required verdict string not found" in proc.stderr


def test_missing_file():
    proc = _run(ROOT / "no-such-verdict.md", "abc", "VERIFIED")
    assert proc.returncode != 0
    assert "missing verdict file" in proc.stderr
