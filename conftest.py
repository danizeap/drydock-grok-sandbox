"""Make the ``src`` layout importable for pytest without packaging setup."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
