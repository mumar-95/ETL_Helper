"""Admin: generate, dedup, review, and publish new scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.connection import get_connection, init_db
from src.db.repositories import GenerationQueueRepository, ScenarioRepository
from src.services.generator_service import enqueue_expansion, promote_queue_item
from src.taxonomy import CATEGORIES, DIFFICULTIES, LABELS, TECHNOLOGIES
from src.ui.theme import apply_theme, hero

apply_theme(page_title="Scenario Expansion")
init_db()
conn = get_connection()
repo = ScenarioRepository(conn)
queue_repo = GenerationQueueRepository(conn)

hero(
    "Grow the question bank",
    "Create new practice scenarios. AI-generated items are clearly labeled and never claimed as company interview questions.",
)

with st.form("generate_form"):
    row = st.container(horizontal=True, gap="medium")
    with row:
        technology = st.selectbox("Tool", TECHNOLOGIES)
        difficulty = st.selectbox("Level", DIFFICULTIES, index=1)
    category = st.selectbox("Category", CATEGORIES)
    topic = st.text_input(
        "Topic in simple words",
        value="load only new customer changes when some rows arrive late",
    )
    use_groq = st.checkbox("Use Groq AI (otherwise local simple-English author)", value=False)
    submitted = st.form_submit_button("Create scenario", type="primary", width="stretch")

if submitted:
    with st.spinner("Creating and checking for duplicates…"):
        try:
            result = enqueue_expansion(
                conn,
                technology=technology,
                category=category,
                difficulty=difficulty,
                topic=topic,
                use_groq=use_groq,
            )
            if result["duplicate"]:
                st.warning(
                    f"This looks too similar to {result['match_id']} "
                    f"(score {result['dedup_score']:.2f}).",
                    title="Near duplicate",
                )
            else:
                st.success(f"Added to review queue #{result['queue_id']}.", title="Queued")
                if result["validation_errors"]:
                    st.info("; ".join(result["validation_errors"]), title="Quality notes")
                bundle = result["bundle"]
                if bundle:
                    st.markdown(f"**Preview:** {bundle.scenario.title}")
                    st.write(bundle.scenario.stem)
        except Exception as exc:
            st.error(str(exc), title="Generation failed")

st.divider()
st.subheader("Review queue")
pending = queue_repo.list_pending(40)
if not pending:
    st.caption("Nothing waiting for review.")
else:
    for item in pending:
        with st.expander(f"#{item['id']} · {item['title']} · {item['status']}"):
            st.write(item["stem"])
            st.caption(
                f"{item['technology']} / {item['category']} / {item['difficulty']}"
            )
            label = st.selectbox(
                "Label",
                LABELS,
                index=LABELS.index("ai_generated"),
                key=f"label_{item['id']}",
            )
            actions = st.container(horizontal=True, gap="small")
            with actions:
                if st.button("Publish", key=f"pub_{item['id']}", type="primary"):
                    sid = promote_queue_item(conn, item["id"], label=label, status="published")
                    if sid:
                        st.success(f"Published {sid}")
                        st.rerun()
                    else:
                        st.error("Could not publish this item.")
                if st.button("Validate only", key=f"val_{item['id']}"):
                    sid = promote_queue_item(conn, item["id"], label=label, status="validated")
                    st.info(f"Validated {sid}")
                    st.rerun()
                if st.button("Reject", key=f"rej_{item['id']}"):
                    queue_repo.update_status(item["id"], "rejected")
                    st.rerun()
            if item.get("payload_json"):
                try:
                    preview = json.loads(item["payload_json"])
                    st.caption(f"Draft id: {preview.get('scenario', {}).get('id')}")
                except Exception:
                    pass

st.divider()
st.subheader("Update an existing scenario label")
all_ids = [s.id for s in repo.search(status="published", limit=5000)]
if all_ids:
    sid = st.selectbox("Scenario id", all_ids)
    new_label = st.selectbox("New label", LABELS, key="relabel_label")
    new_status = st.selectbox("Status", ["published", "validated", "draft"], key="relabel_status")
    if st.button("Save label / status", type="primary"):
        repo.update_status_label(sid, status=new_status, label=new_label)
        st.success(f"Updated {sid}")
