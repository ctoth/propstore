"""Data classes, enums, and protocols for the render/store layer."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeAlias, TypeVar, overload, runtime_checkable

from propstore.cel_types import CelExpr, to_cel_expr, to_cel_exprs
from propstore.conflict_detector import ConflictClass
from propstore.core.active_claims import ActiveClaim, coerce_active_claims
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.core.environment import WorldStore, Environment  # noqa: F401
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.id_types import (
    AssumptionId,
    ClaimId,
    ConceptId,
    QueryableId,
    to_concept_id,
    to_queryable_id,
)
from propstore.core.labels import (
    AssumptionRef,
    EnvironmentKey,
    Label,
    SupportQuality,
    SupportMetadata,
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
from propstore.core.store_results import (
    WorldStoreStats,
    ClaimSimilarityHit,
    ConceptSearchHit,
    ConceptSimilarityHit,
)
from propstore.core.row_types import ConflictRow, StanceRow

if TYPE_CHECKING:
    from propstore.core.graph_types import ActiveWorldGraph
    from propstore.grounding.bundle import GroundedRulesBundle

_T = TypeVar("_T")


def _tuple(values: Iterable[_T]) -> tuple[_T, ...]:
    return tuple(values)


def _tuple_of_tuples(values: Iterable[Iterable[_T]]) -> tuple[tuple[_T, ...], ...]:
    return tuple(tuple(value) for value in values)


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"render policy field '{field_name}' must be a mapping")
    return value


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


@overload
def coerce_value_status(value: None) -> None: ...


@overload
def coerce_value_status(value: object) -> ValueStatus: ...


def coerce_value_status(value: object | None) -> ValueStatus | None:
    if value is None:
        return None
    if isinstance(value, ValueStatus):
        return value
    return ValueStatus(str(value))


SerializedEnvironment: TypeAlias = Mapping[str, Sequence[str]]


@dataclass
class ValueResult:
    concept_id: ConceptId
    status: ValueStatus
    claims: list[ActiveClaim] = field(default_factory=list)
    label: Label | None = None
    reason: ValueResultReason | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.status = coerce_value_status(self.status)
        self.claims = coerce_active_claims(self.claims)


@dataclass
class DerivedResult:
    concept_id: ConceptId
    status: ValueStatus
    value: float | None = None
    formula: str | None = None
    input_values: dict[ConceptId, float] = field(default_factory=dict)
    exactness: Exactness | None = None
    label: Label | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.status = coerce_value_status(self.status)
        self.exactness = coerce_exactness(self.exactness)
        self.input_values = {
            to_concept_id(concept_id): float(value)
            for concept_id, value in self.input_values.items()
        }


class ATMSNodeStatus(Enum):
    """ATMS-native node status derived from the propagated label."""

    TRUE = "TRUE"
    IN = "IN"
    OUT = "OUT"


class ATMSOutKind(Enum):
    """Why an ATMS node is currently OUT."""

    MISSING_SUPPORT = "missing_support"
    NOGOOD_PRUNED = "nogood_pruned"
    PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE = "parameterization_input_type_incompatible"


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
        digest = hashlib.sha256(f"queryable\0{source}\0{normalized_cel}".encode("utf-8")).hexdigest()
        return cls(
            assumption_id=to_queryable_id(f"queryable:{source}:{digest}"),
            cel=normalized_cel,
            source=source,
        )


QueryableInput: TypeAlias = QueryableAssumption | str | CelExpr


def normalize_queryable_cel(queryable: str | CelExpr) -> CelExpr:
    queryable_text = str(queryable)
    if any(operator in queryable_text for operator in ("==", "!=", ">=", "<=", ">", "<")):
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
    return tuple(
        normalized[key]
        for key in sorted(normalized)
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
        object.__setattr__(self, "supported_claim_ids", _tuple(self.supported_claim_ids))
        object.__setattr__(self, "nogoods", _tuple_of_tuples(self.nogoods))


@dataclass(frozen=True)
class ATMSNodeFutureStatusEntry:
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    status: ATMSNodeStatus
    out_kind: ATMSOutKind | None
    reason: str
    support_quality: SupportQuality
    essential_support: SerializedEnvironment

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))


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
        object.__setattr__(self, "supported_claim_ids", _tuple(self.supported_claim_ids))


@dataclass(frozen=True)
class ATMSFutureStatusReport:
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    could_become_in: bool
    could_become_out: bool
    futures: Sequence[ATMSNodeFutureStatusEntry]

    def __post_init__(self) -> None:
        object.__setattr__(self, "futures", _tuple(self.futures))


@dataclass(frozen=True)
class ATMSWhyOutReport:
    node_id: str
    claim_id: str | None
    status: ATMSNodeStatus
    out_kind: ATMSOutKind | None
    reason: str
    support_quality: SupportQuality
    future_activatable: bool
    candidate_queryable_cels: Sequence[Sequence[str]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidate_queryable_cels",
            _tuple_of_tuples(self.candidate_queryable_cels),
        )


@dataclass(frozen=True)
class ATMSNodeStabilityReport:
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    stable: bool
    limit: int | None
    future_count: int
    consistent_future_count: int
    inconsistent_future_count: int
    witnesses: Sequence[ATMSNodeFutureStatusEntry]

    def __post_init__(self) -> None:
        object.__setattr__(self, "witnesses", _tuple(self.witnesses))


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
class ATMSNodeRelevanceState:
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    status: ATMSNodeStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))


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
class ATMSNodeWitnessPair:
    queryable_id: QueryableId
    queryable_cel: str
    without_state: ATMSNodeRelevanceState
    with_state: ATMSNodeRelevanceState


@dataclass(frozen=True)
class ATMSConceptWitnessPair:
    queryable_id: QueryableId
    queryable_cel: str
    without_state: ATMSConceptRelevanceState
    with_state: ATMSConceptRelevanceState


@dataclass(frozen=True)
class ATMSNodeRelevanceReport:
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    current_status: ATMSNodeStatus
    relevant_queryables: Sequence[str]
    irrelevant_queryables: Sequence[str]
    witness_pairs: Mapping[str, Sequence[ATMSNodeWitnessPair]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "relevant_queryables", _tuple(self.relevant_queryables))
        object.__setattr__(self, "irrelevant_queryables", _tuple(self.irrelevant_queryables))
        object.__setattr__(
            self,
            "witness_pairs",
            {str(key): _tuple(value) for key, value in self.witness_pairs.items()},
        )


@dataclass(frozen=True)
class ATMSConceptRelevanceReport:
    concept_id: str
    current_status: ValueStatus
    relevant_queryables: Sequence[str]
    irrelevant_queryables: Sequence[str]
    witness_pairs: Mapping[str, Sequence[ATMSConceptWitnessPair]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "relevant_queryables", _tuple(self.relevant_queryables))
        object.__setattr__(self, "irrelevant_queryables", _tuple(self.irrelevant_queryables))
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
        object.__setattr__(self, "plan_queryable_cels", _tuple_of_tuples(self.plan_queryable_cels))
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
    ATMSCycleAntecedent
    | ATMSAssumptionAntecedent
    | ATMSNestedNodeExplanation
)


@dataclass(frozen=True)
class ATMSNogoodProvenanceDetail:
    claim_a_id: str
    claim_b_id: str
    concept_id: str | None
    warning_class: ConflictClass | None
    environment_a: Sequence[str]
    environment_b: Sequence[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "environment_a", _tuple(self.environment_a))
        object.__setattr__(self, "environment_b", _tuple(self.environment_b))


@dataclass(frozen=True)
class ATMSNogoodDetail:
    environment: Mapping[str, Sequence[str]]
    provenance: Sequence[ATMSNogoodProvenanceDetail]

    def __post_init__(self) -> None:
        object.__setattr__(self, "provenance", _tuple(self.provenance))


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
        object.__setattr__(self, "completeness_errors", _tuple(self.completeness_errors))


class ResolutionStrategy(StrEnum):
    RECENCY = "recency"
    SAMPLE_SIZE = "sample_size"
    ARGUMENTATION = "argumentation"
    OVERRIDE = "override"
    ASSIGNMENT_SELECTION_MERGE = "assignment_selection_merge"


class MergeOperator(StrEnum):
    SIGMA = "sigma"
    MAX = "max"
    GMAX = "gmax"


def normalize_merge_operator(value: MergeOperator | str) -> MergeOperator:
    if isinstance(value, MergeOperator):
        return value
    try:
        return MergeOperator(str(value))
    except ValueError as exc:
        raise ValueError(f"Unknown merge_operator '{value}'") from exc


@dataclass
class ResolvedResult:
    concept_id: ConceptId
    status: ValueStatus
    value: float | str | None = None
    claims: list[ActiveClaim] = field(default_factory=list)
    winning_claim_id: ClaimId | None = None
    strategy: str | None = None
    reason: str | None = None
    label: Label | None = None
    acceptance_probs: dict[str, float] | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.status = coerce_value_status(self.status)
        self.claims = coerce_active_claims(self.claims)


class IntegrityConstraintKind(StrEnum):
    RANGE = "range"
    CATEGORY = "category"
    CEL = "cel"
    CUSTOM = "custom"


@dataclass(frozen=True)
class IntegrityConstraint:
    kind: IntegrityConstraintKind
    concept_ids: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    cel: CelExpr | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_ids", tuple(self.concept_ids))
        object.__setattr__(self, "metadata", dict(self.metadata))
        if self.cel is not None:
            object.__setattr__(self, "cel", to_cel_expr(self.cel))
        if not self.concept_ids:
            raise ValueError("IntegrityConstraint requires at least one concept id")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ValueError("IntegrityConstraint has duplicate concept ids")
        if self.kind == IntegrityConstraintKind.CUSTOM:
            predicate = self.metadata.get("predicate")
            if not callable(predicate):
                raise TypeError("CUSTOM integrity constraint requires callable metadata['predicate']")


def integrity_constraint_from_dict(data: Mapping[str, Any]) -> IntegrityConstraint:
    return IntegrityConstraint(
        kind=(
            data["kind"]
            if isinstance(data["kind"], IntegrityConstraintKind)
            else IntegrityConstraintKind(str(data["kind"]))
        ),
        concept_ids=tuple(str(concept_id) for concept_id in data.get("concept_ids", ())),
        metadata=dict(_optional_mapping(data.get("metadata"), "metadata")),
        cel=None if data.get("cel") is None else to_cel_expr(str(data["cel"])),
        description=(
            None
            if data.get("description") is None
            else str(data["description"])
        ),
    )


def integrity_constraint_to_dict(constraint: IntegrityConstraint) -> dict[str, Any]:
    metadata = dict(constraint.metadata)
    if constraint.kind == IntegrityConstraintKind.CUSTOM and "predicate" in metadata:
        raise TypeError("CUSTOM integrity constraints with callable predicates are not serializable")
    return {
        "kind": constraint.kind.value,
        "concept_ids": list(constraint.concept_ids),
        "metadata": metadata,
        "cel": constraint.cel,
        "description": constraint.description,
    }


@dataclass(frozen=True)
class MergeAssignment:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", dict(self.values))

    def value_for(self, concept_id: str) -> Any:
        return self.values.get(concept_id)


@dataclass(frozen=True)
class MergeSource:
    source_id: str
    assignment: MergeAssignment
    weight: float = 1.0


@dataclass(frozen=True)
class MergeAssignmentScore:
    assignment: MergeAssignment
    score: float | tuple[float, ...]


@dataclass(frozen=True)
class AssignmentSelectionProblem:
    concept_ids: tuple[str, ...]
    sources: tuple[MergeSource, ...]
    constraints: tuple[IntegrityConstraint, ...] = field(default_factory=tuple)
    operator: MergeOperator = MergeOperator.SIGMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_ids", tuple(self.concept_ids))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "operator", normalize_merge_operator(self.operator))
        if not self.concept_ids:
            raise ValueError("AssignmentSelectionProblem requires at least one concept id")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ValueError("AssignmentSelectionProblem has duplicate concept ids")

        declared_concepts = set(self.concept_ids)
        for source in self.sources:
            unknown_concepts = tuple(
                concept_id
                for concept_id in source.assignment.values
                if concept_id not in declared_concepts
            )
            if unknown_concepts:
                joined = ", ".join(sorted(unknown_concepts))
                raise ValueError(
                    f"AssignmentSelectionProblem source {source.source_id!r} references unknown concept ids: {joined}"
                )

        for constraint in self.constraints:
            unknown_concepts = tuple(
                concept_id
                for concept_id in constraint.concept_ids
                if concept_id not in declared_concepts
            )
            if unknown_concepts:
                joined = ", ".join(sorted(unknown_concepts))
                raise ValueError(
                    f"AssignmentSelectionProblem constraint references unknown concept ids: {joined}"
                )


@dataclass(frozen=True)
class AssignmentSelectionResult:
    winners: tuple[MergeAssignment, ...]
    scored_candidates: tuple[MergeAssignmentScore, ...]
    admissible_count: int
    total_candidate_count: int
    reason: str | None = None


@dataclass
class SyntheticClaim:
    id: str
    concept_id: ConceptId
    type: ClaimType = ClaimType.PARAMETER
    value: float | str | None = None
    conditions: list[CelExpr] = field(default_factory=list)
    sample_size: int | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.type = coerce_claim_type(self.type) or ClaimType.PARAMETER
        self.conditions = list(to_cel_exprs(self.conditions))
        if self.sample_size is not None:
            self.sample_size = int(self.sample_size)
        if self.confidence is not None:
            self.confidence = float(self.confidence)


@dataclass
class ChainStep:
    concept_id: str
    value: float | str | None
    source: str  # "binding" | "claim" | "derived" | "resolved"


@dataclass
class ChainResult:
    target_concept_id: ConceptId
    result: ValueResult | DerivedResult
    steps: list[ChainStep] = field(default_factory=list)
    bindings_used: dict[str, Any] = field(default_factory=dict)
    unresolved_dependencies: list[ConceptId] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.target_concept_id = to_concept_id(self.target_concept_id)
        self.steps = list(self.steps)
        self.bindings_used = dict(self.bindings_used)
        self.unresolved_dependencies = [
            to_concept_id(concept_id)
            for concept_id in self.unresolved_dependencies
        ]


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
    # assignment-selection merge fields for the assignment-level Konieczny-style adaptation.
    # merge_operator selects the aggregation family used by the global solver.
    merge_operator: MergeOperator = MergeOperator.SIGMA
    # branch_filter restricts which branches are included as sources.
    branch_filter: tuple[str, ...] | None = None
    # branch_weights assigns per-branch importance weights.
    branch_weights: Mapping[str, float] | None = None
    # explicit integrity constraints for global assignment-selection merge
    integrity_constraints: tuple[IntegrityConstraint, ...] = field(default_factory=tuple)
    future_queryables: tuple[str, ...] = field(default_factory=tuple)
    future_limit: int | None = None
    overrides: Mapping[str, str] = field(default_factory=dict)
    concept_strategies: Mapping[str, ResolutionStrategy] = field(default_factory=dict)
    # Lifecycle visibility flags (WS-Z-gates Phase 4; axis-1 findings 3.1/3.2/3.3).
    # Default False preserves the "don't show problems by default" posture the
    # design checklist requires (see CLAUDE.md and
    # reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md).
    # - include_drafts: lifts the default filter that hides claim_core rows
    #   carrying stage='draft' (Phase 3 Gate 2; per
    #   propstore/compiler/passes.py draft traversal).
    # - include_blocked: lifts the default filter that hides rows with
    #   build_status='blocked' (raw-id quarantine; Phase 3 Gate 1) or
    #   promotion_status='blocked' (partial-promote mirror rows; Phase 3
    #   Gate 3).
    # - show_quarantined: surfaces build_diagnostics rows in render output.
    include_drafts: bool = False
    include_blocked: bool = False
    show_quarantined: bool = False

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
        object.__setattr__(
            self,
            "merge_operator",
            normalize_merge_operator(self.merge_operator),
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
            "integrity_constraints",
            tuple(self.integrity_constraints),
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
            for concept_id, strategy in _optional_mapping(
                data.get("concept_strategies"),
                "concept_strategies",
            ).items()
        }
        branch_weights = (
            None
            if data.get("branch_weights") is None
            else dict(_optional_mapping(data.get("branch_weights"), "branch_weights"))
        )
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
            merge_operator=normalize_merge_operator(
                data.get("merge_operator", MergeOperator.SIGMA)
            ),
            branch_filter=(
                None
                if data.get("branch_filter") is None
                else tuple(data["branch_filter"])
            ),
            branch_weights=branch_weights,
            integrity_constraints=tuple(
                integrity_constraint_from_dict(item)
                for item in (data.get("integrity_constraints") or ())
            ),
            future_queryables=tuple(data.get("future_queryables") or ()),
            future_limit=(
                None
                if data.get("future_limit") is None
                else int(data["future_limit"])
            ),
            overrides=dict(_optional_mapping(data.get("overrides"), "overrides")),
            concept_strategies=concept_strategies,
            include_drafts=bool(data.get("include_drafts", False)),
            include_blocked=bool(data.get("include_blocked", False)),
            show_quarantined=bool(data.get("show_quarantined", False)),
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
        if self.merge_operator != MergeOperator.SIGMA:
            data["merge_operator"] = self.merge_operator
        if self.branch_filter is not None:
            data["branch_filter"] = list(self.branch_filter)
        if self.branch_weights is not None:
            data["branch_weights"] = dict(self.branch_weights)
        if self.integrity_constraints:
            data["integrity_constraints"] = [
                integrity_constraint_to_dict(constraint)
                for constraint in self.integrity_constraints
            ]
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
        if self.include_drafts:
            data["include_drafts"] = self.include_drafts
        if self.include_blocked:
            data["include_blocked"] = self.include_blocked
        if self.show_quarantined:
            data["show_quarantined"] = self.show_quarantined
        return data


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
    def claim_support(self, claim: ActiveClaim) -> tuple[Label | None, SupportQuality]: ...


@runtime_checkable
class ATMSEngineView(Protocol):
    def supported_claim_ids(self, concept_id: str | None = None) -> set[str]: ...
    def argumentation_state(
        self,
        *,
        queryables: Sequence[QueryableAssumption],
        future_limit: int,
    ) -> dict[str, Any]: ...


@runtime_checkable
class HasATMSEngine(Protocol):
    def atms_engine(self) -> ATMSEngineView: ...


@runtime_checkable
class HasActiveGraph(Protocol):
    _active_graph: ActiveWorldGraph | None


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
    def conflicts(self, concept_id: str | None = None) -> list[ConflictRow]: ...
    def explain(self, claim_id: str) -> list[StanceRow]: ...
