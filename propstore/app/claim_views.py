"""Application-layer single-claim view report — the per-field state machine.

:func:`build_claim_view` lowers one charter :class:`~propstore.families.claims.Claim`
into a :class:`ClaimViewReport`: each field (concept / value / uncertainty /
condition / provenance / status) carries its own :class:`ViewState` and a
natural-language *sentence*. The states are honest about the charter's actual
shape — the charter claim has no provenance (it lives in git notes), so the
provenance field renders ``MISSING`` rather than a fabricated source; a concept
reference present but unresolvable renders ``UNKNOWN`` (PLAN.md §12.4: the
referent exists, its identity does not), distinct from ``MISSING`` (no reference)
and ``BLOCKED`` (policy-hidden).

The builder takes an already-open :class:`~propstore.world.WorldQuery` and a
:class:`~propstore.world.RenderPolicy`; visibility is a render-time decision —
a claim hidden by the policy raises :class:`ClaimViewBlockedError` rather than
being silently dropped. The list/search summary surface lives in
:mod:`propstore.app.claims` and reuses the shared field helpers here.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.app.rendering import RenderPolicySummary, summarize_render_policy
from propstore.app.view_state import ViewState
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.reporting import JsonReportMixin
from propstore.world import RenderPolicy, WorldQuery

# Claim types whose assertion is not a single scalar value: an absent ``value``
# on one of these is expected (``NOT_APPLICABLE``), not a hole (``MISSING``).
_NON_SCALAR_CLAIM_TYPES = frozenset(
    {
        ClaimType.MECHANISM,
        ClaimType.LIMITATION,
        ClaimType.COMPARISON,
        ClaimType.ALGORITHM,
        ClaimType.EQUATION,
        ClaimType.MODEL,
    }
)
_TEXT_CLAIM_TYPES = frozenset(
    {
        ClaimType.OBSERVATION,
        ClaimType.COMPARISON,
        ClaimType.MECHANISM,
        ClaimType.LIMITATION,
    }
)


class ClaimViewAppError(Exception):
    """Base class for expected claim-view failures."""


class ClaimViewUnknownClaimError(ClaimViewAppError):
    def __init__(self, claim_id: str) -> None:
        super().__init__(f"Claim '{claim_id}' not found.")
        self.claim_id = claim_id


class ClaimViewBlockedError(ClaimViewAppError):
    def __init__(self, claim_id: str) -> None:
        super().__init__("Not Found")
        self.claim_id = claim_id


@dataclass(frozen=True)
class ClaimViewConcept:
    state: ViewState
    concept_id: str | None
    canonical_name: str | None
    form: str | None
    sentence: str


@dataclass(frozen=True)
class ClaimViewValue:
    state: ViewState
    value: float | None
    unit: str | None
    sentence: str


@dataclass(frozen=True)
class ClaimViewUncertainty:
    state: ViewState
    uncertainty: float | None
    uncertainty_type: str | None
    lower_bound: float | None
    upper_bound: float | None
    sample_size: int | None
    confidence: float | None
    sentence: str


@dataclass(frozen=True)
class ClaimViewCondition:
    state: ViewState
    expression: str | None
    sentence: str


@dataclass(frozen=True)
class ClaimViewProvenance:
    state: ViewState
    sentence: str


@dataclass(frozen=True)
class ClaimViewStatus:
    state: ViewState
    visible_under_policy: bool
    claim_status: str
    reason: str


@dataclass(frozen=True)
class ClaimViewReport(JsonReportMixin):
    claim_id: str
    heading: str
    name: str | None
    claim_type: str
    statement: str | None
    concept: ClaimViewConcept
    value: ClaimViewValue
    uncertainty: ClaimViewUncertainty
    condition: ClaimViewCondition
    provenance: ClaimViewProvenance
    status: ClaimViewStatus
    render_policy: RenderPolicySummary


def build_claim_view(
    world: WorldQuery, claim_id: str, *, policy: RenderPolicy
) -> ClaimViewReport:
    """Render one claim into a per-field view report under ``policy``.

    Raises :class:`ClaimViewUnknownClaimError` when the claim does not exist and
    :class:`ClaimViewBlockedError` when it exists but the policy hides it — the
    row is present in storage, so hiding is a render-time decision, surfaced
    honestly rather than collapsed to "not found".
    """

    claim = world.get_claim(claim_id)
    if claim is None:
        raise ClaimViewUnknownClaimError(claim_id)
    visible_ids = {str(row.claim_id) for row in world.claims_with_policy(None, policy)}
    if str(claim.claim_id) not in visible_ids:
        raise ClaimViewBlockedError(str(claim.claim_id))
    concept = claim_focus_concept(world, claim)
    concept_view = _claim_concept(claim, concept)
    return ClaimViewReport(
        claim_id=str(claim.claim_id),
        heading=f"Claim {claim_display_id(claim)}",
        name=claim.name,
        claim_type=claim_type_text(claim),
        statement=claim.statement,
        concept=concept_view,
        value=_claim_value(claim),
        uncertainty=_claim_uncertainty(claim),
        condition=_claim_condition(claim),
        provenance=_claim_provenance(),
        status=_claim_status(claim, True),
        render_policy=summarize_render_policy(policy),
    )


# ── shared field helpers (reused by the list/search summary surface) ──────────


def claim_type_text(claim: Claim) -> str:
    return "unknown" if claim.claim_type is None else claim.claim_type.value


def claim_display_id(claim: Claim) -> str:
    return claim.name or str(claim.claim_id)


def claim_focus_concept_id(claim: Claim) -> str | None:
    """The single concept this claim is *about*, when there is exactly one.

    The output concept (the concept whose value the claim asserts) wins; failing
    that, a lone entry in ``concepts``. A claim spanning multiple concepts has no
    single focus.
    """

    if claim.output_concept is not None:
        return claim.output_concept
    if len(claim.concepts) == 1:
        return claim.concepts[0]
    return None


def claim_focus_concept(world: WorldQuery, claim: Claim) -> Concept | None:
    concept_id = claim_focus_concept_id(claim)
    if concept_id is None:
        return None
    return world.get_concept(concept_id)


def _concept_form_name(concept: Concept) -> str | None:
    entry = concept.lexical_entry
    return None if entry is None else entry.physical_dimension_form


def _claim_concept(claim: Claim, concept: Concept | None) -> ClaimViewConcept:
    concept_id = claim_focus_concept_id(claim)
    if concept_id is None:
        return ClaimViewConcept(
            state=ViewState.NOT_APPLICABLE,
            concept_id=None,
            canonical_name=None,
            form=None,
            sentence="The claim has no single focus concept.",
        )
    if concept is None:
        return ClaimViewConcept(
            state=ViewState.UNKNOWN,
            concept_id=concept_id,
            canonical_name=None,
            form=None,
            sentence=(
                f"The claim references concept {concept_id}, "
                "which is not resolvable under the current view."
            ),
        )
    return ClaimViewConcept(
        state=ViewState.KNOWN,
        concept_id=str(concept.concept_id),
        canonical_name=concept.canonical_name,
        form=_concept_form_name(concept),
        sentence=f"The claim is about {concept.canonical_name}.",
    )


def _claim_value(claim: Claim) -> ClaimViewValue:
    if claim.value is None:
        if claim.claim_type in _NON_SCALAR_CLAIM_TYPES:
            return ClaimViewValue(
                state=ViewState.NOT_APPLICABLE,
                value=None,
                unit=claim.unit,
                sentence=f"Value is not applicable for a {claim_type_text(claim)} claim.",
            )
        return ClaimViewValue(
            state=ViewState.MISSING,
            value=None,
            unit=claim.unit,
            sentence="Value is missing.",
        )
    unit = claim.unit
    sentence = f"Value is {claim.value} {unit}." if unit else f"Value is {claim.value}."
    return ClaimViewValue(
        state=ViewState.KNOWN,
        value=claim.value,
        unit=unit,
        sentence=sentence,
    )


def _claim_uncertainty(claim: Claim) -> ClaimViewUncertainty:
    has_interval = claim.lower_bound is not None or claim.upper_bound is not None
    if (
        claim.uncertainty is None
        and not has_interval
        and claim.sample_size is None
        and claim.confidence is None
    ):
        return ClaimViewUncertainty(
            state=ViewState.MISSING,
            uncertainty=None,
            uncertainty_type=claim.uncertainty_type,
            lower_bound=None,
            upper_bound=None,
            sample_size=None,
            confidence=None,
            sentence="Uncertainty is missing.",
        )
    return ClaimViewUncertainty(
        state=ViewState.KNOWN,
        uncertainty=claim.uncertainty,
        uncertainty_type=claim.uncertainty_type,
        lower_bound=claim.lower_bound,
        upper_bound=claim.upper_bound,
        sample_size=claim.sample_size,
        confidence=claim.confidence,
        sentence="Uncertainty information is present.",
    )


def claim_condition_expression(claim: Claim) -> str | None:
    return "; ".join(claim.conditions) if claim.conditions else None


def _claim_condition(claim: Claim) -> ClaimViewCondition:
    expression = claim_condition_expression(claim)
    if expression is None:
        return ClaimViewCondition(
            state=ViewState.VACUOUS,
            expression=None,
            sentence="Conditions are vacuous; the claim has no explicit condition filter.",
        )
    return ClaimViewCondition(
        state=ViewState.KNOWN,
        expression=expression,
        sentence=f"Condition expression: {expression}",
    )


def _claim_provenance() -> ClaimViewProvenance:
    # The charter claim is provenance-free by construction (identity carries no
    # source); provenance rides on the git-notes sidecar, not the claim row, so
    # the sidecar-backed view honestly reports it absent rather than fabricating.
    return ClaimViewProvenance(
        state=ViewState.MISSING,
        sentence="Provenance is not carried on the claim record.",
    )


def claim_status_view(claim: Claim, visible: bool) -> ClaimViewStatus:
    status_value = claim.status.value
    if visible:
        return ClaimViewStatus(
            state=ViewState.KNOWN,
            visible_under_policy=True,
            claim_status=status_value,
            reason="Claim is visible under the current render policy.",
        )
    reason = (
        f"Claim is blocked under the current render policy because {status_value} "
        "claims are hidden."
    )
    return ClaimViewStatus(
        state=ViewState.BLOCKED,
        visible_under_policy=False,
        claim_status=status_value,
        reason=reason,
    )


_claim_status = claim_status_view
