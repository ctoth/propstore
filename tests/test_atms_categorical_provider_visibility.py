"""WS-I Step 3: categorical parameterization inputs must be visible."""

from __future__ import annotations

import json

from propstore.world.atms import ATMSDerivedNode
from propstore.world.types import ATMSNodeStatus, ATMSOutKind

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_ws_i_categorical_provider_creates_visible_rejected_derived_node() -> None:
    """E.H3: categorical providers are rejected explicitly, not silently dropped."""

    store = _ATMSStore(
        claims=[
            {
                "id": "color_claim",
                "concept_id": "paint_color",
                "type": "parameter",
                "value": "red",
            }
        ],
        parameterizations=[
            {
                "output_concept_id": "paint_score",
                "concept_ids": json.dumps(["paint_color"]),
                "sympy": "Eq(paint_score, paint_color + 1)",
                "formula": "score = color + 1",
                "conditions_cel": None,
            }
        ],
    )

    engine = _make_bound(store).atms_engine()
    rejected_nodes = [
        node
        for node in engine._nodes.values()
        if isinstance(node, ATMSDerivedNode) and node.concept_id == "paint_score"
    ]

    assert len(rejected_nodes) == 1
    status = engine.node_status(rejected_nodes[0].node_id)
    assert status.status is ATMSNodeStatus.OUT
    assert status.out_kind is ATMSOutKind.PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE
    assert "color_claim" in status.reason
    assert "paint_color" in status.reason
