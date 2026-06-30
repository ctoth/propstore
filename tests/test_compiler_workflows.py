"""Compiler workflows: validate / build, sharing ONE check set (PLAN.md §12.6).

These pin the Z1 abort-vs-quarantine split:

* schema-structural / form-concept-context validation failures and a structural
  concept in a CEL expression ABORT (both workflows, identically);
* a semantically invalid *claim* is QUARANTINED (blocked, build proceeds).

The sidecar materialisation (9-0-rest-B) and the WorldQuery-backed conflict
summary (9-1) are not in this tree yet, so ``build_repository`` honestly reports
``sidecar_missing`` and never fabricates a sidecar.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from condition_ir import KindType

from propstore.compiler.errors import CompilerWorkflowError
from propstore.compiler.workflows import build_repository, validate_repository
from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.forms import FormDefinition
from propstore.repository import Repository


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path)
    repo.families.concept.save(
        "freq", Concept(concept_id="freq", canonical_name="frequency"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="Ctx1"), message="m"
    )
    return repo


def _structural_concept() -> Concept:
    return Concept(
        concept_id="shape",
        canonical_name="shape",
        lexical_entry=LexicalEntry(
            identifier="e:shape",
            canonical_form=LexicalForm(written_rep="shape", language="en"),
            senses=(LexicalSense(reference=OntologyReference(uri="u:shape")),),
            physical_dimension_form="shape_form",
        ),
    )


# --- happy path ------------------------------------------------------------ #


def test_validate_clean_repo_is_ok(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.families.claim.save(
        "c1",
        Claim(claim_id="c1", context_id="ctx1", claim_type=ClaimType.OBSERVATION, statement="x"),
        message="m",
    )
    summary = validate_repository(repo)
    assert summary.ok
    assert summary.concept_count == 1
    assert summary.claim_count == 1


def test_build_materializes_sidecar(tmp_path: Path) -> None:
    # 9-0-rest-B filled the materialize seam: build now writes the content-addressed
    # world sidecar and reports it honestly (no longer ``sidecar_missing``).
    repo = _repo(tmp_path)
    repo.families.claim.save(
        "c1",
        Claim(claim_id="c1", context_id="ctx1", claim_type=ClaimType.OBSERVATION, statement="x"),
        message="m",
    )
    report = build_repository(repo)
    assert report.sidecar_missing is False
    assert report.rebuilt is True
    assert report.concept_count == 1
    assert report.claim_count == 1
    assert report.conflicts == ()
    assert report.derived_store is not None
    assert Path(report.derived_store.path).is_file()
    # quire owns rebuild-on-change: an unchanged repo is not rebuilt.
    assert build_repository(repo).rebuilt is False


def test_empty_repo_reports_no_concepts(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    summary = validate_repository(repo)
    assert summary.no_concepts
    report = build_repository(repo)
    assert report.no_concepts


# --- Z1 QUARANTINE: claim semantic invalidity does not abort --------------- #


def test_invalid_claim_quarantines_not_aborts(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    # PARAMETER requires output_concept; omitting it is a contract violation.
    repo.families.claim.save(
        "bad", Claim(claim_id="bad", context_id="ctx1", claim_type=ClaimType.PARAMETER), message="m"
    )
    # validate does not raise; it reports the diagnostic.
    summary = validate_repository(repo)
    assert not summary.ok
    assert any(d.code == "claim.contract" for d in summary.errors)
    # build does not raise either; the claim is quarantined (blocked).
    report = build_repository(repo)
    assert report.claim_count == 1
    assert report.blocked_claim_count == 1


# --- Z1 ABORT: structural / form / concept / context failures -------------- #


def test_duplicate_context_aborts(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.families.context.save(
        "ctx1b", Context(context_id="ctx1", name="dup"), message="m"
    )
    with pytest.raises(CompilerWorkflowError):
        build_repository(repo)
    with pytest.raises(CompilerWorkflowError):
        validate_repository(repo)


def test_structural_concept_in_cel_aborts_both_workflows(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    repo.families.form.save(
        "shape_form", FormDefinition(name="shape_form", kind=KindType.STRUCTURAL), message="m"
    )
    repo.families.concept.save("shape", _structural_concept(), message="m")
    repo.families.context.save("ctx1", Context(context_id="ctx1", name="Ctx1"), message="m")
    repo.families.claim.save(
        "c1",
        Claim(
            claim_id="c1",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            statement="x",
            conditions=("shape == 1",),
        ),
        message="m",
    )
    with pytest.raises(CompilerWorkflowError) as excinfo:
        build_repository(repo)
    assert any(d.code == "cel.structural_in_expression" for d in excinfo.value.messages)
    with pytest.raises(CompilerWorkflowError):
        validate_repository(repo)


def test_invalid_form_aborts(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    repo.families.concept.save(
        "c", Concept(concept_id="c", canonical_name="C"), message="m"
    )
    repo.families.form.save(
        "bad",
        FormDefinition(name="bad", kind=KindType.QUANTITY, is_dimensionless=True, dimensions={"mass": 1}),
        message="m",
    )
    with pytest.raises(CompilerWorkflowError):
        build_repository(repo)
