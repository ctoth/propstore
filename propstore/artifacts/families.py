from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.artifacts.refs import (
    ContextRef,
    FormRef,
    SourceRef,
    source_branch_name,
    source_finalize_relpath,
)
from propstore.artifacts.types import ArtifactFamily, ResolvedArtifact
from propstore.context_types import ContextDocument
from propstore.form_utils import FormDocument
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


def _default_branch(repo: Repository) -> str:
    if repo.git is None:
        raise ValueError("artifact operations require a git-backed repository")
    return repo.git.current_branch_name() or repo.git.primary_branch_name()


def _context_artifact(repo: Repository, ref: ContextRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_default_branch(repo),
        relpath=f"contexts/{ref.name}.yaml",
    )


def _form_artifact(repo: Repository, ref: FormRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_default_branch(repo),
        relpath=f"forms/{ref.name}.yaml",
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

CONTEXT_FAMILY = ArtifactFamily[ContextRef, ContextDocument](
    name="context",
    doc_type=ContextDocument,
    resolve_ref=_context_artifact,
)

FORM_FAMILY = ArtifactFamily[FormRef, FormDocument](
    name="form",
    doc_type=FormDocument,
    resolve_ref=_form_artifact,
)
