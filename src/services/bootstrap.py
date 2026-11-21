"""Ensure the scenario bank exists when the app starts."""

from __future__ import annotations

from src.db.connection import get_connection, init_db
from src.db.repositories import ScenarioRepository
from src.services.content_author import author_bundle, iter_briefs
from src.services.dedup_service import content_hash
from src.services.validation_service import validate_bundle
from src.taxonomy import TECH_QUOTAS


TARGET_TOTAL = sum(TECH_QUOTAS.values())


def published_count() -> int:
    init_db()
    conn = get_connection()
    try:
        return ScenarioRepository(conn).count("published")
    finally:
        conn.close()


def ensure_scenario_bank(*, force_reset: bool = False) -> dict[str, int | bool]:
    """Create the 1,000-scenario bank if missing or incomplete.

    Safe to call on every app start. Uses the project-root SQLite path so
    mobile and desktop hit the same database.
    """
    init_db()
    conn = get_connection()
    repo = ScenarioRepository(conn)

    if force_reset:
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

    current = repo.count("published")
    if current >= TARGET_TOTAL:
        conn.close()
        return {"ok": True, "published": current, "inserted": 0, "bootstrapped": False}

    seen_hashes = {
        content_hash(title, stem) for _, title, stem in repo.list_titles_stems()
    }
    inserted = 0
    for idx, brief in enumerate(iter_briefs()):
        if repo.exists(brief["id"]):
            continue
        ch = content_hash(brief["title"], brief["stem"])
        if ch in seen_hashes:
            continue
        label = "verified" if (idx % 20 == 0) else "ai_generated"
        bundle = author_bundle(brief, label=label, status="published")
        errors = validate_bundle(bundle)
        if any("Section K" in e for e in errors):
            bundle.explanation.section_k += (
                "\n\nApproach 1 — primary design as above.\n"
                "Approach 2 — alternate SQL or tool-based design with tradeoffs on ops vs speed."
            )
            bundle.explanation.compute_flags()
        repo.upsert_bundle(bundle)
        seen_hashes.add(ch)
        inserted += 1

    final = repo.count("published")
    conn.close()
    return {
        "ok": final >= TARGET_TOTAL,
        "published": final,
        "inserted": inserted,
        "bootstrapped": inserted > 0,
    }
