"""Data classes, enums, and protocols for the render/store layer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from propstore.world.labelled import (
    AssumptionRef,
    EnvironmentKey,
    Label,
    SupportQuality,
)

if TYPE_CHECKING:
    from propstore.z3_conditions import Z3ConditionSolver


@dataclass
class ValueResult:
    concept_id: str
    status: str  # "determined" | "conflicted" | "underdetermined" | "no_claims"
    claims: list[dict] = field(default_factory=list)
    label: Label | None = None


@dataclass
class DerivedResult:
    concept_id: str
    status: str  # "derived" | "underspecified" | "no_relationship" | "conflicted"
    value: float | None = None
    formula: str | None = None
    input_values: dict[str, float] = field(default_factory=dict)
    exactness: str | None = None
    label: Label | None = None


class ATMSNodeStatus(Enum):
    """ATMS-native node status derived from the propagated label."""

    TRUE = "TRUE"
    IN = "IN"
    OUT = "OUT"


@dataclass(frozen=True)
class ATMSInspection:
    """Inspectible ATMS status plus support-quality honesty metadata."""

    node_id: str
    status: ATMSNodeStatus
    support_quality: SupportQuality
    label: Label | None
    essential_support: EnvironmentKey | None
    reason: str
    claim_id: str | None = None
    kind: str | None = None


class ResolutionStrategy(Enum):
    RECENCY = "recency"
    SAMPLE_SIZE = "sample_size"
    ARGUMENTATION = "argumentation"
    OVERRIDE = "override"


class ReasoningBackend(Enum):
    """Argumentation implementation selector.

    Only consulted inside the ARGUMENTATION resolution strategy to choose
    which argumentation backend to call. The active belief space is computed
    by BoundWorld (Z3 condition solving), not by this enum. `structured_projection`
    is a first structured-argument projection over active claims, and `atms`
    is a global label/nogood propagation backend. Neither is full ASPIC+.
    """

    CLAIM_GRAPH = "claim_graph"
    STRUCTURED_PROJECTION = "structured_projection"
    ATMS = "atms"


@dataclass
class ResolvedResult:
    concept_id: str
    status: str  # "determined" | "conflicted" | "no_claims" | "resolved"
    value: float | str | None = None
    claims: list[dict] = field(default_factory=list)
    winning_claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    label: Label | None = None


@dataclass(frozen=True)
class Environment:
    bindings: Mapping[str, Any] = field(default_factory=dict)
    context_id: str | None = None
    effective_assumptions: tuple[str, ...] = field(default_factory=tuple)
    assumptions: tuple[AssumptionRef, ...] = field(default_factory=tuple)


@dataclass
class SyntheticClaim:
    id: str
    concept_id: str
    type: str = "parameter"
    value: float | str | None = None
    conditions: list[str] = field(default_factory=list)


@dataclass
class ChainStep:
    concept_id: str
    value: float | str | None
    source: str  # "binding" | "claim" | "derived" | "resolved"


@dataclass
class ChainResult:
    target_concept_id: str
    result: ValueResult | DerivedResult
    steps: list[ChainStep] = field(default_factory=list)
    bindings_used: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RenderPolicy:
    """Render-time policy.

    `reasoning_backend` selects the argumentation implementation used when
    `strategy` is ARGUMENTATION. `strategy` chooses a winner among active
    claims when a concept is conflicted at render time.
    """

    reasoning_backend: ReasoningBackend = ReasoningBackend.CLAIM_GRAPH
    strategy: ResolutionStrategy | None = None
    semantics: str = "grounded"
    comparison: str = "elitist"
    confidence_threshold: float = 0.5
    overrides: Mapping[str, str] = field(default_factory=dict)
    concept_strategies: Mapping[str, ResolutionStrategy] = field(default_factory=dict)


@runtime_checkable
class ArtifactStore(Protocol):
    def get_concept(self, concept_id: str) -> dict | None: ...
    def get_claim(self, claim_id: str) -> dict | None: ...
    def resolve_alias(self, alias: str) -> str | None: ...
    def resolve_concept(self, name: str) -> str | None: ...
    def claims_for(self, concept_id: str | None) -> list[dict]: ...
    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]: ...
    def stances_between(self, claim_ids: set[str]) -> list[dict]: ...
    def conflicts(self) -> list[dict]: ...
    def all_concepts(self) -> list[dict]: ...
    def all_parameterizations(self) -> list[dict]: ...
    def all_relationships(self) -> list[dict]: ...
    def all_claim_stances(self) -> list[dict]: ...
    def concept_ids_for_group(self, group_id: int) -> set[str]: ...
    def search(self, query: str) -> list[dict]: ...
    def similar_claims(
        self,
        claim_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[dict]: ...
    def similar_concepts(
        self,
        concept_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[dict]: ...
    def stats(self) -> dict: ...
    def explain(self, claim_id: str) -> list[dict]: ...
    def condition_solver(self) -> Z3ConditionSolver: ...
    def has_table(self, name: str) -> bool: ...
    def parameterizations_for(self, concept_id: str) -> list[dict]: ...
    def group_members(self, concept_id: str) -> list[str]: ...
    def chain_query(
        self,
        target_concept_id: str,
        strategy: ResolutionStrategy | None = None,
        **bindings: Any,
    ) -> ChainResult: ...


@runtime_checkable
class BeliefSpace(Protocol):
    def active_claims(self, concept_id: str | None = None) -> list[dict]: ...
    def inactive_claims(self, concept_id: str | None = None) -> list[dict]: ...
    def value_of(self, concept_id: str) -> ValueResult: ...
    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: dict[str, float | str | None] | None = None,
    ) -> DerivedResult: ...
    def resolved_value(self, concept_id: str) -> ResolvedResult: ...
    def is_determined(self, concept_id: str) -> bool: ...
    def conflicts(self, concept_id: str | None = None) -> list[dict]: ...
    def explain(self, claim_id: str) -> list[dict]: ...
