"""start_probe.check_discover fails closed when no Codex core is findable.

The probe must not print ok:true while coplan is about to fail at negotiate stage
'discover'. Discovery is exercised for real against fake trees under tmp_path --
discover_core() reads exactly LOCALAPPDATA / PATH / HOME, so passing all three
kwargs substitutes the whole search input and no live Codex binary is required.
"""
import json
from pathlib import Path

import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import start_probe  # type: ignore  # noqa: E402


def _exe(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture(autouse=True)
def _no_ambient_env(monkeypatch):
    """Keep the real machine out of the fake-tree tests.

    HOME is blanked with setenv, not delenv: expanduser("~") falls back to the
    passwd database when HOME is absent. GITHUB_ACTIONS is cleared because this
    repo's own CI sets it, and without this every fail-closed test below would
    take the skip branch and pass for the wrong reason.
    """
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("HOME", "")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)


def test_found_core_yields_no_errors(tmp_path: Path):
    _exe(tmp_path / "bin/codex")
    errors, skipped = start_probe.check_discover(
        localappdata="", path_env=str(tmp_path / "bin"), home=""
    )
    assert errors == []
    assert skipped == ""


def test_missing_core_is_an_error(tmp_path: Path):
    errors, skipped = start_probe.check_discover(
        localappdata="", path_env="", home=str(tmp_path)
    )
    assert len(errors) == 1
    assert "discover_core" in errors[0]
    assert skipped == ""


def test_sandbox_bin_copy_does_not_count_as_found(tmp_path: Path):
    """A stale ~/.codex/.sandbox-bin copy is not an installed core."""
    sandbox_bin = tmp_path / ".codex/.sandbox-bin"
    _exe(sandbox_bin / "codex")
    errors, skipped = start_probe.check_discover(
        localappdata="", path_env=str(sandbox_bin), home=str(tmp_path)
    )
    assert len(errors) == 1
    assert "discover_core" in errors[0]
    assert skipped == ""


def test_check_discover_never_spawns_codex(tmp_path: Path, monkeypatch):
    """Token-free by test, not by claim: keeps holding if discovery ever grows a probe call."""
    from conductor import codex_bridge as cb

    def _boom(*args, **kwargs):
        raise AssertionError("check_discover must not spawn a subprocess")

    monkeypatch.setattr(cb.subprocess, "Popen", _boom)
    monkeypatch.setattr(cb.subprocess, "run", _boom)
    _exe(tmp_path / "bin/codex")
    assert start_probe.check_discover(
        localappdata="", path_env=str(tmp_path / "bin"), home=""
    ) == ([], "")


def test_github_actions_skips_the_check(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    errors, skipped = start_probe.check_discover(
        localappdata="", path_env="", home=str(tmp_path)
    )
    assert errors == []
    assert isinstance(skipped, str) and skipped
    assert "GitHub Actions" in skipped


def test_github_actions_skip_does_not_call_discover_core(monkeypatch):
    """The skip short-circuits before the call, not merely before the error."""
    from conductor import codex_bridge as cb

    def _boom(*args, **kwargs):
        raise AssertionError("the skip must not reach discover_core")

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(cb, "discover_core", _boom)
    errors, skipped = start_probe.check_discover()
    assert errors == []
    assert skipped


def test_empty_github_actions_does_not_skip(tmp_path: Path, monkeypatch):
    """Set *and non-empty*: an empty value must not widen the hole."""
    monkeypatch.setenv("GITHUB_ACTIONS", "")
    errors, skipped = start_probe.check_discover(
        localappdata="", path_env="", home=str(tmp_path)
    )
    assert len(errors) == 1
    assert "discover_core" in errors[0]
    assert skipped == ""


def _stub_other_checks(monkeypatch):
    """Make every check but discover pass, so main() depends on no pin/hook tree."""
    monkeypatch.setattr(start_probe, "check_pins", lambda: [])
    monkeypatch.setattr(start_probe, "check_hooks", lambda: ([], []))
    monkeypatch.setattr(start_probe, "check_secret_tree", lambda: [])
    monkeypatch.setattr(start_probe, "ensure_pre_push", lambda root: [])
    monkeypatch.setattr(start_probe, "ensure_pre_commit", lambda root: [])


def test_main_reports_a_missing_core_and_exits_1(monkeypatch, capsys):
    """The autouse fixture leaves no findable core, so discover alone flips ok."""
    _stub_other_checks(monkeypatch)
    code = start_probe.main()
    result = json.loads(capsys.readouterr().out)
    assert result["discover_errors"]
    assert "discover_core" in result["discover_errors"][0]
    assert result["discover_skipped"] == ""
    assert result["ok"] is False
    assert code == 1


def test_main_records_the_skip_without_flipping_ok(monkeypatch, capsys):
    _stub_other_checks(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    code = start_probe.main()
    result = json.loads(capsys.readouterr().out)
    assert result["discover_errors"] == []
    assert result["discover_skipped"]
    assert result["ok"] is True
    assert code == 0
