from __future__ import annotations

from propstore.world.atms import ATMSEngine

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_atms_build_marks_partial_state_past_iteration_ceiling(
    monkeypatch,
) -> None:
    bound = _make_bound(_ATMSStore(claims=[]))

    monkeypatch.setattr(ATMSEngine, "_propagate_labels", lambda self: None)
    monkeypatch.setattr(
        ATMSEngine,
        "_materialize_parameterization_justifications",
        lambda self: False,
    )
    monkeypatch.setattr(ATMSEngine, "_update_nogoods", lambda self: True)

    engine = ATMSEngine(bound, max_build_iterations=2)

    assert engine.fixpoint_reached is False
    assert engine.iterations_run == 2
    assert engine.warnings == (
        "ATMS build stopped before fixpoint after 2 iterations",
    )
