from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.artifacts.refs import (
    ContextRef,
    FormRef,
    SourceRef,
    WorldlineRef,
    source_branch_name,
    source_finalize_relpath,
    worldline_relpath,
)
from propstore.artifacts.types import ArtifactFamily, ResolvedArtifact
from propstore.context_types import ContextDocument
from propstore.form_utils import FormDocument
from propstore.repo.branch import branch_head
from propstore.source_documents import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
)
from propstore.worldline.definition import WorldlineDefinitionDocument

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


def _worldline_artifact(repo: Repository, ref: WorldlineRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_default_branch(repo),
        relpath=worldline_relpath(ref.name),
    )


def _list_yaml_refs_in_directory(
    repo: Repository,
    branch: str | None,
    commit: str | None,
    *,
    subdir: str,
    ref_type: type[WorldlineRef],
) -> list[WorldlineRef]:
    target_commit = commit
    if repo.git is not None and target_commit is None:
        target_branch = branch or _default_branch(repo)
        target_commit = branch_head(repo.git, target_branch)
        if target_commit is None:
            return []

    tree = repo.tree(commit=target_commit)
    directory = tree / subdir
    if not directory.exists():
        return []

    refs: list[WorldlineRef] = []
    for entry in directory.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        refs.append(ref_type(entry.stem))
    return refs


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

WORLDLINE_FAMILY = ArtifactFamily[WorldlineRef, WorldlineDefinitionDocument](
    name="worldline",
    doc_type=WorldlineDefinitionDocument,
    resolve_ref=_worldline_artifact,
    list_refs=lambda repo, branch, commit: _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="worldlines",
        ref_type=WorldlineRef,
    ),
)
