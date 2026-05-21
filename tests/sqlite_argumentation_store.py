from __future__ import annotations

from collections.abc import Sequence
from sqlite3 import Connection

from propstore.families.relations.declaration import ConflictWitness, Stance
from tests.claim_model_helpers import claim_model_from_test_payload


class SQLiteArgumentationStore:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def _fetch_dicts(
        self,
        query: str,
        params: Sequence[object] = (),
    ) -> list[dict[str, object]]:
        cursor = self._conn.execute(query, params)
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def get_claim(self, claim_id: str):
        return self.claims_by_ids({claim_id}).get(claim_id)

    def claims_by_ids(self, claim_ids: set[str]):
        if not claim_ids:
            return {}
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._fetch_dicts(
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
        )
        return {
            str(row["id"]): claim_model_from_test_payload(row)
            for row in rows
        }

    def stances_between(self, claim_ids: set[str]) -> list[Stance]:
        if not claim_ids:
            return []
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._fetch_dicts(
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
        )
        return [
            Stance(
                source_kind="claim",
                source_id=row["claim_id"],
                relation_type=row["stance_type"],
                target_kind="claim",
                target_id=row["target_claim_id"],
                target_justification_id=row["target_justification_id"],
                strength=row["strength"],
                conditions_differ=row["conditions_differ"],
                note=row["note"],
                resolution_method=row["resolution_method"],
                resolution_model=row["resolution_model"],
                embedding_model=row["embedding_model"],
                embedding_distance=row["embedding_distance"],
                pass_number=row["pass_number"],
                confidence=row["confidence"],
                opinion_belief=row["opinion_belief"],
                opinion_disbelief=row["opinion_disbelief"],
                opinion_uncertainty=row["opinion_uncertainty"],
                opinion_base_rate=row["opinion_base_rate"],
            )
            for row in rows
        ]

    def conflicts(self) -> list[ConflictWitness]:
        try:
            rows = self._fetch_dicts(
                """
                SELECT concept_id, claim_a_id, claim_b_id, warning_class,
                       conditions_a, conditions_b, value_a, value_b, derivation_chain
                FROM conflict_witness
                """
            )
            return [
                ConflictWitness(
                    concept_id=row["concept_id"],
                    claim_a_id=row["claim_a_id"],
                    claim_b_id=row["claim_b_id"],
                    warning_class=row["warning_class"],
                    conditions_a=row["conditions_a"],
                    conditions_b=row["conditions_b"],
                    value_a=row["value_a"],
                    value_b=row["value_b"],
                    derivation_chain=row["derivation_chain"],
                )
                for row in rows
            ]
        except Exception:
            return []
