"""Build a canonical :class:`CompiledWorldGraph` from a charter-backed store.

This is the row-free graph builder: it reads the ONE canonical charter objects a
:class:`~propstore.core.environment.WorldStore` exposes — ``Concept`` / ``Claim``
/ ``Stance`` charters plus the graph-carrier
:class:`~propstore.core.graph_types.RelationEdge` /
:class:`~propstore.core.graph_types.ParameterizationEdge` and the
:class:`~propstore.conflict_detector.models.ConflictRecord` value — and lowers
them into the compiled world graph the world layer renders over. There is no
``*Row`` / ``*RowInput`` second spelling and no ``coerce`` round-trip: a concept
becomes a :class:`ConceptNode`, a claim a :class:`ClaimNode`, a stance a
:class:`RelationEdge`, and a conflict record a :class:`ConflictWitness` (CLAUDE.md
substrate boundary). Concept relationships and parameterizations are already the
graph-carrier types on the store surface, so they pass through unchanged.

``core`` must not import ``world``; this builder takes the store protocols and the
core graph carriers only.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, TypeGuard

from condition_ir import CheckedConditionSet, checked_condition_set_from_json

from propstore.conflict_detector.models import ConflictRecord
from propstore.core.environment import (
    ClaimCatalogStore,
    ClaimStanceInventoryStore,
    ConceptCatalogStore,
    ConflictStore,
    ParameterizationCatalogStore,
    RelationshipCatalogStore,
    StanceStore,
)
from propstore.core.graph_relation_types import (
    VALID_GRAPH_RELATION_TYPES,
    coerce_graph_relation_type,
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
from propstore.core.id_types import ConceptId, to_claim_id, to_concept_id
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.relations import Stance


def _value_concept_id(claim: Claim) -> ConceptId | None:
    """The concept a claim's value is about: output, else target, else first ref."""

    for candidate in (claim.output_concept, claim.target_concept, *claim.concepts):
        if candidate:
            return to_concept_id(candidate)
    return None


def _is_str_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _checked_conditions(claim: Claim) -> CheckedConditionSet | None:
    """Rebuild the claim's checked conditions from its stored ``conditions_ir``."""

    if not claim.conditions_ir:
        return None
    decoded = json.loads(claim.conditions_ir)
    if not _is_str_mapping(decoded):
        raise ValueError(f"claim {claim.claim_id} conditions_ir must decode to a mapping")
    return checked_condition_set_from_json(decoded)


def _claim_attributes(claim: Claim) -> tuple[tuple[str, Any], ...]:
    """The non-identity claim fields the analyzer/preference layers read as a row."""

    optional: dict[str, Any] = {
        "status": claim.status.value,
        "context_id": claim.context_id,
        "statement": claim.statement,
        "name": claim.name,
        "body": claim.body,
        "expression": claim.expression,
        "sympy": claim.sympy,
        "measure": claim.measure,
        "methodology": claim.methodology,
        "notes": claim.notes,
        "concepts": list(claim.concepts),
        "equations": list(claim.equations),
        "conditions": list(claim.conditions),
        "lower_bound": claim.lower_bound,
        "upper_bound": claim.upper_bound,
        "uncertainty": claim.uncertainty,
        "uncertainty_type": claim.uncertainty_type,
        "confidence": claim.confidence,
        "unit": claim.unit,
        "sample_size": claim.sample_size,
    }
    return tuple(
        (key, value)
        for key, value in optional.items()
        if value is not None and value != []
    )


def claim_to_node(claim: Claim) -> ClaimNode:
    """Lower one ``Claim`` charter into a :class:`ClaimNode`."""

    return ClaimNode(
        claim_id=to_claim_id(claim.claim_id),
        claim_type=claim.claim_type or ClaimType.UNKNOWN,
        value_concept_id=_value_concept_id(claim),
        scalar_value=claim.value,
        checked_conditions=_checked_conditions(claim),
        attributes=_claim_attributes(claim),
    )


def _concept_node(concept: Concept) -> ConceptNode:
    attributes = (
        (("definition", concept.definition),) if concept.definition is not None else ()
    )
    return ConceptNode(
        concept_id=to_concept_id(concept.concept_id),
        canonical_name=concept.canonical_name,
        status=concept.status.value,
        attributes=attributes,
    )


def stance_to_edge(stance: Stance) -> RelationEdge | None:
    """Lower a stance into a relation edge, or ``None`` when it cannot be one.

    A stance with no endpoints or a stance type outside the graph relation
    vocabulary (e.g. an ``abstain`` or DeLP defeater kind) is not a
    claim-to-claim graph edge; it is skipped here rather than forced into a graph
    relation it is not. Its opinion/confidence columns ride on the edge so the
    downstream stance-row view recovers the calibration.
    """

    if stance.source_claim_id is None or stance.target_claim_id is None:
        return None
    if stance.stance_type is None or stance.stance_type.value not in VALID_GRAPH_RELATION_TYPES:
        return None
    attributes: dict[str, Any] = {
        "resolution_model": stance.resolution_model,
        "confidence": stance.confidence,
        "opinion_belief": stance.opinion_belief,
        "opinion_disbelief": stance.opinion_disbelief,
        "opinion_uncertainty": stance.opinion_uncertainty,
        "opinion_base_rate": stance.opinion_base_rate,
    }
    return RelationEdge(
        source_id=str(stance.source_claim_id),
        target_id=str(stance.target_claim_id),
        relation_type=coerce_graph_relation_type(stance.stance_type.value),
        provenance=ProvenanceRecord(
            source_table="relation_edge",
            source_id=(
                f"{stance.source_claim_id}->{stance.target_claim_id}:{stance.stance_type.value}"
            ),
        ),
        attributes=tuple(
            (key, value) for key, value in attributes.items() if value is not None
        ),
    )


def conflict_record_to_witness(record: ConflictRecord) -> ConflictWitness:
    """Lower one :class:`ConflictRecord` into a :class:`ConflictWitness`."""

    return ConflictWitness(
        left_claim_id=to_claim_id(record.claim_a_id),
        right_claim_id=to_claim_id(record.claim_b_id),
        kind=record.warning_class.value,
        details=(("concept_id", record.concept_id),) if record.concept_id else (),
    )


def _claim_stances(store: object, claim_ids: set[str]) -> Sequence[Stance]:
    if isinstance(store, ClaimStanceInventoryStore):
        return store.all_claim_stances()
    if isinstance(store, StanceStore):
        return store.stances_between(claim_ids)
    raise TypeError(
        "build_compiled_world_graph requires all_claim_stances() or stances_between()"
    )


def build_compiled_world_graph(store: object) -> CompiledWorldGraph:
    """Compile a charter-backed store into a :class:`CompiledWorldGraph`.

    Reads every authored concept, claim, concept relationship, parameterization,
    claim stance, and conflict record; lowers each into its graph carrier. Never
    filters — a draft claim, an abstaining stance edge, or an unresolved value all
    land in the compiled graph; activation and render decide visibility.
    """

    if not isinstance(store, ConceptCatalogStore):
        raise TypeError("build_compiled_world_graph requires all_concepts()")
    if not isinstance(store, ClaimCatalogStore):
        raise TypeError("build_compiled_world_graph requires claims_for()")
    if not isinstance(store, ParameterizationCatalogStore):
        raise TypeError("build_compiled_world_graph requires all_parameterizations()")
    if not isinstance(store, ConflictStore):
        raise TypeError("build_compiled_world_graph requires conflicts()")

    concepts = tuple(_concept_node(concept) for concept in store.all_concepts())
    claims = tuple(claim_to_node(claim) for claim in store.claims_for(None))
    claim_ids = {str(claim.claim_id) for claim in claims}

    relationships: tuple[RelationEdge, ...] = (
        tuple(store.all_relationships())
        if isinstance(store, RelationshipCatalogStore)
        else ()
    )
    parameterizations: tuple[ParameterizationEdge, ...] = tuple(
        store.all_parameterizations()
    )
    stance_edges = tuple(
        edge
        for stance in _claim_stances(store, claim_ids)
        if (edge := stance_to_edge(stance)) is not None
    )
    conflicts = tuple(conflict_record_to_witness(record) for record in store.conflicts())

    return CompiledWorldGraph(
        concepts=concepts,
        claims=claims,
        relations=relationships + stance_edges,
        parameterizations=parameterizations,
        conflicts=conflicts,
    )


__all__ = [
    "build_compiled_world_graph",
    "claim_to_node",
    "conflict_record_to_witness",
    "stance_to_edge",
]
