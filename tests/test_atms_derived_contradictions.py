"""WS-I Step 4: contradictory derived values must become visible conflicts."""

from __future__ import annotations

import json

from propstore.core.labels import EnvironmentKey
from propstore.world.types import ValueStatus

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_ws_i_derived_value_collects_all_compatible_parameterizations() -> None:
    """Codex #24: first-compatible derived values cannot hide later disagreement."""

    bound = _derived_conflict_bound()

    result = bound.derived_value("concept3")

    assert result.status is ValueStatus.CONFLICTED
    assert result.value is None


def test_ws_i_derived_derived_contradictions_feed_atms_nogoods() -> None:
    """Codex #24: derived-vs-derived conflicts become ATMS nogood environments."""

    bound = _derived_conflict_bound()
    assumption_ids = {
        assumption.cel: assumption.assumption_id
        for assumption in bound._environment.assumptions
    }
    expected_nogood = EnvironmentKey((
        assumption_ids["a == 1"],
        assumption_ids["b == 2"],
    ))

    assert expected_nogood in bound.atms_engine().nogoods.environments


def _derived_conflict_bound():
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_a",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["a == 1"]),
            },
            {
                "id": "claim_b",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["b == 2"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept3",
                "concept_ids": json.dumps(["concept1"]),
                "sympy": "Eq(concept3, concept1)",
                "formula": "z = a",
                "conditions_cel": None,
            },
            {
                "output_concept_id": "concept3",
                "concept_ids": json.dumps(["concept2"]),
                "sympy": "Eq(concept3, concept2)",
                "formula": "z = b",
                "conditions_cel": None,
            },
        ],
    )
    return _make_bound(store, bindings={"a": 1, "b": 2})
