"""Temporary justification projection residual owned by the justification slice."""

from __future__ import annotations

from typing import Any

from quire.projection_mapping import ProjectionCodec, ProjectionModel, ReferencePath, ScalarPath

from propstore.core.id_types import to_claim_id


def _nullable_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _claim_id(value: Any) -> object:
    return None if value is None else to_claim_id(value)


TEXT_CODEC = ProjectionCodec("text", "TEXT", encoder=_nullable_text, decoder=_nullable_text)
CLAIM_ID_CODEC = ProjectionCodec("claim_id", "TEXT", encoder=_nullable_text, decoder=_claim_id)


JUSTIFICATION_STORAGE_MODEL: ProjectionModel[dict[str, object]] = ProjectionModel(
    name="justification_storage",
    table="justification",
    result_type=dict,
    fields=(
        ScalarPath(("id",), "id", codec=TEXT_CODEC, nullable=False, primary_key=True, missing="raise"),
        ScalarPath(("justification_kind",), "justification_kind", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ReferencePath(("conclusion_claim_id",), "conclusion_claim_id", family="claim_core", codec=CLAIM_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(("premise_claim_ids",), "premise_claim_ids", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("source_relation_type",), "source_relation_type", codec=TEXT_CODEC),
        ReferencePath(("source_claim_id",), "source_claim_id", family="claim_core", codec=CLAIM_ID_CODEC),
        ScalarPath(("provenance_json",), "provenance_json", codec=TEXT_CODEC),
        ScalarPath(("rule_strength",), "rule_strength", codec=TEXT_CODEC, nullable=False, default_sql="'defeasible'"),
    ),
)


JUSTIFICATION_TABLE = JUSTIFICATION_STORAGE_MODEL.projection_tables()[0]
