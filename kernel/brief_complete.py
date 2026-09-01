#!/usr/bin/env python3
"""Overlay alias: same gate as kernel/brief.py.

Vendored completeness bytes are at kernel/vendor/brief.py. Calling this path
with bare --record-verify is refused (execs kernel/brief.py).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

OVERLAY = Path(__file__).resolve().parent / "brief.py"

if __name__ == "__main__":
    os.execv(sys.executable, [sys.executable, str(OVERLAY), *sys.argv[1:]])
