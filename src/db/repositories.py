"""Data access for scenarios, explanations, chat, and generation queue."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from src.models.scenario import ExplanationRecord, FollowUp, ScenarioBundle, ScenarioRecord, utc_now


class ScenarioRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def upsert_bundle(self, bundle: ScenarioBundle) -> None:
        rows = bundle.to_row_dicts()
        s = rows["scenario"]
        e = rows["explanation"]
        self.conn.execute(
            """
            INSERT INTO scenarios (
                id, technology, category, difficulty, years_min, years_max,
                title, stem, iics_service_scope, label, status, tags,
                created_at, updated_at, content_hash
            ) VALUES (
                :id, :technology, :category, :difficulty, :years_min, :years_max,
                :title, :stem, :iics_service_scope, :label, :status, :tags,
                :created_at, :updated_at, :content_hash
            )
            ON CONFLICT(id) DO UPDATE SET
                technology=excluded.technology,
                category=excluded.category,
                difficulty=excluded.difficulty,
                years_min=excluded.years_min,
                years_max=excluded.years_max,
                title=excluded.title,
                stem=excluded.stem,
                iics_service_scope=excluded.iics_service_scope,
                label=excluded.label,
                status=excluded.status,
                tags=excluded.tags,
                updated_at=excluded.updated_at,
                content_hash=excluded.content_hash
            """,
            s,
        )
        self.conn.execute(
            """
            INSERT INTO explanations (
                scenario_id, section_a, section_b, section_c, section_d, section_e,
                section_f, section_g, section_h, section_i, section_j, section_k,
                section_l, section_m, sample_input_json, expected_output_json,
                mapping_flow_ascii, mapping_flow_mermaid, sql_logic, interview_answer,
                has_sample_data, has_alternatives, has_followups, word_count
            ) VALUES (
                :scenario_id, :section_a, :section_b, :section_c, :section_d, :section_e,
                :section_f, :section_g, :section_h, :section_i, :section_j, :section_k,
                :section_l, :section_m, :sample_input_json, :expected_output_json,
                :mapping_flow_ascii, :mapping_flow_mermaid, :sql_logic, :interview_answer,
                :has_sample_data, :has_alternatives, :has_followups, :word_count
            )
            ON CONFLICT(scenario_id) DO UPDATE SET
                section_a=excluded.section_a, section_b=excluded.section_b,
                section_c=excluded.section_c, section_d=excluded.section_d,
                section_e=excluded.section_e, section_f=excluded.section_f,
                section_g=excluded.section_g, section_h=excluded.section_h,
                section_i=excluded.section_i, section_j=excluded.section_j,
                section_k=excluded.section_k, section_l=excluded.section_l,
                section_m=excluded.section_m,
                sample_input_json=excluded.sample_input_json,
                expected_output_json=excluded.expected_output_json,
                mapping_flow_ascii=excluded.mapping_flow_ascii,
                mapping_flow_mermaid=excluded.mapping_flow_mermaid,
                sql_logic=excluded.sql_logic,
                interview_answer=excluded.interview_answer,
                has_sample_data=excluded.has_sample_data,
                has_alternatives=excluded.has_alternatives,
                has_followups=excluded.has_followups,
                word_count=excluded.word_count
            """,
            e,
        )
        self.conn.execute("DELETE FROM followup_questions WHERE scenario_id = ?", (bundle.scenario.id,))
        for fu in rows["followups"]:
            self.conn.execute(
                """
                INSERT INTO followup_questions (scenario_id, ordinal, question, difficulty_step)
                VALUES (?, ?, ?, ?)
                """,
                (bundle.scenario.id, fu["ordinal"], fu["question"], fu["difficulty_step"]),
            )
        self.conn.commit()

    def exists(self, scenario_id: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        return row is not None

    def count(self, status: str | None = "published") -> int:
        if status:
            row = self.conn.execute(
                "SELECT COUNT(*) AS c FROM scenarios WHERE status = ?", (status,)
            ).fetchone()
        else:
            row = self.conn.execute("SELECT COUNT(*) AS c FROM scenarios").fetchone()
        return int(row["c"])

    def counts_by_technology(self, status: str = "published") -> dict[str, int]:
        rows = self.conn.execute(
            """
            SELECT technology, COUNT(*) AS c
            FROM scenarios
            WHERE status = ?
            GROUP BY technology
            """,
            (status,),
        ).fetchall()
        return {r["technology"]: int(r["c"]) for r in rows}

    def list_titles_stems(self) -> list[tuple[str, str, str]]:
        rows = self.conn.execute("SELECT id, title, stem FROM scenarios").fetchall()
        return [(r["id"], r["title"], r["stem"]) for r in rows]

    def search(
        self,
        *,
        technology: str | None = None,
        category: str | None = None,
        difficulty: str | None = None,
        difficulties: list[str] | None = None,
        label: str | None = None,
        status: str = "published",
        query: str | None = None,
        years_min: int | None = None,
        years_max: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ScenarioRecord]:
        clauses = ["status = ?"]
        params: list[Any] = [status]
        if technology and technology != "All":
            clauses.append("technology = ?")
            params.append(technology)
        if category and category != "All":
            clauses.append("category = ?")
            params.append(category)
        if difficulty and difficulty != "All":
            clauses.append("difficulty = ?")
            params.append(difficulty)
        if difficulties:
            placeholders = ",".join("?" * len(difficulties))
            clauses.append(f"difficulty IN ({placeholders})")
            params.extend(difficulties)
        if label and label != "All":
            clauses.append("label = ?")
            params.append(label)
        if years_min is not None:
            clauses.append("years_max >= ?")
            params.append(years_min)
        if years_max is not None:
            clauses.append("years_min <= ?")
            params.append(years_max)
        if query:
            clauses.append("(title LIKE ? OR stem LIKE ? OR id LIKE ?)")
            q = f"%{query.strip()}%"
            params.extend([q, q, q])
        sql = f"""
            SELECT * FROM scenarios
            WHERE {' AND '.join(clauses)}
            ORDER BY technology, difficulty, id
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        rows = self.conn.execute(sql, params).fetchall()
        return [self._scenario_from_row(r) for r in rows]

    def get_scenario(self, scenario_id: str) -> ScenarioRecord | None:
        row = self.conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        return self._scenario_from_row(row) if row else None

    def get_explanation(self, scenario_id: str) -> ExplanationRecord | None:
        row = self.conn.execute(
            "SELECT * FROM explanations WHERE scenario_id = ?", (scenario_id,)
        ).fetchone()
        return self._explanation_from_row(row) if row else None

    def get_followups(self, scenario_id: str) -> list[FollowUp]:
        rows = self.conn.execute(
            """
            SELECT ordinal, question, difficulty_step
            FROM followup_questions
            WHERE scenario_id = ?
            ORDER BY ordinal
            """,
            (scenario_id,),
        ).fetchall()
        return [
            FollowUp(
                ordinal=r["ordinal"],
                question=r["question"],
                difficulty_step=r["difficulty_step"],
            )
            for r in rows
        ]

    def get_bundle(self, scenario_id: str) -> ScenarioBundle | None:
        scenario = self.get_scenario(scenario_id)
        explanation = self.get_explanation(scenario_id)
        if not scenario or not explanation:
            return None
        return ScenarioBundle(
            scenario=scenario,
            explanation=explanation,
            followups=self.get_followups(scenario_id),
        )

    def update_status_label(self, scenario_id: str, status: str | None = None, label: str | None = None) -> None:
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return
        if status:
            scenario.status = status
        if label:
            scenario.label = label
        scenario.updated_at = utc_now()
        self.conn.execute(
            """
            UPDATE scenarios
            SET status = ?, label = ?, updated_at = ?
            WHERE id = ?
            """,
            (scenario.status, scenario.label, scenario.updated_at, scenario_id),
        )
        self.conn.commit()

    def delete(self, scenario_id: str) -> None:
        self.conn.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
        self.conn.commit()

    @staticmethod
    def _scenario_from_row(row: sqlite3.Row) -> ScenarioRecord:
        tags = row["tags"]
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        return ScenarioRecord(
            id=row["id"],
            technology=row["technology"],
            category=row["category"],
            difficulty=row["difficulty"],
            years_min=row["years_min"],
            years_max=row["years_max"],
            title=row["title"],
            stem=row["stem"],
            iics_service_scope=row["iics_service_scope"],
            label=row["label"],
            status=row["status"],
            tags=tags or [],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            content_hash=row["content_hash"],
        )

    @staticmethod
    def _explanation_from_row(row: sqlite3.Row) -> ExplanationRecord:
        return ExplanationRecord(
            scenario_id=row["scenario_id"],
            section_a=row["section_a"],
            section_b=row["section_b"],
            section_c=row["section_c"],
            section_d=row["section_d"],
            section_e=row["section_e"],
            section_f=row["section_f"],
            section_g=row["section_g"],
            section_h=row["section_h"],
            section_i=row["section_i"],
            section_j=row["section_j"],
            section_k=row["section_k"],
            section_l=row["section_l"],
            section_m=row["section_m"],
            sample_input_json=row["sample_input_json"],
            expected_output_json=row["expected_output_json"],
            mapping_flow_ascii=row["mapping_flow_ascii"],
            mapping_flow_mermaid=row["mapping_flow_mermaid"],
            sql_logic=row["sql_logic"],
            interview_answer=row["interview_answer"],
            has_sample_data=bool(row["has_sample_data"]),
            has_alternatives=bool(row["has_alternatives"]),
            has_followups=bool(row["has_followups"]),
            word_count=row["word_count"],
        )


class ChatRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add_message(self, session_id: str, scenario_id: str, role: str, content: str) -> None:
        self.conn.execute(
            """
            INSERT INTO chat_messages (session_id, scenario_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, scenario_id, role, content, utc_now()),
        )
        self.conn.commit()

    def list_messages(self, session_id: str, scenario_id: str) -> list[dict[str, str]]:
        rows = self.conn.execute(
            """
            SELECT role, content FROM chat_messages
            WHERE session_id = ? AND scenario_id = ?
            ORDER BY id
            """,
            (session_id, scenario_id),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    def clear(self, session_id: str, scenario_id: str) -> None:
        self.conn.execute(
            "DELETE FROM chat_messages WHERE session_id = ? AND scenario_id = ?",
            (session_id, scenario_id),
        )
        self.conn.commit()


class GenerationQueueRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def enqueue(self, item: dict[str, Any]) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO generation_queue (
                scenario_id, technology, category, difficulty, title, stem,
                payload_json, dedup_score, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("scenario_id"),
                item["technology"],
                item["category"],
                item["difficulty"],
                item["title"],
                item["stem"],
                item.get("payload_json"),
                item.get("dedup_score"),
                item.get("status", "draft"),
                utc_now(),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_pending(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM generation_queue
            WHERE status IN ('draft', 'pending_review')
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, queue_id: int, status: str, scenario_id: str | None = None) -> None:
        self.conn.execute(
            """
            UPDATE generation_queue
            SET status = ?, reviewed_at = ?, scenario_id = COALESCE(?, scenario_id)
            WHERE id = ?
            """,
            (status, utc_now(), scenario_id, queue_id),
        )
        self.conn.commit()
