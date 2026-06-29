from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason=(
        "depends on the gunray argument-enumeration budget surfacing "
        "ResultStatus.BUDGET_EXCEEDED through the propstore PrAF consumer (later phase)"
    )
)
def test_praf_argument_enumeration_budget_surfaces_partial_result() -> None:
    """No silent truncation of partial argument enumeration (gunray budget)."""

    raise AssertionError("unskipped when propstore consumes the gunray enumeration budget")
