"""Typed runtime graph mechanics over canonical semantic owners.

The compiled graph carries the authored ``Concept``, ``Claim``, and ``Stance``
charters plus detected ``ConflictRecord`` values directly. Only topology,
parameterization, deltas, and activation state are owned here. Runtime graph
objects are not a persistence format and expose no mapping codecs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from condition_ir import CelExpr, CheckedConditionSet, to_cel_exprs

from propstore.conflict_detector.models import ConflictRecord
from propstore.core.environment import Environment
from propstore.core.graph_relation_types import (
    GraphRelationType,
    coerce_graph_relation_type,
)
from propstore.core.id_types import ClaimId, ConceptId, to_claim_ids, to_concept_ids
from propstore.families.claims import Claim, Exactness
from propstore.families.concepts import Concept
from propstore.families.relations import Stance


@dataclass(frozen=True, order=True)
class RelationEdge:
    """A graph-native relationship that is not an authored claim stance."""

    source_id: str
    target_id: str
    relation_type: GraphRelationType
    derived_from: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "relation_type", coerce_graph_relation_type(self.relation_type)
        )
        object.__setattr__(self, "derived_from", tuple(sorted(self.derived_from)))


@dataclass(frozen=True, order=True)
class ParameterizationEdge:
    output_concept_id: ConceptId
    input_concept_ids: tuple[ConceptId, ...]
    formula: str | None = None
    sympy: str | None = None
    exactness: Exactness | None = None
    conditions: tuple[CelExpr, ...] = ()
    checked_conditions: CheckedConditionSet | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "input_concept_ids", to_concept_ids(self.input_concept_ids)
        )
        object.__setattr__(
            self,
            "conditions",
            (
                self.checked_conditions.sources
                if self.checked_conditions is not None
                else to_cel_exprs(self.conditions)
            ),
        )


@dataclass(frozen=True)
class CompiledWorldGraph:
    concepts: tuple[Concept, ...] = ()
    claims: tuple[Claim, ...] = ()
    relations: tuple[RelationEdge, ...] = ()
    parameterizations: tuple[ParameterizationEdge, ...] = ()
    stances: tuple[Stance, ...] = ()
    conflicts: tuple[ConflictRecord, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "concepts",
            tuple(sorted(self.concepts, key=lambda item: item.concept_id)),
        )
        object.__setattr__(
            self, "claims", tuple(sorted(self.claims, key=lambda item: item.claim_id))
        )
        object.__setattr__(self, "relations", tuple(sorted(self.relations)))
        object.__setattr__(
            self, "parameterizations", tuple(sorted(self.parameterizations))
        )
        object.__setattr__(
            self,
            "stances",
            tuple(sorted(self.stances, key=lambda item: item.stance_id)),
        )
        object.__setattr__(
            self,
            "conflicts",
            tuple(
                sorted(
                    self.conflicts,
                    key=lambda item: (
                        min(item.claim_a_id, item.claim_b_id),
                        max(item.claim_a_id, item.claim_b_id),
                        str(item.warning_class),
                    ),
                )
            ),
        )


@dataclass(frozen=True)
class GraphDelta:
    add_claims: tuple[Claim, ...] = ()
    remove_claim_ids: tuple[ClaimId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "add_claims",
            tuple(sorted(self.add_claims, key=lambda item: item.claim_id)),
        )
        object.__setattr__(
            self,
            "remove_claim_ids",
            tuple(sorted(dict.fromkeys(to_claim_ids(self.remove_claim_ids)))),
        )

    @property
    def is_identity(self) -> bool:
        return not self.add_claims and not self.remove_claim_ids

    def apply(self, graph: CompiledWorldGraph) -> CompiledWorldGraph:
        removed_ids = {str(claim_id) for claim_id in self.remove_claim_ids}
        claims = {
            claim.claim_id: claim
            for claim in graph.claims
            if claim.claim_id not in removed_ids
        }
        for claim in self.add_claims:
            claims[claim.claim_id] = claim
        claim_ids = set(claims)
        original_claim_ids = {claim.claim_id for claim in graph.claims}

        return CompiledWorldGraph(
            concepts=graph.concepts,
            claims=tuple(claims.values()),
            relations=tuple(
                edge
                for edge in graph.relations
                if (edge.source_id in claim_ids and edge.target_id in claim_ids)
                or (
                    edge.source_id not in original_claim_ids
                    and edge.source_id not in claim_ids
                    and edge.target_id not in original_claim_ids
                    and edge.target_id not in claim_ids
                )
            ),
            parameterizations=graph.parameterizations,
            stances=tuple(
                stance
                for stance in graph.stances
                if stance.source_claim_id in claim_ids
                and stance.target_claim_id in claim_ids
            ),
            conflicts=tuple(
                conflict
                for conflict in graph.conflicts
                if conflict.claim_a_id in claim_ids and conflict.claim_b_id in claim_ids
            ),
        )

    def then(self, other: GraphDelta) -> GraphDelta:
        carried = tuple(
            claim
            for claim in self.apply(CompiledWorldGraph()).claims
            if claim.claim_id
            not in {str(claim_id) for claim_id in other.remove_claim_ids}
        )
        return GraphDelta(
            add_claims=carried + other.add_claims,
            remove_claim_ids=tuple(self.remove_claim_ids)
            + tuple(other.remove_claim_ids),
        )


@dataclass(frozen=True)
class ActiveWorldGraph:
    compiled: CompiledWorldGraph
    environment: Environment = field(default_factory=Environment)
    active_claim_ids: tuple[ClaimId, ...] = ()
    inactive_claim_ids: tuple[ClaimId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "active_claim_ids",
            tuple(sorted(dict.fromkeys(to_claim_ids(self.active_claim_ids)))),
        )
        object.__setattr__(
            self,
            "inactive_claim_ids",
            tuple(sorted(dict.fromkeys(to_claim_ids(self.inactive_claim_ids)))),
        )
