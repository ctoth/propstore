"""Build canonical semantic graphs from existing sidecar-backed stores."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from propstore.conflict_detector import ConflictClass
from propstore.cel_types import to_cel_exprs
from propstore.core.conditions import CheckedConditionSet, checked_condition_set_from_json
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
    to_concept_ids,
)
from propstore.core.graph_relation_types import coerce_graph_relation_type
from propstore.core.graph_types import (
    CompiledWorldGraph,
    ConceptNode,
    ConflictWitness,
    ParameterizationEdge,
    ProvenanceRecord,
    RelationEdge,
)
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import Claim
from propstore.families.claims.graph import claim_node_from_claim
from propstore.families.relations.declaration import (
    Stance,
)
from propstore.families.concepts.declaration import (
    Concept,
    Parameterization,
)


def _row_provenance(
    row: Mapping[str, Any] | Claim,
    *,
    source_table: str,
    source_id: str | None = None,
) -> ProvenanceRecord | None:
    if source_table == "claim":
        if not isinstance(row, Claim):
            raise TypeError("claim provenance rows must be typed Claim objects")
        provenance_json = row.provenance_json
        extras: dict[str, Any] = {}
        if provenance_json:
            try:
                loaded = json.loads(provenance_json)
                if isinstance(loaded, dict):
                    extras.update(loaded)
            except json.JSONDecodeError:
                extras["provenance_json"] = provenance_json
        if row.source_paper is not None:
            extras.setdefault("paper", row.source_paper)
        if row.provenance_page is not None:
            extras.setdefault("page", row.provenance_page)
        extras["source_table"] = source_table
        extras["source_id"] = source_id or row.id
        return ProvenanceRecord.from_json_payload(extras)

    if not isinstance(row, Mapping):
        raise TypeError("non-claim provenance rows must be mappings")
    extras = dict(row)
    extras["source_table"] = source_table
    if source_id is not None:
        extras["source_id"] = source_id
    return ProvenanceRecord.from_json_payload(extras)


def _concept_attributes(row: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    known = {"id", "canonical_name", "status", "form", "kind_type"}
    return tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in known and value is not None
    )


def _display_claim_id_from_row(row: Claim) -> str:
    if row.primary_logical_id:
        return row.primary_logical_id
    return str(row.id)


def _display_claim_id(store, claim_id: str) -> str:
    getter = getattr(store, "get_claim", None)
    if callable(getter):
        row = getter(claim_id)
        if row is not None:
            if not isinstance(row, Claim):
                raise TypeError("get_claim() must return typed Claim objects")
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


def _checked_conditions_from_json_text(
    value: str | None,
    *,
    owner: str,
) -> CheckedConditionSet | None:
    if not value:
        return None
    loaded = json.loads(value)
    if not isinstance(loaded, Mapping):
        raise ValueError(f"{owner} conditions_ir must decode to a mapping")
    return checked_condition_set_from_json(loaded)


def _parameterization_condition_sources(
    parameterization: Parameterization,
) -> tuple[str, ...]:
    if parameterization.conditions_ir:
        condition_set = _checked_conditions_from_json_text(
            parameterization.conditions_ir,
            owner=f"parameterization {parameterization.output_concept_id}",
        )
        return () if condition_set is None else condition_set.sources
    if parameterization.conditions_cel:
        raise ValueError(
            "parameterization "
            f"{parameterization.output_concept_id} has conditions_cel without "
            "conditions_ir; rebuild the sidecar"
        )
    return ()


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

    concept_rows = list(store.all_concepts())
    claim_rows = list(store.claims_for(None))
    for row in claim_rows:
        if not isinstance(row, Claim):
            raise TypeError("claims_for() must return typed Claim objects")
    relationship_rows = list(store.all_relationships()) if isinstance(store, RelationshipCatalogStore) else []
    parameterization_rows = list(store.all_parameterizations())
    conflict_rows = list(store.conflicts())

    if isinstance(store, ClaimStanceInventoryStore):
        claim_stance_rows = list(store.all_claim_stances())
    elif isinstance(store, StanceStore):
        claim_ids = {
            str(row.id)
            for row in claim_rows
        }
        claim_stance_rows = list(store.stances_between(claim_ids))
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
            attributes=tuple(row.attribute_mapping().items()),
        )
        for row in concept_rows
    )
    claim_display_ids = {
            str(row.id): (
                _display_claim_id_from_row(row)
            if prefer_logical_claim_ids
            else str(row.id)
        )
        for row in claim_rows
    }

    claims = tuple(
        sorted(
            (
                claim_node_from_claim(row, claim_id=claim_display_ids[str(row.id)])
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
                    relation_type=coerce_graph_relation_type(row.relation_type),
                    provenance=_row_provenance(
                        {
                            "source_id": row.source_id,
                            "target_id": row.target_id,
                            "relation_type": row.relation_type,
                            **row.attribute_mapping(),
                        },
                        source_table="relationship",
                        source_id=f"{row.source_id}->{row.target_id}:{row.relation_type}",
                    ),
                    attributes=_relation_attributes(
                        {
                            "source_id": row.source_id,
                            "target_id": row.target_id,
                            "relation_type": row.relation_type,
                            **row.attribute_mapping(),
                        },
                        known={"source_id", "target_id", "relation_type"},
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
                    relation_type=coerce_graph_relation_type(stance.stance_type.value),
                    provenance=_row_provenance(
                        {
                            "claim_id": str(stance.claim_id),
                            "target_claim_id": str(stance.target_claim_id),
                            "stance_type": stance.stance_type,
                            **stance.attribute_mapping(),
                        },
                        source_table="relation_edge",
                        source_id=(
                            f"{claim_display_ids.get(str(stance.claim_id), (_display_claim_id(store, str(stance.claim_id)) if prefer_logical_claim_ids else str(stance.claim_id)))}->"
                            f"{claim_display_ids.get(str(stance.target_claim_id), (_display_claim_id(store, str(stance.target_claim_id)) if prefer_logical_claim_ids else str(stance.target_claim_id)))}:{stance.stance_type}"
                        ),
                    ),
                    attributes=tuple(stance.attribute_mapping().items()),
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
                    conditions=to_cel_exprs(
                        _parameterization_condition_sources(parameterization)
                    ),
                    checked_conditions=_checked_conditions_from_json_text(
                        parameterization.conditions_ir,
                        owner=f"parameterization {parameterization.output_concept_id}",
                    ),
                    provenance=_row_provenance(
                        {
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
                    left_claim_id=to_claim_id(
                        claim_display_ids.get(
                            str(conflict.claim_a_id),
                            (
                                _display_claim_id(store, str(conflict.claim_a_id))
                                if prefer_logical_claim_ids
                                else str(conflict.claim_a_id)
                            ),
                        )
                    ),
                    right_claim_id=to_claim_id(
                        claim_display_ids.get(
                            str(conflict.claim_b_id),
                            (
                                _display_claim_id(store, str(conflict.claim_b_id))
                                if prefer_logical_claim_ids
                                else str(conflict.claim_b_id)
                            ),
                        )
                    ),
                    kind=(
                        warning_class.value
                        if isinstance(
                            warning_class := (conflict.warning_class or conflict.conflict_class),
                            ConflictClass,
                        )
                        else str(warning_class or "conflict")
                    ),
                    details=tuple(
                        entry
                        for entry in (
                            (
                                ("concept_id", conflict.concept_id)
                                if conflict.concept_id is not None
                                else None
                            ),
                            *tuple(conflict.attribute_mapping().items()),
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
