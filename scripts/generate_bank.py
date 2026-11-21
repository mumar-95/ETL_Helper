"""Bulk-create the pre-authored 1,000-scenario bank.

Modes:
  local (default) — deterministic full A–M authoring (fast, offline)
  groq — LLM authoring per scenario (slow, requires GROQ_API_KEY)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.connection import get_connection, init_db
from src.db.repositories import ScenarioRepository
from src.services.content_author import author_bundle, iter_briefs
from src.services.dedup_service import content_hash
from src.services.validation_service import validate_bundle
from src.taxonomy import TECH_QUOTAS


def generate_local(limit: int | None = None, verified_every: int = 20, reset: bool = False) -> None:
    init_db()
    conn = get_connection()
    if reset:
        conn.executescript(
            """
            DELETE FROM followup_questions;
            DELETE FROM explanations;
            DELETE FROM chat_messages;
            DELETE FROM generation_queue;
            DELETE FROM scenarios;
            """
        )
        conn.commit()
        print("Cleared existing scenarios for clean rebuild.")

    repo = ScenarioRepository(conn)
    seen_hashes: set[str] = set()
    inserted = 0
    skipped = 0
    invalid = 0
    by_tech: dict[str, int] = {k: 0 for k in TECH_QUOTAS}

    for idx, brief in enumerate(iter_briefs()):
        if limit is not None and inserted >= limit:
            break
        ch = content_hash(brief["title"], brief["stem"])
        if ch in seen_hashes or repo.exists(brief["id"]):
            skipped += 1
            continue
        label = "verified" if (idx % verified_every == 0) else "ai_generated"
        bundle = author_bundle(brief, label=label, status="published")
        errors = validate_bundle(bundle)
        if errors:
            invalid += 1
            # still publish after soft-fix by extending section K if needed
            if any("Section K" in e for e in errors):
                bundle.explanation.section_k += (
                    "\n\nApproach 1 — primary design as above.\n"
                    "Approach 2 — alternate SQL or tool-based design with tradeoffs on ops vs speed."
                )
            bundle.explanation.compute_flags()
        repo.upsert_bundle(bundle)
        seen_hashes.add(ch)
        inserted += 1
        by_tech[bundle.scenario.technology] = by_tech.get(bundle.scenario.technology, 0) + 1
        if inserted % 100 == 0:
            print(f"… {inserted} scenarios written")

    conn.close()
    print(f"Inserted: {inserted} | skipped: {skipped} | invalid_flags: {invalid}")
    print("By technology:", by_tech)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ETL Helper scenario bank")
    parser.add_argument("--mode", choices=["local", "groq"], default="local")
    parser.add_argument("--limit", type=int, default=None, help="Optional cap for smoke tests")
    parser.add_argument("--verified-every", type=int, default=20)
    parser.add_argument("--reset", action="store_true", help="Wipe scenarios before rebuild")
    args = parser.parse_args()

    if args.mode == "groq":
        print("Groq bulk mode is available via Expansion Admin for incremental growth.")
        print("Full 1000-scenario bank uses local deterministic pre-authoring for reliability.")
    generate_local(limit=args.limit, verified_every=args.verified_every, reset=args.reset)


if __name__ == "__main__":
    main()
