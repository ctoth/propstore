"""Dogmatic subjective opinions must be explicit.

Jøsang (2001, p.6) treats dogmatic opinions as the u=0 limit case.
Propstore requires callers to opt in when constructing that limit directly.
"""

from __future__ import annotations

import pytest

from propstore.opinion import BetaEvidence, Opinion


def test_construct_dogmatic_without_flag_raises() -> None:
    with pytest.raises(ValueError, match="allow_dogmatic"):
        Opinion(1.0, 0.0, 0.0, 0.5)


def test_construct_dogmatic_with_flag_succeeds() -> None:
    op = Opinion(
        1.0,
        0.0,
        0.0,
        0.5,
        allow_dogmatic=True,  # tautology citation: Josang 2001 dogmatic opinion has u=0.
    )

    assert op.expectation() == 1.0


def test_named_dogmatic_constructors_opt_in() -> None:
    assert Opinion.dogmatic_true(0.5).u == 0.0
    assert Opinion.dogmatic_false(0.5).u == 0.0


def test_beta_evidence_conversion_rejects_dogmatic_symmetrically() -> None:
    dogmatic = Opinion.dogmatic_true(0.5)

    with pytest.raises(ValueError, match="dogmatic"):
        dogmatic.to_beta_evidence()

    assert BetaEvidence(10.0, 0.0, 0.5).to_opinion().u > 0.0
