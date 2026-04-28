"""Paper-anchored audit for subjective-logic operators."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from propstore.opinion import Opinion, ccf, consensus_pair, discount, wbf
from propstore.world.types import DecisionValueSource, apply_decision_criterion


MANIFEST = Path(__file__).parent / "data" / "subjective_logic_canonical.yaml"


def _manifest() -> dict[str, Any]:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _opinion(values: list[float]) -> Opinion:
    return Opinion(*values)


def _assert_opinion(result: Opinion, expected: list[float], tolerance: float) -> None:
    assert result.b == pytest.approx(expected[0], abs=tolerance)
    assert result.d == pytest.approx(expected[1], abs=tolerance)
    assert result.u == pytest.approx(expected[2], abs=tolerance)
    assert result.a == pytest.approx(expected[3], abs=tolerance)


@pytest.mark.parametrize("row", _manifest()["operators"], ids=lambda row: row["id"])
def test_subjective_logic_operator_manifest(row: dict[str, Any]) -> None:
    opinions = [_opinion(values) for values in row["inputs"]]
    tolerance = float(row.get("tolerance", 1e-12))

    if row["id"] == "negation":
        result = ~opinions[0]
    elif row["id"] == "conjunction":
        result = opinions[0].conjunction(opinions[1])
    elif row["id"] == "disjunction":
        result = opinions[0].disjunction(opinions[1])
    elif row["id"] == "consensus_pair":
        result = consensus_pair(opinions[0], opinions[1])
    elif row["id"] == "discount":
        result = discount(opinions[0], opinions[1])
    elif row["id"] == "maximize_uncertainty":
        result = opinions[0].maximize_uncertainty()
    elif row["id"] == "wbf":
        result = wbf(*opinions)
    elif row["id"] == "ccf":
        result = ccf(*opinions)
    else:
        raise AssertionError(f"unknown operator audit row {row['id']!r}")

    _assert_opinion(result, row["expected"], tolerance)


@pytest.mark.parametrize("row", _manifest()["scalars"], ids=lambda row: row["id"])
def test_subjective_logic_scalar_manifest(row: dict[str, Any]) -> None:
    b, d, u, a = row["input"]

    if row["id"] == "expectation":
        value = Opinion(b, d, u, a).expectation()
    else:
        decision = apply_decision_criterion(
            b,
            d,
            u,
            a,
            confidence=None,
            criterion=row["id"],
        )
        assert decision.source is DecisionValueSource.OPINION
        value = decision.value

    assert value == pytest.approx(row["expected"], abs=1e-12)


@pytest.mark.parametrize("row", _manifest()["comparisons"], ids=lambda row: row["id"])
def test_subjective_logic_comparison_manifest(row: dict[str, Any]) -> None:
    left = _opinion(row["left"])
    right = _opinion(row["right"])

    if row["relation"] == ">":
        assert left > right
    else:
        raise AssertionError(f"unknown comparison relation {row['relation']!r}")
