from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.artifacts.refs import SourceRef, source_branch_name, source_finalize_relpath
from propstore.artifacts.types import ArtifactFamily, ResolvedArtifact
from propstore.source_documents import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
)

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


def _source_artifact(repo: Repository, ref: SourceRef, relpath: str) -> ResolvedArtifact:
    del repo
    return ResolvedArtifact(
        branch=source_branch_name(ref.name),
        relpath=relpath,
    )


SOURCE_DOCUMENT_FAMILY = ArtifactFamily[SourceRef, SourceDocument](
    name="source_document",
    doc_type=SourceDocument,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, "source.yaml"),
)

SOURCE_CONCEPTS_FAMILY = ArtifactFamily[SourceRef, SourceConceptsDocument](
    name="source_concepts",
    doc_type=SourceConceptsDocument,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, "concepts.yaml"),
)

SOURCE_CLAIMS_FAMILY = ArtifactFamily[SourceRef, SourceClaimsDocument](
    name="source_claims",
    doc_type=SourceClaimsDocument,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, "claims.yaml"),
)

SOURCE_JUSTIFICATIONS_FAMILY = ArtifactFamily[SourceRef, SourceJustificationsDocument](
    name="source_justifications",
    doc_type=SourceJustificationsDocument,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, "justifications.yaml"),
)

SOURCE_STANCES_FAMILY = ArtifactFamily[SourceRef, SourceStancesDocument](
    name="source_stances",
    doc_type=SourceStancesDocument,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, "stances.yaml"),
)

SOURCE_FINALIZE_REPORT_FAMILY = ArtifactFamily[SourceRef, SourceFinalizeReportDocument](
    name="source_finalize_report",
    doc_type=SourceFinalizeReportDocument,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, source_finalize_relpath(ref.name)),
)
