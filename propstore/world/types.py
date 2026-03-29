"""Data classes, enums, and protocols for the render/store layer."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any, Protocol, TypedDict, runtime_checkable

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


class ATMSFutureEnvironmentReport(TypedDict):
    queryable_ids: list[str]
    queryable_cels: list[str]
    environment: list[str]
    consistent: bool
    supported_claim_ids: list[str]
    nogoods: list[list[str]]


class ATMSNodeFutureStatusEntry(TypedDict):
    queryable_ids: list[str]
    queryable_cels: list[str]
    environment: list[str]
    consistent: bool
    status: ATMSNodeStatus
    out_kind: ATMSOutKind | None
    reason: str
    support_quality: SupportQuality
    essential_support: list[str]


class ATMSConceptFutureStatusEntry(TypedDict):
    queryable_ids: list[str]
    queryable_cels: list[str]
    environment: list[str]
    consistent: bool
    status: str
    supported_claim_ids: list[str]


class ATMSFutureStatusReport(TypedDict):
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    could_become_in: bool
    could_become_out: bool
    futures: list[ATMSNodeFutureStatusEntry]


class ATMSWhyOutReport(TypedDict):
    node_id: str
    claim_id: str | None
    status: ATMSNodeStatus
    out_kind: ATMSOutKind | None
    reason: str
    support_quality: SupportQuality
    future_activatable: bool
    candidate_queryable_cels: list[list[str]]


class ATMSNodeStabilityReport(TypedDict):
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    stable: bool
    limit: int
    future_count: int
    consistent_future_count: int
    inconsistent_future_count: int
    witnesses: list[ATMSNodeFutureStatusEntry]


class ATMSConceptStabilityReport(TypedDict):
    concept_id: str
    current_status: str
    stable: bool
    limit: int
    future_count: int
    consistent_future_count: int
    inconsistent_future_count: int
    witnesses: list[ATMSConceptFutureStatusEntry]


class ATMSNodeRelevanceState(TypedDict):
    queryable_ids: list[str]
    queryable_cels: list[str]
    environment: list[str]
    consistent: bool
    status: ATMSNodeStatus


class ATMSConceptRelevanceState(TypedDict):
    queryable_ids: list[str]
    queryable_cels: list[str]
    environment: list[str]
    consistent: bool
    status: str


ATMSNodeWitnessPair = TypedDict(
    "ATMSNodeWitnessPair",
    {
        "queryable_id": str,
        "queryable_cel": str,
        "without": ATMSNodeRelevanceState,
        "with": ATMSNodeRelevanceState,
    },
)

ATMSConceptWitnessPair = TypedDict(
    "ATMSConceptWitnessPair",
    {
        "queryable_id": str,
        "queryable_cel": str,
        "without": ATMSConceptRelevanceState,
        "with": ATMSConceptRelevanceState,
    },
)


class ATMSNodeRelevanceReport(TypedDict):
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    current_status: ATMSNodeStatus
    relevant_queryables: list[str]
    irrelevant_queryables: list[str]
    witness_pairs: dict[str, list[ATMSNodeWitnessPair]]


class ATMSConceptRelevanceReport(TypedDict):
    concept_id: str
    current_status: str
    relevant_queryables: list[str]
    irrelevant_queryables: list[str]
    witness_pairs: dict[str, list[ATMSConceptWitnessPair]]


class ATMSNodeInterventionPlan(TypedDict):
    target: str
    node_id: str
    claim_id: str | None
    current_status: ATMSNodeStatus
    target_status: ATMSNodeStatus
    queryable_ids: list[str]
    queryable_cels: list[str]
    environment: list[str]
    consistent: bool
    result_status: ATMSNodeStatus
    result_out_kind: ATMSOutKind | None
    minimality_basis: str


class ATMSConceptInterventionPlan(TypedDict):
    target: str
    concept_id: str
    current_status: str
    target_status: str
    queryable_ids: list[str]
    queryable_cels: list[str]
    environment: list[str]
    consistent: bool
    result_status: str
    minimality_basis: str


class ATMSNextQuerySuggestion(TypedDict):
    queryable_id: str
    queryable_cel: str
    plan_count: int
    smallest_plan_size: int
    plan_queryable_cels: list[list[str]]
    example_plans: list[ATMSNodeInterventionPlan | ATMSConceptInterventionPlan]


class ResolutionStrategy(StrEnum):
    RECENCY = "recency"
    SAMPLE_SIZE = "sample_size"
    ARGUMENTATION = "argumentation"
    OVERRIDE = "override"
    IC_MERGE = "ic_merge"


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


class ArgumentationSemantics(StrEnum):
    """Canonical semantics names exposed by argumentation-capable backends."""

    GROUNDED = "grounded"
    LEGACY_GROUNDED = "legacy_grounded"
    HYBRID_GROUNDED = "hybrid-grounded"
    BIPOLAR_GROUNDED = "bipolar-grounded"
    PREFERRED = "preferred"
    STABLE = "stable"
    D_PREFERRED = "d-preferred"
    S_PREFERRED = "s-preferred"
    C_PREFERRED = "c-preferred"
    BIPOLAR_STABLE = "bipolar-stable"
    COMPLETE = "complete"


_ARGUMENTATION_SEMANTICS_ALIASES: dict[str, ArgumentationSemantics] = {
    ArgumentationSemantics.GROUNDED.value: ArgumentationSemantics.GROUNDED,
    ArgumentationSemantics.LEGACY_GROUNDED.value: ArgumentationSemantics.LEGACY_GROUNDED,
    "hybrid_grounded": ArgumentationSemantics.HYBRID_GROUNDED,
    ArgumentationSemantics.HYBRID_GROUNDED.value: ArgumentationSemantics.HYBRID_GROUNDED,
    ArgumentationSemantics.BIPOLAR_GROUNDED.value: ArgumentationSemantics.BIPOLAR_GROUNDED,
    ArgumentationSemantics.PREFERRED.value: ArgumentationSemantics.PREFERRED,
    ArgumentationSemantics.STABLE.value: ArgumentationSemantics.STABLE,
    ArgumentationSemantics.D_PREFERRED.value: ArgumentationSemantics.D_PREFERRED,
    ArgumentationSemantics.S_PREFERRED.value: ArgumentationSemantics.S_PREFERRED,
    ArgumentationSemantics.C_PREFERRED.value: ArgumentationSemantics.C_PREFERRED,
    "bipolar_stable": ArgumentationSemantics.BIPOLAR_STABLE,
    ArgumentationSemantics.BIPOLAR_STABLE.value: ArgumentationSemantics.BIPOLAR_STABLE,
    ArgumentationSemantics.COMPLETE.value: ArgumentationSemantics.COMPLETE,
}

_CLI_ARGUMENTATION_SEMANTICS = (
    ArgumentationSemantics.GROUNDED,
    ArgumentationSemantics.LEGACY_GROUNDED,
    ArgumentationSemantics.HYBRID_GROUNDED,
    ArgumentationSemantics.BIPOLAR_GROUNDED,
    ArgumentationSemantics.PREFERRED,
    ArgumentationSemantics.STABLE,
    ArgumentationSemantics.D_PREFERRED,
    ArgumentationSemantics.S_PREFERRED,
    ArgumentationSemantics.C_PREFERRED,
    ArgumentationSemantics.BIPOLAR_STABLE,
    ArgumentationSemantics.COMPLETE,
)

_BACKEND_SEMANTICS: dict[ReasoningBackend, frozenset[ArgumentationSemantics]] = {
    ReasoningBackend.CLAIM_GRAPH: frozenset({
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.LEGACY_GROUNDED,
        ArgumentationSemantics.HYBRID_GROUNDED,
        ArgumentationSemantics.BIPOLAR_GROUNDED,
        ArgumentationSemantics.PREFERRED,
        ArgumentationSemantics.STABLE,
        ArgumentationSemantics.D_PREFERRED,
        ArgumentationSemantics.S_PREFERRED,
        ArgumentationSemantics.C_PREFERRED,
        ArgumentationSemantics.BIPOLAR_STABLE,
    }),
    ReasoningBackend.STRUCTURED_PROJECTION: frozenset({
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.HYBRID_GROUNDED,
        ArgumentationSemantics.PREFERRED,
        ArgumentationSemantics.STABLE,
    }),
    ReasoningBackend.ASPIC: frozenset({
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.HYBRID_GROUNDED,
        ArgumentationSemantics.PREFERRED,
        ArgumentationSemantics.STABLE,
    }),
    ReasoningBackend.ATMS: frozenset({
        ArgumentationSemantics.GROUNDED,
    }),
    ReasoningBackend.PRAF: frozenset({
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.HYBRID_GROUNDED,
        ArgumentationSemantics.PREFERRED,
        ArgumentationSemantics.STABLE,
        ArgumentationSemantics.COMPLETE,
    }),
}


def normalize_reasoning_backend(value: ReasoningBackend | str) -> ReasoningBackend:
    if isinstance(value, ReasoningBackend):
        return value
    try:
        return ReasoningBackend(str(value))
    except ValueError as exc:
        raise ValueError(f"Unknown reasoning_backend '{value}'") from exc


def normalize_argumentation_semantics(
    value: ArgumentationSemantics | str,
) -> ArgumentationSemantics:
    if isinstance(value, ArgumentationSemantics):
        return value
    normalized = _ARGUMENTATION_SEMANTICS_ALIASES.get(str(value))
    if normalized is None:
        raise ValueError(f"Unknown semantics: {value}")
    return normalized


def cli_argumentation_semantics_values() -> tuple[str, ...]:
    return tuple(semantics.value for semantics in _CLI_ARGUMENTATION_SEMANTICS)


def supported_argumentation_semantics(
    backend: ReasoningBackend | str,
) -> frozenset[ArgumentationSemantics]:
    normalized_backend = normalize_reasoning_backend(backend)
    return _BACKEND_SEMANTICS[normalized_backend]


def validate_backend_semantics(
    backend: ReasoningBackend | str,
    semantics: ArgumentationSemantics | str,
    *,
    hybrid_graph: bool = False,
) -> tuple[ReasoningBackend, ArgumentationSemantics]:
    normalized_backend = normalize_reasoning_backend(backend)
    normalized_semantics = normalize_argumentation_semantics(semantics)
    supported = supported_argumentation_semantics(normalized_backend)
    if normalized_semantics not in supported:
        supported_names = ", ".join(item.value for item in sorted(supported, key=str))
        raise ValueError(
            f"{normalized_backend.value} does not support semantics "
            f"'{normalized_semantics.value}'; supported semantics: {supported_names}"
        )
    if (
        normalized_backend == ReasoningBackend.CLAIM_GRAPH
        and normalized_semantics == ArgumentationSemantics.GROUNDED
        and hybrid_graph
    ):
        raise ValueError(
            "grounded is ambiguous for hybrid claim graphs; "
            "use legacy_grounded or explicit bipolar semantics such as "
            "d-preferred, s-preferred, or c-preferred."
        )
    return normalized_backend, normalized_semantics


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
    semantics: ArgumentationSemantics = ArgumentationSemantics.GROUNDED
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
    # IC merge fields (Konieczny & Pino Pérez 2002)
    # merge_operator selects distance aggregation: "sigma" (majority), "max"
    # (quasi-merge), or "gmax" (arbitration).
    merge_operator: str = "sigma"
    # branch_filter restricts which branches are included as sources.
    branch_filter: tuple[str, ...] | None = None
    # branch_weights assigns per-branch importance weights.
    branch_weights: Mapping[str, float] | None = None
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
            "semantics",
            normalize_argumentation_semantics(self.semantics),
        )
        if self.merge_operator not in ("sigma", "max", "gmax"):
            raise ValueError(
                f"RenderPolicy.merge_operator must be 'sigma', 'max', or 'gmax', "
                f"got '{self.merge_operator}'"
            )
        if self.branch_filter is not None:
            object.__setattr__(
                self,
                "branch_filter",
                tuple(self.branch_filter),
            )
        if self.branch_weights is not None:
            object.__setattr__(
                self,
                "branch_weights",
                dict(self.branch_weights),
            )
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
        reasoning_backend = normalize_reasoning_backend(reasoning_backend_value)
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
            semantics=normalize_argumentation_semantics(
                data.get("semantics", ArgumentationSemantics.GROUNDED)
            ),
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
            merge_operator=str(data.get("merge_operator", "sigma")),
            branch_filter=(
                None
                if data.get("branch_filter") is None
                else tuple(data["branch_filter"])
            ),
            branch_weights=(
                None
                if data.get("branch_weights") is None
                else dict(data["branch_weights"])
            ),
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
        if self.semantics != ArgumentationSemantics.GROUNDED:
            data["semantics"] = self.semantics.value
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
        if self.merge_operator != "sigma":
            data["merge_operator"] = self.merge_operator
        if self.branch_filter is not None:
            data["branch_filter"] = list(self.branch_filter)
        if self.branch_weights is not None:
            data["branch_weights"] = dict(self.branch_weights)
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


SupportMetadata = Mapping[str, tuple[Label | None, SupportQuality]]


@runtime_checkable
class ClaimSupportView(Protocol):
    def claim_support(self, claim: dict[str, Any]) -> tuple[Label | None, SupportQuality]: ...


@runtime_checkable
class ATMSEngineView(Protocol):
    def supported_claim_ids(self, concept_id: str | None = None) -> set[str]: ...
    def argumentation_state(
        self,
        *,
        queryables: tuple[str, ...] | list[str],
        future_limit: int,
    ) -> dict[str, Any]: ...


@runtime_checkable
class HasATMSEngine(Protocol):
    def atms_engine(self) -> ATMSEngineView: ...


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
