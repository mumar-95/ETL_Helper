"""ETL Helper — scenario-first Informatica interview preparation."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.connection import get_connection, init_db
from src.db.repositories import ScenarioRepository
from src.services.bootstrap import TARGET_TOTAL, ensure_scenario_bank, published_count
from src.services.difficulty_service import difficulties_for_experience, experience_options
from src.ui.theme import apply_theme, hero

apply_theme(page_title="ETL Helper")

init_db()

# Auto-build the bank if this install has no/partial DB (common on first run / deploy).
if published_count() < TARGET_TOTAL:
    with st.spinner("Preparing your 1,000 interview scenarios for the first time…"):
        boot = ensure_scenario_bank()
    if boot.get("bootstrapped"):
        st.toast(f"Loaded {boot['published']} scenarios", icon=":material/check_circle:")

conn = get_connection()
repo = ScenarioRepository(conn)

hero(
    "ETL Helper",
    "Practice real Informatica interview scenarios in simple English — PowerCenter, IICS/CDI, and SQL.",
)

st.markdown(
    """
Choose your experience, open a scenario, try to solve it, then review a clear step-by-step explanation.
Ask follow-up questions just like a real technical interview.
"""
)

if "experience_band" not in st.session_state:
    st.session_state.experience_band = experience_options()[1]

band = st.selectbox(
    "Your experience",
    experience_options(),
    index=experience_options().index(st.session_state.experience_band)
    if st.session_state.experience_band in experience_options()
    else 1,
    help="We use this to suggest matching difficulty levels.",
)
st.session_state.experience_band = band
st.session_state.default_difficulties = list(difficulties_for_experience(band))

counts = repo.counts_by_technology("published")
total = repo.count("published")

m1, m2, m3, m4 = st.columns(4)
m1.metric("All scenarios", total)
m2.metric("PowerCenter", counts.get("PowerCenter", 0))
m3.metric("IICS / CDI", counts.get("IICS", 0))
m4.metric("SQL", counts.get("SQL", 0))

st.info(
    f"Suggested levels for **{band}**: "
    + ", ".join(st.session_state.default_difficulties),
    title="Difficulty suggestion",
)

st.subheader("How to use this app")
steps = st.container(horizontal=True, gap="medium")
with steps:
    with st.container(border=True):
        st.markdown("#### 1. Browse")
        st.caption("Open Scenario Bank and pick a question that matches your level.")
    with st.container(border=True):
        st.markdown("#### 2. Practice")
        st.caption("In Workbench: try Solve first, then Explain step by step.")
    with st.container(border=True):
        st.markdown("#### 3. Grow")
        st.caption("Use Expansion to add more practice scenarios when you want fresh ones.")

if total < TARGET_TOTAL:
    st.warning(
        "Still loading scenarios. Pull to refresh, or wait a few seconds and reopen Home.",
        title="Almost ready",
    )
    if st.button("Build scenario bank now", type="primary"):
        with st.spinner("Building 1,000 scenarios…"):
            ensure_scenario_bank()
        st.rerun()
else:
    st.success("You have 1,000+ practical scenarios ready to practice.", title="Ready")
