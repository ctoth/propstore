"""WBF regression tests against van der Heijden et al. 2018.

Paper anchors are the actual PDF page numbers:
- Definition 4 and Remarks 2-3: p.5.
- Table I numerical example: p.8.
"""

import pytest

from propstore.opinion import Opinion, wbf


def test_wbf_table_i_three_source_matches_paper() -> None:
    """van der Heijden et al. 2018 Table I (p.8), WBF column."""
    a1 = Opinion(0.10, 0.30, 0.60, 0.5)
    a2 = Opinion(0.40, 0.20, 0.40, 0.5)
    a3 = Opinion(0.70, 0.10, 0.20, 0.5)

    result = wbf(a1, a2, a3)

    assert result.b == pytest.approx(0.562, abs=5e-4)
    assert result.d == pytest.approx(0.146, abs=5e-4)
    assert result.u == pytest.approx(0.292, abs=5e-4)
    assert result.a == pytest.approx(0.5, abs=1e-12)


def test_wbf_definition_4_base_rate_is_confidence_weighted() -> None:
    """Definition 4 (p.5) defines a_hat from confidence weights."""
    a1 = Opinion(0.10, 0.30, 0.60, 0.2)
    a2 = Opinion(0.40, 0.20, 0.40, 0.5)
    a3 = Opinion(0.70, 0.10, 0.20, 0.8)

    result = wbf(a1, a2, a3)

    expected_a = ((0.2 * 0.4) + (0.5 * 0.6) + (0.8 * 0.8)) / (0.4 + 0.6 + 0.8)
    assert result.a == pytest.approx(expected_a, abs=1e-12)


def test_wbf_single_dogmatic_source_dominates_finite_evidence() -> None:
    """Definition 4 case 2 / Remark 2 (p.5): dogmatic evidence dominates."""
    dogmatic = Opinion.dogmatic_true(0.3)
    finite = Opinion(0.10, 0.30, 0.60, 0.7)

    result = wbf(dogmatic, finite)

    assert result.b == pytest.approx(1.0, abs=1e-12)
    assert result.d == pytest.approx(0.0, abs=1e-12)
    assert result.u == pytest.approx(0.0, abs=1e-12)
    assert result.a == pytest.approx(0.3, abs=1e-12)


def test_wbf_all_vacuous_remains_vacuous_with_average_base_rate() -> None:
    """Definition 4 case 3 / Remark 3 (p.5): no evidence stays no evidence."""
    result = wbf(Opinion.vacuous(0.2), Opinion.vacuous(0.8))

    assert result.b == pytest.approx(0.0, abs=1e-12)
    assert result.d == pytest.approx(0.0, abs=1e-12)
    assert result.u == pytest.approx(1.0, abs=1e-12)
    assert result.a == pytest.approx(0.5, abs=1e-12)
