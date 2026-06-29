"""The opinion is doxa's; propstore pairs it with typed provenance.

These tests cover ``doxa.Opinion`` *as propstore uses it* (the honesty-relevant
constructors and the dogmatic opt-in) plus the propstore delta — the
provenance pairing. They do NOT re-test doxa's internal algebra (consensus, WBF,
CCF, …): doxa owns and tests that itself.
"""

from __future__ import annotations

import pytest
from doxa import BetaEvidence, Opinion

from propstore.opinion_provenance import OpinionWithProvenance, opinion_or_vacuous
from propstore.provenance import Provenance, ProvenanceStatus


# --- doxa.Opinion as propstore relies on it (Jøsang 2001) ---


def test_construct_dogmatic_without_flag_raises() -> None:
    with pytest.raises(ValueError, match="allow_dogmatic"):
        Opinion(1.0, 0.0, 0.0, 0.5)


def test_construct_dogmatic_with_flag_succeeds() -> None:
    op = Opinion(1.0, 0.0, 0.0, 0.5, allow_dogmatic=True)
    assert op.expectation() == 1.0


def test_named_dogmatic_constructors_opt_in() -> None:
    assert Opinion.dogmatic_true(0.5).u == 0.0
    assert Opinion.dogmatic_false(0.5).u == 0.0


def test_beta_evidence_conversion_rejects_dogmatic_symmetrically() -> None:
    dogmatic = Opinion.dogmatic_true(0.5)
    with pytest.raises(ValueError, match="dogmatic"):
        dogmatic.to_beta_evidence()
    assert BetaEvidence(10.0, 0.0, 0.5).to_opinion().u > 0.0


def test_vacuous_opinion_is_total_ignorance() -> None:
    vac = Opinion.vacuous(0.4)
    assert vac.uncertainty == 1.0
    assert vac.base_rate == 0.4


# --- The propstore delta: the provenance pairing holds-a doxa.Opinion ---


def _stated() -> Provenance:
    return Provenance(status=ProvenanceStatus.STATED, operations=("test",))


def test_pairing_holds_a_doxa_opinion_by_composition() -> None:
    opinion = Opinion.from_probability(0.8, 10.0, 0.5)
    pair = OpinionWithProvenance(opinion=opinion, provenance=_stated())

    # It HOLDS the doxa opinion (identity), it does not re-spell it.
    assert pair.opinion is opinion
    assert isinstance(pair.opinion, Opinion)
    # Read-through accessors forward to the held opinion.
    assert pair.uncertainty == opinion.uncertainty
    assert pair.base_rate == opinion.base_rate
    assert pair.expectation() == opinion.expectation()
    assert pair.provenance.status is ProvenanceStatus.STATED


def test_missing_opinion_becomes_vacuous_not_fabricated() -> None:
    pair = opinion_or_vacuous(None, base_rate=0.3)

    assert isinstance(pair.opinion, Opinion)
    assert pair.opinion == Opinion.vacuous(0.3)
    assert pair.is_vacuous
    assert pair.base_rate == 0.3
    # Absence is recorded honestly as VACUOUS provenance.
    assert pair.provenance.status is ProvenanceStatus.VACUOUS


def test_present_opinion_is_paired_with_supplied_provenance() -> None:
    opinion = Opinion.from_evidence(8.0, 2.0, 0.5)
    pair = opinion_or_vacuous(opinion, base_rate=0.5, provenance=_stated())

    assert pair.opinion is opinion
    assert not pair.is_vacuous
    assert pair.provenance.status is ProvenanceStatus.STATED
