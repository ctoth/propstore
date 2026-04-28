"""Application-layer concept view reports for durable presenters."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal, TypeAlias, cast

from propstore.app.concepts.display import _find_concept_entry
from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicySummary,
    build_render_policy,
    summarize_render_policy,
)
from propstore.app.repository_views import (
    AppRepositoryViewRequest,
    repository_view_label,
)
from propstore.app.world import open_app_world_model
from propstore.core.row_types import ClaimRow
from propstore.repository import Repository

ConceptViewState: TypeAlias = Literal[
    "known",
    "unknown",
    "vacuous",
    "underspecified",
    "blocked",
    "missing",
    "not_applicable",
]


class ConceptViewAppError(Exception):
    """Base class for expected concept-view failures."""


class ConceptViewUnknownConceptError(ConceptViewAppError):
    def __init__(self, concept_id_or_name: str) -> None:
        super().__init__(f"Concept '{concept_id_or_name}' not found.")
        self.concept_id_or_name = concept_id_or_name


@dataclass(frozen=True)
class ConceptViewRequest:
    concept_id_or_name: str
    repository_view: AppRepositoryViewRequest = field(default_factory=AppRepositoryViewRequest)
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)


@dataclass(frozen=True)
class ConceptViewForm:
    state: ConceptViewState
    form_name: str | None
    unit: str | None
    range_text: str | None
    sentence: str


@dataclass(frozen=True)
class ConceptViewStatus:
    state: ConceptViewState
    concept_status: str | None
    visible_claim_count: int
    blocked_claim_count: int
    total_claim_count: int
    reason: str


@dataclass(frozen=True)
class ConceptClaimEntry:
    claim_id: str
    logical_id: str | None
    claim_type: str
    value_display: str
    condition_display: str
    status_state: ConceptViewState
    status_reason: str


@dataclass(frozen=True)
class ConceptClaimGroup:
    claim_type: str
    visible_count: int
    blocked_count: int
    entries: tuple[ConceptClaimEntry, ...]
    sentence: str


@dataclass(frozen=True)
class ConceptValueSummary:
    state: ConceptViewState
    claim_count: int
    unit: str | None
    sentence: str


@dataclass(frozen=True)
class ConceptUncertaintySummary:
    state: ConceptViewState
    claim_count: int
    sentence: str


@dataclass(frozen=True)
class ConceptProvenanceSummary:
    state: ConceptViewState
    claim_count: int
    source_count: int
    papers: tuple[str, ...]
    sentence: str


@dataclass(frozen=True)
class ConceptRelatedClaimLink:
    claim_id: str
    logical_id: str | None
    relation: str
    sentence: str


@dataclass(frozen=True)
class ConceptViewReport:
    concept_id: str
    logical_id: str | None
    artifact_id: str | None
    version_id: str | None
    heading: str
    canonical_name: str | None
    definition: str | None
    domain: str | None
    kind_type: str | None
    form: ConceptViewForm
    status: ConceptViewStatus
    render_policy: RenderPolicySummary
    repository_state: str
    claim_groups: tuple[ConceptClaimGroup, ...]
    value_summary: ConceptValueSummary
    uncertainty_summary: ConceptUncertaintySummary
    provenance_summary: ConceptProvenanceSummary
    related_claim_links: tuple[ConceptRelatedClaimLink, ...]


def build_concept_view(repo: Repository, request: ConceptViewRequest) -> ConceptViewReport:
    repository_state = repository_view_label(request.repository_view)
    policy = build_render_policy(request.render_policy)
    with open_app_world_model(repo) as world:
        resolved_concept_id = world.resolve_concept(request.concept_id_or_name)
        concept_row = world.get_concept(request.concept_id_or_name)
        if concept_row is None:
            raise ConceptViewUnknownConceptError(request.concept_id_or_name)
        concept_id = str(concept_row.concept_id)
        concept_entry = _resolve_concept_entry(
            repo,
            request.concept_id_or_name,
            resolved_concept_id=resolved_concept_id,
            concept_id=concept_id,
            canonical_name=concept_row.canonical_name,
        )

        visible_claims = tuple(world.claims_with_policy(concept_id, policy))
        all_claims = (
            tuple(world.claims_related_to_concept(concept_id))
            if policy.include_blocked
            else visible_claims
        )

    artifact_id = str(concept_entry.record.artifact_id) if concept_entry is not None else concept_id
    version_id = None if concept_entry is None else concept_entry.record.version_id
    logical_id = (
        concept_entry.record.primary_logical_id
        if concept_entry is not None
        else concept_row.primary_logical_id
    )
    claim_groups = _claim_groups(all_claims, visible_claims)
    return ConceptViewReport(
        concept_id=concept_id,
        logical_id=logical_id,
        artifact_id=artifact_id,
        version_id=version_id,
        heading=f"Concept {concept_row.canonical_name}",
        canonical_name=concept_row.canonical_name,
        definition=concept_row.definition,
        domain=concept_row.domain,
        kind_type=concept_row.kind_type,
        form=_concept_form(concept_row, concept_entry, visible_claims),
        status=_concept_status(concept_row, all_claims, visible_claims),
        render_policy=summarize_render_policy(policy),
        repository_state=repository_state,
        claim_groups=claim_groups,
        value_summary=_value_summary(visible_claims),
        uncertainty_summary=_uncertainty_summary(visible_claims),
        provenance_summary=_provenance_summary(visible_claims),
        related_claim_links=_related_claim_links(concept_id, visible_claims),
    )


def _resolve_concept_entry(
    repo: Repository,
    handle: str,
    *,
    resolved_concept_id: str | None,
    concept_id: str,
    canonical_name: str,
):
    for candidate in (handle, resolved_concept_id, concept_id, canonical_name):
        if candidate is None:
            continue
        concept_entry = _find_concept_entry(repo, candidate)
        if concept_entry is not None:
            return concept_entry
    return None


def _concept_form(concept_row, concept_entry, visible_claims) -> ConceptViewForm:
    units = sorted({claim.unit for claim in visible_claims if claim.unit})
    unit = units[0] if len(units) == 1 else None
    range_text = None
    if concept_entry is not None and concept_entry.record.range is not None:
        lower, upper = concept_entry.record.range
        range_text = f"{lower} to {upper}"
    if concept_row.form is None:
        return ConceptViewForm(
            state="missing",
            form_name=None,
            unit=unit,
            range_text=range_text,
            sentence="Concept form is missing.",
        )
    if unit is not None:
        sentence = f"Concept form is {concept_row.form} with visible unit {unit}."
    elif units:
        sentence = f"Concept form is {concept_row.form} with multiple visible units."
    else:
        sentence = f"Concept form is {concept_row.form}."
    return ConceptViewForm(
        state="known",
        form_name=concept_row.form,
        unit=unit,
        range_text=range_text,
        sentence=sentence,
    )


def _concept_status(concept_row, all_claims, visible_claims) -> ConceptViewStatus:
    total_claim_count = len(all_claims)
    visible_claim_count = len(visible_claims)
    blocked_claim_count = total_claim_count - visible_claim_count
    concept_status = None if concept_row.status is None else concept_row.status.value
    if total_claim_count == 0:
        return ConceptViewStatus(
            state="missing",
            concept_status=concept_status,
            visible_claim_count=0,
            blocked_claim_count=0,
            total_claim_count=0,
            reason="No claims refer to this concept.",
        )
    if visible_claim_count == 0:
        return ConceptViewStatus(
            state="blocked",
            concept_status=concept_status,
            visible_claim_count=0,
            blocked_claim_count=blocked_claim_count,
            total_claim_count=total_claim_count,
            reason="Claims for this concept are blocked under the current render policy.",
        )
    return ConceptViewStatus(
        state="known",
        concept_status=concept_status,
        visible_claim_count=visible_claim_count,
        blocked_claim_count=blocked_claim_count,
        total_claim_count=total_claim_count,
        reason="Concept is readable under the current render policy.",
    )


def _claim_groups(all_claims, visible_claims) -> tuple[ConceptClaimGroup, ...]:
    visible_by_id = {str(claim.claim_id): claim for claim in visible_claims}
    all_groups: dict[str, list[ClaimRow]] = defaultdict(list)
    blocked_counts: dict[str, int] = defaultdict(int)
    for claim in sorted(all_claims, key=_claim_sort_key):
        claim_type = _claim_type_text(claim)
        all_groups[claim_type].append(claim)
        if str(claim.claim_id) not in visible_by_id:
            blocked_counts[claim_type] += 1

    groups: list[ConceptClaimGroup] = []
    for claim_type in sorted(all_groups):
        visible_entries = tuple(
            _concept_claim_entry(claim)
            for claim in sorted(
                (claim for claim in all_groups[claim_type] if str(claim.claim_id) in visible_by_id),
                key=_claim_sort_key,
            )
        )
        visible_count = len(visible_entries)
        blocked_count = blocked_counts[claim_type]
        if blocked_count == 0:
            sentence = f"{visible_count} visible {claim_type} claims refer to this concept."
        else:
            sentence = (
                f"{visible_count} visible {claim_type} claims and {blocked_count} blocked "
                "claims refer to this concept."
            )
        groups.append(
            ConceptClaimGroup(
                claim_type=claim_type,
                visible_count=visible_count,
                blocked_count=blocked_count,
                entries=visible_entries,
                sentence=sentence,
            )
        )
    return tuple(groups)


def _concept_claim_entry(claim) -> ConceptClaimEntry:
    condition_display = "(vacuous)" if not claim.conditions_cel else cast(str, claim.conditions_cel)
    return ConceptClaimEntry(
        claim_id=str(claim.claim_id),
        logical_id=claim.primary_logical_id,
        claim_type=_claim_type_text(claim),
        value_display=_value_display(claim),
        condition_display=condition_display,
        status_state="known",
        status_reason="Claim is visible under the current render policy.",
    )


def _value_summary(visible_claims) -> ConceptValueSummary:
    value_claims = tuple(claim for claim in visible_claims if claim.value is not None)
    if not value_claims:
        return ConceptValueSummary(
            state="missing",
            claim_count=0,
            unit=None,
            sentence="Visible claims do not provide a value summary.",
        )
    units = sorted({claim.unit for claim in value_claims if claim.unit})
    unit = units[0] if len(units) == 1 else None
    if unit is not None:
        sentence = f"{len(value_claims)} visible claims provide values in {unit}."
    elif units:
        sentence = f"{len(value_claims)} visible claims provide values in multiple units."
    else:
        sentence = f"{len(value_claims)} visible claims provide values."
    return ConceptValueSummary(
        state="known",
        claim_count=len(value_claims),
        unit=unit,
        sentence=sentence,
    )


def _uncertainty_summary(visible_claims) -> ConceptUncertaintySummary:
    uncertain_claims = tuple(claim for claim in visible_claims if _claim_has_uncertainty(claim))
    if not uncertain_claims:
        return ConceptUncertaintySummary(
            state="missing",
            claim_count=0,
            sentence="Visible claims do not provide uncertainty information.",
        )
    return ConceptUncertaintySummary(
        state="known",
        claim_count=len(uncertain_claims),
        sentence=f"{len(uncertain_claims)} visible claims provide uncertainty information.",
    )


def _provenance_summary(visible_claims) -> ConceptProvenanceSummary:
    claims_with_provenance = tuple(
        claim for claim in visible_claims if claim.provenance is not None or claim.source is not None
    )
    if not claims_with_provenance:
        return ConceptProvenanceSummary(
            state="missing",
            claim_count=0,
            source_count=0,
            papers=(),
            sentence="Visible claims do not provide provenance.",
        )
    sources = {
        claim.source.slug or claim.source.source_id
        for claim in claims_with_provenance
        if claim.source is not None and (claim.source.slug or claim.source.source_id)
    }
    papers = tuple(
        sorted(
            {
                claim.provenance.paper
                for claim in claims_with_provenance
                if claim.provenance is not None and claim.provenance.paper is not None
            }
        )
    )
    return ConceptProvenanceSummary(
        state="known",
        claim_count=len(claims_with_provenance),
        source_count=len(sources),
        papers=papers,
        sentence=(
            f"{len(claims_with_provenance)} visible claims provide provenance "
            f"across {len(sources)} sources."
        ),
    )


def _related_claim_links(concept_id: str, visible_claims) -> tuple[ConceptRelatedClaimLink, ...]:
    links: list[ConceptRelatedClaimLink] = []
    for claim in sorted(visible_claims, key=_claim_sort_key):
        if str(claim.output_concept_id or "") == concept_id:
            relation = "instantiates"
            sentence = f"Claim {claim.primary_logical_value or claim.claim_id} instantiates this concept."
        elif str(claim.target_concept) == concept_id:
            relation = "targets"
            sentence = f"Claim {claim.primary_logical_value or claim.claim_id} targets this concept."
        else:
            relation = "related"
            sentence = f"Claim {claim.primary_logical_value or claim.claim_id} refers to this concept."
        links.append(
            ConceptRelatedClaimLink(
                claim_id=str(claim.claim_id),
                logical_id=claim.primary_logical_id,
                relation=relation,
                sentence=sentence,
            )
        )
    return tuple(links)


def _claim_type_text(claim) -> str:
    if claim.claim_type is None:
        return "unknown"
    return claim.claim_type.value


def _value_display(claim) -> str:
    if claim.value is None:
        return "(missing)"
    return f"{claim.value} {claim.unit or ''}".rstrip()


def _claim_has_uncertainty(claim) -> bool:
    return (
        claim.uncertainty is not None
        or claim.lower_bound is not None
        or claim.upper_bound is not None
        or claim.sample_size is not None
    )


def _claim_sort_key(claim) -> tuple[str, str]:
    logical_id = claim.primary_logical_id or ""
    return (logical_id, str(claim.claim_id))
