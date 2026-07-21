"""Data classes, enums, and protocols for the world/render layer.

This module is the shared spine of the world layer: every other ``world``
module imports its result types, the canonical :class:`RenderPolicy`, the ATMS
inspection/report types, and the belief-space protocols from here. It is kept as
one module on purpose — the B/C slice labels in ``reports/scout-p7w-map.md``
describe which tests gate which types, not a file split, and several types
(``ValueStatus``, ``ValueResult``, ``DerivedResult``, ``BeliefSpace``,
``RenderPolicy``, ``ResolutionStrategy``, ``QueryableAssumption``) are shared by
both halves.

Substrate boundary: ``CelExpr`` comes from ``condition_ir``; the
assignment-selection merge operator comes from the ``assignment_selection``
package (one canonical spelling, no propstore mirror). The label algebra
(``Label``/``EnvironmentKey``/``SupportQuality``/``SupportMetadata``/
``AssumptionRef``) is re-exported from ``propstore.core`` which itself re-exports
the carved provenance-semiring algebra.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import (
    TYPE_CHECKING,
    Literal,
    Protocol,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)

from assignment_selection import MergeOperator
from condition_ir import CelExpr, to_cel_expr, to_cel_exprs

from propstore.conflict_detector import ConflictClass
from propstore.core.active_claims import ActiveClaim
from propstore.core.atms_reports import (
    ATMSFutureStatusReport,
    ATMSInspection,
    ATMSNodeFutureStatusEntry,
    ATMSNodeRelevanceReport,
    ATMSNodeRelevanceState,
    ATMSNodeStabilityReport,
    ATMSNodeStatus,
    ATMSNodeWitnessPair,
    ATMSNogoodDetail,
    ATMSNogoodProvenanceDetail,
    ATMSOutKind,
    ATMSWhyOutReport,
    SerializedEnvironment,
)
from propstore.core.environment import AssumptionRef, Environment, WorldStore
from propstore.core.id_types import (
    AssumptionId,
    ClaimId,
    ConceptId,
    QueryableId,
    to_concept_id,
    to_queryable_id,
)
from propstore.core.labels import (
    EnvironmentKey,
    Label,
    SupportMetadata,
    SupportQuality,
)
from propstore.core.reasoning import (
    ArgumentationSemantics,
    ReasoningBackend,
    cli_argumentation_semantics_values,
    normalize_argumentation_semantics,
    normalize_reasoning_backend,
    supported_argumentation_semantics,
    validate_backend_semantics,
)
from propstore.core.render_policy import (
    IntegrityConstraint,
    IntegrityConstraintKind,
    RenderPolicy,
    ResolutionStrategy,
    normalize_merge_operator,
)
from propstore.core.store_results import (
    ClaimSimilarityHit,
    ConceptSearchHit,
    ConceptSimilarityHit,
    WorldStoreStats,
)
from propstore.families.claims import ClaimType, Exactness
from propstore.families.concepts import ConceptStatus
from propstore.worldline.result_types import WorldlineArgumentationState

if TYPE_CHECKING:
    from propstore.conflict_detector.models import ConflictRecord
    from propstore.core.graph_types import ActiveWorldGraph
    from propstore.families.claims import Claim
    from propstore.families.relations import Stance
    from propstore.grounding.bundle import GroundedRulesBundle
    from propstore.support_revision.state import RevisionScope

_T = TypeVar("_T")


def _tuple(values: Iterable[_T]) -> tuple[_T, ...]:
    return tuple(values)


def _tuple_of_tuples(values: Iterable[Iterable[_T]]) -> tuple[tuple[_T, ...], ...]:
    return tuple(tuple(value) for value in values)


def _coerce_claim_type(value: object) -> ClaimType:
    if isinstance(value, ClaimType):
        return value
    return ClaimType(str(value))


class ValueStatus(StrEnum):
    """Status of a value/derived/resolved result.

    Because StrEnum subclasses str, ``ValueStatus.DETERMINED == "determined"``
    is True — all existing string comparisons keep working with zero migration.
    """

    DETERMINED = "determined"
    CONFLICTED = "conflicted"
    NO_CLAIMS = "no_claims"
    NO_VALUES = "no_values"
    DERIVED = "derived"
    NO_RELATIONSHIP = "no_relationship"
    UNDERSPECIFIED = "underspecified"
    RESOLVED = "resolved"


class ValueResultReason(Enum):
    """Typed annotation for *why* a ``ValueResult`` carries a non-trivial status.

    Deliberately a plain ``Enum`` (not ``StrEnum``) so that comparisons are
    identity-based and no string interop is possible. New variants may be
    added as other structured failure classes arise; start intentionally
    narrow.
    """

    ALGORITHM_UNPARSEABLE = "algorithm_unparseable"


def coerce_value_status(value: object) -> ValueStatus:
    if isinstance(value, ValueStatus):
        return value
    return ValueStatus(str(value))


@dataclass
class ValueResult:
    concept_id: ConceptId
    status: ValueStatus
    claims: tuple[ActiveClaim, ...] = field(default_factory=tuple)
    label: Label | None = None
    reason: ValueResultReason | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.status = coerce_value_status(self.status)
        self.claims = tuple(self.claims)


@dataclass
class DerivedResult:
    concept_id: ConceptId
    status: ValueStatus
    value: float | None = None
    formula: str | None = None
    input_values: dict[ConceptId, float] = field(default_factory=dict[ConceptId, float])
    exactness: Exactness | None = None
    label: Label | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.status = coerce_value_status(self.status)
        self.input_values = {
            to_concept_id(concept_id): float(value)
            for concept_id, value in self.input_values.items()
        }


@dataclass(frozen=True, order=True)
class QueryableAssumption:
    """Future/queryable assumption available only to bounded future analysis."""

    assumption_id: QueryableId
    cel: CelExpr
    kind: str = "queryable"
    source: str = "future"

    @classmethod
    def from_cel(
        cls,
        cel: str | CelExpr,
        *,
        source: str = "future",
    ) -> QueryableAssumption:
        normalized_cel = to_cel_expr(cel)
        digest = hashlib.sha256(
            f"queryable\0{source}\0{normalized_cel}".encode("utf-8")
        ).hexdigest()
        return cls(
            assumption_id=to_queryable_id(f"queryable:{source}:{digest}"),
            cel=normalized_cel,
            source=source,
        )


QueryableInput: TypeAlias = QueryableAssumption | str | CelExpr


def normalize_queryable_cel(queryable: str | CelExpr) -> CelExpr:
    queryable_text = str(queryable)
    if any(
        operator in queryable_text for operator in ("==", "!=", ">=", "<=", ">", "<")
    ):
        return to_cel_expr(queryable_text)
    if "=" in queryable_text:
        key, _, value = queryable_text.partition("=")
        return to_cel_expr(f"{key} == '{value}'")
    return to_cel_expr(queryable_text)


def coerce_queryable_assumptions(
    queryables: Iterable[QueryableInput],
) -> tuple[QueryableAssumption, ...]:
    normalized: dict[tuple[CelExpr, QueryableId], QueryableAssumption] = {}
    for queryable in queryables:
        candidate = (
            queryable
            if isinstance(queryable, QueryableAssumption)
            else QueryableAssumption.from_cel(normalize_queryable_cel(str(queryable)))
        )
        normalized[(candidate.cel, candidate.assumption_id)] = candidate
    return tuple(normalized[key] for key in sorted(normalized))


@dataclass(frozen=True)
class ATMSFutureEnvironmentReport:
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    supported_claim_ids: Sequence[ClaimId]
    nogoods: Sequence[Sequence[AssumptionId]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))
        object.__setattr__(
            self, "supported_claim_ids", _tuple(self.supported_claim_ids)
        )
        object.__setattr__(self, "nogoods", _tuple_of_tuples(self.nogoods))


@dataclass(frozen=True)
class ATMSConceptFutureStatusEntry:
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    status: ValueStatus
    supported_claim_ids: Sequence[ClaimId]

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))
        object.__setattr__(
            self, "supported_claim_ids", _tuple(self.supported_claim_ids)
        )


@dataclass(frozen=True)
class ATMSConceptStabilityReport:
    concept_id: str
    current_status: ValueStatus
    stable: bool
    limit: int | None
    future_count: int
    consistent_future_count: int
    inconsistent_future_count: int
    witnesses: Sequence[ATMSConceptFutureStatusEntry]

    def __post_init__(self) -> None:
        object.__setattr__(self, "witnesses", _tuple(self.witnesses))


@dataclass(frozen=True)
class ATMSConceptRelevanceState:
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    status: ValueStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))


@dataclass(frozen=True)
class ATMSConceptWitnessPair:
    queryable_id: QueryableId
    queryable_cel: str
    without_state: ATMSConceptRelevanceState
    with_state: ATMSConceptRelevanceState


@dataclass(frozen=True)
class ATMSConceptRelevanceReport:
    concept_id: str
    current_status: ValueStatus
    relevant_queryables: Sequence[str]
    irrelevant_queryables: Sequence[str]
    witness_pairs: Mapping[str, Sequence[ATMSConceptWitnessPair]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "relevant_queryables", _tuple(self.relevant_queryables)
        )
        object.__setattr__(
            self, "irrelevant_queryables", _tuple(self.irrelevant_queryables)
        )
        object.__setattr__(
            self,
            "witness_pairs",
            {str(key): _tuple(value) for key, value in self.witness_pairs.items()},
        )


@dataclass(frozen=True)
class ATMSNodeInterventionPlan:
    target: str
    node_id: str
    claim_id: str | None
    current_status: ATMSNodeStatus
    target_status: ATMSNodeStatus
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    result_status: ATMSNodeStatus
    result_out_kind: ATMSOutKind | None
    minimality_basis: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))


@dataclass(frozen=True)
class ATMSConceptInterventionPlan:
    target: str
    concept_id: str
    current_status: ValueStatus
    target_status: ValueStatus
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    result_status: ValueStatus
    minimality_basis: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))


@dataclass(frozen=True)
class ATMSNextQuerySuggestion:
    queryable_id: QueryableId
    queryable_cel: str
    plan_count: int
    smallest_plan_size: int
    plan_queryable_cels: Sequence[Sequence[str]]
    example_plans: Sequence[ATMSNodeInterventionPlan | ATMSConceptInterventionPlan]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "plan_queryable_cels", _tuple_of_tuples(self.plan_queryable_cels)
        )
        object.__setattr__(self, "example_plans", _tuple(self.example_plans))


@dataclass(frozen=True)
class ATMSCycleAntecedent:
    node_id: str
    kind: str
    cycle: Literal[True]


@dataclass(frozen=True)
class ATMSAssumptionAntecedent:
    node_id: str
    kind: str
    label: Sequence[SerializedEnvironment] | None

    def __post_init__(self) -> None:
        if self.label is not None:
            object.__setattr__(self, "label", _tuple(self.label))


@dataclass(frozen=True)
class ATMSJustificationExplanation:
    node_id: str
    justification_id: str
    antecedent_ids: Sequence[str]
    consequent_id: str
    informant: str
    support: Sequence[SerializedEnvironment] | None
    antecedents: Sequence["ATMSExplanationAntecedent"]

    def __post_init__(self) -> None:
        object.__setattr__(self, "antecedent_ids", _tuple(self.antecedent_ids))
        if self.support is not None:
            object.__setattr__(self, "support", _tuple(self.support))
        object.__setattr__(self, "antecedents", _tuple(self.antecedents))


@dataclass(frozen=True)
class ATMSNodeExplanation:
    node_id: str
    claim_id: str | None
    kind: str
    status: ATMSNodeStatus
    support_quality: SupportQuality
    label: Sequence[SerializedEnvironment] | None
    essential_support: SerializedEnvironment | None
    reason: str
    traces: Sequence[ATMSJustificationExplanation]

    def __post_init__(self) -> None:
        if self.label is not None:
            object.__setattr__(self, "label", _tuple(self.label))
        object.__setattr__(self, "traces", _tuple(self.traces))


@dataclass(frozen=True)
class ATMSNestedNodeExplanation(ATMSNodeExplanation):
    antecedent_of: str


ATMSExplanationAntecedent: TypeAlias = (
    ATMSCycleAntecedent | ATMSAssumptionAntecedent | ATMSNestedNodeExplanation
)


@dataclass(frozen=True)
class ATMSLabelVerificationReport:
    ok: bool
    consistency_errors: Sequence[str]
    minimality_errors: Sequence[str]
    soundness_errors: Sequence[str]
    completeness_errors: Sequence[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "consistency_errors", _tuple(self.consistency_errors))
        object.__setattr__(self, "minimality_errors", _tuple(self.minimality_errors))
        object.__setattr__(self, "soundness_errors", _tuple(self.soundness_errors))
        object.__setattr__(
            self, "completeness_errors", _tuple(self.completeness_errors)
        )


@dataclass
class ResolvedResult:
    concept_id: ConceptId
    status: ValueStatus
    value: float | str | None = None
    claims: tuple[ActiveClaim, ...] = field(default_factory=tuple)
    winning_claim_id: ClaimId | None = None
    strategy: str | None = None
    reason: str | None = None
    label: Label | None = None
    acceptance_probs: dict[str, float] | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.status = coerce_value_status(self.status)
        self.claims = tuple(self.claims)


@dataclass
class SyntheticClaim:
    id: str
    concept_id: ConceptId
    type: ClaimType = ClaimType.PARAMETER
    value: float | str | None = None
    conditions: list[CelExpr] = field(default_factory=list[CelExpr])
    sample_size: int | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.type = _coerce_claim_type(self.type)
        self.conditions = list(to_cel_exprs(self.conditions))
        if self.sample_size is not None:
            self.sample_size = int(self.sample_size)
        if self.confidence is not None:
            self.confidence = float(self.confidence)


@dataclass(frozen=True)
class ClaimView:
    """Bridge return type for :func:`propstore.world.bridge.at_journal_step`.

    Carries the claim-id-keyed charter :class:`~propstore.families.claims.Claim`
    rows projected from a journal step, the snapshot's ``RevisionScope`` (so
    callers know what bindings/context the view is taken under), plus optional
    tuples of stances and conflicts populated only by the heavy variant.

    Single canonical type (CLAUDE.md substrate boundary): ``claims`` holds the
    charter ``Claim`` — there is no ``ClaimRow`` second spelling — and
    ``stances`` / ``conflicts`` hold the charter ``Stance`` and the
    ``conflict_detector`` ``ConflictRecord`` directly.
    """

    claims: Mapping[str, Claim]
    scope: RevisionScope
    stances: tuple[Stance, ...] = field(default_factory=tuple)
    conflicts: tuple[ConflictRecord, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "claims", dict(self.claims))
        object.__setattr__(self, "stances", tuple(self.stances))
        object.__setattr__(self, "conflicts", tuple(self.conflicts))

    def claim_ids(self) -> set[str]:
        """Return the set of claim id strings in this view."""

        return {str(key) for key in self.claims}


@dataclass
class ChainStep:
    concept_id: str
    value: float | str | None
    source: str  # "binding" | "claim" | "derived" | "resolved"


@dataclass
class ChainResult:
    target_concept_id: ConceptId
    result: ValueResult | DerivedResult
    steps: list[ChainStep] = field(default_factory=list[ChainStep])
    # The bindings the chain was evaluated under, in the one canonical binding
    # scalar type (``Environment.bindings``). This used to be ``dict[str, Any]``
    # holding a *lossy* rewrite of them: the producer ran each value through the
    # narrowing that exists for ``ChainStep.value``, so a bool binding came back
    # as the string "True" and an int came back as a float. A binding is a
    # binding; there is one spelling of its value.
    bindings_used: dict[str, str | int | float | bool] = field(
        default_factory=dict[str, str | int | float | bool]
    )
    unresolved_dependencies: list[ConceptId] = field(default_factory=list[ConceptId])

    def __post_init__(self) -> None:
        self.target_concept_id = to_concept_id(self.target_concept_id)
        self.steps = list(self.steps)
        self.bindings_used = dict(self.bindings_used)
        self.unresolved_dependencies = [
            to_concept_id(concept_id) for concept_id in self.unresolved_dependencies
        ]


class DecisionValueSource(Enum):
    """Provenance tag for the value returned by ``apply_decision_criterion``.

    Per CLAUDE.md "Honest ignorance over fabricated confidence": a value
    derived from a calibrated opinion tuple must be distinguishable from
    "no data at all".

    This is a plain ``Enum`` (NOT ``StrEnum``, NOT ``Literal``) so that
    callers must use identity comparisons (``source is OPINION``) rather
    than string equality. Bare-string comparisons for structured tags are
    forbidden by the project's strong-typing directive.
    """

    OPINION = "opinion"
    NO_DATA = "no_data"


@dataclass(frozen=True)
class DecisionValue:
    """Tagged return of ``apply_decision_criterion``.

    Attributes:
        value: The numeric decision value, or ``None`` when ``source`` is
            ``DecisionValueSource.NO_DATA``.
        source: Provenance tag describing how ``value`` was obtained.
    """

    value: float | None
    source: DecisionValueSource


def apply_decision_criterion(
    opinion_b: float | None,
    opinion_d: float | None,
    opinion_u: float | None,
    opinion_a: float | None,
    confidence: float | None,
    criterion: str = "pignistic",
    pessimism_index: float = 0.5,
) -> DecisionValue:
    """Apply decision criterion to complete opinion data.

    Decision criteria determine how belief-function uncertainty maps to
    actionable values at render time. The binomial pignistic path follows
    Smets & Kennes 1994 (journal p.202) and Denoeux 2019 (pp.17-18).
    The projected-probability path follows Jøsang 2001 Definition 6 (p.5).

    Args:
        opinion_b/d/u/a: Opinion components.
        confidence: Ignored scalar claim confidence retained at call sites
            that still carry this field for unrelated render reporting.
        criterion: One of "pignistic", "projected_probability",
            "lower_bound", "upper_bound", "hurwicz"
        pessimism_index: α for Hurwicz criterion

    Returns:
        ``DecisionValue`` whose ``source`` distinguishes a calibrated
        opinion result (``OPINION``) from total absence of data (``NO_DATA``).
        ``value`` is ``None`` only when ``source is DecisionValueSource.NO_DATA``.
    """
    # If opinion components are all present, compute from opinion
    if (
        opinion_b is not None
        and opinion_d is not None
        and opinion_u is not None
        and opinion_a is not None
    ):
        if criterion == "pignistic":
            # Smets & Kennes 1994, journal p.202: BetP distributes
            # focal-set mass equally. For binomial opinions, BetP(x)=b+u/2.
            value = opinion_b + (opinion_u / 2.0)
        elif criterion == "projected_probability":
            # Jøsang 2001, Definition 6 (p.5): E(ω)=b+a·u.
            value = opinion_b + opinion_a * opinion_u
        elif criterion == "lower_bound":
            # Jøsang (2001, p.4): Bel(x) = b
            value = opinion_b
        elif criterion == "upper_bound":
            # Jøsang (2001, p.4): Pl(x) = 1 - d
            value = 1.0 - opinion_d
        elif criterion == "hurwicz":
            # Denoeux (2019, p.17): α·Bel + (1-α)·Pl
            bel = opinion_b
            pl = 1.0 - opinion_d
            value = pessimism_index * bel + (1.0 - pessimism_index) * pl
        else:
            raise ValueError(f"Unknown decision criterion: {criterion!r}")
        return DecisionValue(value=value, source=DecisionValueSource.OPINION)

    _ = confidence
    return DecisionValue(value=None, source=DecisionValueSource.NO_DATA)


@runtime_checkable
class ClaimSupportView(Protocol):
    def claim_support(
        self, claim: ActiveClaim
    ) -> tuple[Label | None, SupportQuality]: ...


@runtime_checkable
class ATMSEngineView(Protocol):
    def supported_claim_ids(self, concept_id: str | None = None) -> set[str]: ...
    def argumentation_state(
        self,
        *,
        queryables: Sequence[QueryableAssumption],
        future_limit: int,
    ) -> WorldlineArgumentationState: ...


@runtime_checkable
class HasATMSEngine(Protocol):
    def atms_engine(self) -> ATMSEngineView: ...


@runtime_checkable
class HasActiveGraph(Protocol):
    def active_world_graph(self) -> ActiveWorldGraph | None: ...


@runtime_checkable
class GroundingBundleStore(Protocol):
    def grounding_bundle(self) -> GroundedRulesBundle: ...


@runtime_checkable
class BeliefSpace(Protocol):
    def active_claims(self, concept_id: str | None = None) -> list[ActiveClaim]: ...
    def inactive_claims(self, concept_id: str | None = None) -> list[ActiveClaim]: ...
    def value_of(self, concept_id: str) -> ValueResult: ...
    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: Mapping[str, float | str | None] | None = None,
    ) -> DerivedResult: ...
    def resolved_value(self, concept_id: str) -> ResolvedResult: ...
    def is_determined(self, concept_id: str) -> bool: ...
    def conflicts(self, concept_id: str | None = None) -> list[ConflictRecord]: ...
    def explain(self, claim_id: str) -> list[Stance]: ...


__all__ = [
    # substrate / core re-exports (the spine consumers import from here)
    "MergeOperator",
    "CelExpr",
    "to_cel_expr",
    "to_cel_exprs",
    "ConflictClass",
    "ActiveClaim",
    "AssumptionRef",
    "Environment",
    "WorldStore",
    "Exactness",
    "AssumptionId",
    "ClaimId",
    "ConceptId",
    "QueryableId",
    "to_concept_id",
    "to_queryable_id",
    "EnvironmentKey",
    "Label",
    "SupportMetadata",
    "SupportQuality",
    "ArgumentationSemantics",
    "ReasoningBackend",
    "cli_argumentation_semantics_values",
    "normalize_argumentation_semantics",
    "normalize_reasoning_backend",
    "supported_argumentation_semantics",
    "validate_backend_semantics",
    "ClaimSimilarityHit",
    "ConceptSearchHit",
    "ConceptSimilarityHit",
    "WorldStoreStats",
    "ClaimType",
    "ConceptStatus",
    # value / derived / resolved result types
    "ValueStatus",
    "ValueResultReason",
    "coerce_value_status",
    "SerializedEnvironment",
    "ValueResult",
    "DerivedResult",
    "ResolvedResult",
    # ATMS inspection / report types
    "ATMSNodeStatus",
    "ATMSOutKind",
    "QueryableAssumption",
    "QueryableInput",
    "normalize_queryable_cel",
    "coerce_queryable_assumptions",
    "ATMSInspection",
    "ATMSFutureEnvironmentReport",
    "ATMSNodeFutureStatusEntry",
    "ATMSConceptFutureStatusEntry",
    "ATMSFutureStatusReport",
    "ATMSWhyOutReport",
    "ATMSNodeStabilityReport",
    "ATMSConceptStabilityReport",
    "ATMSNodeRelevanceState",
    "ATMSConceptRelevanceState",
    "ATMSNodeWitnessPair",
    "ATMSConceptWitnessPair",
    "ATMSNodeRelevanceReport",
    "ATMSConceptRelevanceReport",
    "ATMSNodeInterventionPlan",
    "ATMSConceptInterventionPlan",
    "ATMSNextQuerySuggestion",
    "ATMSCycleAntecedent",
    "ATMSAssumptionAntecedent",
    "ATMSJustificationExplanation",
    "ATMSNodeExplanation",
    "ATMSNestedNodeExplanation",
    "ATMSExplanationAntecedent",
    "ATMSNogoodProvenanceDetail",
    "ATMSNogoodDetail",
    "ATMSLabelVerificationReport",
    # resolution / render policy / decision
    "ResolutionStrategy",
    "normalize_merge_operator",
    "IntegrityConstraintKind",
    "IntegrityConstraint",
    "SyntheticClaim",
    "ClaimView",
    "ChainStep",
    "ChainResult",
    "RenderPolicy",
    "DecisionValueSource",
    "DecisionValue",
    "apply_decision_criterion",
    # protocols
    "ClaimSupportView",
    "ATMSEngineView",
    "HasATMSEngine",
    "HasActiveGraph",
    "GroundingBundleStore",
    "BeliefSpace",
]
