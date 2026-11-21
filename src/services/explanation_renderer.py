"""Render A–M explanations for Streamlit."""

from __future__ import annotations

import json

import streamlit as st

from src.models.scenario import ExplanationRecord, FollowUp
from src.taxonomy import SECTION_TITLES


def render_explanation(
    explanation: ExplanationRecord,
    *,
    sections: list[str] | None = None,
    followups: list[FollowUp] | None = None,
) -> None:
    wanted = sections or list(SECTION_TITLES.keys())
    mapping = explanation.sections_dict()
    for key in wanted:
        title = SECTION_TITLES[key]
        st.subheader(f"{key}. {title}")
        st.markdown(mapping[key])
        if key == "C" and explanation.sample_input_json:
            _maybe_table(explanation.sample_input_json, "Sample input")
        if key == "D" and explanation.expected_output_json:
            _maybe_table(explanation.expected_output_json, "Expected output")
        if key == "G" and explanation.sql_logic:
            st.code(explanation.sql_logic, language="sql")
        if key == "H":
            if explanation.mapping_flow_ascii:
                st.code(explanation.mapping_flow_ascii, language="text")
            if explanation.mapping_flow_mermaid:
                try:
                    st.markdown(f"```mermaid\n{explanation.mapping_flow_mermaid}\n```")
                except Exception:
                    st.code(explanation.mapping_flow_mermaid, language="text")
        if key == "L" and explanation.interview_answer:
            st.info(explanation.interview_answer)
        if key == "M" and followups:
            for fu in followups:
                st.markdown(f"{fu.ordinal}. ({fu.difficulty_step}) {fu.question}")
        st.divider()


def _maybe_table(raw: str, caption: str) -> None:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            for name, rows in data.items():
                st.caption(f"{caption}: {name}")
                st.dataframe(rows, use_container_width=True)
        elif isinstance(data, list):
            st.caption(caption)
            st.dataframe(data, use_container_width=True)
    except Exception:
        st.code(raw, language="json")


def summary_for_chat(explanation: ExplanationRecord, max_chars: int = 6000) -> str:
    parts = [
        f"A: {explanation.section_a}",
        f"E: {explanation.section_e}",
        f"G: {explanation.section_g}",
        f"I: {explanation.section_i}",
        f"J: {explanation.section_j}",
        f"K: {explanation.section_k}",
        f"L: {explanation.section_l}",
    ]
    text = "\n\n".join(parts)
    return text[:max_chars]
