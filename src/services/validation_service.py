"""Structural quality gates for A–M explanations."""

from __future__ import annotations

from src.models.scenario import ScenarioBundle


MIN_SECTION_CHARS = {
    "A": 180,
    "B": 180,
    "C": 120,
    "D": 120,
    "E": 250,
    "F": 200,
    "G": 100,
    "H": 80,
    "I": 150,
    "J": 150,
    "K": 180,
    "L": 120,
    "M": 120,
}

SHALLOW_PHRASES = (
    "use a lookup and update the target",
    "just use a lookup",
    "simply create a mapping",
)


def validate_bundle(bundle: ScenarioBundle) -> list[str]:
    errors: list[str] = []
    sections = bundle.explanation.sections_dict()
    for key, min_len in MIN_SECTION_CHARS.items():
        text = sections.get(key, "") or ""
        if len(text.strip()) < min_len:
            errors.append(f"Section {key} too short ({len(text)} < {min_len})")
    joined = " ".join(sections.values()).lower()
    for phrase in SHALLOW_PHRASES:
        if phrase in joined and bundle.explanation.word_count < 800:
            errors.append(f"Shallow phrase detected: {phrase}")
    if "approach 1" not in bundle.explanation.section_k.lower() and "alternative 1" not in bundle.explanation.section_k.lower():
        if bundle.explanation.section_k.lower().count("approach") < 2:
            errors.append("Section K must include at least two approaches")
    followups = bundle.followups or []
    if len(followups) < 5:
        # also accept section_m question marks
        if bundle.explanation.section_m.count("?") < 5:
            errors.append("Need at least 5 follow-up questions")
    if bundle.scenario.technology == "IICS" and not bundle.scenario.iics_service_scope:
        errors.append("IICS scenarios require iics_service_scope")
    return errors


def is_valid(bundle: ScenarioBundle) -> bool:
    return not validate_bundle(bundle)
