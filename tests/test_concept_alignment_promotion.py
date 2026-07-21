"""Established decision/promotion behavior over typed alignment artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
)
from propstore.families.alignment import AlignmentArgument, ConceptAlignmentRef
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.repository import Repository
from propstore.source.alignment import (
    _alignment_slug,
    build_alignment_artifact,
    concept_proposal_branch,
    decide_alignment,
    promote_alignment,
)


def _store_open_alignment(repo: Repository) -> str:
    ontology_reference = OntologyReference(uri="https://example.org/shared#gravity")
    lexical_entry = LexicalEntry(
        identifier="gravity",
        canonical_form=LexicalForm(written_rep="gravity", language="en"),
        senses=(LexicalSense(reference=ontology_reference),),
        physical_dimension_form="quantity",
    )
    artifact = build_alignment_artifact(
        [
            AlignmentArgument(
                id="arg:a",
                repository_origin="repo-a",
                source_commit="a" * 40,
                import_branch="import/repo-a",
                import_commit="b" * 40,
                concept_id="ps:concept:a",
                canonical_name="gravity",
                ontology_reference=ontology_reference,
                lexical_entry=lexical_entry,
                definition="Acceleration due to gravity.",
                form="quantity",
            )
        ]
    )
    branch = concept_proposal_branch(repo)
    if repo.require_git().branch_sha(branch) is None:
        repo.require_git().create_branch(branch)
    repo.families.concept_alignments.save(
        ConceptAlignmentRef(_alignment_slug(artifact.alignment_id)),
        artifact,
        message="store alignment",
    )
    return artifact.alignment_id


def test_decide_then_promote_writes_canonical_concept(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    cluster_id = _store_open_alignment(repo)
    artifact = repo.families.concept_alignments.require(
        ConceptAlignmentRef(_alignment_slug(cluster_id))
    )

    decided = decide_alignment(
        repo, cluster_id, accept=[artifact.arguments[0].id], reject=[]
    )
    assert decided.decision.status == "decided"
    assert list(repo.families.concept.iter_refs()) == []

    promoted = promote_alignment(repo, cluster_id)
    assert promoted.decision.status == "promoted"
    assert promoted.decision.promoted_concept is not None

    concept_id = derive_concept_artifact_id("gravity")
    concept = repo.families.concept.require(concept_id)
    assert concept.canonical_name == "gravity"
    assert concept.lexical_entry is not None
    assert concept.lexical_entry.canonical_form.written_rep == "gravity"
    assert concept.lexical_entry.physical_dimension_form is None

    reloaded = repo.families.concept_alignments.require(
        ConceptAlignmentRef(_alignment_slug(cluster_id))
    )
    assert reloaded.decision.status == "promoted"


def test_promote_without_accept_is_rejected(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    cluster_id = _store_open_alignment(repo)

    with pytest.raises(ValueError, match="No accepted alternatives"):
        promote_alignment(repo, cluster_id)


def test_concept_proposal_branch_is_fixed() -> None:
    assert concept_proposal_branch() == "proposal/concepts"
