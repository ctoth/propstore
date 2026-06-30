"""Authoring lints and diagnostic lowering (9-0-rest-B, scout-p9-map §B5).

The lints are advisory warnings the build appends to its messages;
``--strict-authoring`` (``build_repository(..., strict_authoring=True)``) upgrades
every one to an error and aborts. The lowering helpers turn pass / quarantine /
exception diagnostics into ``BuildDiagnostic`` rows.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.build_diagnostics import (
    QuarantineDiagnostic,
    build_exception_diagnostic,
    collect_authoring_lints,
    pass_to_build_diagnostic,
    quarantine_to_build_diagnostic,
    upgrade_lints_to_errors,
)
from propstore.compiler.errors import CompilerWorkflowError
from propstore.compiler.workflows import build_repository
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.registry import PropstoreFamily
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.stances import StanceType


def test_collect_lints_flags_unknown_type_and_missing_confidence() -> None:
    claims = (
        Claim(claim_id="ok", claim_type=ClaimType.OBSERVATION),
        Claim(claim_id="typeless", claim_type=None),
    )
    stances = (
        Stance(stance_id="s1", stance_type=StanceType.REBUTS, confidence=0.5),
        Stance(stance_id="s2", stance_type=StanceType.REBUTS, confidence=None),
        Stance(stance_id="u1", stance_type=StanceType.UNDERCUTS, confidence=0.5),
    )
    lints = collect_authoring_lints(claims=claims, stances=stances)
    codes = {lint.code for lint in lints}
    assert "authoring.claim_unknown_type" in codes
    assert "authoring.stance_missing_confidence" in codes
    assert "authoring.undercut_missing_target" in codes
    assert all(lint.is_warning for lint in lints)


def test_upgrade_lints_to_errors() -> None:
    lints = collect_authoring_lints(
        claims=(Claim(claim_id="x", claim_type=None),), stances=()
    )
    upgraded = upgrade_lints_to_errors(lints)
    assert all(lint.is_error for lint in upgraded)


def test_quarantine_lowers_to_blocking_row() -> None:
    diagnostic = quarantine_to_build_diagnostic(
        QuarantineDiagnostic(
            artifact_id="s1",
            kind="stance",
            diagnostic_kind="stance_validation",
            message="dangling",
        ),
        diagnostic_id="diag:1",
    )
    assert diagnostic.blocking == 1
    assert diagnostic.severity == "error"
    assert diagnostic.source_kind == "stance"
    assert diagnostic.source_ref == "s1"
    assert diagnostic.claim_id is None


def test_pass_warning_lowers_to_non_blocking_row() -> None:
    (lint,) = collect_authoring_lints(
        claims=(Claim(claim_id="x", claim_type=None),), stances=()
    )
    diagnostic = pass_to_build_diagnostic(lint, diagnostic_id="diag:2")
    assert diagnostic.blocking == 0
    assert diagnostic.severity == "warning"
    assert diagnostic.source_kind == PropstoreFamily.CLAIM.value
    assert diagnostic.claim_id == "x"


def test_build_exception_diagnostic_uses_message() -> None:
    diagnostic = build_exception_diagnostic(ValueError("boom"), diagnostic_id="diag:3")
    assert diagnostic.diagnostic_kind == "build_exception"
    assert diagnostic.blocking == 1
    assert "boom" in diagnostic.message


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save("ctx1", Context(context_id="ctx1", name="ctx"), message="m")
    return repo


def test_strict_authoring_aborts_on_lint(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    # A claim with no recognized type triggers an authoring lint.
    repo.families.claim.save(
        "cl1", Claim(claim_id="cl1", context_id="ctx1", claim_type=None), message="m"
    )
    with pytest.raises(CompilerWorkflowError):
        build_repository(repo, strict_authoring=True)
    # Without strict, the same repo builds and reports the lint as a warning.
    report = build_repository(repo)
    assert report.sidecar_missing is False
    assert report.warning_count >= 1
