"""Working-tree secret scan (leftover-hole: Grok Shell can write .env)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_secret_tree.py"


def _run():
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def test_clean_tree_ok():
    proc = _run()
    payload = json.loads(proc.stdout)
    assert proc.returncode == 0, proc.stderr
    assert payload["ok"] is True
    assert payload["secret_paths"] == []


def test_gitignored_env_is_caught(tmp_path, monkeypatch):
    # Import the finder directly so we don't plant a real .env in the repo.
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_secret_tree as cst  # type: ignore

    (tmp_path / ".env").write_text("API_KEY=not-a-real-secret\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("API_KEY=\n", encoding="utf-8")
    hits = cst.find_secrets(tmp_path)
    assert ".env" in hits
    assert ".env.example" not in hits
