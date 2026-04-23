"""Application-layer claim view reports for durable presenters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicySummary,
    build_render_policy,
    summarize_render_policy,
)
from propstore.app.world import open_app_world_model
from propstore.repository import Repository

ClaimViewState: TypeAlias = Literal[
    "known",
    "unknown",
    "vacuous",
    "underspecified",
    "blocked",
    "missing",
    "not_applicable",
]
ClaimViewScalar: TypeAlias = str | int | float | bool


class ClaimViewAppError(Exception):
    """Base class for expected claim-view failures."""


class ClaimViewUnsupportedStateError(ClaimViewAppError):
    """Raised when a requested repository state is not implemented."""


class ClaimViewUnknownClaimError(ClaimViewAppError):
    def __init__(self, claim_id: str) -> None:
        super().__init__(f"Claim '{claim_id}' not found.")
        self.claim_id = claim_id


@dataclass(frozen=True)
class ClaimViewRequest:
    claim_id: str
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)
    branch: str | None = None
    revision: str | None = None


@dataclass(frozen=True)
class ClaimViewConcept:
    state: ClaimViewState
    concept_id: str | None
    canonical_name: str | None
    form: str | None


@dataclass(frozen=True)
class ClaimViewValue:
    state: ClaimViewState
    value: ClaimViewScalar | None
    unit: str | None
    value_si: float | None
    canonical_unit: str | None
    sentence: str


@dataclass(frozen=True)
class ClaimViewUncertainty:
    state: ClaimViewState
    uncertainty: float | None
    uncertainty_type: str | None
    lower_bound: float | None
    lower_bound_si: float | None
    upper_bound: float | None
    upper_bound_si: float | None
    sample_size: int | None
    sentence: str


@dataclass(frozen=True)
class ClaimViewCondition:
    state: ClaimViewState
    expression: str | None
    sentence: str


@dataclass(frozen=True)
class ClaimViewProvenance:
    state: ClaimViewState
    source_slug: str | None
    source_id: str | None
    source_kind: str | None
    paper: str | None
    page: int | None
    origin_type: str | None
    origin_value: str | None
    sentence: str


@dataclass(frozen=True)
class ClaimViewStatus:
    state: ClaimViewState
    visible_under_policy: bool
    reason: str
    branch: str
    build_status: str
    stage: str
    promotion_status: str


@dataclass(frozen=True)
class ClaimViewReport:
    claim_id: str
    logical_id: str | None
    artifact_id: str | None
    version_id: str | None
    heading: str
    claim_type: str
    statement: str | None
    concept: ClaimViewConcept
    value: ClaimViewValue
    uncertainty: ClaimViewUncertainty
    condition: ClaimViewCondition
    provenance: ClaimViewProvenance
    render_policy: RenderPolicySummary
    status: ClaimViewStatus
    repository_state: str


def build_claim_view(repo: Repository, request: ClaimViewRequest) -> ClaimViewReport:
    if request.branch is not None:
        raise ClaimViewUnsupportedStateError("branch-qualified claim views are not implemented")
    if request.revision is not None:
        raise ClaimViewUnsupportedStateError("revision-qualified claim views are not implemented")

    policy = build_render_policy(request.render_policy)
    with open_app_world_model(repo) as world:
        claim = world.get_claim(request.claim_id)
        if claim is None:
            raise ClaimViewUnknownClaimError(request.claim_id)
        concept = world.get_concept(str(claim.concept_id)) if claim.concept_id else None
        visible_ids = {str(row.claim_id) for row in world.claims_with_policy(None, policy)}
        status = _claim_status(claim, str(claim.claim_id) in visible_ids)
        concept_view = _claim_concept(claim, concept)
        return ClaimViewReport(
            claim_id=str(claim.claim_id),
            logical_id=claim.primary_logical_id,
            artifact_id=claim.artifact_id,
            version_id=claim.version_id,
            heading=f"Claim {claim.primary_logical_value or claim.claim_id}",
            claim_type="unknown" if claim.claim_type is None else claim.claim_type.value,
            statement=claim.statement,
            concept=concept_view,
            value=_claim_value(claim, concept_view),
            uncertainty=_claim_uncertainty(claim),
            condition=_claim_condition(claim),
            provenance=_claim_provenance(claim),
            render_policy=summarize_render_policy(policy),
            status=status,
            repository_state="current worktree",
        )


def _claim_concept(claim, concept) -> ClaimViewConcept:
    if claim.concept_id is None:
        return ClaimViewConcept(
            state="not_applicable",
            concept_id=None,
            canonical_name=None,
            form=None,
        )
    if concept is None:
        return ClaimViewConcept(
            state="unknown",
            concept_id=str(claim.concept_id),
            canonical_name=None,
            form=None,
        )
    return ClaimViewConcept(
        state="known",
        concept_id=str(concept.concept_id),
        canonical_name=concept.canonical_name,
        form=concept.form,
    )


def _claim_value(claim, concept: ClaimViewConcept) -> ClaimViewValue:
    value = _scalar_value(claim.value)
    if value is None:
        if claim.claim_type is not None and claim.claim_type.value in {
            "mechanism",
            "limitation",
            "comparison",
            "algorithm",
            "equation",
        }:
            return ClaimViewValue(
                state="not_applicable",
                value=None,
                unit=None,
                value_si=None,
                canonical_unit=concept.form,
                sentence=f"Value is not applicable for {claim.claim_type.value} claim.",
            )
        return ClaimViewValue(
            state="missing",
            value=None,
            unit=None,
            value_si=None,
            canonical_unit=concept.form,
            sentence="Value is missing.",
        )
    unit = claim.unit
    value_sentence = f"Value is {value}."
    if unit:
        value_sentence = f"Value is {value} {unit}."
    return ClaimViewValue(
        state="known",
        value=value,
        unit=unit,
        value_si=claim.value_si,
        canonical_unit=concept.form,
        sentence=value_sentence,
    )


def _claim_uncertainty(claim) -> ClaimViewUncertainty:
    has_interval = claim.lower_bound is not None or claim.upper_bound is not None
    if claim.uncertainty is None and not has_interval and claim.sample_size is None:
        return ClaimViewUncertainty(
            state="missing",
            uncertainty=None,
            uncertainty_type=claim.uncertainty_type,
            lower_bound=claim.lower_bound,
            lower_bound_si=claim.lower_bound_si,
            upper_bound=claim.upper_bound,
            upper_bound_si=claim.upper_bound_si,
            sample_size=claim.sample_size,
            sentence="Uncertainty is missing.",
        )
    return ClaimViewUncertainty(
        state="known",
        uncertainty=claim.uncertainty,
        uncertainty_type=claim.uncertainty_type,
        lower_bound=claim.lower_bound,
        lower_bound_si=claim.lower_bound_si,
        upper_bound=claim.upper_bound,
        upper_bound_si=claim.upper_bound_si,
        sample_size=claim.sample_size,
        sentence="Uncertainty information is present.",
    )


def _claim_condition(claim) -> ClaimViewCondition:
    if not claim.conditions_cel:
        return ClaimViewCondition(
            state="vacuous",
            expression=None,
            sentence="Conditions are vacuous; the claim has no explicit condition filter.",
        )
    return ClaimViewCondition(
        state="known",
        expression=claim.conditions_cel,
        sentence=f"Condition expression: {claim.conditions_cel}",
    )


def _claim_provenance(claim) -> ClaimViewProvenance:
    source = claim.source
    provenance = claim.provenance
    source_slug = None if source is None else source.slug
    source_id = None if source is None else source.source_id
    source_kind = None if source is None or source.kind is None else source.kind.value
    origin = None if source is None else source.origin
    origin_type = None if origin is None or origin.origin_type is None else origin.origin_type.value
    origin_value = None if origin is None else origin.value
    paper = None if provenance is None else provenance.paper
    page = None if provenance is None else provenance.page
    if source_slug is None and source_id is None and paper is None and page is None:
        state: ClaimViewState = "missing"
        sentence = "Provenance is missing."
    else:
        state = "known"
        label = paper or source_id or source_slug or "source"
        sentence = f"Provenance source is {label}."
    return ClaimViewProvenance(
        state=state,
        source_slug=source_slug,
        source_id=source_id,
        source_kind=source_kind,
        paper=paper,
        page=page,
        origin_type=origin_type,
        origin_value=origin_value,
        sentence=sentence,
    )


def _claim_status(claim, visible: bool) -> ClaimViewStatus:
    branch = _attribute_text(claim, "branch", "master")
    build_status = _attribute_text(claim, "build_status", "ingested")
    stage = _attribute_text(claim, "stage", "accepted")
    promotion_status = _attribute_text(claim, "promotion_status", "accepted")
    if visible:
        return ClaimViewStatus(
            state="known",
            visible_under_policy=True,
            reason="Claim is visible under the current render policy.",
            branch=branch,
            build_status=build_status,
            stage=stage,
            promotion_status=promotion_status,
        )
    if stage == "draft":
        reason = "Claim is blocked under the current render policy because drafts are hidden."
    elif build_status == "blocked":
        reason = "Claim is blocked under the current render policy because build-blocked rows are hidden."
    elif promotion_status == "blocked":
        reason = "Claim is blocked under the current render policy because promotion-blocked rows are hidden."
    else:
        reason = "Claim is blocked under the current render policy."
    return ClaimViewStatus(
        state="blocked",
        visible_under_policy=False,
        reason=reason,
        branch=branch,
        build_status=build_status,
        stage=stage,
        promotion_status=promotion_status,
    )


def _attribute_text(claim, key: str, default: str) -> str:
    raw = claim.attributes.get(key)
    if raw is None or raw == "":
        return default
    return str(raw)


def _scalar_value(value) -> ClaimViewScalar | None:
    if value is None:
        return None
    if isinstance(value, str | int | float | bool):
        return value
    return str(value)
