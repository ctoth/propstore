"""PLAN.md §12.4 — the distinct ``unknown`` view state.

The view tier needs an ``unknown`` state that is neither ``blocked`` (present but
policy-hidden) nor ``missing`` (no data authored). A value reached only by
context *lifting*, a claim defeated by an *exception*, and a condition the solver
returned ``UNKNOWN`` for all route to ``unknown`` — collapsing any of them into
``blocked``/``missing`` would erase the honest-ignorance signal.
"""

from __future__ import annotations

from condition_ir import SolverSat, SolverUnknown, SolverUnknownReason, SolverUnsat

from propstore.app.view_state import (
    ViewState,
    applicability_view_state,
    lifting_view_state,
    solver_view_state,
)
from propstore.context_lifting import LiftingDecisionStatus
from propstore.defeasibility import ClaimApplicability


def test_unknown_is_distinct_from_blocked_and_missing() -> None:
    assert ViewState.UNKNOWN != ViewState.BLOCKED
    assert ViewState.UNKNOWN != ViewState.MISSING
    assert ViewState.BLOCKED != ViewState.MISSING
    assert len({ViewState.UNKNOWN, ViewState.BLOCKED, ViewState.MISSING}) == 3
    assert ViewState.UNKNOWN.value == "unknown"


def test_lifted_routes_to_unknown() -> None:
    assert lifting_view_state(LiftingDecisionStatus.LIFTED) is ViewState.UNKNOWN
    assert lifting_view_state(LiftingDecisionStatus.UNKNOWN) is ViewState.UNKNOWN
    assert lifting_view_state(LiftingDecisionStatus.BLOCKED) is ViewState.BLOCKED


def test_excepted_and_unknown_applicability_route_to_unknown() -> None:
    assert applicability_view_state(ClaimApplicability.EXCEPTED) is ViewState.UNKNOWN
    assert applicability_view_state(ClaimApplicability.UNKNOWN) is ViewState.UNKNOWN
    assert applicability_view_state(ClaimApplicability.HOLDS) is ViewState.KNOWN


def test_solver_unknown_routes_to_unknown() -> None:
    unknown = SolverUnknown(reason=SolverUnknownReason.TIMEOUT, hint="timed out")
    assert solver_view_state(unknown) is ViewState.UNKNOWN
    assert solver_view_state(SolverSat()) is ViewState.KNOWN
    assert solver_view_state(SolverUnsat()) is ViewState.NOT_APPLICABLE


def test_unknown_routes_never_collapse_to_blocked_or_missing() -> None:
    # The three indeterminate sources must never produce blocked/missing.
    routed = {
        lifting_view_state(LiftingDecisionStatus.LIFTED),
        applicability_view_state(ClaimApplicability.EXCEPTED),
        solver_view_state(
            SolverUnknown(reason=SolverUnknownReason.INCOMPLETE, hint="incomplete")
        ),
    }
    assert routed == {ViewState.UNKNOWN}
    assert ViewState.BLOCKED not in routed
    assert ViewState.MISSING not in routed
