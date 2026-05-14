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
from propstore.sidecar.claims import (
    CLAIM_ALGORITHM_PAYLOAD_PROJECTION,
    CLAIM_CONCEPT_LINK_PROJECTION,
    CLAIM_CORE_PROJECTION,
    CLAIM_FTS_PROJECTION,
    CLAIM_NUMERIC_PAYLOAD_PROJECTION,
    CLAIM_TEXT_PAYLOAD_PROJECTION,
    CONFLICT_WITNESS_PROJECTION,
    JUSTIFICATION_PROJECTION,
)
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
from propstore.sidecar.diagnostics import BUILD_DIAGNOSTICS_PROJECTION
from propstore.sidecar.rules import (
    GROUNDED_BUNDLE_INPUT_PROJECTION,
    GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION,
    GROUNDED_FACT_PROJECTION,
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
    CLAIM_CORE_PROJECTION,
    CLAIM_CONCEPT_LINK_PROJECTION,
    CLAIM_NUMERIC_PAYLOAD_PROJECTION,
    CLAIM_TEXT_PAYLOAD_PROJECTION,
    CLAIM_ALGORITHM_PAYLOAD_PROJECTION,
    CLAIM_FTS_PROJECTION,
    CONFLICT_WITNESS_PROJECTION,
    GROUNDED_FACT_PROJECTION,
    GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION,
    GROUNDED_BUNDLE_INPUT_PROJECTION,
    JUSTIFICATION_PROJECTION,
    CALIBRATION_COUNTS_PROJECTION,
    BUILD_DIAGNOSTICS_PROJECTION,
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
