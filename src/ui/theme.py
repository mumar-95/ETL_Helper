"""Shared visual theme — calm trust greens + warm action accents."""

from __future__ import annotations

import streamlit as st

# Color psychology:
# Teal/forest = trust, focus, learning growth
# Warm sand background = calm readability (not sterile white)
# Amber accent = energy for CTAs without aggression
# Charcoal text = strong legibility

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

html, body, [class*="css"] {
  font-family: "DM Sans", "Segoe UI", sans-serif !important;
}

.stApp {
  background:
    radial-gradient(1200px 500px at 10% -10%, #d9ebe3 0%, transparent 55%),
    radial-gradient(900px 420px at 100% 0%, #f3e6d8 0%, transparent 50%),
    linear-gradient(180deg, #f4f7f5 0%, #eef3f0 100%);
}

h1, h2, h3, .etl-hero-title {
  font-family: "Fraunces", Georgia, serif !important;
  letter-spacing: -0.02em;
  color: #14352c !important;
}

.block-container {
  padding-top: 1.25rem !important;
  padding-bottom: 3rem !important;
  max-width: 1100px;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #12382f 0%, #1a4a3d 100%);
}
[data-testid="stSidebar"] * {
  color: #eef6f2 !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stCheckbox label {
  color: #d7ebe3 !important;
}

.etl-hero {
  padding: 1.25rem 1.35rem;
  border-radius: 18px;
  background: linear-gradient(135deg, #0f4c3a 0%, #1b6b52 55%, #2f7d5b 100%);
  color: #f4fbf7;
  box-shadow: 0 12px 32px rgba(15, 76, 58, 0.22);
  margin-bottom: 1rem;
}
.etl-hero h1 {
  color: #ffffff !important;
  margin: 0 0 0.35rem 0 !important;
  font-size: clamp(1.55rem, 4vw, 2.2rem) !important;
}
.etl-hero p {
  margin: 0;
  color: #d9efe6;
  font-size: clamp(0.95rem, 2.4vw, 1.05rem);
  line-height: 1.45;
  max-width: 46rem;
}

.etl-card {
  border: 1px solid #c9ddd4;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  padding: 1rem 1.05rem;
  margin-bottom: 0.85rem;
  box-shadow: 0 4px 14px rgba(20, 53, 44, 0.05);
}
.etl-card:hover {
  border-color: #7fad98;
  box-shadow: 0 8px 22px rgba(20, 53, 44, 0.09);
}

.etl-pill {
  display: inline-block;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.35rem;
  margin-bottom: 0.25rem;
  letter-spacing: 0.01em;
}
.etl-pill-tech { background: #d7eee4; color: #0f4c3a; }
.etl-pill-diff-beginner { background: #e5f3ea; color: #1f6b3f; }
.etl-pill-diff-intermediate { background: #e7eefc; color: #274a8a; }
.etl-pill-diff-advanced { background: #fff0d9; color: #8a4b00; }
.etl-pill-diff-senior { background: #fde8e4; color: #8a2f22; }
.etl-pill-diff-expert { background: #efe4f8; color: #5b2d86; }
.etl-pill-label { background: #f3e7d8; color: #7a4a1e; }

div[data-testid="stMetric"] {
  background: rgba(255,255,255,0.78);
  border: 1px solid #cfe0d8;
  border-radius: 14px;
  padding: 0.65rem 0.8rem;
}
div[data-testid="stMetric"] label { color: #4d635a !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #14352c !important; }

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #c45c26, #d97834) !important;
  border: none !important;
  color: white !important;
  font-weight: 600 !important;
}
.stButton > button {
  border-radius: 12px !important;
  border: 1px solid #b7cfc3 !important;
}

@media (max-width: 768px) {
  .block-container {
    padding-left: 0.85rem !important;
    padding-right: 0.85rem !important;
  }
  .etl-hero { padding: 1rem; border-radius: 14px; }
  div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.45rem !important;
  }
  div[data-testid="stHorizontalBlock"] > div {
    min-width: min(100%, 10.5rem) !important;
    flex: 1 1 10.5rem !important;
  }
  .etl-card { padding: 0.85rem; }
}
</style>
"""


def apply_theme(*, page_title: str | None = None) -> None:
    if page_title:
        st.set_page_config(
            page_title=page_title,
            page_icon=":material/school:",
            layout="wide",
            initial_sidebar_state="auto",
        )
    st.html(CSS)


def tech_badge(technology: str) -> str:
    return f'<span class="etl-pill etl-pill-tech">{technology}</span>'


def difficulty_badge(difficulty: str) -> str:
    key = difficulty.lower().replace(" ", "-")
    return f'<span class="etl-pill etl-pill-diff-{key}">{difficulty}</span>'


def label_badge(label: str) -> str:
    nice = label.replace("_", " ")
    return f'<span class="etl-pill etl-pill-label">{nice}</span>'


def hero(title: str, subtitle: str) -> None:
    st.html(
        f"""
        <div class="etl-hero">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """
    )
