"""WS-D closure sentinel."""

from __future__ import annotations

from pathlib import Path

from propstore.opinion import Opinion, wbf
from propstore.world.types import apply_decision_criterion


def test_workstream_d_done() -> None:
    manifest = Path(__file__).parent / "data" / "subjective_logic_canonical.yaml"

    assert manifest.exists()
    assert wbf(
        Opinion(0.10, 0.30, 0.60, 0.5),
        Opinion(0.40, 0.20, 0.40, 0.5),
        Opinion(0.70, 0.10, 0.20, 0.5),
    ).u < 0.3
    assert apply_decision_criterion(
        0.5,
        0.2,
        0.3,
        0.7,
        confidence=None,
        criterion="pignistic",
    ).value == 0.65
    assert apply_decision_criterion(
        0.5,
        0.2,
        0.3,
        0.7,
        confidence=None,
        criterion="projected_probability",
    ).value == 0.71
