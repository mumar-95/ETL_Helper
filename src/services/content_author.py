"""Deterministic pre-authoring of full A–M scenario bundles for the bank."""

from __future__ import annotations

import itertools
import json
import re
from typing import Iterator

from src.models.scenario import ExplanationRecord, FollowUp, ScenarioBundle, ScenarioRecord, utc_now
from src.services.dedup_service import content_hash
from src.taxonomy import (
    BUSINESS_DOMAINS,
    CATEGORIES,
    DATA_VOLUMES,
    DIFFICULTIES,
    DIFFICULTY_YEAR_RANGES,
    IICS_SERVICE_SCOPES,
    IICS_TOPICS,
    POWERCENTER_TOPICS,
    SQL_TOPICS,
    TECH_QUOTAS,
)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", text.upper()).strip("-")[:28]


def _topic_pool(technology: str, category: str) -> list[str]:
    mapping = {
        "PowerCenter": POWERCENTER_TOPICS,
        "IICS": IICS_TOPICS,
        "SQL": SQL_TOPICS,
    }[technology]
    if category in mapping:
        return mapping[category]
    # fallback: flatten all topics for that tech
    topics: list[str] = []
    for values in mapping.values():
        topics.extend(values)
    if not topics:
        topics = [category.replace(" scenarios", "")]
    return topics


def _prefix(technology: str) -> str:
    return {"PowerCenter": "PC", "IICS": "IICS", "SQL": "SQL"}[technology]


def _iics_scope(index: int, category: str) -> str:
    if "API" in category or "Architecture" in category:
        return IICS_SERVICE_SCOPES[index % len(IICS_SERVICE_SCOPES)]
    if "Workflow" in category or "Recovery" in category:
        return "CDI + Taskflows"
    if "Data quality" in category.lower() or "Data quality" in category:
        return "CDI + Data Quality"
    return "CDI"


def iter_briefs() -> Iterator[dict]:
    """Yield exactly TECH_QUOTAS briefs with balanced category/difficulty."""
    for technology, quota in TECH_QUOTAS.items():
        # distribute across categories and difficulties
        combo = list(itertools.product(CATEGORIES, DIFFICULTIES))
        # cycle combos until quota filled
        for i in range(quota):
            category, difficulty = combo[i % len(combo)]
            topics = _topic_pool(technology, category)
            topic = topics[i % len(topics)]
            domain = BUSINESS_DOMAINS[i % len(BUSINESS_DOMAINS)]
            volume = DATA_VOLUMES[i % len(DATA_VOLUMES)]
            years = DIFFICULTY_YEAR_RANGES[difficulty]
            cat_code = _slug(category.split()[0])
            scenario_id = f"{_prefix(technology)}-{cat_code}-{i+1:04d}"
            title = _build_title(technology, topic, domain, difficulty, i)
            stem = _build_stem(
                technology, topic, domain, volume, difficulty, category, i, scenario_id
            )
            yield {
                "id": scenario_id,
                "technology": technology,
                "category": category,
                "difficulty": difficulty,
                "years_min": years[0],
                "years_max": years[1],
                "title": title,
                "stem": stem,
                "topic": topic,
                "domain": domain,
                "volume": volume,
                "iics_service_scope": _iics_scope(i, category) if technology == "IICS" else None,
                "tags": [topic, domain.split()[0].lower(), difficulty, scenario_id],
            }


def _simple_topic(topic: str) -> str:
    """Make technical topic phrases easier to read in titles."""
    replacements = {
        "large lookup table performance": "slow big lookup table",
        "dynamic lookup cache": "dynamic lookup",
        "lookup cache synchronization": "lookup cache out of date",
        "connected versus unconnected lookup": "connected vs unconnected lookup",
        "lookup returning multiple matching records": "lookup finds many matches",
        "last successful load date": "load only new changes",
        "mapping variable implementation": "mapping variables",
        "late-arriving records": "data that arrives late",
        "deleted source records": "records deleted in source",
        "watermark management": "keeping a last-load timestamp",
        "session suddenly running slowly": "job suddenly became slow",
        "Secure Agent failures": "Secure Agent went down",
        "PowerCenter to IICS migration": "moving from PowerCenter to IICS",
        "duplicate removal": "remove duplicate rows",
        "latest record selection": "pick the latest record",
        "SCD Type 1 with MERGE": "SCD Type 1 using MERGE",
        "SCD Type 2 with MERGE": "SCD Type 2 using MERGE",
    }
    return replacements.get(topic, topic)


def _build_title(technology: str, topic: str, domain: str, difficulty: str, index: int) -> str:
    return f"{_simple_topic(topic).capitalize()} for {domain} ({technology}, {difficulty})"


def _build_stem(
    technology: str,
    topic: str,
    domain: str,
    volume: str,
    difficulty: str,
    category: str,
    index: int,
    scenario_id: str,
) -> str:
    constraints = [
        "some rows arrive late, after you already moved the last-load time forward",
        "the same customer id appears more than once in one batch",
        "the source file comes in two parts instead of one file",
        "the lookup/reference data changes while the job is running",
        "restarting the job creates duplicate rows in the target",
        "the job must finish in about 45 minutes",
        "the source marks deletes with a soft-delete flag",
        "some rows have blank business keys and must be sent to a reject table",
        "two source systems have slightly different clocks/timestamps",
        "the production parameter file is missing after deployment",
    ]
    constraint = constraints[index % len(constraints)]
    simple_topic = _simple_topic(topic)
    return (
        f"You work on an ETL project for {domain}.\n\n"
        f"Tool to use: {technology}.\n"
        f"Topic: {simple_topic}.\n"
        f"Category: {category}.\n"
        f"Data size: about {volume}.\n"
        f"Level: {difficulty}.\n\n"
        f"Main problem: {constraint}.\n\n"
        f"In simple words, explain how you would build a safe solution. Cover:\n"
        f"1) how you read the source data\n"
        f"2) how you transform or look up data\n"
        f"3) how you load the target (insert/update/history)\n"
        f"4) what you do if the job fails halfway\n"
        f"5) how you check the final data is correct\n\n"
        f"Scenario id: {scenario_id}."
    )


def _sample_tables(domain: str, topic: str) -> tuple[str, str, str]:
    src_rows = [
        {"CUST_ID": f"C{100+i}", "NAME": f"Customer {i}", "CITY": city, "STATUS": status, "UPD_TS": ts}
        for i, (city, status, ts) in enumerate(
            [
                ("Austin", "ACTIVE", "2024-01-01 08:00:00"),
                ("Dallas", "ACTIVE", "2024-01-02 09:15:00"),
                ("Austin", "INACTIVE", "2024-01-02 10:00:00"),
                ("Houston", "ACTIVE", "2024-01-03 11:20:00"),
                ("Dallas", "ACTIVE", "2024-01-03 12:00:00"),
                ("Austin", "ACTIVE", "2024-01-04 08:30:00"),
                ("Plano", "ACTIVE", "2024-01-04 09:00:00"),
                ("Houston", "INACTIVE", "2024-01-05 14:00:00"),
            ]
        )
    ]
    tgt_rows = [
        {"CUST_SK": i + 1, "CUST_ID": r["CUST_ID"], "NAME": r["NAME"], "CITY": r["CITY"], "EFF_START": r["UPD_TS"][:10], "IS_CURRENT": "Y" if r["STATUS"] == "ACTIVE" else "N"}
        for i, r in enumerate(src_rows[:6])
    ]
    sample = {"SRC_CUSTOMER": src_rows, "notes": f"Sample for {domain} / {topic}"}
    expected = {"TGT_DIM_CUSTOMER": tgt_rows}
    return json.dumps(sample), json.dumps(expected), json.dumps(src_rows)


def _ascii_flow(technology: str) -> str:
    if technology == "SQL":
        return (
            "Source Tables\n"
            "      |\n"
            "      v\n"
            "Staging / CTE Layer\n"
            "      |\n"
            "      v\n"
            "Transform Logic (Window/MERGE)\n"
            "      |\n"
            "      v\n"
            "Target Table + Audit"
        )
    if technology == "IICS":
        return (
            "Cloud Source Connection\n"
            "      |\n"
            "      v\n"
            "Mapping (Source -> Expression -> Lookup -> Router)\n"
            "      |\n"
            "      v\n"
            "Mapping Task\n"
            "      |\n"
            "      v\n"
            "Taskflow (parallel/conditional) -> Target -> Monitor"
        )
    return (
        "Source Definition\n"
        "      |\n"
        "      v\n"
        "Source Qualifier\n"
        "      |\n"
        "      v\n"
        "Expression Transformation\n"
        "      |\n"
        "      v\n"
        "Lookup Transformation\n"
        "      |\n"
        "      v\n"
        "Router / Update Strategy\n"
        "      |\n"
        "      +------------------+\n"
        "      |                  |\n"
        "      v                  v\n"
        "Insert New         Update Existing\n"
        "      |                  |\n"
        "      +--------+---------+\n"
        "               |\n"
        "               v\n"
        "          Target Table"
    )


def _mermaid_flow(technology: str) -> str:
    if technology == "SQL":
        return "flowchart TD\n  SRC[SourceTables] --> CTE[CTETransform]\n  CTE --> MERGE[MERGEOrInsert]\n  MERGE --> TGT[Target]\n  MERGE --> AUD[Audit]"
    if technology == "IICS":
        return "flowchart TD\n  SRC[CloudSource] --> MAP[Mapping]\n  MAP --> MT[MappingTask]\n  MT --> TF[Taskflow]\n  TF --> TGT[Target]\n  TF --> MON[Monitor]"
    return (
        "flowchart TD\n  SRC[Source] --> SQ[SourceQualifier]\n  SQ --> EXP[Expression]\n"
        "  EXP --> LKP[Lookup]\n  LKP --> RTR[Router]\n  RTR --> INS[InsertPath]\n"
        "  RTR --> UPD[UpdatePath]\n  INS --> TGT[Target]\n  UPD --> TGT"
    )


def _sql_block(technology: str, topic: str) -> str:
    return f"""-- Representative SQL for: {topic}
-- Works conceptually on Oracle and SQL Server; note dialect differences below.

WITH ranked AS (
  SELECT
    s.CUST_ID,
    s.NAME,
    s.CITY,
    s.STATUS,
    s.UPD_TS,
    ROW_NUMBER() OVER (PARTITION BY s.CUST_ID ORDER BY s.UPD_TS DESC) AS RN
  FROM SRC_CUSTOMER s
  WHERE s.UPD_TS > :LAST_SUCCESS_TS
)
SELECT CUST_ID, NAME, CITY, STATUS, UPD_TS
FROM ranked
WHERE RN = 1;

/* Oracle: use MERGE INTO ... USING ... ON (...)
   SQL Server: MERGE ... ; or staging + UPDATE/INSERT pattern.
   Incremental watermark: persist LAST_SUCCESS_TS after commit.
   Topic focus: {topic} | Engine context: {technology}
*/"""


def _section_e(technology: str, topic: str, domain: str) -> str:
    simple = _simple_topic(topic)
    if technology == "PowerCenter":
        return f"""Build this in PowerCenter, step by step, for {domain} ({simple}):

1. Import the source tables or files.
2. Create/import the target table, plus an error/reject table and an audit table.
3. Create a mapping for this problem.
4. Add the needed transformations: Source Qualifier, Expression, Lookup, Router, Update Strategy (and Sequence Generator if you need surrogate keys).
5. Set lookup conditions on the business key. Choose static, dynamic, or persistent cache based on the problem.
6. Connect only the columns you need.
7. Add Source Qualifier or Lookup SQL Override if that makes the extract faster or cleaner.
8. Validate the mapping.
9. Configure the session (commit interval, error logging, cache directory, data-driven writes).
10. Build the workflow (dependencies, file wait events, failure email).
11. Use parameters for last-load time, file path, and connections.
12. Test with sample data, check counts, then move DEV → QA → PROD."""
    if technology == "IICS":
        return f"""Build this in IICS, step by step, for {domain} ({simple}):

1. Create source and target connections.
2. Check the Secure Agent / runtime environment has enough memory and the right drivers.
3. Create a mapping for this problem in Mapping Designer.
4. Configure source filters and target fields (including incremental options if needed).
5. Add Expression, Lookup, Router, and other transformations as needed.
6. Add mapping parameters for last-load time, paths, and environment values.
7. Create a mapping task (schedule, parameters, error rows).
8. If needed, wrap it in a taskflow (parallel steps, decisions, failure path).
9. Capture bad rows and task failures.
10. Deploy to the next environment and monitor row counts.
Always say if this is CDI-only or needs another IICS service."""
    return f"""Build this in SQL, step by step, for {domain} ({simple}):

1. Create staging and target tables with keys and useful indexes.
2. Load a small sample that includes duplicates, late rows, and blank keys.
3. Write the query in layers: filter new rows → remove duplicates → apply insert/update or SCD → write audit rows.
4. Use MERGE (or INSERT + UPDATE) for the final load.
5. Check the expected output.
6. Tune with indexes and fresh statistics.
7. Prefer set-based SQL over row-by-row loops."""


def _section_f(technology: str, topic: str) -> str:
    simple = _simple_topic(topic)
    if technology == "SQL":
        return f"""SQL pieces used for {simple}:

- Filter step: read only new/changed rows first so the query stays small.
- Ranking step: use ROW_NUMBER or RANK to keep the latest row per key. Common mistake: wrong PARTITION BY.
- MERGE step: if the key exists, update; if not, insert. Needs good indexes.
- Audit step: store batch id, counts, and reject reasons.

Flow: source → filter → rank → merge → target + audit."""
    return f"""Transformations used for {simple}:

1. Source Qualifier / Source — reads the data. Tip: filter early; do not select unused columns.
2. Expression — cleans keys, builds flags, and prepares lookup values.
3. Lookup — checks if the row already exists (or brings reference data). Match = update path. No match = insert path. Watch cache size and NULL keys.
4. Router — sends rows to insert, update, or reject groups.
5. Update Strategy / Target — marks DD_INSERT or DD_UPDATE. Session must be data-driven.

Tip: size the lookup cache correctly and push filters to the source when possible."""


def author_bundle(brief: dict, *, label: str = "ai_generated", status: str = "published") -> ScenarioBundle:
    technology = brief["technology"]
    topic = brief["topic"]
    domain = brief["domain"]
    volume = brief["volume"]
    sample_json, expected_json, _ = _sample_tables(domain, topic)
    ascii_flow = _ascii_flow(technology)
    mermaid = _mermaid_flow(technology)
    sql_logic = _sql_block(technology, topic)

    simple = _simple_topic(topic)

    section_a = f"""What does the business need?
They need a reliable ETL process for {domain} that handles: {simple}.

Why?
Reports and daily operations need correct data on time. Volume is about {volume}.

What problem are we solving?
If we load data the wrong way, we can create duplicates, miss updates, or lose history.

What should the final result look like?
Clean target data, plus reject rows and audit counts, even if a job fails and is restarted."""

    section_b = f"""Simple project picture:

- Business area: {domain}
- Source: operational tables/files (example: SRC_CUSTOMER)
- Target: TGT_DIM_CUSTOMER, plus staging, reject, and audit tables
- Volume: {volume}
- Main topic: {simple}
- Extra challenges: late data, safe restart, speed, and environment parameters

Expected result: correct inserts/updates (or history), with count checks you can explain in an interview."""

    section_c = f"""Here is sample source data (SRC_CUSTOMER) for {domain}.
Columns: CUST_ID, NAME, CITY, STATUS, UPD_TS.

Use these rows to explain:
- which rows are new
- which rows are updates
- which rows are duplicates
- how {simple} changes the result

The table view is available from sample_input_json."""

    section_d = f"""Expected target after applying {simple}:

- New keys → insert
- Changed attributes → update or SCD history, based on the design
- Bad rows → reject table with a reason
- Audit table → batch id and row counts

Walk through each sample row and say what happens to it."""

    section_e = _section_e(technology, topic, domain)
    section_f = _section_f(technology, topic)

    section_g = f"""SQL you can use for {simple}:

{sql_logic}

In plain English:
- The WITH block gets only newer rows.
- ROW_NUMBER keeps the latest row for each customer.
- WHERE RN = 1 removes duplicates.
- Then MERGE/INSERT-UPDATE writes the target.

Oracle vs SQL Server: date functions and identity/sequence syntax can differ, but the idea is the same."""

    section_h = f"""Flow diagram for {simple}:

ASCII:
{ascii_flow}

Mermaid:
{mermaid}
"""

    if technology == "PowerCenter":
        section_i = f"""How to make {simple} faster in PowerCenter:

- Find the bottleneck: source read, lookup cache, or target write.
- Size the lookup cache so it fits in memory.
- Use persistent cache only when the lookup data is stable.
- Filter in Source Qualifier SQL so you read fewer rows.
- Tune commit interval and use bulk load when it is safe.
- Use partitioning for very large volumes.
- Watch DTM buffer and cache overflow."""
    elif technology == "IICS":
        section_i = f"""How to make {simple} faster in IICS/CDI:

- Give the Secure Agent enough CPU and memory.
- Filter lookup and source data before caching.
- Tune target batch size.
- Use parallel taskflow steps only when dependencies allow it.
- Use pushdown when the connector supports it.
- Watch agent CPU, memory, and disk."""
    else:
        section_i = f"""How to make {simple} faster in SQL:

- Add indexes on join keys and last-update columns.
- Keep statistics up to date.
- Prefer set-based MERGE over loops.
- Avoid functions on filter columns.
- Check the plan for sorts/spills on large volumes ({volume})."""

    section_j = f"""What can go wrong with {simple}, and how to handle it:

- Job crashes halfway → do not move the last-load time until success.
- Bad rows → send them to a reject table with a clear reason.
- Restart creates duplicates → use natural key checks, dynamic lookup, or MERGE.
- Late files or bad parameters → fail early and alert the team.
- Always compare source vs target counts before you say the load is done.
- Monitor logs, row counts, and runtime."""

    section_k = f"""Approach 1 — {'Informatica mapping design' if technology != 'SQL' else 'Pure SQL (CTE + MERGE)'}:
Good for: {'clear steps, reuse, and operations control' if technology != 'SQL' else 'speed and fewer tools'}.
Watch out for: {'agent/session setup and cache tuning' if technology != 'SQL' else 'SQL that becomes hard to read'}.

Approach 2 — {'More SQL / pushdown' if technology != 'SQL' else 'Informatica job that calls SQL procedures'}:
Good for: heavy database work and large set updates.
Watch out for: harder restart control and logic split across tools.

For {domain} at about {volume}, pick the approach that best fits the SLA and your team’s skills."""

    section_l = (
        f"For this {technology} interview question on {domain}, I would keep the design simple and safe. "
        f"I would load only new changes, use a lookup or MERGE to decide insert vs update for {simple}, "
        f"send bad rows to a reject table, write audit counts, and move the last-load time only after success. "
        f"If the job fails halfway, I can restart without creating duplicates, and I would prove success with "
        f"source-to-target count checks."
    )

    followup_texts = [
        f"In simple words, what is a last-load timestamp (watermark) and where do you store it for {simple}?",
        f"What happens if the job fails after half the rows are already loaded?",
        f"When would you use a dynamic lookup instead of SQL MERGE for {domain}?",
        f"How would you make this design handle about {volume} without becoming too slow?",
        f"How do you know the lookup cache is wrong, and how do you fix it?",
        f"How would you test late-arriving data for this design?",
        f"Which parameters must change when you move from QA to PROD?",
        f"How do you handle deletes coming from the source?",
        f"What changes if the business asks for SCD Type 2 history as well?",
        f"How would you move this design from PowerCenter to IICS without breaking restarts?",
    ]
    # keep 8
    followups = [
        FollowUp(ordinal=i + 1, question=q, difficulty_step=DIFFICULTIES[min(i // 2, 4)])
        for i, q in enumerate(followup_texts[:8])
    ]
    section_m = "\n".join(f"{fu.ordinal}. {fu.question}" for fu in followups)

    explanation = ExplanationRecord(
        scenario_id=brief["id"],
        section_a=section_a,
        section_b=section_b,
        section_c=section_c,
        section_d=section_d,
        section_e=section_e,
        section_f=section_f,
        section_g=section_g,
        section_h=section_h,
        section_i=section_i,
        section_j=section_j,
        section_k=section_k,
        section_l=section_l,
        section_m=section_m,
        sample_input_json=sample_json,
        expected_output_json=expected_json,
        mapping_flow_ascii=ascii_flow,
        mapping_flow_mermaid=mermaid,
        sql_logic=sql_logic,
        interview_answer=section_l,
    )
    explanation.compute_flags()

    scenario = ScenarioRecord(
        id=brief["id"],
        technology=technology,
        category=brief["category"],
        difficulty=brief["difficulty"],
        years_min=brief["years_min"],
        years_max=brief["years_max"],
        title=brief["title"],
        stem=brief["stem"],
        iics_service_scope=brief.get("iics_service_scope"),
        label=label,
        status=status,
        tags=brief.get("tags", []),
        created_at=utc_now(),
        updated_at=utc_now(),
        content_hash=content_hash(brief["title"], brief["stem"]),
    )
    return ScenarioBundle(scenario=scenario, explanation=explanation, followups=followups)
