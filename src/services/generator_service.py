"""Scenario generation for bank expansion and optional Groq enrichment."""

from __future__ import annotations

import json
from typing import Any

from src.db.repositories import GenerationQueueRepository, ScenarioRepository
from src.models.scenario import ExplanationRecord, FollowUp, ScenarioBundle, ScenarioRecord, utc_now
from src.prompts.explain_am import build_explain_prompt, build_generate_scenario_prompt
from src.services.content_author import author_bundle
from src.services.dedup_service import content_hash, is_duplicate
from src.services.groq_client import chat_completion, extract_json
from src.services.validation_service import validate_bundle
from src.taxonomy import BUSINESS_DOMAINS, DATA_VOLUMES, DIFFICULTY_YEAR_RANGES, IICS_SERVICE_SCOPES


def generate_local_variant(
    *,
    technology: str,
    category: str,
    difficulty: str,
    topic: str,
    index: int = 0,
) -> ScenarioBundle:
    domain = BUSINESS_DOMAINS[index % len(BUSINESS_DOMAINS)]
    volume = DATA_VOLUMES[index % len(DATA_VOLUMES)]
    years = DIFFICULTY_YEAR_RANGES[difficulty]
    prefix = {"PowerCenter": "PC", "IICS": "IICS", "SQL": "SQL"}[technology]
    scenario_id = f"{prefix}-GEN-{index+1:04d}-{abs(hash(topic + domain + str(index))) % 100000:05d}"
    brief = {
        "id": scenario_id,
        "technology": technology,
        "category": category,
        "difficulty": difficulty,
        "years_min": years[0],
        "years_max": years[1],
        "title": f"{technology} expansion #{index+1}: {topic.title()} — {domain} [{difficulty}]",
        "stem": (
            f"[{scenario_id}] Design a production ETL approach for {domain} focusing on {topic}. "
            f"Volume ~{volume}. Technology: {technology}. Include recovery and validation. "
            f"Make the design specific to constraint set #{index+1}."
        ),
        "topic": topic,
        "domain": domain,
        "volume": volume,
        "iics_service_scope": IICS_SERVICE_SCOPES[index % len(IICS_SERVICE_SCOPES)]
        if technology == "IICS"
        else None,
        "tags": [topic, difficulty, "expansion"],
    }
    return author_bundle(brief, label="ai_generated", status="draft")


def generate_with_groq(
    *,
    technology: str,
    category: str,
    difficulty: str,
    topic: str,
    domain: str | None = None,
    volume: str | None = None,
) -> ScenarioBundle:
    domain = domain or BUSINESS_DOMAINS[0]
    volume = volume or DATA_VOLUMES[0]
    iics_scope = IICS_SERVICE_SCOPES[0] if technology == "IICS" else None
    meta_prompt = build_generate_scenario_prompt(
        technology, category, difficulty, topic, domain, volume, iics_scope
    )
    meta_raw = chat_completion(
        [{"role": "user", "content": meta_prompt}],
        temperature=0.7,
    )
    meta = extract_json(meta_raw)
    title = meta["title"]
    stem = meta["stem"]
    explain_prompt = build_explain_prompt(technology, title, stem, category, difficulty)
    explain_raw = chat_completion(
        [{"role": "user", "content": explain_prompt}],
        temperature=0.35,
    )
    data = extract_json(explain_raw)
    years = DIFFICULTY_YEAR_RANGES[difficulty]
    scenario_id = f"{technology[:2].upper()}-AI-{abs(hash(title)) % 10_000_000:07d}"
    followup_list = data.get("followups") or []
    if isinstance(followup_list, str):
        followup_list = [q.strip() for q in followup_list.split("\n") if q.strip()]
    followups = [
        FollowUp(ordinal=i + 1, question=str(q), difficulty_step=difficulty)
        for i, q in enumerate(followup_list[:10])
    ]
    if not followups and data.get("section_m"):
        lines = [ln.strip(" -") for ln in str(data["section_m"]).splitlines() if "?" in ln]
        followups = [
            FollowUp(ordinal=i + 1, question=ln, difficulty_step=difficulty)
            for i, ln in enumerate(lines[:10])
        ]

    explanation = ExplanationRecord(
        scenario_id=scenario_id,
        section_a=data["section_a"],
        section_b=data["section_b"],
        section_c=data["section_c"],
        section_d=data["section_d"],
        section_e=data["section_e"],
        section_f=data["section_f"],
        section_g=data["section_g"],
        section_h=data["section_h"],
        section_i=data["section_i"],
        section_j=data["section_j"],
        section_k=data["section_k"],
        section_l=data["section_l"],
        section_m=data.get("section_m")
        or "\n".join(f"{f.ordinal}. {f.question}" for f in followups),
        sample_input_json=json.dumps(data.get("sample_input_json"))
        if not isinstance(data.get("sample_input_json"), str)
        else data.get("sample_input_json"),
        expected_output_json=json.dumps(data.get("expected_output_json"))
        if not isinstance(data.get("expected_output_json"), str)
        else data.get("expected_output_json"),
        mapping_flow_ascii=data.get("mapping_flow_ascii"),
        mapping_flow_mermaid=data.get("mapping_flow_mermaid"),
        sql_logic=data.get("sql_logic"),
        interview_answer=data.get("interview_answer") or data.get("section_l"),
    )
    explanation.compute_flags()
    scenario = ScenarioRecord(
        id=scenario_id,
        technology=technology,
        category=category,
        difficulty=difficulty,
        years_min=years[0],
        years_max=years[1],
        title=title,
        stem=stem,
        iics_service_scope=meta.get("iics_service_scope") or iics_scope,
        label="ai_generated",
        status="draft",
        tags=meta.get("tags") or [topic, difficulty],
        created_at=utc_now(),
        updated_at=utc_now(),
        content_hash=content_hash(title, stem),
    )
    return ScenarioBundle(scenario=scenario, explanation=explanation, followups=followups)


def enqueue_expansion(
    conn,
    *,
    technology: str,
    category: str,
    difficulty: str,
    topic: str,
    use_groq: bool = False,
) -> dict[str, Any]:
    repo = ScenarioRepository(conn)
    queue = GenerationQueueRepository(conn)
    existing = repo.list_titles_stems()
    if use_groq:
        bundle = generate_with_groq(
            technology=technology,
            category=category,
            difficulty=difficulty,
            topic=topic,
        )
    else:
        bundle = generate_local_variant(
            technology=technology,
            category=category,
            difficulty=difficulty,
            topic=topic,
            index=repo.count(status=None) + 1,
        )
    dup, score, match_id = is_duplicate(
        bundle.scenario.title, bundle.scenario.stem, existing, threshold=0.85
    )
    errors = validate_bundle(bundle)
    qid = queue.enqueue(
        {
            "scenario_id": None if dup else bundle.scenario.id,
            "technology": technology,
            "category": category,
            "difficulty": difficulty,
            "title": bundle.scenario.title,
            "stem": bundle.scenario.stem,
            "payload_json": bundle.model_dump_json(),
            "dedup_score": score,
            "status": "rejected_duplicate" if dup else "pending_review",
        }
    )
    return {
        "queue_id": qid,
        "duplicate": dup,
        "dedup_score": score,
        "match_id": match_id,
        "validation_errors": errors,
        "bundle": bundle if not dup else None,
    }


def promote_queue_item(conn, queue_id: int, *, label: str = "ai_generated", status: str = "published") -> str | None:
    queue = GenerationQueueRepository(conn)
    repo = ScenarioRepository(conn)
    rows = [r for r in queue.list_pending(200) if r["id"] == queue_id]
    if not rows:
        # also allow fetching any status
        row = conn.execute("SELECT * FROM generation_queue WHERE id = ?", (queue_id,)).fetchone()
        if not row:
            return None
        item = dict(row)
    else:
        item = rows[0]
    if not item.get("payload_json"):
        return None
    data = json.loads(item["payload_json"])
    bundle = ScenarioBundle.model_validate(data)
    bundle.scenario.label = label
    bundle.scenario.status = status
    bundle.scenario.updated_at = utc_now()
    errors = validate_bundle(bundle)
    if errors and status == "published":
        bundle.scenario.status = "validated"
    repo.upsert_bundle(bundle)
    queue.update_status(queue_id, "published" if bundle.scenario.status == "published" else "validated", bundle.scenario.id)
    return bundle.scenario.id
