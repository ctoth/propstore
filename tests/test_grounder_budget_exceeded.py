"""`ground` degrades to a budget-exceeded bundle when enumeration overflows."""

from __future__ import annotations

from types import SimpleNamespace

import gunray
import pytest

from propstore.grounding.bundle import SECTION_NAMES, GroundingStatus
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry


class _BudgetEvaluator:
    """A stand-in evaluator that always overflows its argument budget."""

    def evaluate_with_trace(
        self,
        theory: object,
        *,
        marking_policy: object,
        closure_policy: object,
        max_arguments: object,
    ) -> None:
        raise gunray.EnumerationExceeded(
            partial_arguments=("arg:partial",),
            max_arguments=1,
            partial_trace=SimpleNamespace(grounding_inspection="inspection"),
            partial_count=7,
            reason="budget hit",
        )


def test_budget_overflow_yields_budget_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gunray, "GunrayEvaluator", _BudgetEvaluator)
    bundle = ground((), (), PredicateRegistry.from_documents(()), max_arguments=1)
    assert bundle.status is GroundingStatus.BUDGET_EXCEEDED
    assert bundle.budget_reason == "budget hit"
    assert bundle.max_arguments == 1
    assert bundle.partial_candidate_count == 7
    assert bundle.arguments == ("arg:partial",)
    assert bundle.grounding_inspection == "inspection"
    assert set(bundle.sections.keys()) == set(SECTION_NAMES)
    assert all(bundle.sections[name] == {} for name in SECTION_NAMES)
