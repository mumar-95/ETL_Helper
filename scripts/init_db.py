"""Initialize the SQLite database schema."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.connection import init_db


def main() -> None:
    path = init_db()
    print(f"Initialized database at {path}")


if __name__ == "__main__":
    main()
