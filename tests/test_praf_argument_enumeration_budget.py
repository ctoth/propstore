from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason=(
        "ground() already returns a budget-exceeded bundle with partial arguments; "
        "production build/analysis callers do not yet accept max_arguments or "
        "propagate that incomplete bundle status into a Propstore analysis result"
    )
)
def test_praf_argument_enumeration_budget_surfaces_partial_result() -> None:
    """Production PrAF-facing results must expose an incomplete grounding bundle."""

    raise AssertionError(
        "unskipped when Propstore propagates incomplete grounding status"
    )
