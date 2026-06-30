"""Owner-layer algorithm-claim comparison (Phase 10-0b).

``compare_algorithm_claims`` compares two algorithm claims' bodies via
``ast_equiv``. Missing claims raise :class:`UnknownClaimError`; a claim without an
algorithm body raises :class:`ClaimComparisonError`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.app.claims import (
    ClaimCompareReport,
    ClaimCompareRequest,
    ClaimComparisonError,
    UnknownClaimError,
    compare_algorithm_claims,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository
from propstore.world import WorldQuery


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save("A", Concept(concept_id="A", canonical_name="A"), message="m")
    repo.families.context.save("ctx1", Context(context_id="ctx1", name="ctx"), message="m")
    repo.families.claim.save(
        "alg1",
        Claim(
            claim_id="alg1",
            context_id="ctx1",
            claim_type=ClaimType.ALGORITHM,
            output_concept="A",
            body="def f(x):\n    return x * 2 + 1\n",
        ),
        message="m",
    )
    # Same computation, different surface (x*2 -> 2*x) — algebraically equivalent.
    repo.families.claim.save(
        "alg2",
        Claim(
            claim_id="alg2",
            context_id="ctx1",
            claim_type=ClaimType.ALGORITHM,
            output_concept="A",
            body="def f(x):\n    return 2 * x + 1\n",
        ),
        message="m",
    )
    # A parameter claim with no body.
    repo.families.claim.save(
        "p1",
        Claim(
            claim_id="p1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="A",
            value=3.0,
        ),
        message="m",
    )
    return repo


def test_compare_equivalent_algorithm_bodies(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path)) as world:
        report = compare_algorithm_claims(
            world, ClaimCompareRequest("alg1", "alg2")
        )
    assert isinstance(report, ClaimCompareReport)
    assert report.equivalent is True
    assert report.similarity == pytest.approx(1.0)
    assert report.to_json()["equivalent"] is True


def test_compare_unknown_claim_raises(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path)) as world:
        with pytest.raises(UnknownClaimError):
            compare_algorithm_claims(world, ClaimCompareRequest("alg1", "nope"))


def test_compare_non_algorithm_claim_raises(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path)) as world:
        with pytest.raises(ClaimComparisonError):
            compare_algorithm_claims(world, ClaimCompareRequest("alg1", "p1"))
