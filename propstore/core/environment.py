"""Core environment and store protocol types.

Moved from world/types.py to fix the inverted layer dependency
(core must not import from world).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from propstore.cel_types import CelExpr, to_cel_expr, to_cel_exprs
from propstore.core.id_types import ContextId, to_assumption_id, to_context_id
from propstore.core.labels import AssumptionRef
from propstore.core.micropublications import ActiveMicropublicationInput
from propstore.core.store_results import (
    WorldStoreStats,
    ClaimSimilarityHit,
    ConceptSearchHit,
    ConceptSimilarityHit,
)
from propstore.core.row_types import (
    ClaimRowInput,
    ConceptRowInput,
    ConflictRowInput,
    ParameterizationRowInput,
    RelationshipRowInput,
    StanceRowInput,
)


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"environment field '{field_name}' must be a mapping")
    return value


if TYPE_CHECKING:
    from propstore.core.graph_types import CompiledWorldGraph
    from propstore.core.conditions.solver import ConditionSolver


@dataclass(frozen=True)
class Environment:
    bindings: Mapping[str, Any] = field(default_factory=dict)
    context_id: ContextId | None = None
    effective_assumptions: tuple[CelExpr, ...] = field(default_factory=tuple)
    assumptions: tuple[AssumptionRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "bindings", dict(self.bindings))
        object.__setattr__(
            self,
            "effective_assumptions",
            to_cel_exprs(self.effective_assumptions),
        )
        object.__setattr__(self, "assumptions", tuple(self.assumptions))

    @classmethod
    def from_dict(cls, data: object) -> Environment:
        if data is None:
            return cls()
        if not isinstance(data, Mapping):
            raise ValueError("environment must be a mapping")
        if not data:
            return cls()

        raw_assumptions = data.get("assumptions") or ()
        assumptions: list[AssumptionRef] = []
        for entry in raw_assumptions:
            if isinstance(entry, AssumptionRef):
                assumptions.append(entry)
                continue
            if isinstance(entry, Mapping):
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
                None
                if data.get("context_id") is None
                else to_context_id(data["context_id"])
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
            data["assumptions"] = [
                {
                    "assumption_id": assumption.assumption_id,
                    "kind": assumption.kind,
                    "source": assumption.source,
                    "cel": assumption.cel,
                }
                for assumption in self.assumptions
            ]
        return data


@runtime_checkable
class StanceStore(Protocol):
    def stances_between(self, claim_ids: set[str]) -> Sequence[StanceRowInput]: ...


@runtime_checkable
class ClaimCatalogStore(Protocol):
    def claims_for(self, concept_id: str | None) -> Sequence[ClaimRowInput]: ...


@runtime_checkable
class ClaimLookupStore(Protocol):
    def get_claim(self, claim_id: str) -> ClaimRowInput | None: ...


@runtime_checkable
class ConceptCatalogStore(Protocol):
    def all_concepts(self) -> Sequence[ConceptRowInput]: ...


@runtime_checkable
class RelationshipCatalogStore(Protocol):
    def all_relationships(self) -> Sequence[RelationshipRowInput]: ...


@runtime_checkable
class ExplanationStore(Protocol):
    def explain(self, claim_id: str) -> Sequence[StanceRowInput]: ...


@runtime_checkable
class ClaimStanceInventoryStore(Protocol):
    def all_claim_stances(self) -> Sequence[StanceRowInput]: ...


@runtime_checkable
class ConflictStore(Protocol):
    def conflicts(self) -> Sequence[ConflictRowInput]: ...


@runtime_checkable
class ParameterizationLookupStore(Protocol):
    def parameterizations_for(self, concept_id: str) -> Sequence[ParameterizationRowInput]: ...


@runtime_checkable
class ParameterizationCatalogStore(Protocol):
    def all_parameterizations(self) -> Sequence[ParameterizationRowInput]: ...


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
    def get_concept(self, concept_id: str) -> ConceptRowInput | None: ...
    def get_claim(self, claim_id: str) -> ClaimRowInput | None: ...
    def resolve_alias(self, alias: str) -> str | None: ...
    def resolve_concept(self, name: str) -> str | None: ...
    def resolve_claim(self, name: str) -> str | None: ...
    def claims_for(self, concept_id: str | None) -> Sequence[ClaimRowInput]: ...
    def claims_by_ids(self, claim_ids: set[str]) -> Mapping[str, ClaimRowInput]: ...
    def stances_between(self, claim_ids: set[str]) -> Sequence[StanceRowInput]: ...
    def conflicts(self) -> Sequence[ConflictRowInput]: ...
    def all_concepts(self) -> Sequence[ConceptRowInput]: ...
    def all_parameterizations(self) -> Sequence[ParameterizationRowInput]: ...
    def all_relationships(self) -> Sequence[RelationshipRowInput]: ...
    def all_claim_stances(self) -> Sequence[StanceRowInput]: ...
    def all_micropublications(self) -> Sequence[ActiveMicropublicationInput]: ...
    def concept_ids_for_group(self, group_id: int) -> set[str]: ...
    def search(self, query: str) -> list[ConceptSearchHit]: ...
    def similar_claims(
        self,
        claim_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[ClaimSimilarityHit]: ...
    def similar_concepts(
        self,
        concept_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[ConceptSimilarityHit]: ...
    def stats(self) -> WorldStoreStats: ...
    def explain(self, claim_id: str) -> Sequence[StanceRowInput]: ...
    def condition_solver(self) -> ConditionSolver: ...
    def has_table(self, name: str) -> bool: ...
    def parameterizations_for(self, concept_id: str) -> Sequence[ParameterizationRowInput]: ...
    def group_members(self, concept_id: str) -> list[str]: ...
    def chain_query(
        self,
        target_concept_id: str,
        strategy: Any | None = None,
        **bindings: Any,
    ) -> Any: ...
