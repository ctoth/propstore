from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason=(
        "depends on WS-O-gun D-18 plus WS-M propstore consumer surfacing of "
        "ResultStatus.BUDGET_EXCEEDED"
    )
)
def test_praf_argument_enumeration_budget_surfaces_partial_result():
    """Codex 1.13 / D-18: no silent truncation of partial argument enumeration."""
    raise AssertionError("unskipped in WS-M when propstore consumes gunray EnumerationExceeded")
