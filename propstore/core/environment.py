"""Core environment and store-protocol types for the world layer.

These live in ``core`` rather than ``world`` so the dependency runs one way: the
world layer depends on ``core``, never the reverse (CLAUDE.md layering; the
reference moved ``Environment`` here to fix an inverted dependency).

An :class:`Environment` is the assumption/binding/context frame a world query
renders under. The store protocols are the read surface the world layer consumes;
each is typed over the ONE canonical domain object the rewrite already owns —
``Claim`` / ``Concept`` / ``Stance`` charters, the ``ConflictRecord`` /
``CanonicalJustification`` value types, the ``RelationEdge`` / ``ParameterizationEdge``
graph carriers, and condition-ir's ``ConditionSolver`` — never a ``*RowInput``
second spelling. Because ``from __future__ import annotations`` makes every
annotation lazy, the domain-type imports are ``TYPE_CHECKING``-only, so importing
this module pulls in no charter, condition-ir solver, or graph module at runtime
(and ``core`` never imports ``world``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import msgspec
from quire.documents import DocumentStruct

from condition_ir import CelExpr
from propstore.core.id_types import (
    AssumptionId,
    ContextId,
)
from propstore.core.scalars import ScalarValue

if TYPE_CHECKING:
    from condition_ir import ConditionSolver

    from propstore.conflict_detector.models import ConflictRecord
    from propstore.core.graph_types import (
        CompiledWorldGraph,
        ParameterizationEdge,
        RelationEdge,
    )
    from propstore.core.justifications import CanonicalJustification
    from propstore.core.store_results import (
        ClaimSimilarityHit,
        ConceptSearchHit,
        ConceptSimilarityHit,
        WorldStoreStats,
    )
    from propstore.families.claims import Claim
    from propstore.families.concepts import Concept
    from propstore.families.forms import FormDefinition
    from propstore.families.micropublications import Micropublication
    from propstore.families.relations import Stance


class AssumptionRef(DocumentStruct):
    """A reference to one assumption carried by an :class:`Environment`.

    ``kind`` distinguishes a binding assumption from a context assumption;
    ``source`` records who introduced it; ``cel`` is the assumption's CEL form.
    The stable identity is ``assumption_id``.
    """

    assumption_id: AssumptionId
    kind: str
    source: str
    cel: CelExpr


class Environment(DocumentStruct):
    """The assumption/binding/context frame a world query renders under."""

    bindings: dict[str, ScalarValue] = msgspec.field(
        default_factory=dict[str, ScalarValue]
    )
    context_id: ContextId | None = None
    effective_assumptions: tuple[CelExpr, ...] = ()
    assumptions: tuple[AssumptionRef, ...] = ()


@runtime_checkable
class StanceStore(Protocol):
    def stances_between(self, claim_ids: set[str]) -> Sequence[Stance]: ...


@runtime_checkable
class ClaimCatalogStore(Protocol):
    def claims_for(self, concept_id: str | None) -> Sequence[Claim]: ...


@runtime_checkable
class ClaimLookupStore(Protocol):
    def get_claim(self, claim_id: str) -> Claim | None: ...


@runtime_checkable
class ConceptCatalogStore(Protocol):
    def all_concepts(self) -> Sequence[Concept]: ...


@runtime_checkable
class RelationshipCatalogStore(Protocol):
    def all_relationships(self) -> Sequence[RelationEdge]: ...


@runtime_checkable
class ExplanationStore(Protocol):
    def explain(self, claim_id: str) -> Sequence[Stance]: ...


@runtime_checkable
class ClaimStanceInventoryStore(Protocol):
    def all_claim_stances(self) -> Sequence[Stance]: ...


@runtime_checkable
class AuthoredJustificationStore(Protocol):
    def justifications_for_claim_scope(
        self, claim_ids: set[str]
    ) -> Sequence[CanonicalJustification]: ...


@runtime_checkable
class ConflictStore(Protocol):
    def conflicts(self) -> Sequence[ConflictRecord]: ...


@runtime_checkable
class ParameterizationLookupStore(Protocol):
    def parameterizations_for(
        self, concept_id: str
    ) -> Sequence[ParameterizationEdge]: ...


@runtime_checkable
class ParameterizationCatalogStore(Protocol):
    def all_parameterizations(self) -> Sequence[ParameterizationEdge]: ...


@runtime_checkable
class MicropublicationCatalogStore(Protocol):
    def all_micropublications(self) -> Sequence[Micropublication]: ...


@runtime_checkable
class ConditionSolverStore(Protocol):
    def condition_solver(self) -> ConditionSolver: ...


@runtime_checkable
class CompiledGraphStore(Protocol):
    def compiled_graph(self) -> CompiledWorldGraph: ...


@runtime_checkable
class WorldStore(Protocol):
    """The umbrella read surface the world layer queries.

    Aggregates the single-method store protocols above. ``chain_query`` is the
    one method whose ``strategy``/return are ``Any``: the resolution-strategy and
    chain-result types are defined in the world layer (Phase 7a-world), which
    ``core`` must not import, so they cannot be named here without inverting the
    dependency. Concrete stores narrow them at the world-layer call site.
    """

    def get_concept(self, concept_id: str) -> Concept | None: ...
    def get_claim(self, claim_id: str) -> Claim | None: ...
    def resolve_alias(self, alias: str) -> str | None: ...
    def resolve_concept(self, name: str) -> str | None: ...
    def resolve_claim(self, name: str) -> str | None: ...
    def claims_for(self, concept_id: str | None) -> Sequence[Claim]: ...
    def claims_by_ids(self, claim_ids: set[str]) -> Mapping[str, Claim]: ...
    def stances_between(self, claim_ids: set[str]) -> Sequence[Stance]: ...
    def conflicts(self) -> Sequence[ConflictRecord]: ...
    def all_concepts(self) -> Sequence[Concept]: ...
    def all_forms(self) -> Sequence[FormDefinition]: ...
    def all_parameterizations(self) -> Sequence[ParameterizationEdge]: ...
    def all_relationships(self) -> Sequence[RelationEdge]: ...
    def all_claim_stances(self) -> Sequence[Stance]: ...
    def all_micropublications(self) -> Sequence[Micropublication]: ...
    def concept_ids_for_group(self, group_id: int) -> set[str]: ...
    def search(self, query: str) -> list[ConceptSearchHit]: ...
    def similar_claims(
        self, claim_id: str, model_name: str | None = None, top_k: int = 10
    ) -> list[ClaimSimilarityHit]: ...
    def similar_concepts(
        self, concept_id: str, model_name: str | None = None, top_k: int = 10
    ) -> list[ConceptSimilarityHit]: ...
    def stats(self) -> WorldStoreStats: ...
    def explain(self, claim_id: str) -> Sequence[Stance]: ...
    def condition_solver(self) -> ConditionSolver: ...
    def parameterizations_for(
        self, concept_id: str
    ) -> Sequence[ParameterizationEdge]: ...
    def group_members(self, concept_id: str) -> list[str]: ...
    def chain_query(
        self,
        target_concept_id: str,
        strategy: Any | None = None,
        **bindings: Any,
    ) -> Any: ...
