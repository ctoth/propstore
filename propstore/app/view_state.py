"""The view tier's single state vocabulary and honest-ignorance routing.

Every per-field view state in the ``app`` view-builders is one
:class:`ViewState`. The enum carries a distinct ``UNKNOWN`` member (PLAN.md
§12.4): a render-time outcome the system genuinely cannot decide — a value only
available through context *lifting*, a claim defeated by an *exception*, or a
condition the solver returned ``UNKNOWN`` for — is ``UNKNOWN``, which is **not**
``BLOCKED`` (present but hidden by policy) and **not** ``MISSING`` (no data was
authored). Collapsing those three into one would erase the honest-ignorance
signal the design checklist requires.

The routing functions below map the substrate-owned outcome enums
(``condition_ir`` solver results, :class:`propstore.defeasibility.ClaimApplicability`,
:class:`propstore.context_lifting.LiftingDecisionStatus`) onto :class:`ViewState`.
They are the single place the view tier decides "indeterminate ⇒ unknown"; the
build_claim_view / build_concept_view state machines consume them rather than
re-deciding per field.
"""

from __future__ import annotations

from enum import StrEnum

from condition_ir import SolverResult, SolverSat, SolverUnsat

from propstore.context_lifting import LiftingDecisionStatus
from propstore.defeasibility import ClaimApplicability


class ViewState(StrEnum):
    """A per-field render state in the owner-layer view tier.

    ``StrEnum`` so each member lowers to its string value through
    :func:`propstore.reporting.json_ready` and compares equal to that string,
    keeping the report payloads stable across the CLI and web adapters.
    """

    KNOWN = "known"
    UNKNOWN = "unknown"
    VACUOUS = "vacuous"
    UNDERSPECIFIED = "underspecified"
    BLOCKED = "blocked"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE = "unavailable"


def lifting_view_state(status: LiftingDecisionStatus) -> ViewState:
    """Route a context-lifting decision onto a view state.

    A ``LIFTED`` value is not asserted directly in the viewing context — its
    truth here rode in through a lifting rule, so the conservative view state is
    ``UNKNOWN`` rather than ``KNOWN``. ``UNKNOWN`` (gate undecided) is likewise
    ``UNKNOWN``; only an explicit ``BLOCKED`` lift is ``BLOCKED``.
    """

    if status is LiftingDecisionStatus.BLOCKED:
        return ViewState.BLOCKED
    return ViewState.UNKNOWN


def applicability_view_state(applicability: ClaimApplicability) -> ViewState:
    """Route a defeasible-applicability verdict onto a view state.

    ``HOLDS`` is ``KNOWN``; an ``EXCEPTED`` claim (defeated by a justified
    exception) and an ``UNKNOWN`` verdict (solver could not decide) are both the
    honest ``UNKNOWN`` — the claim exists, but its value here is undetermined.
    """

    if applicability is ClaimApplicability.HOLDS:
        return ViewState.KNOWN
    return ViewState.UNKNOWN


def solver_view_state(result: SolverResult) -> ViewState:
    """Route a condition-ir solver result onto a view state.

    A satisfiable condition is ``KNOWN``; an unsatisfiable one makes the field
    ``NOT_APPLICABLE`` (it cannot hold in this frame); a solver ``UNKNOWN``
    (timeout, incompleteness) is the honest ``UNKNOWN``.
    """

    if isinstance(result, SolverSat):
        return ViewState.KNOWN
    if isinstance(result, SolverUnsat):
        return ViewState.NOT_APPLICABLE
    return ViewState.UNKNOWN
