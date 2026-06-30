"""Application-layer single-concept view report — the per-section state machine.

:func:`build_concept_view` lowers one charter
:class:`~propstore.families.concepts.Concept` and the claims that refer to it into
a :class:`ConceptViewReport`. Each section (form / status / value / uncertainty /
provenance) carries its own :class:`ViewState` and a natural-language sentence,
honest about the charter's shape: the concept's *form* derives from its lemon
``physical_dimension_form`` (``MISSING`` when the concept has no lexical entry);
provenance is always ``MISSING`` because charter claims carry none. Claims are
grouped by type; the visible/blocked split is a render-time decision read off the
policy.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from collections.abc import Sequence

from propstore.app.claim_views import claim_display_id, claim_type_text
from propstore.app.rendering import RenderPolicySummary, summarize_render_policy
from propstore.app.view_state import ViewState
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.reporting import JsonReportMixin
from propstore.world import RenderPolicy, WorldQuery


class ConceptViewAppError(Exception):
    """Base class for expected concept-view failures."""


class ConceptViewUnknownConceptError(ConceptViewAppError):
    def __init__(self, concept_id_or_name: str) -> None:
        super().__init__(f"Concept '{concept_id_or_name}' not found.")
        self.concept_id_or_name = concept_id_or_name


@dataclass(frozen=True)
class ConceptViewForm:
    state: ViewState
    form_name: str | None
    unit: str | None
    sentence: str


@dataclass(frozen=True)
class ConceptViewStatus:
    state: ViewState
    concept_status: str
    visible_claim_count: int
    blocked_claim_count: int
    total_claim_count: int
    reason: str


@dataclass(frozen=True)
class ConceptClaimEntry:
    claim_id: str
    claim_type: str
    value_display: str
    condition_display: str
    status_state: ViewState
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
    state: ViewState
    claim_count: int
    unit: str | None
    sentence: str


@dataclass(frozen=True)
class ConceptUncertaintySummary:
    state: ViewState
    claim_count: int
    sentence: str


@dataclass(frozen=True)
class ConceptProvenanceSummary:
    state: ViewState
    claim_count: int
    sentence: str


@dataclass(frozen=True)
class ConceptRelatedClaimLink:
    claim_id: str
    relation: str
    sentence: str


@dataclass(frozen=True)
class ConceptViewReport(JsonReportMixin):
    concept_id: str
    heading: str
    canonical_name: str
    definition: str | None
    concept_status: str
    form: ConceptViewForm
    status: ConceptViewStatus
    claim_groups: tuple[ConceptClaimGroup, ...]
    value_summary: ConceptValueSummary
    uncertainty_summary: ConceptUncertaintySummary
    provenance_summary: ConceptProvenanceSummary
    related_claim_links: tuple[ConceptRelatedClaimLink, ...]
    render_policy: RenderPolicySummary


def build_concept_view(
    world: WorldQuery, concept_id_or_name: str, *, policy: RenderPolicy
) -> ConceptViewReport:
    """Render one concept and its referring claims into a view report.

    Raises :class:`ConceptViewUnknownConceptError` when the concept does not
    exist. When ``policy.include_blocked`` is set the report exposes the
    visible/blocked claim split; otherwise only visible claims are read (the
    blocked ones remain in storage, simply unread here).
    """

    concept = world.get_concept(concept_id_or_name)
    if concept is None:
        raise ConceptViewUnknownConceptError(concept_id_or_name)
    concept_id = str(concept.concept_id)
    visible_claims = list(world.claims_with_policy(concept_id, policy))
    all_claims = (
        list(world.claims_for(concept_id)) if policy.include_blocked else visible_claims
    )
    return ConceptViewReport(
        concept_id=concept_id,
        heading=f"Concept {concept.canonical_name}",
        canonical_name=concept.canonical_name,
        definition=concept.definition,
        concept_status=concept.status.value,
        form=_concept_form(concept, visible_claims),
        status=_concept_status(concept, all_claims, visible_claims),
        claim_groups=_claim_groups(all_claims, visible_claims),
        value_summary=_value_summary(visible_claims),
        uncertainty_summary=_uncertainty_summary(visible_claims),
        provenance_summary=_provenance_summary(visible_claims),
        related_claim_links=_related_claim_links(concept_id, visible_claims),
        render_policy=summarize_render_policy(policy),
    )


def _single_unit(claims: Sequence[Claim]) -> str | None:
    units = sorted({claim.unit for claim in claims if claim.unit})
    return units[0] if len(units) == 1 else None


def _concept_form(concept: Concept, visible_claims: Sequence[Claim]) -> ConceptViewForm:
    unit = _single_unit(visible_claims)
    entry = concept.lexical_entry
    form_name = None if entry is None else entry.physical_dimension_form
    if form_name is None:
        return ConceptViewForm(
            state=ViewState.MISSING,
            form_name=None,
            unit=unit,
            sentence="Concept form is missing.",
        )
    if unit is not None:
        sentence = f"Concept form is {form_name} with visible unit {unit}."
    else:
        sentence = f"Concept form is {form_name}."
    return ConceptViewForm(
        state=ViewState.KNOWN,
        form_name=form_name,
        unit=unit,
        sentence=sentence,
    )


def _concept_status(
    concept: Concept,
    all_claims: Sequence[Claim],
    visible_claims: Sequence[Claim],
) -> ConceptViewStatus:
    total = len(all_claims)
    visible = len(visible_claims)
    blocked = total - visible
    status_value = concept.status.value
    if total == 0:
        return ConceptViewStatus(
            state=ViewState.MISSING,
            concept_status=status_value,
            visible_claim_count=0,
            blocked_claim_count=0,
            total_claim_count=0,
            reason="No claims refer to this concept.",
        )
    if visible == 0:
        return ConceptViewStatus(
            state=ViewState.BLOCKED,
            concept_status=status_value,
            visible_claim_count=0,
            blocked_claim_count=blocked,
            total_claim_count=total,
            reason="Claims for this concept are blocked under the current render policy.",
        )
    return ConceptViewStatus(
        state=ViewState.KNOWN,
        concept_status=status_value,
        visible_claim_count=visible,
        blocked_claim_count=blocked,
        total_claim_count=total,
        reason="Concept is readable under the current render policy.",
    )


def _claim_groups(
    all_claims: Sequence[Claim], visible_claims: Sequence[Claim]
) -> tuple[ConceptClaimGroup, ...]:
    visible_ids = {str(claim.claim_id) for claim in visible_claims}
    grouped: dict[str, list[Claim]] = defaultdict(list)
    blocked_counts: dict[str, int] = defaultdict(int)
    for claim in sorted(all_claims, key=_claim_sort_key):
        claim_type = claim_type_text(claim)
        grouped[claim_type].append(claim)
        if str(claim.claim_id) not in visible_ids:
            blocked_counts[claim_type] += 1

    groups: list[ConceptClaimGroup] = []
    for claim_type in sorted(grouped):
        entries = tuple(
            _concept_claim_entry(claim)
            for claim in sorted(grouped[claim_type], key=_claim_sort_key)
            if str(claim.claim_id) in visible_ids
        )
        visible_count = len(entries)
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
                entries=entries,
                sentence=sentence,
            )
        )
    return tuple(groups)


def _concept_claim_entry(claim: Claim) -> ConceptClaimEntry:
    condition = "; ".join(claim.conditions) if claim.conditions else "(vacuous)"
    return ConceptClaimEntry(
        claim_id=str(claim.claim_id),
        claim_type=claim_type_text(claim),
        value_display=_value_display(claim),
        condition_display=condition,
        status_state=ViewState.KNOWN,
        status_reason="Claim is visible under the current render policy.",
    )


def _value_summary(visible_claims: Sequence[Claim]) -> ConceptValueSummary:
    value_claims = [claim for claim in visible_claims if claim.value is not None]
    if not value_claims:
        return ConceptValueSummary(
            state=ViewState.MISSING,
            claim_count=0,
            unit=None,
            sentence="Visible claims do not provide a value summary.",
        )
    unit = _single_unit(value_claims)
    if unit is not None:
        sentence = f"{len(value_claims)} visible claims provide values in {unit}."
    else:
        sentence = f"{len(value_claims)} visible claims provide values."
    return ConceptValueSummary(
        state=ViewState.KNOWN,
        claim_count=len(value_claims),
        unit=unit,
        sentence=sentence,
    )


def _uncertainty_summary(visible_claims: Sequence[Claim]) -> ConceptUncertaintySummary:
    uncertain = [claim for claim in visible_claims if _has_uncertainty(claim)]
    if not uncertain:
        return ConceptUncertaintySummary(
            state=ViewState.MISSING,
            claim_count=0,
            sentence="Visible claims do not provide uncertainty information.",
        )
    return ConceptUncertaintySummary(
        state=ViewState.KNOWN,
        claim_count=len(uncertain),
        sentence=f"{len(uncertain)} visible claims provide uncertainty information.",
    )


def _provenance_summary(visible_claims: Sequence[Claim]) -> ConceptProvenanceSummary:
    # Charter claims are provenance-free (source rides on the git-notes sidecar,
    # not the claim row), so the claim-backed view honestly reports no provenance.
    return ConceptProvenanceSummary(
        state=ViewState.MISSING,
        claim_count=0,
        sentence="Visible claims do not carry provenance on the claim record.",
    )


def _related_claim_links(
    concept_id: str, visible_claims: Sequence[Claim]
) -> tuple[ConceptRelatedClaimLink, ...]:
    links: list[ConceptRelatedClaimLink] = []
    for claim in sorted(visible_claims, key=_claim_sort_key):
        display = claim_display_id(claim)
        if claim.output_concept == concept_id:
            relation = "instantiates"
            sentence = f"Claim {display} instantiates this concept."
        elif claim.target_concept == concept_id:
            relation = "targets"
            sentence = f"Claim {display} targets this concept."
        else:
            relation = "related"
            sentence = f"Claim {display} refers to this concept."
        links.append(
            ConceptRelatedClaimLink(
                claim_id=str(claim.claim_id),
                relation=relation,
                sentence=sentence,
            )
        )
    return tuple(links)


def _value_display(claim: Claim) -> str:
    if claim.value is None:
        return "(missing)"
    return f"{claim.value} {claim.unit or ''}".rstrip()


def _has_uncertainty(claim: Claim) -> bool:
    return (
        claim.uncertainty is not None
        or claim.lower_bound is not None
        or claim.upper_bound is not None
        or claim.sample_size is not None
    )


def _claim_sort_key(claim: Claim) -> str:
    return str(claim.claim_id)
