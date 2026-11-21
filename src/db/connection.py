"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import get_settings


def get_db_path() -> Path:
    return get_settings().db_path


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | None = None) -> Path:
    path = db_path or get_db_path()
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    conn = get_connection(path)
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()
    return path
