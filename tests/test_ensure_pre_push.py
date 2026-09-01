"""start_probe.ensure_pre_push copies backstops/pre-push into .git/hooks."""
import hashlib
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import start_probe  # type: ignore  # noqa: E402


def _src_bytes() -> bytes:
    return (ROOT / "backstops" / "pre-push").read_bytes()


def test_installs_when_missing(tmp_path: Path):
    src = tmp_path / "backstops" / "pre-push"
    src.parent.mkdir()
    src.write_bytes(_src_bytes())
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    errs = start_probe.ensure_pre_push(tmp_path)
    assert errs == []
    dst = tmp_path / ".git" / "hooks" / "pre-push"
    assert dst.is_file()
    assert hashlib.sha256(dst.read_bytes()).hexdigest() == hashlib.sha256(_src_bytes()).hexdigest()
    assert dst.stat().st_mode & 0o111  # executable bit


def test_noop_when_hash_matches(tmp_path: Path):
    src = tmp_path / "backstops" / "pre-push"
    src.parent.mkdir()
    src.write_bytes(_src_bytes())
    dst = tmp_path / ".git" / "hooks" / "pre-push"
    dst.parent.mkdir(parents=True)
    dst.write_bytes(_src_bytes())
    dst.chmod(0o755)
    mtime = dst.stat().st_mtime_ns
    errs = start_probe.ensure_pre_push(tmp_path)
    assert errs == []
    assert dst.stat().st_mtime_ns == mtime


def test_replaces_drifted_hook(tmp_path: Path):
    src = tmp_path / "backstops" / "pre-push"
    src.parent.mkdir()
    src.write_bytes(_src_bytes())
    dst = tmp_path / ".git" / "hooks" / "pre-push"
    dst.parent.mkdir(parents=True)
    dst.write_text("not the hook\n", encoding="utf-8")
    errs = start_probe.ensure_pre_push(tmp_path)
    assert errs == []
    assert dst.read_bytes() == _src_bytes()


def test_fail_closed_without_git(tmp_path: Path):
    src = tmp_path / "backstops" / "pre-push"
    src.parent.mkdir()
    src.write_bytes(_src_bytes())
    errs = start_probe.ensure_pre_push(tmp_path)
    assert errs
    assert "missing .git" in errs[0]


def test_fail_closed_without_source(tmp_path: Path):
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    errs = start_probe.ensure_pre_push(tmp_path)
    assert errs
    assert "missing backstops/pre-push" in errs[0]
