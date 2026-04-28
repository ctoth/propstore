"""WS-I Step 2: cyclic support pruned by nogoods is not missing support."""

from __future__ import annotations

from propstore.core.labels import AssumptionRef, EnvironmentKey, Label, NogoodSet
from propstore.core.id_types import to_assumption_id
from propstore.world.atms import ATMSAssumptionNode, ATMSDerivedNode
from propstore.world.types import ATMSNodeStatus, ATMSOutKind

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_ws_i_cycle_whose_external_support_is_nogood_is_nogood_pruned() -> None:
    """E.H2: de Kleer 1986 p.146 cyclic assumption hierarchies need SCC resolution."""

    engine = _make_bound(_ATMSStore(claims=[])).atms_engine()
    assumption_a = AssumptionRef(
        assumption_id=to_assumption_id("cycle_a"),
        kind="binding",
        source="test",
        cel="a == 1",
    )
    assumption_b = AssumptionRef(
        assumption_id=to_assumption_id("cycle_b"),
        kind="binding",
        source="test",
        cel="b == 2",
    )
    node_a = "assumption:cycle_a"
    node_b = "assumption:cycle_b"
    d1 = engine._derived_node_id("cycle1", 1.0)
    d2 = engine._derived_node_id("cycle2", 2.0)

    engine._nodes[node_a] = ATMSAssumptionNode(
        node_id=node_a,
        assumption=assumption_a,
        label=Label.singleton(assumption_a),
    )
    engine._nodes[node_b] = ATMSAssumptionNode(
        node_id=node_b,
        assumption=assumption_b,
        label=Label.singleton(assumption_b),
    )
    engine._nodes[d1] = ATMSDerivedNode(
        node_id=d1,
        concept_id="cycle1",
        value=1.0,
        parameterization_index=1,
    )
    engine._nodes[d2] = ATMSDerivedNode(
        node_id=d2,
        concept_id="cycle2",
        value=2.0,
        parameterization_index=2,
    )
    engine.nogoods = NogoodSet([
        EnvironmentKey((to_assumption_id("cycle_a"), to_assumption_id("cycle_b")))
    ])
    engine._add_justification(
        antecedent_ids=(node_a, d2),
        consequent_id=d1,
        informant="cycle",
    )
    engine._add_justification(
        antecedent_ids=(node_b, d1),
        consequent_id=d2,
        informant="cycle",
    )

    status = engine.node_status(d1)

    assert status.status is ATMSNodeStatus.OUT
    assert status.out_kind is ATMSOutKind.NOGOOD_PRUNED
    assert status.reason == "exact-support environments were pruned by nogoods"
