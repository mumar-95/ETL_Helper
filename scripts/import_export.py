"""Export / import scenario bundles as JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.connection import get_connection, init_db
from src.db.repositories import ScenarioRepository
from src.models.scenario import ScenarioBundle


def export_jsonl(path: Path, status: str = "published") -> int:
    init_db()
    conn = get_connection()
    repo = ScenarioRepository(conn)
    rows = repo.search(status=status, limit=100000)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for sc in rows:
            bundle = repo.get_bundle(sc.id)
            if not bundle:
                continue
            fh.write(bundle.model_dump_json() + "\n")
            count += 1
    conn.close()
    return count


def import_jsonl(path: Path) -> int:
    init_db()
    conn = get_connection()
    repo = ScenarioRepository(conn)
    count = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            bundle = ScenarioBundle.model_validate(json.loads(line))
            repo.upsert_bundle(bundle)
            count += 1
    conn.close()
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["export", "import"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--status", default="published")
    args = parser.parse_args()
    if args.action == "export":
        n = export_jsonl(args.path, status=args.status)
        print(f"Exported {n} bundles to {args.path}")
    else:
        n = import_jsonl(args.path)
        print(f"Imported {n} bundles from {args.path}")


if __name__ == "__main__":
    main()
