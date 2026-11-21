"""Validate published scenarios against structural quality gates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.connection import get_connection, init_db
from src.db.repositories import ScenarioRepository
from src.services.validation_service import validate_bundle
from src.taxonomy import TECH_QUOTAS


def main() -> int:
    init_db()
    conn = get_connection()
    repo = ScenarioRepository(conn)
    counts = repo.counts_by_technology("published")
    total = repo.count("published")
    print(f"Published total: {total}")
    print("By technology:", counts)

    ok = True
    for tech, quota in TECH_QUOTAS.items():
        have = counts.get(tech, 0)
        if have < quota:
            print(f"FAIL: {tech} has {have}, need {quota}")
            ok = False
        else:
            print(f"OK: {tech} has {have} (>= {quota})")

    # sample validate first 50 of each tech
    failures = 0
    checked = 0
    for tech in TECH_QUOTAS:
        rows = repo.search(technology=tech, status="published", limit=50)
        for sc in rows:
            bundle = repo.get_bundle(sc.id)
            if not bundle:
                failures += 1
                continue
            errs = validate_bundle(bundle)
            checked += 1
            if errs:
                failures += 1
                if failures <= 10:
                    print(f"Validation issues for {sc.id}: {errs}")

    print(f"Checked {checked} sample bundles; failures={failures}")
    conn.close()
    return 0 if ok and failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
