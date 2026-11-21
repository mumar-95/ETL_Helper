"""Follow-up question generation prompt."""

from __future__ import annotations


def build_followup_prompt(title: str, stem: str, technology: str) -> str:
    return f"""Based on this {technology} interview scenario, generate 8 progressive
follow-up questions from clarifying basics to expert failure/architecture probes.

Title: {title}
Scenario: {stem}

Return JSON: {{"followups": ["q1", "q2", ...]}}
"""
