"""Quire projection models for relation row views."""

from __future__ import annotations

from typing import Any

from quire.projection_mapping import ProjectionCodec, ProjectionModel, ScalarPath

from propstore.conflict_detector.models import coerce_conflict_class
from propstore.core.concept_relationship_types import coerce_concept_relationship_type
from propstore.core.id_types import (
    to_claim_id,
    to_concept_id,
    to_justification_id,
)
from propstore.families.relations.declaration import (
    ConflictRow,
    RelationshipRow,
    StanceRow,
)
from propstore.stances import coerce_stance_type


def _nullable_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _claim_id(value: Any) -> object:
    return None if value is None else to_claim_id(value)


def _concept_id(value: Any) -> object:
    return None if value is None else to_concept_id(value)


def _justification_id(value: Any) -> object:
    return None if value is None else to_justification_id(value)


def _concept_relationship_value(value: Any) -> str | None:
    relation_type = coerce_concept_relationship_type(value)
    return None if relation_type is None else relation_type.value


def _stance_type_value(value: Any) -> str | None:
    stance_type = coerce_stance_type(value)
    return None if stance_type is None else stance_type.value


def _conflict_class_value(value: Any) -> str | None:
    conflict_class = coerce_conflict_class(value)
    return None if conflict_class is None else conflict_class.value


TEXT_CODEC = ProjectionCodec("text", "TEXT", encoder=_nullable_text, decoder=_nullable_text)
CLAIM_ID_CODEC = ProjectionCodec("claim_id", "TEXT", encoder=_nullable_text, decoder=_claim_id)
CONCEPT_ID_CODEC = ProjectionCodec("concept_id", "TEXT", encoder=_nullable_text, decoder=_concept_id)
JUSTIFICATION_ID_CODEC = ProjectionCodec(
    "justification_id",
    "TEXT",
    encoder=_nullable_text,
    decoder=_justification_id,
)
CONCEPT_RELATIONSHIP_TYPE_CODEC = ProjectionCodec(
    "concept_relationship_type",
    "TEXT",
    encoder=_concept_relationship_value,
    decoder=coerce_concept_relationship_type,
)
STANCE_TYPE_CODEC = ProjectionCodec(
    "stance_type",
    "TEXT",
    encoder=_stance_type_value,
    decoder=coerce_stance_type,
)
CONFLICT_CLASS_CODEC = ProjectionCodec(
    "conflict_class",
    "TEXT",
    encoder=_conflict_class_value,
    decoder=coerce_conflict_class,
)


RELATIONSHIP_ROW_MODEL: ProjectionModel[RelationshipRow] = ProjectionModel(
    name="relationship_row",
    table="relation_edge",
    result_type=RelationshipRow,
    fields=(
        ScalarPath(("source_id",), "source_id", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("target_id",), "target_id", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(
            ("relation_type",),
            "relation_type",
            codec=CONCEPT_RELATIONSHIP_TYPE_CODEC,
            nullable=False,
            missing="raise",
        ),
        ScalarPath(("conditions_cel",), "conditions_cel", codec=TEXT_CODEC),
        ScalarPath(("note",), "note", codec=TEXT_CODEC),
    ),
    attribute_bucket=("attributes",),
)


STANCE_ROW_MODEL: ProjectionModel[StanceRow] = ProjectionModel(
    name="stance_row",
    table="relation_edge",
    result_type=StanceRow,
    fields=(
        ScalarPath(("claim_id",), "claim_id", codec=CLAIM_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(
            ("target_claim_id",),
            "target_claim_id",
            codec=CLAIM_ID_CODEC,
            nullable=False,
            missing="raise",
        ),
        ScalarPath(
            ("stance_type",),
            "stance_type",
            codec=STANCE_TYPE_CODEC,
            nullable=False,
            missing="raise",
        ),
        ScalarPath(("target_justification_id",), "target_justification_id", codec=JUSTIFICATION_ID_CODEC),
    ),
    attribute_bucket=("attributes",),
)


CONFLICT_ROW_MODEL: ProjectionModel[ConflictRow] = ProjectionModel(
    name="conflict_row",
    table="conflict_witness",
    result_type=ConflictRow,
    fields=(
        ScalarPath(("claim_a_id",), "claim_a_id", codec=CLAIM_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(("claim_b_id",), "claim_b_id", codec=CLAIM_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(("concept_id",), "concept_id", codec=CONCEPT_ID_CODEC),
        ScalarPath(("warning_class",), "warning_class", codec=CONFLICT_CLASS_CODEC),
        ScalarPath(("conflict_class",), "conflict_class", codec=CONFLICT_CLASS_CODEC),
    ),
    attribute_bucket=("attributes",),
)
