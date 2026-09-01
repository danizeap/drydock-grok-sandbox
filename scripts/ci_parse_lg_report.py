#!/usr/bin/env python3
"""Fail closed on a LaunchGuardian report JSON.

Exit nonzero if any scanner_availability value is not exactly "ran",
or if launch_status is BLOCKED or INCOMPLETE, or if the report is missing.
Quiet/missing scan is a fail. Stdlib only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FAIL_STATUSES = {"BLOCKED", "INCOMPLETE"}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 ci_parse_lg_report.py <report.json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"missing LaunchGuardian report: {path}", file=sys.stderr)
        return 1
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"unreadable LaunchGuardian report JSON: {exc}", file=sys.stderr)
        return 1
    avail = report.get("scanner_availability")
    if not isinstance(avail, dict) or not avail:
        print("scanner_availability missing or empty — quiet scan is a fail", file=sys.stderr)
        return 1
    not_ran = {name: state for name, state in avail.items() if state != "ran"}
    if not_ran:
        print(f"scanner_availability not all ran: {not_ran}", file=sys.stderr)
        return 1
    status = report.get("launch_status")
    if status is None or status == "":
        print("launch_status missing — quiet scan is a fail", file=sys.stderr)
        return 1
    if status in FAIL_STATUSES:
        print(f"launch_status={status!r} is a fail", file=sys.stderr)
        return 1
    print(f"launch_status={status} scanner_availability all ran ({len(avail)} scanners)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
