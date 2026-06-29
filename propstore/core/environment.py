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
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, TypeGuard, runtime_checkable

from condition_ir import CelExpr, to_cel_expr, to_cel_exprs
from propstore.core.id_types import (
    AssumptionId,
    ContextId,
    to_assumption_id,
    to_context_id,
)

if TYPE_CHECKING:
    from condition_ir import ConditionSolver

    from propstore.conflict_detector.models import ConflictRecord
    from propstore.core.graph_types import (
        CompiledWorldGraph,
        ParameterizationEdge,
        RelationEdge,
    )
    from propstore.core.justifications import CanonicalJustification
    from propstore.core.micropublications import ActiveMicropublicationInput
    from propstore.core.store_results import (
        ClaimSimilarityHit,
        ConceptSearchHit,
        ConceptSimilarityHit,
        WorldStoreStats,
    )
    from propstore.families.claims import Claim
    from propstore.families.concepts import Concept
    from propstore.families.relations import Stance


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _empty_bindings() -> dict[str, Any]:
    return {}


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not _is_mapping(value):
        raise ValueError(f"environment field '{field_name}' must be a mapping")
    return value


@dataclass(frozen=True)
class AssumptionRef:
    """A reference to one assumption carried by an :class:`Environment`.

    ``kind`` distinguishes a binding assumption from a context assumption;
    ``source`` records who introduced it; ``cel`` is the assumption's CEL form.
    The stable identity is ``assumption_id``.
    """

    assumption_id: AssumptionId
    kind: str
    source: str
    cel: CelExpr

    def __post_init__(self) -> None:
        object.__setattr__(self, "assumption_id", to_assumption_id(self.assumption_id))
        object.__setattr__(self, "cel", to_cel_expr(self.cel))

    def to_dict(self) -> dict[str, Any]:
        return {
            "assumption_id": self.assumption_id,
            "kind": self.kind,
            "source": self.source,
            "cel": self.cel,
        }


@dataclass(frozen=True)
class Environment:
    """The assumption/binding/context frame a world query renders under."""

    bindings: Mapping[str, Any] = field(default_factory=_empty_bindings)
    context_id: ContextId | None = None
    effective_assumptions: tuple[CelExpr, ...] = field(default_factory=tuple)
    assumptions: tuple[AssumptionRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "bindings", dict(self.bindings))
        object.__setattr__(
            self, "effective_assumptions", to_cel_exprs(self.effective_assumptions)
        )
        object.__setattr__(self, "assumptions", tuple(self.assumptions))

    @classmethod
    def from_dict(cls, data: object) -> Environment:
        if data is None:
            return cls()
        if not _is_mapping(data):
            raise ValueError("environment must be a mapping")
        if not data:
            return cls()

        raw_assumptions = data.get("assumptions") or ()
        assumptions: list[AssumptionRef] = []
        for entry in raw_assumptions:
            if isinstance(entry, AssumptionRef):
                assumptions.append(entry)
                continue
            if _is_mapping(entry):
                assumptions.append(
                    AssumptionRef(
                        assumption_id=to_assumption_id(entry["assumption_id"]),
                        kind=str(entry["kind"]),
                        source=str(entry["source"]),
                        cel=to_cel_expr(entry["cel"]),
                    )
                )

        return cls(
            bindings=dict(_optional_mapping(data.get("bindings"), "bindings")),
            context_id=(
                None if data.get("context_id") is None else to_context_id(data["context_id"])
            ),
            effective_assumptions=to_cel_exprs(data.get("effective_assumptions") or ()),
            assumptions=tuple(assumptions),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.bindings:
            data["bindings"] = dict(self.bindings)
        if self.context_id is not None:
            data["context_id"] = self.context_id
        if self.effective_assumptions:
            data["effective_assumptions"] = list(self.effective_assumptions)
        if self.assumptions:
            data["assumptions"] = [assumption.to_dict() for assumption in self.assumptions]
        return data


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
    def parameterizations_for(self, concept_id: str) -> Sequence[ParameterizationEdge]: ...


@runtime_checkable
class ParameterizationCatalogStore(Protocol):
    def all_parameterizations(self) -> Sequence[ParameterizationEdge]: ...


@runtime_checkable
class MicropublicationCatalogStore(Protocol):
    def all_micropublications(self) -> Sequence[ActiveMicropublicationInput]: ...


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
    def all_parameterizations(self) -> Sequence[ParameterizationEdge]: ...
    def all_relationships(self) -> Sequence[RelationEdge]: ...
    def all_claim_stances(self) -> Sequence[Stance]: ...
    def all_micropublications(self) -> Sequence[ActiveMicropublicationInput]: ...
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
    def parameterizations_for(self, concept_id: str) -> Sequence[ParameterizationEdge]: ...
    def group_members(self, concept_id: str) -> list[str]: ...
    def chain_query(
        self,
        target_concept_id: str,
        strategy: Any | None = None,
        **bindings: Any,
    ) -> Any: ...
