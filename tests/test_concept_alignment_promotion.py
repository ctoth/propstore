"""Phase 8-4: the repository-bound concept-alignment lifecycle.

Ports the owner-layer behaviour of the reference
``test_source_promotion_alignment::test_align_and_promote_alignment_use_artifact_store``
to the rewrite charters: ``align_sources`` records a proposal artifact on the
``proposal/concepts`` branch (never a source mutation), ``decide_alignment``
records an accept/reject decision, and ``promote_alignment`` is the single
proposal→source boundary that writes a canonical concept on an explicit accept.

The reference CLI surface (``test_concept_alignment_cli``) is Phase 10 and stays
recorded in docs/rewrite/deferred-tests.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.alignment import ConceptAlignmentRef
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.repository import Repository
from propstore.source import (
    align_sources,
    concept_proposal_branch,
    decide_alignment,
    init_source_branch,
    promote_alignment,
    source_branch_name,
)
from propstore.source.alignment import _alignment_slug
from propstore.source.concepts import commit_source_concept_proposal


def _seed_source(repo: Repository, name: str) -> None:
    init_source_branch(
        repo,
        name,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value=name,
    )
    commit_source_concept_proposal(
        repo,
        name,
        local_name="gravity",
        definition="Acceleration due to gravity.",
        form="quantity",
    )


def test_align_records_proposal_without_touching_canonical(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_source(repo, "paper_a")
    _seed_source(repo, "paper_b")

    artifact = align_sources(
        repo,
        [source_branch_name("paper_a"), source_branch_name("paper_b")],
    )

    slug = _alignment_slug(artifact.alignment_id)
    stored = repo.families.concept_alignments.require(ConceptAlignmentRef(slug))
    assert stored == artifact
    assert artifact.decision.status == "open"
    # Proposing never mutates the canonical corpus.
    assert list(repo.families.concept.iter_refs()) == []


def test_decide_then_promote_writes_canonical_concept(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_source(repo, "paper_a")
    _seed_source(repo, "paper_b")

    artifact = align_sources(
        repo,
        [source_branch_name("paper_a"), source_branch_name("paper_b")],
    )

    decided = decide_alignment(
        repo, artifact.alignment_id, accept=[artifact.arguments[0].id], reject=[]
    )
    assert decided.decision.status == "decided"
    # Deciding still writes nothing canonical.
    assert list(repo.families.concept.iter_refs()) == []

    promoted = promote_alignment(repo, artifact.alignment_id)
    assert promoted.decision.status == "promoted"
    assert promoted.decision.promoted_concept is not None

    concept_id = derive_concept_artifact_id("gravity")
    concept = repo.families.concept.require(concept_id)
    assert concept.canonical_name == "gravity"
    assert concept.lexical_entry is not None
    assert concept.lexical_entry.canonical_form.written_rep == "gravity"

    # The promotion decision is durable on the proposal branch.
    slug = _alignment_slug(artifact.alignment_id)
    reloaded = repo.families.concept_alignments.require(ConceptAlignmentRef(slug))
    assert reloaded.decision.status == "promoted"


def test_promote_without_accept_is_rejected(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_source(repo, "paper_a")

    artifact = align_sources(repo, [source_branch_name("paper_a")])

    with pytest.raises(ValueError, match="No accepted alternatives"):
        promote_alignment(repo, artifact.alignment_id)


def test_concept_proposal_branch_is_fixed() -> None:
    assert concept_proposal_branch() == "proposal/concepts"
