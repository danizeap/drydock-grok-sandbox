#!/usr/bin/env python3
"""Choreography overlay on the vendored completeness engine.

Completeness lives at kernel/brief_engine.py (bytes unchanged from Drydock
kernel/brief.py @ 5f76f67). kernel/brief.py and kernel/brief_complete.py are
overlays: bare --record-verify is refused. Bound form:

  python3 kernel/brief.py --record-verify <packet> <verdict-file> \\
      <expected-sha256> <required-verdict-string>

which execs scripts/record_verify_bound.py (check_verdict first, then
kernel/brief_engine.py). Other modes are delegated unchanged to
kernel/brief_engine.py.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPLETE = ROOT / "kernel" / "brief_engine.py"
BOUND = ROOT / "scripts" / "record_verify_bound.py"


def main(argv: list[str]) -> int:
    if "--record-verify" in argv:
        i = argv.index("--record-verify")
        rest = argv[i + 1 :]
        if len(rest) != 4:
            print(
                json.dumps(
                    {
                        "recorded": False,
                        "reason": "bare-record-verify-refused",
                        "detail": (
                            "kernel/brief.py --record-verify requires "
                            "<packet> <verdict-file> <expected-sha256> "
                            "<required-verdict-string>; completeness-only "
                            "kernel/brief_engine.py is not provenance"
                        ),
                    },
                    indent=2,
                )
            )
            print(
                "refused: bare --record-verify is not provenance. "
                "usage: python3 kernel/brief.py --record-verify "
                "<packet> <verdict-file> <expected-sha256> "
                "<required-verdict-string>",
                file=sys.stderr,
            )
            return 1
        if not BOUND.is_file():
            print(
                json.dumps({"recorded": False, "reason": "missing-record_verify_bound"}),
                indent=2,
            )
            return 1
        os.execv(
            sys.executable,
            [sys.executable, str(BOUND), rest[0], rest[1], rest[2], rest[3]],
        )
    if not COMPLETE.is_file():
        print("missing kernel/brief_engine.py", file=sys.stderr)
        return 1
    os.execv(sys.executable, [sys.executable, str(COMPLETE), *argv[1:]])
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
