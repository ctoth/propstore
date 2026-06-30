"""CLI adapter tests for the ``pks concept`` alignment lifecycle (Phase 10-1).

Ports the reference ``test_concept_alignment_cli`` to the rewrite owner API: the
``concept align`` / ``concept decide`` / ``concept promote`` adapters drive the
repository-bound lifecycle in :mod:`propstore.source.alignment` through the root
``cli`` lazy registry. Sources are seeded through the rewrite source owner
functions (``init_source_branch`` / ``commit_source_concept_proposal``) rather than
the source CLI, mirroring ``test_concept_alignment_promotion`` which owns the
non-CLI lifecycle assertions.
"""
from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result

from propstore.cli import cli
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.alignment import ConceptAlignmentRef
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.repository import Repository
from propstore.source import (
    init_source_branch,
    source_branch_name,
)
from propstore.source.concepts import commit_source_concept_proposal


def _alignment_slug(cluster_id: str) -> str:
    """The storage slug of an ``align:<slug>`` cluster id (CLI output token)."""

    return cluster_id.split(":", 1)[1] if ":" in cluster_id else cluster_id


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


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "concept", *args])


def test_align_decide_promote_writes_canonical_concept(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _seed_source(repo, "paper_a")
    _seed_source(repo, "paper_b")

    align = _invoke(
        repo,
        [
            "align",
            "--sources",
            source_branch_name("paper_a"),
            "--sources",
            source_branch_name("paper_b"),
        ],
    )
    assert align.exit_code == 0, align.output
    assert "align:" in align.output
    cluster_id = align.output.strip().split()[-1]

    slug = _alignment_slug(cluster_id)
    artifact = repo.families.concept_alignments.require(ConceptAlignmentRef(slug))
    first_arg = artifact.arguments[0].id

    decide = _invoke(repo, ["decide", cluster_id, "--accept", first_arg])
    assert decide.exit_code == 0, decide.output

    promote = _invoke(repo, ["promote", cluster_id])
    assert promote.exit_code == 0, promote.output

    concept_id = derive_concept_artifact_id("gravity")
    concept = repo.families.concept.require(concept_id)
    assert concept.canonical_name == "gravity"

    reloaded = repo.families.concept_alignments.require(ConceptAlignmentRef(slug))
    assert reloaded.decision.status == "promoted"


def test_promote_without_accept_fails(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _seed_source(repo, "paper_a")

    align = _invoke(repo, ["align", "--sources", source_branch_name("paper_a")])
    assert align.exit_code == 0, align.output
    cluster_id = align.output.strip().split()[-1]

    promote = _invoke(repo, ["promote", cluster_id])
    assert promote.exit_code != 0
    assert "No accepted alternatives" in promote.output
