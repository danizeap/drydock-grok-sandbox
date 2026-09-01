#!/usr/bin/env python3
"""Choreography wrapper around kernel/brief.py.

kernel/brief_complete.py --record-verify is completeness, not provenance (case 5b).
This wrapper refuses a bare --record-verify. Bound form:

  python3 scripts/brief.py --record-verify <packet> <verdict-file> \\
      <expected-sha256> <required-verdict-string>

which execs scripts/record_verify_bound.py (check_verdict first).
Other modes are delegated unchanged to kernel/brief_complete.py.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel" / "brief_complete.py"
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
                            "scripts/brief.py --record-verify requires "
                            "<packet> <verdict-file> <expected-sha256> "
                            "<required-verdict-string>; completeness-only "
                            "kernel/brief_complete.py is not provenance"
                        ),
                    },
                    indent=2,
                )
            )
            print(
                "refused: bare --record-verify is not provenance. "
                "usage: python3 scripts/brief.py --record-verify "
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
    if not KERNEL.is_file():
        print("missing kernel/brief_complete.py", file=sys.stderr)
        return 1
    os.execv(sys.executable, [sys.executable, str(KERNEL), *argv[1:]])
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
