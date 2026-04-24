from __future__ import annotations

from typing import TYPE_CHECKING

from .mutation import (
    ConceptAlignmentBuildRequest,
    ConceptAlignmentDecisionRequest,
    ConceptAlignmentQueryReport,
    ConceptAlignmentQueryRequest,
    ConceptAlignmentQueryScore,
    ConceptAlignmentReport,
    ConceptDisplayError,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


def build_concept_alignment(
    repo: Repository,
    request: ConceptAlignmentBuildRequest,
) -> ConceptAlignmentReport:
    from propstore.source import align_sources

    artifact = align_sources(repo, list(request.sources))
    return ConceptAlignmentReport(alignment_id=artifact.id)


def query_concept_alignment(
    repo: Repository,
    request: ConceptAlignmentQueryRequest,
) -> ConceptAlignmentQueryReport:
    from propstore.source import load_alignment_artifact

    try:
        _, artifact = load_alignment_artifact(repo, request.cluster_id)
    except FileNotFoundError as exc:
        raise ConceptDisplayError(
            f"Concept alignment '{request.cluster_id}' not found"
        ) from exc
    if request.operator is not None:
        scores = artifact.queries.operator_scores.get(request.operator, {})
        return ConceptAlignmentQueryReport(
            scores=tuple(
                ConceptAlignmentQueryScore(argument_id=str(argument_id), score=score)
                for argument_id, score in sorted(scores.items())
            )
        )
    accepted = (
        artifact.queries.skeptical_acceptance
        if request.mode == "skeptical"
        else artifact.queries.credulous_acceptance
    )
    return ConceptAlignmentQueryReport(
        accepted_argument_ids=tuple(str(argument_id) for argument_id in accepted)
    )


def decide_concept_alignment(
    repo: Repository,
    request: ConceptAlignmentDecisionRequest,
) -> ConceptAlignmentReport:
    from propstore.source import decide_alignment

    updated = decide_alignment(
        repo,
        request.cluster_id,
        accept=list(request.accepted),
        reject=list(request.rejected),
    )
    return ConceptAlignmentReport(alignment_id=updated.id)


def promote_concept_alignment(
    repo: Repository,
    cluster_id: str,
) -> ConceptAlignmentReport:
    from propstore.source import promote_alignment

    updated = promote_alignment(repo, cluster_id)
    return ConceptAlignmentReport(alignment_id=updated.id)
