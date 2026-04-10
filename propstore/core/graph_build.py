"""Build canonical semantic graphs from existing sidecar-backed stores."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from propstore.core.environment import (
    ClaimCatalogStore,
    ClaimStanceInventoryStore,
    ConceptCatalogStore,
    ConflictStore,
    ParameterizationCatalogStore,
    RelationshipCatalogStore,
    StanceStore,
)
from propstore.core.id_types import (
    ConceptId,
    to_claim_id,
    to_concept_id,
    to_concept_ids,
)
from propstore.core.graph_types import (
    ClaimNode,
    CompiledWorldGraph,
    ConceptNode,
    ConflictWitness,
    ParameterizationEdge,
    ProvenanceRecord,
    RelationEdge,
)
from propstore.core.row_types import (
    ClaimRow,
    coerce_claim_row,
    coerce_concept_row,
    coerce_conflict_row,
    coerce_parameterization_row,
    coerce_relationship_row,
    coerce_stance_row,
)


def _row_provenance(
    row: Mapping[str, Any] | ClaimRow,
    *,
    source_table: str,
    source_id: str | None = None,
) -> ProvenanceRecord | None:
    if source_table == "claim":
        if isinstance(row, ClaimRow):
            extras = {}
            if row.provenance is not None:
                extras.update(row.provenance.to_dict())
            extras["source_table"] = source_table
            extras["source_id"] = source_id or str(row.claim_id)
            return ProvenanceRecord.from_mapping(extras)

        provenance_json = row.get("provenance_json")
        extras: dict[str, Any] = {}
        if provenance_json:
            try:
                loaded = json.loads(provenance_json)
                if isinstance(loaded, dict):
                    extras.update(loaded)
            except json.JSONDecodeError:
                extras["provenance_json"] = provenance_json
        if row.get("source_paper") is not None:
            extras.setdefault("paper", row.get("source_paper"))
        if row.get("provenance_page") is not None:
            extras.setdefault("page", row.get("provenance_page"))
        extras["source_table"] = source_table
        extras["source_id"] = source_id or row.get("id")
        return ProvenanceRecord.from_mapping(extras)

    extras = dict(row)
    extras["source_table"] = source_table
    if source_id is not None:
        extras["source_id"] = source_id
    return ProvenanceRecord.from_mapping(extras)


def _concept_attributes(row: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    known = {"id", "canonical_name", "status", "form", "kind_type"}
    return tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in known and value is not None
    )


def _claim_attributes(row: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    claim_data: dict[str, Any] = dict(row.attributes)
    optional_fields = {
        "seq": row.seq,
        "lower_bound": row.lower_bound,
        "upper_bound": row.upper_bound,
        "uncertainty": row.uncertainty,
        "uncertainty_type": row.uncertainty_type,
        "sample_size": row.sample_size,
        "unit": row.unit,
        "conditions_cel": row.conditions_cel,
        "statement": row.statement,
        "expression": row.expression,
        "sympy_generated": row.sympy_generated,
        "sympy_error": row.sympy_error,
        "name": row.name,
        "measure": row.measure,
        "listener_population": row.listener_population,
        "methodology": row.methodology,
        "notes": row.notes,
        "description": row.description,
        "auto_summary": row.auto_summary,
        "body": row.body,
        "canonical_ast": row.canonical_ast,
        "variables_json": row.variables_json,
        "stage": row.stage,
        "value_si": row.value_si,
        "lower_bound_si": row.lower_bound_si,
        "upper_bound_si": row.upper_bound_si,
        "context_id": row.context_id,
    }
    claim_data.pop("content_hash", None)
    for key, value in optional_fields.items():
        if value is not None:
            claim_data[key] = value
    if row.source is not None and not row.source.is_empty:
        claim_data["source"] = row.source.to_dict()
    return tuple((str(key), value) for key, value in claim_data.items() if value is not None)


def _display_claim_id_from_row(row_input) -> str:
    row = coerce_claim_row(row_input)
    logical_value = row.primary_logical_value
    if isinstance(logical_value, str) and logical_value:
        return logical_value
    return str(row.claim_id)


def _display_claim_id(store, claim_id: str) -> str:
    getter = getattr(store, "get_claim", None)
    if callable(getter):
        row = getter(claim_id)
        if row is not None:
            return _display_claim_id_from_row(row)
    return str(claim_id)


def _relation_attributes(
    row: Mapping[str, Any],
    *,
    known: set[str],
) -> tuple[tuple[str, Any], ...]:
    return tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in known and value is not None
    )


def _parse_json_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        loaded = json.loads(value)
        return tuple(str(item) for item in loaded)
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value)
    return tuple(str(item) for item in value)


def _parse_json_concept_ids(value: Any) -> tuple[ConceptId, ...]:
    return to_concept_ids(_parse_json_list(value))


def build_compiled_world_graph(store, *, prefer_logical_claim_ids: bool = True) -> CompiledWorldGraph:
    if not isinstance(store, ConceptCatalogStore):
        raise TypeError("build_compiled_world_graph requires all_concepts()")
    if not isinstance(store, ClaimCatalogStore):
        raise TypeError("build_compiled_world_graph requires claims_for()")
    if not isinstance(store, ParameterizationCatalogStore):
        raise TypeError("build_compiled_world_graph requires all_parameterizations()")
    if not isinstance(store, ConflictStore):
        raise TypeError("build_compiled_world_graph requires conflicts()")

    concept_rows = [
        coerce_concept_row(row)
        for row in store.all_concepts()
    ]
    claim_rows = [
        coerce_claim_row(row)
        for row in store.claims_for(None)
    ]
    relationship_rows = (
        [
            coerce_relationship_row(row)
            for row in store.all_relationships()
        ]
        if isinstance(store, RelationshipCatalogStore)
        else []
    )
    parameterization_rows = [
        coerce_parameterization_row(row)
        for row in store.all_parameterizations()
    ]
    conflict_rows = [
        coerce_conflict_row(row)
        for row in store.conflicts()
    ]

    if isinstance(store, ClaimStanceInventoryStore):
        claim_stance_rows = [
            coerce_stance_row(row)
            for row in store.all_claim_stances()
        ]
    elif isinstance(store, StanceStore):
        claim_ids = {
            str(row.claim_id)
            for row in claim_rows
        }
        claim_stance_rows = [
            coerce_stance_row(row)
            for row in store.stances_between(claim_ids)
        ]
    else:
        raise TypeError(
            "build_compiled_world_graph requires all_claim_stances() or stances_between()"
        )

    concepts = tuple(
        ConceptNode(
            concept_id=row.concept_id,
            canonical_name=row.canonical_name,
            status=row.status,
            form=row.form,
            kind_type=row.kind_type,
            attributes=_concept_attributes(row.to_dict()),
        )
        for row in concept_rows
    )

    claim_display_ids = {
            str(row.claim_id): (
                _display_claim_id_from_row(row)
            if prefer_logical_claim_ids
            else str(row.claim_id)
        )
        for row in claim_rows
    }

    claims = tuple(
        sorted(
            (
                ClaimNode(
                    claim_id=to_claim_id(claim_display_ids[str(row.claim_id)]),
                    concept_id=to_concept_id(str(row.concept_id or row.target_concept or "")),
                    claim_type=str(row.claim_type or "unknown"),
                    scalar_value=row.value,
                    provenance=_row_provenance(
                        row,
                        source_table="claim",
                        source_id=claim_display_ids[str(row.claim_id)],
                    ),
                    attributes=_claim_attributes(row),
                )
                for row in claim_rows
            )
        )
    )

    concept_relationships = tuple(
        sorted(
            (
                RelationEdge(
                    source_id=row.source_id,
                    target_id=row.target_id,
                    relation_type=row.relation_type,
                    provenance=_row_provenance(
                        row.to_dict(),
                        source_table="relationship",
                        source_id=f"{row.source_id}->{row.target_id}:{row.relation_type}",
                    ),
                    attributes=_relation_attributes(
                        row.to_dict(),
                        known={"source_id", "target_id", "type"},
                    ),
                )
                for row in relationship_rows
            )
        )
    )
    claim_stances = tuple(
        sorted(
            (
                RelationEdge(
                    source_id=claim_display_ids.get(
                        str(stance.claim_id),
                        (
                            _display_claim_id(store, str(stance.claim_id))
                            if prefer_logical_claim_ids
                            else str(stance.claim_id)
                        ),
                    ),
                    target_id=claim_display_ids.get(
                        str(stance.target_claim_id),
                        (
                            _display_claim_id(store, str(stance.target_claim_id))
                            if prefer_logical_claim_ids
                            else str(stance.target_claim_id)
                        ),
                    ),
                    relation_type=stance.stance_type,
                    provenance=_row_provenance(
                        stance.to_dict(),
                        source_table="relation_edge",
                        source_id=(
                            f"{claim_display_ids.get(str(stance.claim_id), (_display_claim_id(store, str(stance.claim_id)) if prefer_logical_claim_ids else str(stance.claim_id)))}->"
                            f"{claim_display_ids.get(str(stance.target_claim_id), (_display_claim_id(store, str(stance.target_claim_id)) if prefer_logical_claim_ids else str(stance.target_claim_id)))}:{stance.stance_type}"
                        ),
                    ),
                    attributes=tuple(stance.attributes.items()),
                )
                for stance in claim_stance_rows
            )
        )
    )

    parameterizations = tuple(
        sorted(
            (
                ParameterizationEdge(
                    output_concept_id=parameterization.output_concept_id,
                    input_concept_ids=_parse_json_concept_ids(parameterization.concept_ids),
                    formula=parameterization.formula,
                    sympy=parameterization.sympy,
                    exactness=parameterization.exactness,
                    conditions=_parse_json_list(parameterization.conditions_cel),
                    provenance=_row_provenance(
                        {
                            **parameterization.attributes,
                            "output_concept_id": parameterization.output_concept_id,
                            "concept_ids": parameterization.concept_ids,
                            "formula": parameterization.formula,
                            "sympy": parameterization.sympy,
                            "exactness": parameterization.exactness,
                            "conditions_cel": parameterization.conditions_cel,
                        },
                        source_table="parameterization",
                        source_id=(
                            f"{parameterization.output_concept_id}:"
                            f"{parameterization.formula or parameterization.sympy or 'parameterization'}"
                        ),
                    ),
                )
                for parameterization in parameterization_rows
            )
        )
    )

    conflicts = tuple(
        sorted(
            (
                ConflictWitness(
                    left_claim_id=claim_display_ids.get(
                        str(conflict.claim_a_id),
                        (
                            _display_claim_id(store, str(conflict.claim_a_id))
                            if prefer_logical_claim_ids
                            else str(conflict.claim_a_id)
                        ),
                    ),
                    right_claim_id=claim_display_ids.get(
                        str(conflict.claim_b_id),
                        (
                            _display_claim_id(store, str(conflict.claim_b_id))
                            if prefer_logical_claim_ids
                            else str(conflict.claim_b_id)
                        ),
                    ),
                    kind=str(conflict.warning_class or conflict.conflict_class or "conflict"),
                    details=tuple(
                        entry
                        for entry in (
                            (
                                ("concept_id", conflict.concept_id)
                                if conflict.concept_id is not None
                                else None
                            ),
                            *tuple(conflict.attributes.items()),
                        )
                        if entry is not None
                    ),
                )
                for conflict in conflict_rows
            )
        )
    )

    return CompiledWorldGraph(
        concepts=concepts,
        claims=claims,
        relations=concept_relationships + claim_stances,
        parameterizations=parameterizations,
        conflicts=conflicts,
    )
