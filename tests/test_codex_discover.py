"""Tests for conductor.codex_bridge.discover_core across platforms.

The Windows shape (LOCALAPPDATA glob) is the original behavior and must survive;
the POSIX shapes (PATH, ~/.local/bin) are what make co-planning work on this VM.
The stale ~/.codex/.sandbox-bin copy must never be returned from any branch.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from conductor import codex_bridge as cb  # noqa: E402


def _exe(path, mtime=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


@pytest.fixture(autouse=True)
def _no_ambient_env(monkeypatch):
    """Keep the real machine's LOCALAPPDATA/PATH/HOME out of the fake-tree tests."""
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("HOME", "")


def test_windows_glob_picks_the_newest_core(tmp_path):
    root = tmp_path / "LocalAppData"
    old = _exe(root / "OpenAI/Codex/bin/0.1.0/codex.exe", mtime=1_000_000)
    new = _exe(root / "OpenAI/Codex/bin/0.2.0/codex.exe", mtime=2_000_000)
    assert cb.discover_core(localappdata=str(root)) == str(new)
    assert str(old) != str(new)


def test_windows_root_wins_over_path(tmp_path):
    root = tmp_path / "LocalAppData"
    win = _exe(root / "OpenAI/Codex/bin/0.2.0/codex.exe")
    _exe(tmp_path / "bin/codex")
    got = cb.discover_core(localappdata=str(root), path_env=str(tmp_path / "bin"))
    assert got == str(win)


def test_finds_codex_on_path(tmp_path):
    want = _exe(tmp_path / "bin/codex")
    assert cb.discover_core(path_env=str(tmp_path / "bin")) == str(want)


def test_path_order_is_honoured(tmp_path):
    first = _exe(tmp_path / "a/codex")
    _exe(tmp_path / "b/codex")
    path_env = os.pathsep.join([str(tmp_path / "a"), str(tmp_path / "b")])
    assert cb.discover_core(path_env=path_env) == str(first)


def test_falls_back_to_home_local_bin(tmp_path):
    want = _exe(tmp_path / ".local/bin/codex")
    assert cb.discover_core(path_env="", home=str(tmp_path)) == str(want)


def test_non_executable_candidate_is_skipped(tmp_path):
    dead = tmp_path / "bin/codex"
    dead.parent.mkdir(parents=True)
    dead.write_text("not executable\n", encoding="utf-8")
    dead.chmod(0o644)
    want = _exe(tmp_path / ".local/bin/codex")
    assert cb.discover_core(path_env=str(tmp_path / "bin"), home=str(tmp_path)) == str(want)


def test_sandbox_bin_copy_is_rejected(tmp_path):
    _exe(tmp_path / ".codex/.sandbox-bin/codex")
    got = cb.discover_core(path_env=str(tmp_path / ".codex/.sandbox-bin"), home=str(tmp_path))
    assert got is None


def test_symlink_into_sandbox_bin_is_rejected(tmp_path):
    real = _exe(tmp_path / ".codex/.sandbox-bin/codex")
    link_dir = tmp_path / "bin"
    link_dir.mkdir()
    (link_dir / "codex").symlink_to(real)
    assert cb.discover_core(path_env=str(link_dir), home=str(tmp_path)) is None


def test_windows_sandbox_bin_copy_is_rejected(tmp_path):
    root = tmp_path / "LocalAppData"
    _exe(root / "OpenAI/Codex/bin/.sandbox-bin/codex.exe")
    assert cb.discover_core(localappdata=str(root), path_env="", home="") is None


def test_returns_none_when_nothing_is_installed(tmp_path):
    assert cb.discover_core(localappdata=str(tmp_path), path_env="", home=str(tmp_path)) is None


@pytest.mark.skipif(os.name == "nt", reason="POSIX install layout")
def test_discovers_a_real_core_on_this_machine(monkeypatch):
    """Regression guard for the live-fire failure: with no LOCALAPPDATA, discovery
    must still resolve to a runnable Codex core if one is installed here."""
    import pwd

    # The autouse fixture blanks HOME, so resolve the real one from the passwd db.
    real_home = pwd.getpwuid(os.getuid()).pw_dir
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("PATH", os.defpath + os.pathsep + os.path.join(real_home, ".local", "bin"))
    monkeypatch.setenv("HOME", real_home)
    core = cb.discover_core()
    if core is None:
        pytest.skip("no Codex core installed on this machine")
    assert os.path.isfile(core) and os.access(core, os.X_OK)
    assert ".sandbox-bin" not in core
