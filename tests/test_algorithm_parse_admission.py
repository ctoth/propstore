"""Algorithm parse obligations reach the real claim admission pipeline (#26)."""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.claim_contracts import validate_claim
from propstore.compiler.workflows import (
    build_repository,
    compile_repository_checked_bundle,
    validate_repository,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.repository import Repository


def _algorithm(claim_id: str, body: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        claim_type=ClaimType.ALGORITHM,
        output_concept="output",
        body=body,
    )


@pytest.mark.parametrize("body", ["def", "answer = 42"])
def test_invalid_algorithm_reports_its_parse_failure(body: str) -> None:
    report = validate_claim(_algorithm("invalid", body))

    assert any(
        problem.field == "body" and "parse error" in problem.message
        for problem in report.diagnostics
    )
    assert "AlgorithmParseCheck" not in report.deferred_checks


@pytest.mark.parametrize(
    "body",
    [
        "def compute(x):\n    doubled = x * 2\n    return doubled\n",
        "async def compute(x):\n    return x\n",
        "def compute(xs):\n    return sum(x * x for x in xs)\n",
    ],
)
def test_valid_algorithm_keeps_its_existing_admission(body: str) -> None:
    report = validate_claim(_algorithm("valid", body))

    assert report.diagnostics == ()
    assert "AlgorithmParseCheck" not in report.deferred_checks


def test_repository_quarantines_invalid_algorithm_and_retains_both_claims(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path)
    repo.families.concept.save(
        "output",
        Concept(concept_id="output", canonical_name="output"),
        message="Declare output concept",
    )
    invalid = _algorithm("invalid", "def")
    valid = _algorithm("valid", "def compute():\n    return 42\n")
    for claim in (invalid, valid):
        repo.families.claim.save(claim.claim_id, claim, message="Author algorithm")

    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    assert [entry.claim.claim_id for entry in checked.claim_bundle.claims] == [
        "invalid",
        "valid",
    ]
    assert [
        entry.claim.claim_id for entry in checked.claim_bundle.blocked_claims
    ] == ["invalid"]
    assert [
        entry.claim.claim_id for entry in checked.claim_bundle.checked_claims
    ] == ["valid"]
    diagnostic = checked.claim_bundle.blocked_claims[0].diagnostics[0]
    assert diagnostic.code == "claim.contract"
    assert diagnostic.artifact_id == "invalid"
    assert "parse error" in diagnostic.message

    validation = validate_repository(repo)
    assert not validation.ok
    assert validation.claim_count == 2
    assert any(
        message.artifact_id == "invalid" and "parse error" in message.message
        for message in validation.errors
    )

    built = build_repository(repo)
    assert built.claim_count == 2
    assert built.blocked_claim_count == 1
    assert repo.families.claim.load("invalid") == invalid
    assert repo.families.claim.load("valid") == valid
