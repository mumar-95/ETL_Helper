"""Mandatory A–M explanation prompt structure."""

from __future__ import annotations

AM_STRUCTURE = """
You must produce a COMPLETE explanation with ALL sections A through M.
Never give a two- or three-line answer. Teach WHAT, WHY, HOW, and WHAT HAPPENS IF FAILURE.

A. Understand the Business Requirement
- What is the business requirement?
- Why does the business need this solution?
- What problem are we trying to solve?
- What is the expected output?

B. Understand the Scenario
Identify source system, source tables/files, target tables, data volume, business rules,
technical challenges, and expected result.

C. Sample Input Data
Create realistic sample source tables with 5–10 rows and clear column names.

D. Expected Output
Show final target data and how source transforms into target.

E. Step-by-Step Implementation
Technology-specific steps (PowerCenter / IICS / SQL as applicable).

F. Transformation-by-Transformation Explanation
For each transformation: why required, what it does, properties, ports, flow,
common mistakes, performance considerations.

G. SQL Logic
Complete queries, clause explanations, joins/filters, analytics, alternatives,
Oracle vs SQL Server differences when relevant.

H. Mapping Flow Diagram
Provide ASCII and Mermaid flow diagrams.

I. Performance Optimization
Only techniques applicable to the selected technology.

J. Error Handling and Production Considerations
Failures, rejects, restart, duplicates, consistency, monitoring.

K. Alternative Approaches
At least TWO approaches with advantages, limitations, performance implications.

L. Interview-Ready Answer
Concise but technically strong spoken answer.

M. Advanced Follow-Up Questions
Generate 5–10 progressive follow-up questions.
""".strip()


def build_explain_prompt(technology: str, title: str, stem: str, category: str, difficulty: str) -> str:
    return f"""You are a senior Informatica / SQL interview coach and ETL architect.
Produce a fully detailed, practical, project-realistic explanation.

Technology: {technology}
Category: {category}
Difficulty: {difficulty}
Title: {title}
Scenario:
{stem}

{AM_STRUCTURE}

Return JSON with keys:
section_a, section_b, section_c, section_d, section_e, section_f, section_g,
section_h, section_i, section_j, section_k, section_l, section_m,
sample_input_json, expected_output_json, mapping_flow_ascii, mapping_flow_mermaid,
sql_logic, interview_answer, followups (array of strings).
"""


def build_generate_scenario_prompt(
    technology: str,
    category: str,
    difficulty: str,
    topic: str,
    domain: str,
    volume: str,
    iics_scope: str | None = None,
) -> str:
    scope_line = f"IICS service scope must be stated: {iics_scope}." if iics_scope else ""
    return f"""Generate ONE unique, practical interview scenario (not a theory question).

Technology: {technology}
Category: {category}
Difficulty: {difficulty}
Topic focus: {topic}
Business domain: {domain}
Data volume: {volume}
{scope_line}

Return JSON with keys: title, stem, tags (array), iics_service_scope (string or null).
The stem must describe a realistic end-to-end project challenge with constraints.
Do NOT claim this was asked by a specific company.
"""
