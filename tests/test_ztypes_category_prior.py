"""Category-prior tests for honest ignorance."""

from __future__ import annotations

from propstore.calibrate import (
    CalibrationSource,
    CategoryPrior,
    categorical_to_opinion,
)
from propstore.core.base_rates import BaseRateUnresolved
from propstore.provenance import Provenance, ProvenanceStatus


def _prior(category: str, value: float) -> CategoryPrior:
    return CategoryPrior(
        category=category,
        value=value,
        source=CalibrationSource.USER_DEFAULT,
        provenance=Provenance(
            status=ProvenanceStatus.DEFAULTED,
            witnesses=(),
            operations=("test_prior",),
        ),
    )


def test_uncalibrated_category_without_prior_is_unresolved():
    result = categorical_to_opinion("strong", 1)

    assert isinstance(result, BaseRateUnresolved)
    assert result.reason == "missing_base_rate"
    assert result.missing_fields == ("category_prior",)


def test_non_vacuous_base_rate_requires_explicit_category_prior():
    op = categorical_to_opinion("strong", 1, prior=_prior("strong", 0.7))

    assert op.u == 1.0
    assert op.a == 0.7
    assert op.provenance is not None
    assert op.provenance.status == ProvenanceStatus.DEFAULTED


def test_calibration_counts_compose_with_explicit_prior_provenance():
    op = categorical_to_opinion(
        "strong",
        1,
        calibration_counts={(1, "strong"): (80, 100)},
        prior=_prior("strong", 0.7),
    )

    assert op.u < 1.0
    assert op.a == 0.7
    assert op.provenance is not None
    assert op.provenance.status == ProvenanceStatus.DEFAULTED
    assert "categorical_calibration_counts" in op.provenance.operations


def test_category_prior_must_match_requested_category():
    prior = _prior("weak", 0.3)

    try:
        categorical_to_opinion("strong", 1, prior=prior)
    except ValueError as exc:
        assert "does not match category" in str(exc)
    else:
        raise AssertionError("mismatched CategoryPrior must fail")
