"""Data classes, enums, and protocols for the render/store layer."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from propstore.core.environment import ArtifactStore, Environment  # noqa: F401
from propstore.core.labels import (
    AssumptionRef,
    EnvironmentKey,
    Label,
)
from propstore.world.labelled import SupportQuality

if TYPE_CHECKING:
    from propstore.z3_conditions import Z3ConditionSolver


class ValueStatus(StrEnum):
    """Status of a value/derived/resolved result.

    Because StrEnum subclasses str, ``ValueStatus.DETERMINED == "determined"``
    is True — all existing string comparisons keep working with zero migration.
    """

    DETERMINED = "determined"
    CONFLICTED = "conflicted"
    NO_CLAIMS = "no_claims"
    NO_VALUES = "no_values"
    UNDERDETERMINED = "underdetermined"
    DERIVED = "derived"
    NO_RELATIONSHIP = "no_relationship"
    UNDERSPECIFIED = "underspecified"
    RESOLVED = "resolved"


@dataclass
class ValueResult:
    concept_id: str
    status: ValueStatus
    claims: list[dict] = field(default_factory=list)
    label: Label | None = None


@dataclass
class DerivedResult:
    concept_id: str
    status: ValueStatus
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


class ATMSOutKind(Enum):
    """Why an ATMS node is currently OUT."""

    MISSING_SUPPORT = "missing_support"
    NOGOOD_PRUNED = "nogood_pruned"


@dataclass(frozen=True, order=True)
class QueryableAssumption:
    """Future/queryable assumption available only to bounded future analysis."""

    assumption_id: str
    cel: str
    kind: str = "queryable"
    source: str = "future"

    @classmethod
    def from_cel(
        cls,
        cel: str,
        *,
        source: str = "future",
    ) -> QueryableAssumption:
        digest = hashlib.sha1(f"queryable\0{source}\0{cel}".encode("utf-8")).hexdigest()[:12]
        return cls(
            assumption_id=f"queryable:{source}:{digest}",
            cel=cel,
            source=source,
        )


@dataclass(frozen=True)
class ATMSInspection:
    """Inspectible ATMS status plus support-quality honesty metadata."""

    node_id: str
    status: ATMSNodeStatus
    support_quality: SupportQuality
    label: Label | None
    essential_support: EnvironmentKey | None
    reason: str
    out_kind: ATMSOutKind | None = None
    claim_id: str | None = None
    kind: str | None = None


class ResolutionStrategy(StrEnum):
    RECENCY = "recency"
    SAMPLE_SIZE = "sample_size"
    ARGUMENTATION = "argumentation"
    OVERRIDE = "override"


class ReasoningBackend(StrEnum):
    """Argumentation implementation selector.

    Only consulted inside the ARGUMENTATION resolution strategy to choose
    which argumentation backend to call. The active belief space is computed
    by BoundWorld (Z3 condition solving), not by this enum. `structured_projection`
    is a first structured-argument projection over active claims, `aspic`
    uses the full ASPIC+ engine via aspic_bridge.py, and `atms`
    is a global label/nogood propagation backend.
    """

    CLAIM_GRAPH = "claim_graph"
    STRUCTURED_PROJECTION = "structured_projection"
    ASPIC = "aspic"
    ATMS = "atms"
    PRAF = "praf"


@dataclass
class ResolvedResult:
    concept_id: str
    status: ValueStatus
    value: float | str | None = None
    claims: list[dict] = field(default_factory=list)
    winning_claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    label: Label | None = None
    acceptance_probs: dict[str, float] | None = None


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
    unresolved_dependencies: list[str] = field(default_factory=list)


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
    link: str = "last"
    # Decision criterion for interpreting opinion uncertainty at render time
    # Per Denoeux (2019, p.17-18): pignistic is the default (E(ω) = b + a·u)
    decision_criterion: str = "pignistic"
    # Hurwicz pessimism index α ∈ [0,1] — only used when criterion="hurwicz"
    # α=1.0 → pessimistic (lower bound), α=0.0 → optimistic (upper bound)
    # Per Denoeux (2019, p.17)
    pessimism_index: float = 0.5
    # Whether to include [Bel, Pl] uncertainty interval in output
    # Per Jøsang (2001, p.4): interval endpoints Bel=b, Pl=1-d
    show_uncertainty_interval: bool = False
    # PrAF-specific fields (Li et al. 2012, Popescu 2024)
    # All with defaults for backward compatibility.
    praf_strategy: str = "auto"  # "auto", "mc", "exact", "dfquad_quad", "dfquad_baf"
    praf_mc_epsilon: float = 0.01  # MC error tolerance (Li 2012, p.8)
    praf_mc_confidence: float = 0.95  # MC confidence level
    praf_treewidth_cutoff: int = 12  # max treewidth for exact DP (Popescu 2024, p.8)
    praf_mc_seed: int | None = None  # RNG seed (None = random)
    # When True, conflict-detected claim pairs produce synthetic rebuts stances
    # even if the claims already participate in other stance relationships.
    # Default False preserves legacy suppression behavior; True is the principled
    # non-commitment choice (render-time policy, not build-time filter).
    include_conflict_stances: bool = False
    future_queryables: tuple[str, ...] = field(default_factory=tuple)
    future_limit: int | None = None
    overrides: Mapping[str, str] = field(default_factory=dict)
    concept_strategies: Mapping[str, ResolutionStrategy] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.reasoning_backend, ReasoningBackend):
            raise TypeError("RenderPolicy.reasoning_backend must be a ReasoningBackend")
        if self.strategy is not None and not isinstance(self.strategy, ResolutionStrategy):
            raise TypeError("RenderPolicy.strategy must be a ResolutionStrategy or None")
        object.__setattr__(
            self,
            "future_queryables",
            tuple(self.future_queryables),
        )
        object.__setattr__(self, "overrides", dict(self.overrides))
        concept_strategies: dict[str, ResolutionStrategy] = {}
        for concept_id, strategy in self.concept_strategies.items():
            if not isinstance(strategy, ResolutionStrategy):
                raise TypeError(
                    "RenderPolicy.concept_strategies values must be ResolutionStrategy"
                )
            concept_strategies[concept_id] = strategy
        object.__setattr__(
            self,
            "concept_strategies",
            concept_strategies,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> RenderPolicy:
        if not data:
            return cls()

        strategy_value = data.get("strategy")
        reasoning_backend_value = data.get("reasoning_backend", ReasoningBackend.CLAIM_GRAPH)
        try:
            reasoning_backend = (
                reasoning_backend_value
                if isinstance(reasoning_backend_value, ReasoningBackend)
                else ReasoningBackend(str(reasoning_backend_value))
            )
        except ValueError as exc:
            raise ValueError(
                f"Unknown reasoning_backend '{reasoning_backend_value}'"
            ) from exc
        concept_strategies = {
            str(concept_id): (
                strategy
                if isinstance(strategy, ResolutionStrategy)
                else ResolutionStrategy(str(strategy))
            )
            for concept_id, strategy in (data.get("concept_strategies") or {}).items()
        }
        return cls(
            reasoning_backend=reasoning_backend,
            strategy=(
                None
                if strategy_value is None
                else (
                    strategy_value
                    if isinstance(strategy_value, ResolutionStrategy)
                    else ResolutionStrategy(str(strategy_value))
                )
            ),
            semantics=str(data.get("semantics", "grounded")),
            comparison=str(data.get("comparison", "elitist")),
            link=str(data.get("link", "last")),
            decision_criterion=str(data.get("decision_criterion", "pignistic")),
            pessimism_index=float(data.get("pessimism_index", 0.5)),
            show_uncertainty_interval=bool(data.get("show_uncertainty_interval", False)),
            praf_strategy=str(data.get("praf_strategy", "auto")),
            praf_mc_epsilon=float(data.get("praf_mc_epsilon", 0.01)),
            praf_mc_confidence=float(data.get("praf_mc_confidence", 0.95)),
            praf_treewidth_cutoff=int(data.get("praf_treewidth_cutoff", 12)),
            praf_mc_seed=(
                None
                if data.get("praf_mc_seed") is None
                else int(data["praf_mc_seed"])
            ),
            include_conflict_stances=bool(data.get("include_conflict_stances", False)),
            future_queryables=tuple(data.get("future_queryables") or ()),
            future_limit=(
                None
                if data.get("future_limit") is None
                else int(data["future_limit"])
            ),
            overrides=dict(data.get("overrides") or {}),
            concept_strategies=concept_strategies,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.reasoning_backend != ReasoningBackend.CLAIM_GRAPH:
            data["reasoning_backend"] = self.reasoning_backend.value
        if self.strategy is not None:
            data["strategy"] = self.strategy.value
        if self.semantics != "grounded":
            data["semantics"] = self.semantics
        if self.comparison != "elitist":
            data["comparison"] = self.comparison
        if self.link != "last":
            data["link"] = self.link
        if self.decision_criterion != "pignistic":
            data["decision_criterion"] = self.decision_criterion
        if self.pessimism_index != 0.5:
            data["pessimism_index"] = self.pessimism_index
        if self.show_uncertainty_interval:
            data["show_uncertainty_interval"] = self.show_uncertainty_interval
        if self.praf_strategy != "auto":
            data["praf_strategy"] = self.praf_strategy
        if self.praf_mc_epsilon != 0.01:
            data["praf_mc_epsilon"] = self.praf_mc_epsilon
        if self.praf_mc_confidence != 0.95:
            data["praf_mc_confidence"] = self.praf_mc_confidence
        if self.praf_treewidth_cutoff != 12:
            data["praf_treewidth_cutoff"] = self.praf_treewidth_cutoff
        if self.praf_mc_seed is not None:
            data["praf_mc_seed"] = self.praf_mc_seed
        if self.include_conflict_stances:
            data["include_conflict_stances"] = self.include_conflict_stances
        if self.future_queryables:
            data["future_queryables"] = list(self.future_queryables)
        if self.future_limit is not None:
            data["future_limit"] = self.future_limit
        if self.overrides:
            data["overrides"] = dict(self.overrides)
        if self.concept_strategies:
            data["concept_strategies"] = {
                concept_id: strategy.value
                for concept_id, strategy in self.concept_strategies.items()
            }
        return data


def apply_decision_criterion(
    opinion_b: float | None,
    opinion_d: float | None,
    opinion_u: float | None,
    opinion_a: float | None,
    confidence: float | None,
    criterion: str = "pignistic",
    pessimism_index: float = 0.5,
) -> float | None:
    """Apply decision criterion to opinion data, falling back to raw confidence.

    Per Denoeux (2019, p.17-18): decision criteria determine how belief
    function uncertainty maps to actionable values at render time.

    Args:
        opinion_b/d/u/a: Opinion components (may be None for old data)
        confidence: Scalar fallback (existing backward-compat field)
        criterion: One of "pignistic", "lower_bound", "upper_bound", "hurwicz"
        pessimism_index: α for Hurwicz criterion

    Returns:
        Decision value, or None if no opinion or confidence available.
    """
    # If opinion components are all present, compute from opinion
    if (
        opinion_b is not None
        and opinion_d is not None
        and opinion_u is not None
        and opinion_a is not None
    ):
        if criterion == "pignistic":
            # Jøsang (2001, p.5, Def 6): E(ω) = b + a·u
            return opinion_b + opinion_a * opinion_u
        elif criterion == "lower_bound":
            # Jøsang (2001, p.4): Bel(x) = b
            return opinion_b
        elif criterion == "upper_bound":
            # Jøsang (2001, p.4): Pl(x) = 1 - d
            return 1.0 - opinion_d
        elif criterion == "hurwicz":
            # Denoeux (2019, p.17): α·Bel + (1-α)·Pl
            bel = opinion_b
            pl = 1.0 - opinion_d
            return pessimism_index * bel + (1.0 - pessimism_index) * pl
        else:
            raise ValueError(f"Unknown decision criterion: {criterion!r}")

    # Fall back to raw confidence when opinion is missing (old data)
    return confidence


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
