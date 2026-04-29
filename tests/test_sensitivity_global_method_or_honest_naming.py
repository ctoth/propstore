from __future__ import annotations

import pytest

from propstore.sensitivity import SensitivityEntry, SensitivityResult


def test_sensitivity_result_names_local_oat_method():
    """Cluster F #16: local derivatives must identify themselves as local OAT."""
    result = SensitivityResult(
        concept_id="out",
        formula="out = x1 * x2",
        entries=[
            SensitivityEntry(
                input_concept_id="x1",
                partial_derivative_expr="x2",
                partial_derivative_value=1.0,
                elasticity=1.0,
            )
        ],
    )

    assert result.method == "local_oat"


def test_global_sensitivity_api_reports_variance_decomposition():
    """Cluster F #16: an interaction model needs a global method, not only OAT."""
    from propstore.sensitivity import GlobalSensitivityResult

    result = GlobalSensitivityResult(
        concept_id="out",
        method="sobol_total",
        first_order={"x1": 0.43, "x2": 0.43},
        total={"x1": 0.57, "x2": 0.57},
    )

    assert result.method == "sobol_total"
    assert result.total["x1"] > result.first_order["x1"]
    assert result.total["x2"] > result.first_order["x2"]
    assert sum(result.first_order.values()) == pytest.approx(0.86)
