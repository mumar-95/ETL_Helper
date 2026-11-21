"""Browse and filter the scenario bank."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.connection import get_connection, init_db
from src.db.repositories import ScenarioRepository
from src.services.bootstrap import TARGET_TOTAL, ensure_scenario_bank, published_count
from src.taxonomy import CATEGORIES, DIFFICULTIES, LABELS, TECHNOLOGIES
from src.ui.theme import apply_theme, difficulty_badge, hero, label_badge, tech_badge

apply_theme(page_title="Scenario Bank")
init_db()
if published_count() < TARGET_TOTAL:
    with st.spinner("Preparing scenario bank…"):
        ensure_scenario_bank()
conn = get_connection()
repo = ScenarioRepository(conn)

hero(
    "Scenario bank",
    "Find practical interview questions written in simple English. Filter by tool, topic, and level.",
)

defaults = st.session_state.get("default_difficulties", list(DIFFICULTIES))

with st.sidebar:
    st.header("Filters")
    technology = st.selectbox("Tool", ["All", *TECHNOLOGIES])
    category = st.selectbox("Category", ["All", *CATEGORIES])
    difficulty = st.selectbox("Level", ["All", *DIFFICULTIES], index=0)
    use_experience = st.checkbox("Match my experience", value=True)
    label = st.selectbox("Label", ["All", *LABELS])
    query = st.text_input("Search", placeholder="Type a word…")
    limit = st.slider("How many to show", 20, 200, 40)

difficulties = defaults if (use_experience and difficulty == "All") else None

rows = repo.search(
    technology=None if technology == "All" else technology,
    category=None if category == "All" else category,
    difficulty=None if difficulty == "All" else difficulty,
    difficulties=difficulties if difficulty == "All" and use_experience else None,
    label=None if label == "All" else label,
    query=query or None,
    limit=limit,
)

st.caption(f"Showing {len(rows)} scenarios")

for sc in rows:
    with st.container(border=True):
        st.markdown(f"**{sc.title}**")
        st.html(
            tech_badge(sc.technology)
            + difficulty_badge(sc.difficulty)
            + label_badge(sc.label)
        )
        st.caption(f"{sc.id} · {sc.category}")
        if sc.iics_service_scope:
            st.caption(f"IICS scope: {sc.iics_service_scope}")
        preview = sc.stem.replace("\n", " ")
        st.write(preview[:280] + ("…" if len(preview) > 280 else ""))
        if st.button("Open scenario", key=f"open_{sc.id}", type="primary", width="stretch"):
            st.session_state.selected_scenario_id = sc.id
            st.session_state.workbench_mode = "solve"
            st.switch_page("pages/2_Scenario_Workbench.py")
