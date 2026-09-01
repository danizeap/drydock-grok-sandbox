#!/usr/bin/env python3
"""Bind a verifier verdict file to a stated sha256 and required verdict string.

Exit 0 only if:
  1. the file's bytes sha256 (hex, case-insensitive) match expected, AND
  2. the required verdict string is present as a whole line or substring in UTF-8 text.

Stdlib only. Fail closed. Choreography tooling — not a Drydock kernel file.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(
            "usage: python3 check_verdict.py <verdict-file> <expected-sha256> <required-verdict-string>",
            file=sys.stderr,
        )
        return 2
    path_s, expected, required = argv[1], argv[2], argv[3]
    path = Path(path_s)
    if not path.is_file():
        print(f"missing verdict file: {path_s}", file=sys.stderr)
        return 1
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual.lower() != expected.strip().lower():
        print(f"sha256 mismatch: got {actual} expected {expected.strip().lower()}", file=sys.stderr)
        return 1
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        print("verdict file is not valid UTF-8", file=sys.stderr)
        return 1
    # whole line OR substring
    lines = text.splitlines()
    if required not in text and required not in lines:
        print(f"required verdict string not found: {required!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
