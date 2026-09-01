"""pre-commit blocks leftover gitignored .env even when it is not staged."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "backstops" / "pre-commit"


def _git(repo: Path, *args, check=True):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Daniel Paez"
    env["GIT_AUTHOR_EMAIL"] = "danizeap@users.noreply.github.com"
    env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
    env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=env,
        check=check,
    )


def test_commit_blocked_by_gitignored_env(tmp_path: Path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init")
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    (repo / "readme.txt").write_text("ok\n", encoding="utf-8")
    _git(repo, "add", ".gitignore", "readme.txt")
    _git(repo, "commit", "-m", "init")
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_bytes(HOOK.read_bytes())
    hook.chmod(0o755)
    (repo / ".env").write_text("API_KEY=not-a-real-secret\n", encoding="utf-8")
    (repo / "more.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "more.txt")
    proc = _git(repo, "commit", "-m", "more", check=False)
    assert proc.returncode != 0
    assert "secret-bearing file" in (proc.stderr + proc.stdout)
    assert ".env" in (proc.stderr + proc.stdout)
