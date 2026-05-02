"""WS-I Step 6: ATMS antecedent matching uses CEL semantic equality."""

from __future__ import annotations

from propstore.core.conditions import (
    ConditionSolver,
    check_condition_ir,
    checked_condition_set,
)
from propstore.core.id_types import to_assumption_id
from propstore.core.labels import AssumptionRef, Label
from propstore.world.atms import ATMSAssumptionNode
from tests.atms_helpers import condition_registry_for_sources

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_ws_i_exact_antecedent_sets_match_commuted_cel_equality() -> None:
    """Codex #26: CEL-equivalent antecedents must not be split by raw strings."""

    registry = condition_registry_for_sources(("a == 1", "b == 1"))
    engine = _make_bound(
        _ATMSStore(claims=[]),
        solver=ConditionSolver(registry),
    ).atms_engine()
    left_ref = AssumptionRef(
        assumption_id=to_assumption_id("left_equality"),
        kind="binding",
        source="test",
        cel="a == b",
    )
    right_ref = AssumptionRef(
        assumption_id=to_assumption_id("right_equality"),
        kind="binding",
        source="test",
        cel="b == a",
    )
    left_node_id = "assumption:left_equality"
    right_node_id = "assumption:right_equality"
    engine._nodes[left_node_id] = ATMSAssumptionNode(
        node_id=left_node_id,
        assumption=left_ref,
        label=Label.singleton(left_ref),
    )
    engine._nodes[right_node_id] = ATMSAssumptionNode(
        node_id=right_node_id,
        assumption=right_ref,
        label=Label.singleton(right_ref),
    )

    antecedent_sets = engine._exact_antecedent_sets(
        checked_condition_set([check_condition_ir("a == b", registry)])
    )

    assert (left_node_id,) in antecedent_sets
    assert (right_node_id,) in antecedent_sets
