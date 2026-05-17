"""Quire projection models for relation row views."""

from __future__ import annotations

import json
from typing import Any

from quire.projection_mapping import (
    ProjectionCodec,
    ProjectionDiscriminator,
    ProjectionJoin,
    ProjectionMetadata,
    ProjectionModel,
    ProjectionQueryPlan,
    ProjectionSelectedColumn,
    ScalarPath,
)
from quire.projections import (
    AUTOINCREMENT_ID_FIELD,
    CONDITIONS_CEL_FIELD,
    ProjectionIndex,
    ProjectionRow,
    ProjectionTable,
    family_reference_field,
    integer_field,
    real_field,
    text_field,
)

from propstore.conflict_detector.models import coerce_conflict_class
from propstore.core.concept_relationship_types import coerce_concept_relationship_type
from propstore.core.id_types import (
    ClaimId,
    JustificationId,
    to_claim_id,
    to_concept_id,
    to_justification_id,
)
from propstore.families.relations.declaration import (
    ConflictRow,
    RelationshipRow,
    StanceRow,
)
from propstore.stances import StanceType, coerce_stance_type


def _nullable_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _claim_id(value: Any) -> object:
    return None if value is None else to_claim_id(value)


def _concept_id(value: Any) -> object:
    return None if value is None else to_concept_id(value)


def _justification_id(value: Any) -> object:
    return None if value is None else to_justification_id(value)


def _required_claim_id(value: object) -> ClaimId:
    return to_claim_id(value)


def _optional_claim_id(value: object) -> ClaimId | None:
    return None if value is None else to_claim_id(value)


def _optional_justification_id(value: object) -> JustificationId | None:
    return None if value is None else to_justification_id(value)


def _required_stance_type(value: object) -> StanceType:
    stance_type = coerce_stance_type(value)
    if stance_type is None:
        raise ValueError("claim stance row requires a stance type")
    return stance_type


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("boolean is not a stance float")
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"expected stance float value, got {type(value).__name__}")


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("boolean is not a stance integer")
    if isinstance(value, int | str):
        return int(value)
    raise TypeError(f"expected stance integer value, got {type(value).__name__}")


def _normalize_conditions_differ(value: object) -> object:
    if isinstance(value, list):
        return json.dumps(value)
    return value


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
RAW_CODEC = ProjectionCodec("raw", "TEXT")
INTEGER_CODEC = ProjectionCodec(
    "integer",
    "INTEGER",
    encoder=lambda value: None if value is None else int(value),
    decoder=lambda value: None if value is None else int(value),
)
REAL_CODEC = ProjectionCodec(
    "real",
    "REAL",
    encoder=lambda value: None if value is None else float(value),
    decoder=lambda value: None if value is None else float(value),
)
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


RELATION_EDGE_TABLE = ProjectionTable(
    name="relation_edge",
    columns=(
        AUTOINCREMENT_ID_FIELD.column(),
        text_field("source_kind", nullable=False).column(),
        text_field("source_id", nullable=False).column(),
        text_field("relation_type", nullable=False).column(),
        text_field("target_kind", nullable=False).column(),
        text_field("target_id", nullable=False).column(),
        family_reference_field("claim", role="perspective_source").column(),
        family_reference_field("justification", role="target").column(),
        CONDITIONS_CEL_FIELD.column(),
        text_field("strength").column(),
        text_field("conditions_differ").column(),
        text_field("note").column(),
        text_field("resolution_method").column(),
        text_field("resolution_model").column(),
        text_field("embedding_model").column(),
        real_field("embedding_distance").column(),
        integer_field("pass_number").column(),
        real_field("confidence").column(),
        real_field("opinion_belief").column(
            check_sql="opinion_belief >= 0 AND opinion_belief <= 1"
        ),
        real_field("opinion_disbelief").column(
            check_sql="opinion_disbelief >= 0 AND opinion_disbelief <= 1"
        ),
        real_field("opinion_uncertainty").column(
            check_sql="opinion_uncertainty >= 0 AND opinion_uncertainty <= 1"
        ),
        real_field("opinion_base_rate").column(
            check_sql="opinion_base_rate > 0 AND opinion_base_rate < 1"
        ),
    ),
    checks=(
        "opinion_belief IS NULL OR ABS(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) <= 1e-6",
    ),
    indexes=(
        ProjectionIndex("idx_relation_edge_source", ("source_kind", "source_id")),
        ProjectionIndex("idx_relation_edge_target", ("target_kind", "target_id")),
        ProjectionIndex("idx_relation_edge_type", ("relation_type",)),
    ),
)

CLAIM_SOURCE_DISCRIMINATOR = ProjectionDiscriminator(
    RELATION_EDGE_TABLE.column("source_kind"),
    "claim",
)
CLAIM_TARGET_DISCRIMINATOR = ProjectionDiscriminator(
    RELATION_EDGE_TABLE.column("target_kind"),
    "claim",
)
CONCEPT_SOURCE_DISCRIMINATOR = ProjectionDiscriminator(
    RELATION_EDGE_TABLE.column("source_kind"),
    "concept",
)
CONCEPT_TARGET_DISCRIMINATOR = ProjectionDiscriminator(
    RELATION_EDGE_TABLE.column("target_kind"),
    "concept",
)
CLAIM_STANCE_DISCRIMINATORS = (
    CLAIM_SOURCE_DISCRIMINATOR,
    CLAIM_TARGET_DISCRIMINATOR,
)
CONCEPT_RELATIONSHIP_DISCRIMINATORS = (
    CONCEPT_SOURCE_DISCRIMINATOR,
    CONCEPT_TARGET_DISCRIMINATOR,
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
        ProjectionMetadata(
            path=(),
            fields=(
                ScalarPath(("perspective_source_claim_id",), "perspective_source_claim_id", codec=CLAIM_ID_CODEC),
                ScalarPath(("strength",), "strength", codec=TEXT_CODEC),
                ScalarPath(("conditions_differ",), "conditions_differ", codec=TEXT_CODEC),
                ScalarPath(("note",), "note", codec=TEXT_CODEC),
                ScalarPath(("resolution_method",), "resolution_method", codec=TEXT_CODEC),
                ScalarPath(("resolution_model",), "resolution_model", codec=TEXT_CODEC),
                ScalarPath(("embedding_model",), "embedding_model", codec=TEXT_CODEC),
                ScalarPath(("embedding_distance",), "embedding_distance", codec=REAL_CODEC),
                ScalarPath(("pass_number",), "pass_number", codec=INTEGER_CODEC),
                ScalarPath(("confidence",), "confidence", codec=REAL_CODEC),
                ScalarPath(("opinion_belief",), "opinion_belief", codec=REAL_CODEC),
                ScalarPath(("opinion_disbelief",), "opinion_disbelief", codec=REAL_CODEC),
                ScalarPath(("opinion_uncertainty",), "opinion_uncertainty", codec=REAL_CODEC),
                ScalarPath(("opinion_base_rate",), "opinion_base_rate", codec=REAL_CODEC),
            ),
            result_type=dict,
        ),
    ),
)


CLAIM_STANCE_STORAGE_MODEL: ProjectionModel[StanceRow] = ProjectionModel(
    name="claim_stance_relation_edge",
    table="relation_edge",
    result_type=StanceRow,
    fields=(
        ScalarPath(("claim_id",), "source_id", codec=CLAIM_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(
            ("target_claim_id",),
            "target_id",
            codec=CLAIM_ID_CODEC,
            nullable=False,
            missing="raise",
        ),
        ScalarPath(
            ("stance_type",),
            "relation_type",
            codec=STANCE_TYPE_CODEC,
            nullable=False,
            missing="raise",
        ),
        ScalarPath(("target_justification_id",), "target_justification_id", codec=JUSTIFICATION_ID_CODEC),
        ScalarPath(("perspective_source_claim_id",), "perspective_source_claim_id", codec=CLAIM_ID_CODEC),
        ScalarPath(("strength",), "strength", codec=TEXT_CODEC),
        ScalarPath(("conditions_differ",), "conditions_differ", codec=TEXT_CODEC),
        ScalarPath(("note",), "note", codec=TEXT_CODEC),
        ScalarPath(("resolution_method",), "resolution_method", codec=TEXT_CODEC),
        ScalarPath(("resolution_model",), "resolution_model", codec=TEXT_CODEC),
        ScalarPath(("embedding_model",), "embedding_model", codec=TEXT_CODEC),
        ScalarPath(("embedding_distance",), "embedding_distance", codec=REAL_CODEC),
        ScalarPath(("pass_number",), "pass_number", codec=INTEGER_CODEC),
        ScalarPath(("confidence",), "confidence", codec=REAL_CODEC),
        ScalarPath(("opinion_belief",), "opinion_belief", codec=REAL_CODEC),
        ScalarPath(("opinion_disbelief",), "opinion_disbelief", codec=REAL_CODEC),
        ScalarPath(("opinion_uncertainty",), "opinion_uncertainty", codec=REAL_CODEC),
        ScalarPath(("opinion_base_rate",), "opinion_base_rate", codec=REAL_CODEC),
    ),
)


CONCEPT_RELATIONSHIP_STORAGE_MODEL: ProjectionModel[RelationshipRow] = ProjectionModel(
    name="concept_relationship_relation_edge",
    table="relation_edge",
    result_type=RelationshipRow,
    fields=(
        ScalarPath(("source_id",), "source_id", codec=CONCEPT_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(("target_id",), "target_id", codec=CONCEPT_ID_CODEC, nullable=False, missing="raise"),
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
)


def claim_stance_relation_edge_row(values: tuple[object, ...]) -> ProjectionRow:
    stance = StanceRow(
        claim_id=_required_claim_id(values[0]),
        target_claim_id=_required_claim_id(values[1]),
        stance_type=_required_stance_type(values[2]),
        target_justification_id=_optional_justification_id(values[3]),
        strength=_nullable_text(values[4]),
        conditions_differ=(
            None
            if values[5] is None
            else str(_normalize_conditions_differ(values[5]))
        ),
        note=_nullable_text(values[6]),
        resolution_method=_nullable_text(values[7]),
        resolution_model=_nullable_text(values[8]),
        embedding_model=_nullable_text(values[9]),
        embedding_distance=_optional_float(values[10]),
        pass_number=_optional_int(values[11]),
        confidence=_optional_float(values[12]),
        opinion_belief=_optional_float(values[13]),
        opinion_disbelief=_optional_float(values[14]),
        opinion_uncertainty=_optional_float(values[15]),
        opinion_base_rate=_optional_float(values[16]),
        perspective_source_claim_id=_optional_claim_id(values[17]),
    )
    row_values: dict[str, object] = {}
    for discriminator in CLAIM_STANCE_DISCRIMINATORS:
        row_values.update(discriminator.row_values())
    row_values.update(CLAIM_STANCE_STORAGE_MODEL.to_row(stance))
    return RELATION_EDGE_TABLE.row(**row_values)


def concept_relationship_relation_edge_row(relationship: RelationshipRow) -> ProjectionRow:
    row_values: dict[str, object] = {}
    for discriminator in CONCEPT_RELATIONSHIP_DISCRIMINATORS:
        row_values.update(discriminator.row_values())
    row_values.update(CONCEPT_RELATIONSHIP_STORAGE_MODEL.to_row(relationship))
    return RELATION_EDGE_TABLE.row(**row_values)


def _edge_column(name: str, *, read_name: str | None = None) -> ProjectionSelectedColumn:
    return ProjectionSelectedColumn(
        "edge",
        RELATION_EDGE_TABLE.column(name),
        read_name=read_name,
    )


CLAIM_STANCE_SELECTIONS = (
    _edge_column("source_id", read_name="claim_id"),
    _edge_column("target_id", read_name="target_claim_id"),
    _edge_column("relation_type", read_name="stance_type"),
    _edge_column("target_justification_id"),
    _edge_column("strength"),
    _edge_column("conditions_differ"),
    _edge_column("note"),
    _edge_column("resolution_method"),
    _edge_column("resolution_model"),
    _edge_column("embedding_model"),
    _edge_column("embedding_distance"),
    _edge_column("pass_number"),
    _edge_column("confidence"),
    _edge_column("opinion_belief"),
    _edge_column("opinion_disbelief"),
    _edge_column("opinion_uncertainty"),
    _edge_column("opinion_base_rate"),
)
CLAIM_STANCE_SELECTIONS_WITH_PERSPECTIVE = (
    CLAIM_STANCE_SELECTIONS[0],
    CLAIM_STANCE_SELECTIONS[1],
    CLAIM_STANCE_SELECTIONS[2],
    _edge_column("perspective_source_claim_id"),
    *CLAIM_STANCE_SELECTIONS[3:],
)

CLAIM_STANCE_QUERY_PLAN = ProjectionQueryPlan(
    name="claim_stance",
    base_table=RELATION_EDGE_TABLE,
    base_alias="edge",
    selections=CLAIM_STANCE_SELECTIONS,
    discriminators=CLAIM_STANCE_DISCRIMINATORS,
)


CLAIM_STANCE_WITH_PERSPECTIVE_QUERY_PLAN = ProjectionQueryPlan(
    name="claim_stance_with_perspective",
    base_table=RELATION_EDGE_TABLE,
    base_alias="edge",
    selections=CLAIM_STANCE_SELECTIONS_WITH_PERSPECTIVE,
    discriminators=CLAIM_STANCE_DISCRIMINATORS,
)


CONCEPT_RELATIONSHIP_QUERY_PLAN = ProjectionQueryPlan(
    name="concept_relationship",
    base_table=RELATION_EDGE_TABLE,
    base_alias="edge",
    selections=(
        _edge_column("source_id"),
        _edge_column("relation_type"),
        _edge_column("target_id"),
        _edge_column("conditions_cel"),
        _edge_column("note"),
    ),
    discriminators=CONCEPT_RELATIONSHIP_DISCRIMINATORS,
)


def claim_stance_policy_query_plan(claim_core_table: ProjectionTable) -> ProjectionQueryPlan:
    return ProjectionQueryPlan(
        name="claim_stance_with_claim_policy",
        base_table=RELATION_EDGE_TABLE,
        base_alias="edge",
        selections=CLAIM_STANCE_SELECTIONS_WITH_PERSPECTIVE,
        joins=(
            ProjectionJoin(
                table=claim_core_table,
                alias="source_core",
                left_alias="edge",
                left_column=RELATION_EDGE_TABLE.column("source_id"),
                right_column=claim_core_table.column("id"),
                kind="INNER",
            ),
            ProjectionJoin(
                table=claim_core_table,
                alias="target_core",
                left_alias="edge",
                left_column=RELATION_EDGE_TABLE.column("target_id"),
                right_column=claim_core_table.column("id"),
                kind="INNER",
            ),
        ),
        discriminators=CLAIM_STANCE_DISCRIMINATORS,
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
        ProjectionMetadata(
            path=(),
            fields=(
                ScalarPath(("conditions_a",), "conditions_a", codec=TEXT_CODEC),
                ScalarPath(("conditions_b",), "conditions_b", codec=TEXT_CODEC),
                ScalarPath(("value_a",), "value_a", codec=RAW_CODEC),
                ScalarPath(("value_b",), "value_b", codec=RAW_CODEC),
                ScalarPath(("derivation_chain",), "derivation_chain", codec=TEXT_CODEC),
            ),
            result_type=dict,
        ),
    ),
)
