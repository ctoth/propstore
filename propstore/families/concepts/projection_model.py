"""Quire projection models for concept row views."""

from __future__ import annotations

import json
from typing import Any

from quire.projection_mapping import ProjectionCodec, ProjectionModel, ProjectionRenderView, ScalarPath

from propstore.core.concept_status import coerce_concept_status
from propstore.core.exactness_types import coerce_exactness
from propstore.core.id_types import to_concept_id
from propstore.families.concepts.declaration import ConceptRow, ParameterizationRow


def _nullable_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _concept_id(value: Any) -> object:
    return None if value is None else to_concept_id(value)


def _concept_status_value(value: Any) -> str | None:
    if value is None:
        return None
    status = coerce_concept_status(value)
    return None if status is None else status.value


def _exactness_value(value: Any) -> str | None:
    exactness = coerce_exactness(value)
    return None if exactness is None else exactness.value


def _logical_ids_payload(value: Any) -> object:
    if value is None or value == "":
        return []
    if not isinstance(value, str):
        return value
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


TEXT_CODEC = ProjectionCodec("text", "TEXT", encoder=_nullable_text, decoder=_nullable_text)
CONCEPT_ID_CODEC = ProjectionCodec("concept_id", "TEXT", encoder=_nullable_text, decoder=_concept_id)
CONCEPT_STATUS_CODEC = ProjectionCodec(
    "concept_status",
    "TEXT",
    encoder=_concept_status_value,
    decoder=coerce_concept_status,
)
EXACTNESS_CODEC = ProjectionCodec(
    "exactness",
    "TEXT",
    encoder=_exactness_value,
    decoder=coerce_exactness,
)
LOGICAL_IDS_PAYLOAD_CODEC = ProjectionCodec(
    "logical_ids_payload",
    "JSON",
    encoder=_logical_ids_payload,
)


CONCEPT_ROW_MODEL: ProjectionModel[ConceptRow] = ProjectionModel(
    name="concept_row",
    table="concept",
    result_type=ConceptRow,
    fields=(
        ScalarPath(("concept_id",), "id", codec=CONCEPT_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(("canonical_name",), "canonical_name", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("status",), "status", codec=CONCEPT_STATUS_CODEC),
        ScalarPath(("definition",), "definition", codec=TEXT_CODEC),
        ScalarPath(("kind_type",), "kind_type", codec=TEXT_CODEC),
        ScalarPath(("form",), "form", codec=TEXT_CODEC),
        ScalarPath(("domain",), "domain", codec=TEXT_CODEC),
        ScalarPath(("form_parameters",), "form_parameters", codec=TEXT_CODEC),
        ScalarPath(("primary_logical_id",), "primary_logical_id", codec=TEXT_CODEC),
        ScalarPath(("logical_ids_json",), "logical_ids_json", codec=TEXT_CODEC),
        ProjectionRenderView(source_path=("primary_logical_id",), output_key="logical_id", codec=TEXT_CODEC),
        ProjectionRenderView(
            source_path=("logical_ids_json",),
            output_key="logical_ids",
            codec=LOGICAL_IDS_PAYLOAD_CODEC,
        ),
    ),
    attribute_bucket=("attributes",),
)


PARAMETERIZATION_ROW_MODEL: ProjectionModel[ParameterizationRow] = ProjectionModel(
    name="parameterization_row",
    table="parameterization",
    result_type=ParameterizationRow,
    fields=(
        ScalarPath(
            ("output_concept_id",),
            "output_concept_id",
            codec=CONCEPT_ID_CODEC,
            nullable=False,
            missing="raise",
        ),
        ScalarPath(("concept_ids",), "concept_ids", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("formula",), "formula", codec=TEXT_CODEC),
        ScalarPath(("sympy",), "sympy", codec=TEXT_CODEC),
        ScalarPath(("exactness",), "exactness", codec=EXACTNESS_CODEC),
        ScalarPath(("conditions_cel",), "conditions_cel", codec=TEXT_CODEC),
        ScalarPath(("conditions_ir",), "conditions_ir", codec=TEXT_CODEC),
    ),
    attribute_bucket=("attributes",),
)
