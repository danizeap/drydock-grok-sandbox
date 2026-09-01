"""start_probe.check_conductor_closure holds the read-only coplan closure.

Two conjoined claims: the *tracked* set under scripts/conductor/ is exactly the six
pinned files, and none of the mutating four *exists* there at all, tracked or not.

Every fake conductor tree lives under tmp_path, which pytest places outside the
worktree. No test ever creates a file named mutate.py, coord.py, executors.py or
handoff.py inside the real repo -- the negative paths are proven by injected
tracked=[...] lists and tmp_path trees only.
"""
import json
import shutil
import subprocess
from pathlib import Path

import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import start_probe  # type: ignore  # noqa: E402


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


def _stub_all_checks(monkeypatch):
    """Every check green, so main() depends on no pin/hook/git tree."""
    monkeypatch.setattr(start_probe, "check_pins", lambda: [])
    monkeypatch.setattr(start_probe, "check_conductor_closure", lambda: [])
    monkeypatch.setattr(start_probe, "check_hooks", lambda: ([], []))
    monkeypatch.setattr(start_probe, "check_secret_tree", lambda: [])
    monkeypatch.setattr(start_probe, "ensure_pre_push", lambda root: [])
    monkeypatch.setattr(start_probe, "ensure_pre_commit", lambda root: [])
    monkeypatch.setattr(start_probe, "check_discover", lambda: ([], ""))


def test_exact_six_tracked_files_pass(tmp_path: Path):
    assert start_probe.check_conductor_closure(
        root=_tree(tmp_path), tracked=_tracked()
    ) == []


def test_extra_tracked_file_fails(tmp_path: Path):
    """Closure is by set membership, so the extra file fails whatever it is named."""
    errors = start_probe.check_conductor_closure(
        root=_tree(tmp_path),
        tracked=_tracked() + ["scripts/conductor/extra.py"],
    )
    assert len(errors) == 1
    assert "extra.py" in errors[0]
    assert "unpinned" in errors[0]


@pytest.mark.parametrize("relpath", [
    "__pycache__/negotiate.cpython-313.pyc",   # bytecode of an *allowed* module
    "helper.py",                               # plain untracked scratch file
])
def test_untracked_non_mutating_file_does_not_fail(tmp_path: Path, relpath: str):
    """The accepted residual (OQ-1 default): claim (a) is about *vendored* contents."""
    _tree(tmp_path)
    _tree(tmp_path, (relpath,))
    assert start_probe.check_conductor_closure(
        root=tmp_path, tracked=_tracked()
    ) == []


def test_missing_pinned_file_is_not_reported_here(tmp_path: Path):
    """check_pins() owns missing files; one fault must not print two errors."""
    five = SIX[:-1]
    assert start_probe.check_conductor_closure(
        root=_tree(tmp_path, five), tracked=_tracked(five)
    ) == []


@pytest.mark.parametrize("relpath", [
    "mutate.py",
    "coord.py",
    "executors.py",
    "handoff.py",
    "mutate.pyc",                          # sourceless-import vector
    "__pycache__/coord.cpython-313.pyc",   # bytecode leftover, version tag arbitrary
    "sub/mutate.py",                       # pins rglob over iterdir
    "mutate",                              # extensionless, still runnable
])
def test_banned_name_present_on_disk_fails(tmp_path: Path, relpath: str):
    """Presence, not tracking: every case here is absent from `tracked`."""
    _tree(tmp_path)
    _tree(tmp_path, (relpath,))
    errors = start_probe.check_conductor_closure(root=tmp_path, tracked=_tracked())
    assert len(errors) == 1
    assert f"scripts/conductor/{relpath}" in errors[0]
    assert "present" in errors[0]


@pytest.mark.parametrize("relpath", ["coord.json", "handoff.md"])
def test_benign_suffix_is_not_banned(tmp_path: Path, relpath: str):
    """Stem + suffix rule, not a blunt substring match."""
    _tree(tmp_path)
    _tree(tmp_path, (relpath,))
    assert start_probe.check_conductor_closure(
        root=tmp_path, tracked=_tracked()
    ) == []


def test_tracked_mutating_file_outside_conductor_fails(tmp_path: Path):
    """Repo-wide, tracked-only (OQ-3 default): vendoring one level up is the evasion."""
    errors = start_probe.check_conductor_closure(
        root=_tree(tmp_path),
        tracked=_tracked() + ["scripts/mutate.py"],
    )
    assert len(errors) == 1
    assert "scripts/mutate.py" in errors[0]
    assert "tracked" in errors[0]


def test_banned_file_reported_once(tmp_path: Path):
    """The dedupe: on disk *and* tracked is one fault, reported by the presence scan."""
    _tree(tmp_path)
    _tree(tmp_path, ("mutate.py",))
    errors = start_probe.check_conductor_closure(
        root=tmp_path,
        tracked=_tracked() + ["scripts/conductor/mutate.py"],
    )
    assert len(errors) == 1
    assert "present" in errors[0]


@pytest.mark.parametrize("mode", ["exit_code", "oserror"])
def test_git_failure_fails_closed(tmp_path: Path, monkeypatch, mode: str):
    """A probe that cannot list tracked files must not report closure."""
    class _Proc:
        returncode = 128
        stdout = b""
        stderr = b"fatal: not a git repository\n"

    if mode == "exit_code":
        monkeypatch.setattr(start_probe.subprocess, "run", lambda *a, **k: _Proc())
    else:
        def _boom(*a, **k):
            raise OSError("no git")
        monkeypatch.setattr(start_probe.subprocess, "run", _boom)

    _tree(tmp_path)
    errors = start_probe.check_conductor_closure(root=tmp_path, tracked=None)
    assert len(errors) == 1
    assert "cannot list tracked files" in errors[0]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_real_git_repo_listing_detects_an_extra_file(tmp_path: Path):
    """Integration over the git plumbing: -z parsing and cwd=root, for real."""
    ident = ["-c", "user.email=probe@example.invalid", "-c", "user.name=Probe"]
    subprocess.run(["git", *ident, "init", "-q"], cwd=str(tmp_path), check=True,
                   capture_output=True)
    _tree(tmp_path)
    _tree(tmp_path, ("extra.py",))
    subprocess.run(["git", *ident, "add", "-A"], cwd=str(tmp_path), check=True,
                   capture_output=True)

    errors = start_probe.check_conductor_closure(root=tmp_path)
    assert len(errors) == 1
    assert "scripts/conductor/extra.py" in errors[0]
    assert "unpinned" in errors[0]


def test_live_tree_is_closed():
    """Read-only canary: a seventh vendored conductor file fails here first."""
    assert start_probe.check_conductor_closure() == []


def test_allowlist_matches_pins():
    """Keeps the hardcoded constant honest without deriving the gate from the gated file."""
    pins = json.loads((ROOT / "drydock-pins.json").read_text(encoding="utf-8"))
    pinned = {k.split("/")[-1] for k in pins["files"]
              if k.startswith("scripts/conductor/")}
    assert pinned == set(start_probe.CONDUCTOR_ALLOWED)


def test_main_reports_conductor_errors_and_exits_1(monkeypatch, capsys):
    _stub_all_checks(monkeypatch)
    monkeypatch.setattr(start_probe, "check_conductor_closure", lambda: ["boom"])
    code = start_probe.main()
    result = json.loads(capsys.readouterr().out)
    assert result["conductor_errors"] == ["boom"]
    assert result["ok"] is False
    assert code == 1


def test_main_json_contract(monkeypatch, capsys):
    """Additive only: the new key appears, and discover's two keys are untouched."""
    _stub_all_checks(monkeypatch)
    code = start_probe.main()
    result = json.loads(capsys.readouterr().out)
    assert result["conductor_errors"] == []
    assert isinstance(result["conductor_errors"], list)
    assert isinstance(result["discover_errors"], list)
    assert isinstance(result["discover_skipped"], str)
    assert result["ok"] is True
    assert code == 0
