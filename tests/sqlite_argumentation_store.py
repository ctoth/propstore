from __future__ import annotations

import sqlite3

from propstore.core.row_types import ConflictRowInput, StanceRowInput


class SQLiteArgumentationStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def resolve_claim(self, name: str) -> str | None:
        return name

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        if not claim_ids:
            return {}
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._conn.execute(
            f"""
            SELECT
                core.id,
                core.type,
                COALESCE(output_link.concept_id, target_link.concept_id, core.target_concept) AS value_concept_id,
                core.target_concept,
                core.source_paper,
                core.provenance_page,
                num.value,
                num.sample_size,
                num.uncertainty,
                num.confidence,
                num.uncertainty_type,
                num.unit,
                txt.conditions_cel,
                txt.statement,
                txt.expression,
                txt.auto_summary
            FROM claim_core AS core
            LEFT JOIN claim_numeric_payload AS num ON num.claim_id = core.id
            LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
            LEFT JOIN claim_concept_link AS output_link
                ON output_link.claim_id = core.id AND output_link.role = 'output'
            LEFT JOIN claim_concept_link AS target_link
                ON target_link.claim_id = core.id AND target_link.role = 'target'
            WHERE core.id IN ({placeholders})
            """,  # noqa: S608
            list(claim_ids),
        ).fetchall()
        return {row["id"]: dict(row) for row in rows}

    def stances_between(self, claim_ids: set[str]) -> list[StanceRowInput]:
        if not claim_ids:
            return []
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._conn.execute(
            f"""
            SELECT
                source_id AS claim_id,
                target_id AS target_claim_id,
                relation_type AS stance_type,
                target_justification_id,
                strength,
                conditions_differ,
                note,
                resolution_method,
                resolution_model,
                embedding_model,
                embedding_distance,
                pass_number,
                confidence,
                opinion_belief,
                opinion_disbelief,
                opinion_uncertainty,
                opinion_base_rate
            FROM relation_edge
            WHERE source_kind = 'claim'
              AND target_kind = 'claim'
              AND source_id IN ({placeholders})
              AND target_id IN ({placeholders})
            """,  # noqa: S608
            list(claim_ids) + list(claim_ids),
        ).fetchall()
        return [dict(row) for row in rows]

    def conflicts(self) -> list[ConflictRowInput]:
        try:
            rows = self._conn.execute(
                """
                SELECT concept_id, claim_a_id, claim_b_id, warning_class,
                       conditions_a, conditions_b, value_a, value_b, derivation_chain
                FROM conflict_witness
                """
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception:
            return []
