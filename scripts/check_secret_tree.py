#!/usr/bin/env python3
"""Fail closed if a secret-bearing path exists in the working tree.

Grok Shell is not behind protect_secrets PreToolUse, so `echo > .env` can
succeed. Gitignore + pre-commit still block commit. This scan is the
choreography gate: it looks at the tree *including gitignored secret
basenames*, so a leftover .env cannot ride into start-probe / archive.

Stdlib only. Exit 0 iff none found. Prints JSON.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))
from protect_secrets import path_is_secret  # noqa: E402

_SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
}


def find_secrets(root: Path) -> list[str]:
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR_NAMES]
        for name in filenames:
            rel = (Path(dirpath) / name).relative_to(root).as_posix()
            if path_is_secret(rel):
                found.append(rel)
    return sorted(found)


def main() -> int:
    hits = find_secrets(ROOT)
    print(json.dumps({"ok": not hits, "secret_paths": hits}, indent=2))
    if hits:
        print("SECRET TREE FAILED:", ", ".join(hits), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
