#!/usr/bin/env python3
"""Record a verify-run only after check_verdict.py binds the in-channel report.

brief.py --record-verify is completeness, not provenance. Case 5b showed a
typed PASS with no in-channel hash still produced recorded=true. This wrapper
is the choreography gate: check_verdict must exit 0 *before* record_verify
runs. Completeness is kernel/brief_complete_engine.py; do not call it --record-verify directly. kernel/brief.py, kernel/brief_complete.py, scripts/brief.py and kernel/brief_engine.py all refuse the bare form.

usage:
  python3 scripts/record_verify_bound.py <packet> <verdict-file> <expected-sha256> <required-verdict-string>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = ROOT / "scripts" / "check_verdict.py"
BRIEF = ROOT / "kernel" / "brief_complete_engine.py"


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(
            "usage: python3 record_verify_bound.py <packet> <verdict-file> "
            "<expected-sha256> <required-verdict-string>",
            file=sys.stderr,
        )
        return 2
    packet, verdict, digest, required = argv[1], argv[2], argv[3], argv[4]
    chk = subprocess.run(
        [sys.executable, str(CHECK), verdict, digest, required],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if chk.returncode != 0:
        print(
            json.dumps(
                {
                    "recorded": False,
                    "reason": "check_verdict-failed",
                    "check_verdict_exit": chk.returncode,
                    "detail": (chk.stderr or chk.stdout)[-400:],
                },
                indent=2,
            )
        )
        if chk.stderr:
            print(chk.stderr, file=sys.stderr, end="")
        return 1
    rec = subprocess.run(
        [sys.executable, str(BRIEF), "--record-verify", packet],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    sys.stdout.write(rec.stdout)
    if rec.stderr:
        sys.stderr.write(rec.stderr)
    return 0 if rec.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
