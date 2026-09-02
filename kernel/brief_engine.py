#!/usr/bin/env python3
"""Choreography overlay at the historical completeness path.

Completeness lives at kernel/brief_complete_engine.py (bytes unchanged from
Drydock kernel/brief.py @ 5f76f67, sha256 aa3ba09...). This file used to BE
those bytes, which meant `python3 kernel/brief_engine.py --record-verify NAME`
recorded a verify-run with no in-channel binding (case 5b, leftover hole 2).
It is now the same gate kernel/brief.py applies. Bound form:

  python3 kernel/brief_engine.py --record-verify <packet> <verdict-file> \\
      <expected-sha256> <required-verdict-string>

which execs scripts/record_verify_bound.py (check_verdict first, then
kernel/brief_complete_engine.py). Other modes are delegated unchanged to
kernel/brief_complete_engine.py.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPLETE = ROOT / "kernel" / "brief_complete_engine.py"  # NEVER this file: execv loop
BOUND = ROOT / "scripts" / "record_verify_bound.py"


def _record_verify_index(argv: list[str]) -> int | None:
    """Index of any token the completeness parser would read as --record-verify.

    argparse accepts `--record-verify NAME`, `--record-verify=NAME`, and any
    unambiguous abbreviation (`--record-ver`, `--record`, `--r`) --- checked
    against kernel/brief_complete_engine.py:545-549. The plain
    `"--record-verify" in argv` guard used by kernel/brief.py:28 sees only the
    first spelling, so this overlay matches all of them and lets the canonical
    spelling alone through to the bound form.
    """
    for i, tok in enumerate(argv[1:], start=1):
        if not tok.startswith("--"):
            continue
        name = tok.partition("=")[0]
        if len(name) > 2 and "--record-verify".startswith(name):
            return i
    return None


def main(argv: list[str]) -> int:
    i = _record_verify_index(argv)
    if i is not None:
        rest = argv[i + 1 :]
        if argv[i] != "--record-verify" or len(rest) != 4:
            print(
                json.dumps(
                    {
                        "recorded": False,
                        "reason": "bare-record-verify-refused",
                        "detail": (
                            "kernel/brief_engine.py --record-verify requires "
                            "<packet> <verdict-file> <expected-sha256> "
                            "<required-verdict-string>, spelled exactly; "
                            "completeness-only kernel/brief_complete_engine.py "
                            "is not provenance"
                        ),
                    },
                    indent=2,
                )
            )
            print(
                "refused: bare --record-verify is not provenance. "
                "usage: python3 kernel/brief_engine.py --record-verify "
                "<packet> <verdict-file> <expected-sha256> "
                "<required-verdict-string>",
                file=sys.stderr,
            )
            return 1
        if not BOUND.is_file():
            print(
                json.dumps(
                    {"recorded": False, "reason": "missing-record_verify_bound"},
                    indent=2,
                )
            )
            return 1
        os.execv(
            sys.executable,
            [sys.executable, str(BOUND), rest[0], rest[1], rest[2], rest[3]],
        )
    if not COMPLETE.is_file():
        print("missing kernel/brief_complete_engine.py", file=sys.stderr)
        return 1
    os.execv(sys.executable, [sys.executable, str(COMPLETE), *argv[1:]])
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
