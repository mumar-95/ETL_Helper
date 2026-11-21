"""Pydantic models for scenarios and explanations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.taxonomy import CATEGORIES, DIFFICULTIES, LABELS, STATUSES, TECHNOLOGIES


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class FollowUp(BaseModel):
    ordinal: int
    question: str
    difficulty_step: str = "intermediate"


class ScenarioRecord(BaseModel):
    id: str
    technology: str
    category: str
    difficulty: str
    years_min: int = 0
    years_max: int = 20
    title: str
    stem: str
    iics_service_scope: str | None = None
    label: str = "ai_generated"
    status: str = "draft"
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    content_hash: str = ""

    @field_validator("technology")
    @classmethod
    def _tech(cls, v: str) -> str:
        if v not in TECHNOLOGIES:
            raise ValueError(f"Invalid technology: {v}")
        return v

    @field_validator("category")
    @classmethod
    def _cat(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"Invalid category: {v}")
        return v

    @field_validator("difficulty")
    @classmethod
    def _diff(cls, v: str) -> str:
        if v not in DIFFICULTIES:
            raise ValueError(f"Invalid difficulty: {v}")
        return v

    @field_validator("label")
    @classmethod
    def _label(cls, v: str) -> str:
        if v not in LABELS:
            raise ValueError(f"Invalid label: {v}")
        return v

    @field_validator("status")
    @classmethod
    def _status(cls, v: str) -> str:
        if v not in STATUSES:
            raise ValueError(f"Invalid status: {v}")
        return v


class ExplanationRecord(BaseModel):
    scenario_id: str
    section_a: str
    section_b: str
    section_c: str
    section_d: str
    section_e: str
    section_f: str
    section_g: str
    section_h: str
    section_i: str
    section_j: str
    section_k: str
    section_l: str
    section_m: str
    sample_input_json: str | None = None
    expected_output_json: str | None = None
    mapping_flow_ascii: str | None = None
    mapping_flow_mermaid: str | None = None
    sql_logic: str | None = None
    interview_answer: str | None = None
    has_sample_data: bool = False
    has_alternatives: bool = False
    has_followups: bool = False
    word_count: int = 0

    def sections_dict(self) -> dict[str, str]:
        return {
            "A": self.section_a,
            "B": self.section_b,
            "C": self.section_c,
            "D": self.section_d,
            "E": self.section_e,
            "F": self.section_f,
            "G": self.section_g,
            "H": self.section_h,
            "I": self.section_i,
            "J": self.section_j,
            "K": self.section_k,
            "L": self.section_l,
            "M": self.section_m,
        }

    def compute_flags(self) -> None:
        text = " ".join(self.sections_dict().values())
        self.word_count = len(text.split())
        self.has_sample_data = bool(self.sample_input_json) or (
            "sample" in self.section_c.lower() and len(self.section_c) > 200
        )
        self.has_alternatives = "approach 1" in self.section_k.lower() or "alternative" in self.section_k.lower()
        self.has_followups = len(self.section_m.split("?")) >= 5
        if not self.interview_answer:
            self.interview_answer = self.section_l


class ScenarioBundle(BaseModel):
    scenario: ScenarioRecord
    explanation: ExplanationRecord
    followups: list[FollowUp] = Field(default_factory=list)

    def to_row_dicts(self) -> dict[str, Any]:
        s = self.scenario.model_dump()
        s["tags"] = json.dumps(s["tags"])
        e = self.explanation.model_dump()
        e["has_sample_data"] = int(e["has_sample_data"])
        e["has_alternatives"] = int(e["has_alternatives"])
        e["has_followups"] = int(e["has_followups"])
        return {"scenario": s, "explanation": e, "followups": [f.model_dump() for f in self.followups]}
