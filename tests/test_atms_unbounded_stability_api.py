"""WS-I Step 1: ATMS future-query APIs must not silently truncate."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import propstore.world.atms as atms_module
from propstore.world.types import ATMSNodeStatus, QueryableAssumption

from tests.test_atms_engine import _ATMSStore, _assertion_node_id, _make_bound


def _budget_exhausted_type() -> type[BaseException]:
    return getattr(atms_module, "BudgetExhausted")


def _flip_world(*, queryable_count: int = 12, flip_index: int = 8):
    condition = f"q{flip_index} == {flip_index}"
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept_future",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": f'["{condition}"]',
            }
        ],
    )
    bound = _make_bound(store)
    queryables = [
        QueryableAssumption.from_cel(f"q{index} == {index}")
        for index in range(queryable_count)
    ]
    return bound, _assertion_node_id(bound, "claim_future"), queryables


def test_ws_i_unbounded_stability_finds_witness_beyond_old_default_budget() -> None:
    """E.H1a: de Kleer 1986 p.144 labels require full minimal environment coverage."""

    bound, node_id, queryables = _flip_world(queryable_count=12, flip_index=8)

    assert bound.atms_engine().is_stable(node_id, queryables, limit=None) is False
    report = bound.atms_engine().node_stability(node_id, queryables, limit=None)
    assert report.stable is False
    assert report.witnesses[0].queryable_cels == ("q8 == 8",)


def test_ws_i_budget_exhaustion_is_loud_and_counted() -> None:
    """E.H1a/b/c: budgeted replay raises instead of returning a guessed verdict."""

    bound, node_id, queryables = _flip_world(queryable_count=12, flip_index=8)
    BudgetExhausted = _budget_exhausted_type()

    with pytest.raises(BudgetExhausted) as exc_info:
        bound.atms_engine().is_stable(node_id, queryables, limit=8)

    assert exc_info.value.examined == 8
    assert exc_info.value.total == 4096


def test_ws_i_stability_relevance_and_intervention_limit_is_required_keyword() -> None:
    """Codex 2.9: the old no-budget-call shape is deleted, not preserved."""

    bound, node_id, queryables = _flip_world(queryable_count=3, flip_index=1)

    with pytest.raises(TypeError):
        bound.atms_engine().is_stable(node_id, queryables)
    with pytest.raises(TypeError):
        bound.atms_engine().node_relevance(node_id, queryables)
    with pytest.raises(TypeError):
        bound.atms_engine().node_interventions(node_id, queryables, ATMSNodeStatus.IN)


def test_ws_i_propstore_call_sites_pass_explicit_limit_keyword() -> None:
    """Codex 2.9: callers must declare unbounded or budgeted semantics explicitly."""

    targets = {"is_stable", "node_relevance", "node_interventions"}
    offenders: list[str] = []
    for path in Path("propstore").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            name = function.attr if isinstance(function, ast.Attribute) else None
            if name not in targets:
                continue
            if any(keyword.arg == "limit" for keyword in node.keywords):
                continue
            offenders.append(f"{path}:{node.lineno}:{name}")

    assert offenders == []


@given(flip_index=st.integers(min_value=0, max_value=4))
@pytest.mark.property
@settings(max_examples=8)
def test_ws_i_budgeted_stability_is_monotone_when_a_verdict_is_reached(
    flip_index: int,
) -> None:
    """PROPERTY-BASED-TDD WS-I: increasing a successful budget cannot fail."""

    bound, node_id, queryables = _flip_world(queryable_count=5, flip_index=flip_index)
    BudgetExhausted = _budget_exhausted_type()
    budget = flip_index + 1

    first = bound.atms_engine().is_stable(node_id, queryables, limit=budget)
    try:
        second = bound.atms_engine().is_stable(node_id, queryables, limit=budget + 1)
    except BudgetExhausted as exc:  # pragma: no cover - assertion explains the law.
        raise AssertionError(
            f"limit={budget} reached verdict {first!r}, but limit={budget + 1} exhausted"
        ) from exc

    assert second is first
