"""WS-I Step 4: contradictory derived values must become visible conflicts.

Charter-native port of the reference test (the row-dict ``_ATMSStore`` is
replaced by the ``tests.atms_feed`` charter feed).
"""

from __future__ import annotations

from propstore.core.labels import make_environment_key
from propstore.world.types import ValueStatus
from tests.atms_feed import ClaimSpec, ParamSpec, assumption_id_for, build_bound


def _derived_conflict_bound():
    return build_bound(
        claims=[
            ClaimSpec("claim_a", "concept1", value=1.0, conditions=("a == 1",)),
            ClaimSpec("claim_b", "concept2", value=2.0, conditions=("b == 2",)),
        ],
        parameterizations=[
            ParamSpec("concept3", ("concept1",), "Eq(concept3, concept1)", "z = a"),
            ParamSpec("concept3", ("concept2",), "Eq(concept3, concept2)", "z = b"),
        ],
        bindings={"a": 1, "b": 2},
    )


def test_ws_i_derived_value_collects_all_compatible_parameterizations() -> None:
    """Codex #24: first-compatible derived values cannot hide later disagreement."""

    bound = _derived_conflict_bound()
    result = bound.derived_value("concept3")
    assert result.status is ValueStatus.CONFLICTED
    assert result.value is None


def test_ws_i_derived_derived_contradictions_feed_atms_nogoods() -> None:
    """Codex #24: derived-vs-derived conflicts become ATMS nogood environments."""

    bound = _derived_conflict_bound()
    expected_nogood = make_environment_key(
        assumption_ids=(
            assumption_id_for(bound, "a == 1"),
            assumption_id_for(bound, "b == 2"),
        )
    )
    assert expected_nogood in bound.atms_engine().nogoods.environments
