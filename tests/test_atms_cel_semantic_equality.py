"""WS-I Step 6: ATMS antecedent matching uses CEL semantic equality.

Charter-native port: the antecedent matcher must treat CEL-equivalent
conditions (``a == b`` vs ``b == a``) as matching the same assumption rather
than splitting them by raw string.
"""

from __future__ import annotations

from condition_ir import ConditionSolver, check_condition_ir, checked_condition_set

from propstore.core.environment import AssumptionRef
from propstore.core.id_types import to_assumption_id
from propstore.core.labels import assumption_label
from propstore.world.atms import ATMSAssumptionNode
from tests.atms_feed import ClaimSpec, build_bound, registry_for_sources


def test_ws_i_exact_antecedent_sets_match_commuted_cel_equality() -> None:
    """Codex #26: CEL-equivalent antecedents must not be split by raw strings."""

    registry = registry_for_sources(("a == 1", "b == 1"))
    bound = build_bound(claims=[ClaimSpec("c_a", "concept1", value=1.0)])
    engine = bound.atms_engine()
    # Override the engine's solver registry with one that knows ``a`` and ``b``.
    object.__setattr__(engine._runtime, "condition_registry", registry)

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
        label=assumption_label(left_ref.assumption_id),
    )
    engine._nodes[right_node_id] = ATMSAssumptionNode(
        node_id=right_node_id,
        assumption=right_ref,
        label=assumption_label(right_ref.assumption_id),
    )

    antecedent_sets = engine._exact_antecedent_sets(
        checked_condition_set([check_condition_ir("a == b", registry)])
    )

    assert (left_node_id,) in antecedent_sets
    assert (right_node_id,) in antecedent_sets


def test_condition_solver_proves_commuted_equality_equivalent() -> None:
    registry = registry_for_sources(("a == b", "b == a"))
    solver = ConditionSolver(registry)
    assert solver.are_equivalent(
        checked_condition_set([check_condition_ir("a == b", registry)]),
        checked_condition_set([check_condition_ir("b == a", registry)]),
    )
