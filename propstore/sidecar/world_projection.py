"""Propstore world sidecar projection contract."""

from __future__ import annotations

from collections.abc import Mapping

from propstore.sidecar.projection import (
    ProjectionColumn,
    ProjectionSchema,
    ProjectionTable,
    SemanticProjection,
    create_projection_schema,
)
from propstore.sidecar.calibration import CALIBRATION_COUNTS_PROJECTION
from propstore.sidecar.concepts import (
    ALIAS_PROJECTION,
    CONCEPT_FTS_PROJECTION,
    CONCEPT_PROJECTION,
    FORM_ALGEBRA_PROJECTION,
    FORM_PROJECTION,
    PARAMETERIZATION_PROJECTION,
    PARAMETERIZATION_GROUP_PROJECTION,
)
from propstore.sidecar.contexts import (
    CONTEXT_ASSUMPTION_PROJECTION,
    CONTEXT_LIFTING_MATERIALIZATION_PROJECTION,
    CONTEXT_LIFTING_RULE_PROJECTION,
    CONTEXT_PROJECTION,
)
from propstore.sidecar.relations import RELATION_EDGE_PROJECTION
from propstore.sidecar.sources import SOURCE_PROJECTION


def _required_table(name: str, *columns: str) -> ProjectionTable:
    return ProjectionTable(
        name=name,
        columns=tuple(ProjectionColumn(column, "ANY") for column in columns),
    )


WORLD_SIDECAR_SCHEMA = create_projection_schema(
    SOURCE_PROJECTION,
    CONCEPT_PROJECTION,
    ALIAS_PROJECTION,
    PARAMETERIZATION_PROJECTION,
    PARAMETERIZATION_GROUP_PROJECTION,
    RELATION_EDGE_PROJECTION,
    FORM_PROJECTION,
    FORM_ALGEBRA_PROJECTION,
    CONCEPT_FTS_PROJECTION,
    CONTEXT_PROJECTION,
    CONTEXT_ASSUMPTION_PROJECTION,
    CONTEXT_LIFTING_RULE_PROJECTION,
    CONTEXT_LIFTING_MATERIALIZATION_PROJECTION,
    _required_table(
        "claim_core",
        "id",
        "primary_logical_id",
        "logical_ids_json",
        "version_id",
        "content_hash",
        "seq",
        "type",
        "target_concept",
        "source_slug",
        "source_paper",
        "provenance_page",
        "provenance_json",
        "context_id",
        "premise_kind",
        "branch",
        "build_status",
        "stage",
        "promotion_status",
    ),
    _required_table(
        "claim_concept_link",
        "claim_id",
        "concept_id",
        "role",
        "ordinal",
        "binding_name",
    ),
    _required_table(
        "claim_numeric_payload",
        "claim_id",
        "value",
        "lower_bound",
        "upper_bound",
        "uncertainty",
        "uncertainty_type",
        "sample_size",
        "unit",
        "value_si",
        "lower_bound_si",
        "upper_bound_si",
    ),
    _required_table(
        "claim_text_payload",
        "claim_id",
        "conditions_cel",
        "conditions_ir",
        "statement",
        "expression",
        "sympy_generated",
        "sympy_error",
        "name",
        "measure",
        "listener_population",
        "methodology",
        "notes",
        "description",
        "auto_summary",
    ),
    _required_table(
        "claim_algorithm_payload",
        "claim_id",
        "body",
        "canonical_ast",
        "variables_json",
        "algorithm_stage",
    ),
    _required_table(
        "conflict_witness",
        "concept_id",
        "claim_a_id",
        "claim_b_id",
        "warning_class",
        "conditions_a",
        "conditions_b",
        "value_a",
        "value_b",
        "derivation_chain",
    ),
    _required_table("grounded_fact", "predicate", "arguments", "section"),
    _required_table("grounded_fact_empty_predicate", "section", "predicate"),
    _required_table(
        "justification",
        "id",
        "justification_kind",
        "conclusion_claim_id",
        "premise_claim_ids",
        "source_relation_type",
        "source_claim_id",
        "provenance_json",
        "rule_strength",
    ),
    CALIBRATION_COUNTS_PROJECTION,
    _required_table(
        "build_diagnostics",
        "id",
        "claim_id",
        "source_kind",
        "source_ref",
        "diagnostic_kind",
        "severity",
        "blocking",
        "message",
        "file",
        "detail_json",
    ),
    metadata={"projection": "propstore.world"},
)


def required_columns_by_table(
    schema: ProjectionSchema = WORLD_SIDECAR_SCHEMA,
) -> Mapping[str, frozenset[str]]:
    return {
        _projection_name(projection): frozenset(projection.column_names)
        for projection in schema.projections
    }


def _projection_name(projection: SemanticProjection) -> str:
    if isinstance(projection, ProjectionTable):
        return projection.name
    return projection.table
