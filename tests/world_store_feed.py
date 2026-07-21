"""In-memory world-store feeds for the store->graph->AF assembly tests.

Phase 7a-world-A builds the store-reading half over the ``WorldStore`` protocol;
there is no concrete repo-backed store yet (that is Phase 9). These feeds stand in
for one: :class:`CompiledGraphStore` is the compiled-graph feed the analyzer/PrAF
paths read, and :class:`CharterStore` is the charter feed
``build_compiled_world_graph`` reads.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from propstore.conflict_detector.models import ConflictRecord
from propstore.core.graph_types import (
    CompiledWorldGraph,
    ParameterizationEdge,
    RelationEdge,
)
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.relations import Stance


@dataclass(frozen=True)
class CompiledGraphStore:
    """A store that hands back a prebuilt compiled graph (CompiledGraphStore)."""

    compiled: CompiledWorldGraph

    def compiled_graph(self) -> CompiledWorldGraph:
        return self.compiled

    def resolve_claim(self, name: str) -> str | None:
        return name


@dataclass
class CharterStore:
    """A charter-backed feed for :func:`build_compiled_world_graph`."""

    concepts: tuple[Concept, ...] = ()
    claims: tuple[Claim, ...] = ()
    stances: tuple[Stance, ...] = ()
    relationships: tuple[RelationEdge, ...] = ()
    parameterizations: tuple[ParameterizationEdge, ...] = ()
    conflict_records: tuple[ConflictRecord, ...] = field(default_factory=tuple)

    def all_concepts(self) -> Sequence[Concept]:
        return self.concepts

    def claims_for(self, concept_id: str | None) -> Sequence[Claim]:
        if concept_id is None:
            return self.claims
        return [
            claim
            for claim in self.claims
            if concept_id
            in (claim.output_concept, claim.target_concept, *claim.concepts)
        ]

    def all_relationships(self) -> Sequence[RelationEdge]:
        return self.relationships

    def all_parameterizations(self) -> Sequence[ParameterizationEdge]:
        return self.parameterizations

    def conflicts(self) -> Sequence[ConflictRecord]:
        return self.conflict_records

    def stances_between(self, claim_ids: set[str]) -> Sequence[Stance]:
        return [
            stance
            for stance in self.stances
            if stance.source_claim_id in claim_ids
            and stance.target_claim_id in claim_ids
        ]
