"""Runtime configuration from env / Streamlit secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str
    db_path: Path
    root: Path


def _secret(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st

        secrets = st.secrets
        if name in secrets:
            return str(secrets[name]).strip()
        nested = secrets.get("groq", {})
        if isinstance(nested, dict) and name.replace("GROQ_", "").lower() in {
            k.lower() for k in nested
        }:
            for k, v in nested.items():
                if k.lower() == name.replace("GROQ_", "").lower():
                    return str(v).strip()
    except Exception:
        pass
    return default


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        groq_api_key=_secret("GROQ_API_KEY"),
        groq_model=_secret("GROQ_MODEL", "llama-3.3-70b-versatile"),
        db_path=ROOT / "data" / "etl_helper.db",
        root=ROOT,
    )
