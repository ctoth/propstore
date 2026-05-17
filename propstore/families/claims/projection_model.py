"""Quire projection models for claim row views."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from quire.projection_mapping import (
    ProjectionAttachedRows,
    ProjectionBinding,
    ProjectionCodec,
    ProjectionComponent,
    ProjectionModel,
    ProjectionMetadata,
    ProjectionRenderView,
    ReferencePath,
    ScalarPath,
)
from quire.projections import ProjectionColumn

from propstore.core.algorithm_stage import coerce_algorithm_stage
from propstore.core.claim_types import coerce_claim_type
from propstore.core.claim_values import ClaimProvenance
from propstore.core.id_types import LogicalId, to_claim_id, to_concept_id, to_context_id
from propstore.core.relations import coerce_claim_concept_link_role
from propstore.families.claims.declaration import ClaimConceptLinkRow, ClaimRow


def _nullable_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _claim_id(value: Any) -> object:
    return None if value is None else to_claim_id(value)


def _concept_id(value: Any) -> object:
    return None if value is None else to_concept_id(value)


def _context_id(value: Any) -> object:
    return None if value is None else to_context_id(value)


def _role_value(value: Any) -> str | None:
    role = coerce_claim_concept_link_role(value)
    return None if role is None else role.value


def _claim_type_value(value: Any) -> str | None:
    claim_type = coerce_claim_type(value)
    return None if claim_type is None else claim_type.value


def _algorithm_stage_value(value: Any) -> str | None:
    stage = coerce_algorithm_stage(value)
    return None if stage is None else str(stage)


def _ordinal(value: Any) -> int:
    return 0 if value is None else int(value)


def _nullable_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _nullable_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _identity(value: Any) -> Any:
    return value


def _logical_ids_to_payloads(value: Any) -> list[dict[str, str]]:
    return [logical_id.to_payload() for logical_id in _logical_ids_from_value(value)]


def _logical_ids_from_value(value: Any) -> tuple[LogicalId, ...]:
    if value is None:
        return ()
    if isinstance(value, LogicalId):
        return (value,)
    if isinstance(value, str):
        return _logical_ids_from_primary(value)
    if not isinstance(value, Sequence):
        return ()
    logical_ids: list[LogicalId] = []
    for entry in value:
        if isinstance(entry, LogicalId):
            logical_ids.append(entry)
        elif isinstance(entry, Mapping):
            namespace = entry.get("namespace")
            local_value = entry.get("value")
            if isinstance(namespace, str) and isinstance(local_value, str) and namespace and local_value:
                logical_ids.append(LogicalId(namespace=namespace, value=local_value))
    return tuple(logical_ids)


def _logical_ids_from_primary(value: Any) -> tuple[LogicalId, ...]:
    if not isinstance(value, str) or ":" not in value:
        return ()
    namespace, local_value = value.split(":", 1)
    if not namespace or not local_value:
        return ()
    return (LogicalId(namespace=namespace, value=local_value),)


def _logical_ids_to_columns(value: Any) -> Mapping[str, Any]:
    logical_ids = _logical_ids_from_value(value)
    payloads = [logical_id.to_payload() for logical_id in logical_ids]
    return {
        "primary_logical_id": None if not logical_ids else logical_ids[0].formatted,
        "logical_ids_json": json.dumps(payloads) if payloads else None,
    }


def _logical_ids_from_columns(values: Mapping[str, Any]) -> tuple[LogicalId, ...]:
    raw_entries = values.get("logical_ids_json")
    if isinstance(raw_entries, str) and raw_entries:
        try:
            decoded = json.loads(raw_entries)
        except json.JSONDecodeError:
            decoded = None
        logical_ids = _logical_ids_from_value(decoded)
    else:
        logical_ids = _logical_ids_from_value(raw_entries)
    if logical_ids:
        return logical_ids
    return _logical_ids_from_primary(values.get("primary_logical_id"))


def _provenance_to_columns(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {"source_paper": None, "provenance_page": None, "provenance_json": None}
    if not isinstance(value, ClaimProvenance):
        raise TypeError(f"claim provenance must be ClaimProvenance, got {type(value).__name__}")
    return {
        "source_paper": value.paper,
        "provenance_page": value.page,
        "provenance_json": value.to_json(),
    }


def _provenance_from_columns(values: Mapping[str, Any]) -> ClaimProvenance | None:
    return ClaimProvenance.from_components(
        paper=None if values.get("source_paper") is None else str(values["source_paper"]),
        page=None if values.get("provenance_page") is None else int(values["provenance_page"]),
        provenance_json=values.get("provenance_json"),
    )


TEXT_CODEC = ProjectionCodec("text", "TEXT", encoder=_nullable_text, decoder=_nullable_text)
RAW_CODEC = ProjectionCodec("raw", "TEXT")
CLAIM_ID_CODEC = ProjectionCodec("claim_id", "TEXT", encoder=_nullable_text, decoder=_claim_id)
CONCEPT_ID_CODEC = ProjectionCodec("concept_id", "TEXT", encoder=_nullable_text, decoder=_concept_id)
CONTEXT_ID_CODEC = ProjectionCodec("context_id", "TEXT", encoder=_nullable_text, decoder=_context_id)
CLAIM_TYPE_CODEC = ProjectionCodec("claim_type", "TEXT", encoder=_claim_type_value, decoder=coerce_claim_type)
ALGORITHM_STAGE_CODEC = ProjectionCodec(
    "algorithm_stage",
    "TEXT",
    encoder=_algorithm_stage_value,
    decoder=coerce_algorithm_stage,
)
CLAIM_CONCEPT_LINK_ROLE_CODEC = ProjectionCodec(
    "claim_concept_link_role",
    "TEXT",
    encoder=_role_value,
    decoder=coerce_claim_concept_link_role,
)
ORDINAL_CODEC = ProjectionCodec("integer", "INTEGER", encoder=_ordinal, decoder=_ordinal)
INTEGER_CODEC = ProjectionCodec("integer", "INTEGER", encoder=_nullable_int, decoder=_nullable_int)
REAL_CODEC = ProjectionCodec("real", "REAL", encoder=_nullable_float, decoder=_nullable_float)
LOGICAL_IDS_PAYLOAD_CODEC = ProjectionCodec(
    "logical_ids_payload",
    "TEXT",
    encoder=_logical_ids_to_payloads,
    decoder=_identity,
)


CLAIM_CONCEPT_LINK_CLAIM_ID_PATH = ScalarPath(
    ("claim_id",), "claim_id", codec=CLAIM_ID_CODEC, nullable=False, missing="raise"
)
CLAIM_CONCEPT_LINK_CONCEPT_ID_PATH = ScalarPath(
    ("concept_id",), "concept_id", codec=CONCEPT_ID_CODEC, nullable=False, missing="raise"
)
CLAIM_CONCEPT_LINK_ROLE_PATH = ScalarPath(
    ("role",), "role", codec=CLAIM_CONCEPT_LINK_ROLE_CODEC, nullable=False, missing="raise"
)
CLAIM_CONCEPT_LINK_ORDINAL_PATH = ScalarPath(
    ("ordinal",), "ordinal", codec=ORDINAL_CODEC, nullable=False
)
CLAIM_CONCEPT_LINK_BINDING_NAME_PATH = ScalarPath(
    ("binding_name",), "binding_name", codec=TEXT_CODEC
)
CLAIM_CONCEPT_LINK_ITEM_FIELDS = (
    CLAIM_CONCEPT_LINK_CONCEPT_ID_PATH,
    CLAIM_CONCEPT_LINK_ROLE_PATH,
    CLAIM_CONCEPT_LINK_ORDINAL_PATH,
    CLAIM_CONCEPT_LINK_BINDING_NAME_PATH,
)


CLAIM_CONCEPT_LINK_ROW_MODEL: ProjectionModel[ClaimConceptLinkRow] = ProjectionModel(
    name="claim_concept_link_row",
    table="claim_concept_link",
    result_type=ClaimConceptLinkRow,
    fields=(CLAIM_CONCEPT_LINK_CLAIM_ID_PATH,) + CLAIM_CONCEPT_LINK_ITEM_FIELDS,
)


CLAIM_CONCEPT_LINKS_PATH = ProjectionAttachedRows(
    path=("concept_links",),
    table="claim_concept_link",
    parent_fk="claim_id",
    parent_path=("claim_id",),
    item_parent_path=("claim_id",),
    item_type=ClaimConceptLinkRow,
    order_by=(CLAIM_CONCEPT_LINK_ORDINAL_PATH, CLAIM_CONCEPT_LINK_CONCEPT_ID_PATH),
    fields=CLAIM_CONCEPT_LINK_ITEM_FIELDS,
)


CLAIM_ROW_GENERIC_MODEL: ProjectionModel[ClaimRow] = ProjectionModel(
    name="claim_row",
    table="claim_core",
    result_type=ClaimRow,
    fields=(
        ScalarPath(("claim_id",), "id", codec=CLAIM_ID_CODEC, nullable=False, missing="raise"),
        ProjectionBinding(
            ("artifact_id",),
            projection_column_owner=ProjectionColumn(
                "artifact_id",
                TEXT_CODEC.sql_type,
                nullable=False,
                encoder=TEXT_CODEC.encode,
                decoder=TEXT_CODEC.decode,
            ),
            read_name="id",
            missing="raise",
        ),
        ProjectionBinding(
            ("claim_type",),
            projection_column_owner=ProjectionColumn(
                "type",
                CLAIM_TYPE_CODEC.sql_type,
                encoder=CLAIM_TYPE_CODEC.encode,
                decoder=CLAIM_TYPE_CODEC.decode,
            ),
            read_name="claim_type",
        ),
        CLAIM_CONCEPT_LINKS_PATH,
        ReferencePath(("target_concept",), "target_concept", family="concept", codec=CONCEPT_ID_CODEC),
        ProjectionComponent(
            path=("logical_ids",),
            bindings=(
                ProjectionBinding(
                    ("primary",),
                    projection_column_owner=ProjectionColumn(
                        "primary_logical_id",
                        TEXT_CODEC.sql_type,
                        encoder=TEXT_CODEC.encode,
                        decoder=TEXT_CODEC.decode,
                    ),
                    read_name="logical_id",
                ),
                ProjectionBinding(
                    ("payload",),
                    projection_column_owner=ProjectionColumn(
                        "logical_ids_json",
                        RAW_CODEC.sql_type,
                        encoder=RAW_CODEC.encode,
                        decoder=RAW_CODEC.decode,
                    ),
                    read_name="logical_ids",
                ),
            ),
            encoder=_logical_ids_to_columns,
            decoder=_logical_ids_from_columns,
        ),
        ProjectionRenderView(source_path=("primary_logical_id",), output_key="logical_id", codec=TEXT_CODEC),
        ProjectionRenderView(source_path=("logical_ids",), output_key="logical_ids", codec=LOGICAL_IDS_PAYLOAD_CODEC),
        ScalarPath(("version_id",), "version_id", codec=TEXT_CODEC),
        ScalarPath(("seq",), "seq", codec=INTEGER_CODEC),
        ScalarPath(("value",), "value", codec=RAW_CODEC),
        ScalarPath(("lower_bound",), "lower_bound", codec=REAL_CODEC),
        ScalarPath(("upper_bound",), "upper_bound", codec=REAL_CODEC),
        ScalarPath(("uncertainty",), "uncertainty", codec=REAL_CODEC),
        ScalarPath(("uncertainty_type",), "uncertainty_type", codec=TEXT_CODEC),
        ScalarPath(("sample_size",), "sample_size", codec=INTEGER_CODEC),
        ScalarPath(("unit",), "unit", codec=TEXT_CODEC),
        ScalarPath(("conditions_cel",), "conditions_cel", codec=TEXT_CODEC),
        ScalarPath(("conditions_ir",), "conditions_ir", codec=TEXT_CODEC),
        ScalarPath(("statement",), "statement", codec=TEXT_CODEC),
        ScalarPath(("expression",), "expression", codec=TEXT_CODEC),
        ScalarPath(("sympy_generated",), "sympy_generated", codec=TEXT_CODEC),
        ScalarPath(("sympy_error",), "sympy_error", codec=TEXT_CODEC),
        ScalarPath(("name",), "name", codec=TEXT_CODEC),
        ScalarPath(("measure",), "measure", codec=TEXT_CODEC),
        ScalarPath(("listener_population",), "listener_population", codec=TEXT_CODEC),
        ScalarPath(("methodology",), "methodology", codec=TEXT_CODEC),
        ScalarPath(("notes",), "notes", codec=TEXT_CODEC),
        ScalarPath(("description",), "description", codec=TEXT_CODEC),
        ScalarPath(("auto_summary",), "auto_summary", codec=TEXT_CODEC),
        ScalarPath(("body",), "body", codec=TEXT_CODEC),
        ScalarPath(("canonical_ast",), "canonical_ast", codec=TEXT_CODEC),
        ScalarPath(("variables_json",), "variables_json", codec=TEXT_CODEC),
        ScalarPath(("algorithm_stage",), "algorithm_stage", codec=ALGORITHM_STAGE_CODEC),
        ProjectionComponent(
            path=("provenance",),
            bindings=(
                ProjectionBinding(
                    ("paper",),
                    projection_column_owner=ProjectionColumn(
                        "source_paper",
                        TEXT_CODEC.sql_type,
                        encoder=TEXT_CODEC.encode,
                        decoder=TEXT_CODEC.decode,
                    ),
                ),
                ProjectionBinding(
                    ("page",),
                    projection_column_owner=ProjectionColumn(
                        "provenance_page",
                        INTEGER_CODEC.sql_type,
                        encoder=INTEGER_CODEC.encode,
                        decoder=INTEGER_CODEC.decode,
                    ),
                ),
                ProjectionBinding(
                    ("payload",),
                    projection_column_owner=ProjectionColumn(
                        "provenance_json",
                        TEXT_CODEC.sql_type,
                        encoder=TEXT_CODEC.encode,
                        decoder=TEXT_CODEC.decode,
                    ),
                ),
            ),
            encoder=_provenance_to_columns,
            decoder=_provenance_from_columns,
        ),
        ScalarPath(("value_si",), "value_si", codec=REAL_CODEC),
        ScalarPath(("lower_bound_si",), "lower_bound_si", codec=REAL_CODEC),
        ScalarPath(("upper_bound_si",), "upper_bound_si", codec=REAL_CODEC),
        ReferencePath(("context_id",), "context_id", family="context", codec=CONTEXT_ID_CODEC),
        ProjectionMetadata(
            path=(),
            fields=(
                ScalarPath(("content_hash",), "content_hash", codec=TEXT_CODEC),
                ScalarPath(("branch",), "branch", codec=TEXT_CODEC),
                ScalarPath(("build_status",), "build_status", codec=TEXT_CODEC),
                ScalarPath(("stage",), "stage", codec=TEXT_CODEC),
                ScalarPath(("promotion_status",), "promotion_status", codec=TEXT_CODEC),
                ScalarPath(("confidence",), "confidence", codec=REAL_CODEC),
                ScalarPath(("claim_probability",), "claim_probability", codec=REAL_CODEC),
                ScalarPath(("effective_sample_size",), "effective_sample_size", codec=INTEGER_CODEC),
                ScalarPath(("opinion_belief",), "opinion_belief", codec=REAL_CODEC),
                ScalarPath(("opinion_disbelief",), "opinion_disbelief", codec=REAL_CODEC),
                ScalarPath(("opinion_uncertainty",), "opinion_uncertainty", codec=REAL_CODEC),
                ScalarPath(("opinion_base_rate",), "opinion_base_rate", codec=REAL_CODEC),
                ScalarPath(("source_assertion_ids",), "source_assertion_ids", codec=RAW_CODEC),
                ScalarPath(("concept_id",), "concept_id", codec=CONCEPT_ID_CODEC),
            ),
            result_type=dict,
        ),
    ),
    ignored_columns=(
        "source",
        "source_slug",
        "source_id",
        "source_kind",
        "source_origin_type",
        "source_origin_value",
        "source_origin_retrieved",
        "source_origin_content_ref",
        "source_prior_base_rate",
        "source_quality_json",
        "source_quality_opinion",
        "source_derived_from_json",
    ),
)
