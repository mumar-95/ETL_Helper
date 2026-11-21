"""Scenario detail with Solve / Explain / SQL / Follow-ups + chat."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.connection import get_connection, init_db
from src.db.repositories import ChatRepository, ScenarioRepository
from src.services.chat_service import ask_about_scenario
from src.services.explanation_renderer import render_explanation
from src.ui.theme import apply_theme, difficulty_badge, hero, label_badge, tech_badge

apply_theme(page_title="Scenario Workbench")
init_db()
conn = get_connection()
repo = ScenarioRepository(conn)
chat_repo = ChatRepository(conn)

hero(
    "Scenario workbench",
    "Try the question yourself first. Then open a clear explanation, SQL/mapping steps, or follow-up questions.",
)

published = repo.search(status="published", limit=5000)
id_to_title = {s.id: f"{s.id} — {s.title}" for s in published}
options = list(id_to_title.keys())
if not options:
    st.warning("No scenarios found. Run scripts/generate_bank.py first.", title="Empty bank")
    st.stop()

default_id = st.session_state.get("selected_scenario_id", options[0])
if default_id not in options:
    default_id = options[0]

scenario_id = st.selectbox(
    "Choose a scenario",
    options,
    index=options.index(default_id),
    format_func=lambda i: id_to_title[i],
)
st.session_state.selected_scenario_id = scenario_id

bundle = repo.get_bundle(scenario_id)
if not bundle:
    st.error("This scenario is missing its explanation.", title="Missing content")
    st.stop()

sc = bundle.scenario
st.markdown(f"### {sc.title}")
st.html(
    tech_badge(sc.technology)
    + difficulty_badge(sc.difficulty)
    + label_badge(sc.label)
)
st.caption(sc.category)
if sc.iics_service_scope:
    st.caption(f"IICS scope: {sc.iics_service_scope}")

st.markdown("#### The question")
st.markdown(sc.stem.replace("\n", "  \n"))

st.markdown("#### What do you want to do?")
actions = st.container(horizontal=True, gap="small")
with actions:
    if st.button("Solve", width="stretch"):
        st.session_state.workbench_mode = "solve"
    if st.button("Explain step by step", type="primary", width="stretch"):
        st.session_state.workbench_mode = "explain"
    if st.button("Show SQL / mapping", width="stretch"):
        st.session_state.workbench_mode = "sql"
    if st.button("Follow-up questions", width="stretch"):
        st.session_state.workbench_mode = "followups"

mode = st.session_state.get("workbench_mode", "solve")

if mode == "solve":
    st.info(
        "Write your answer in simple steps. Do not peek at the explanation yet.",
        title="Practice mode",
    )
    st.text_area(
        "Your notes",
        key=f"notes_{scenario_id}",
        height=220,
        placeholder="1) Source…\n2) Transform…\n3) Target…\n4) If job fails…\n5) How I validate…",
    )
elif mode == "explain":
    st.success("Full A–M explanation in clear language.", title="Explanation")
    render_explanation(bundle.explanation, followups=bundle.followups)
elif mode == "sql":
    st.success("Focus on build steps, transformations, SQL, and flow.", title="Technical view")
    render_explanation(
        bundle.explanation,
        sections=["E", "F", "G", "H"],
        followups=bundle.followups,
    )
elif mode == "followups":
    st.success("Harder questions an interviewer may ask next.", title="Follow-ups")
    if bundle.followups:
        for fu in bundle.followups:
            st.markdown(f"**{fu.ordinal}.** ({fu.difficulty_step}) {fu.question}")
    else:
        st.markdown(bundle.explanation.section_m)

st.divider()
st.markdown("#### Ask more about this scenario")
st.caption("Your chat stays linked to this question.")

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())

session_id = st.session_state.chat_session_id
history = chat_repo.list_messages(session_id, scenario_id)
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input(
    "Example: Why use dynamic lookup? Can we do this in SQL? What if the job fails halfway?"
)
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking…"):
                answer = ask_about_scenario(
                    conn,
                    session_id=session_id,
                    scenario_id=scenario_id,
                    user_message=prompt,
                )
            st.markdown(answer)
        except Exception as exc:
            st.error(str(exc), title="Chat unavailable")
            st.caption("Add GROQ_API_KEY in `.env` or `.streamlit/secrets.toml`.")

if st.button("Clear chat"):
    chat_repo.clear(session_id, scenario_id)
    st.rerun()
