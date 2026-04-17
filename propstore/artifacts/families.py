from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.artifacts.documents.contexts import ContextDocument
from propstore.artifacts.documents.forms import FormDocument
from propstore.artifacts.documents.worldlines import WorldlineDefinitionDocument
from propstore.artifacts.identity import normalize_canonical_concept_payload
from propstore.artifacts.refs import (
    CanonicalSourceRef,
    ClaimsFileRef,
    ConceptAlignmentRef,
    ConceptFileRef,
    ContextRef,
    FormRef,
    JustificationsFileRef,
    MergeManifestRef,
    SourceRef,
    StanceFileRef,
    STANCE_PROPOSAL_BRANCH,
    WorldlineRef,
    canonical_source_relpath,
    claims_file_relpath,
    concept_alignment_relpath,
    concept_file_relpath,
    source_branch_name,
    source_claim_from_stance_path,
    source_finalize_relpath,
    stance_file_relpath,
    merge_manifest_relpath,
    worldline_relpath,
    justifications_file_relpath,
)
from propstore.artifacts.types import ArtifactFamily, ResolvedArtifact
from propstore.artifacts.documents.claims import ClaimsFileDocument
from propstore.artifacts.documents.sources import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
)
from propstore.artifacts.documents.source_alignment import ConceptAlignmentArtifactDocument
from propstore.artifacts.documents.stances import StanceFileDocument
from propstore.artifacts.documents.merge import MergeManifestDocument

if TYPE_CHECKING:
    from propstore.repo.repository import Repository


def _source_artifact(repo: Repository, ref: SourceRef, relpath: str) -> ResolvedArtifact:
    del repo
    return ResolvedArtifact(
        branch=source_branch_name(ref.name),
        relpath=relpath,
    )


def _coerce_text_document(payload: object, source: str) -> str:
    if isinstance(payload, str):
        return payload
    raise TypeError(f"{source}: expected UTF-8 text payload")


def _decode_text_document(payload: bytes, source: str) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{source}: expected UTF-8 text payload") from exc


def _encode_text_document(document: str) -> bytes:
    return document.encode("utf-8")


def _coerce_json_mapping(payload: object, source: str) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    raise TypeError(f"{source}: expected JSON object payload")


def _decode_json_mapping(payload: bytes, source: str) -> dict[str, Any]:
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{source}: expected JSON object payload") from exc
    if not isinstance(decoded, dict):
        raise ValueError(f"{source}: expected JSON object payload")
    return decoded


def _encode_json_mapping(document: dict[str, Any]) -> bytes:
    return json.dumps(document, indent=2, ensure_ascii=False).encode("utf-8")


def _render_json_mapping(document: dict[str, Any]) -> str:
    return _encode_json_mapping(document).decode("utf-8")


def _default_branch(repo: Repository) -> str:
    if repo.git is None:
        raise ValueError("artifact operations require a git-backed repository")
    return repo.git.current_branch_name() or repo.git.primary_branch_name()


def _context_artifact(repo: Repository, ref: ContextRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_default_branch(repo),
        relpath=f"contexts/{ref.name}.yaml",
    )


def _primary_branch(repo: Repository) -> str:
    if repo.git is None:
        raise ValueError("artifact operations require a git-backed repository")
    return repo.git.primary_branch_name()


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


def _canonical_source_artifact(repo: Repository, ref: CanonicalSourceRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=canonical_source_relpath(ref.name),
    )


def _claims_file_artifact(repo: Repository, ref: ClaimsFileRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=claims_file_relpath(ref.name),
    )


def _concept_file_artifact(repo: Repository, ref: ConceptFileRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=concept_file_relpath(ref.name),
    )


def _justifications_file_artifact(repo: Repository, ref: JustificationsFileRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=justifications_file_relpath(ref.name),
    )


def _stance_file_artifact(repo: Repository, ref: StanceFileRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=stance_file_relpath(ref.source_claim),
    )


def _proposal_stance_artifact(repo: Repository, ref: StanceFileRef) -> ResolvedArtifact:
    del repo
    return ResolvedArtifact(
        branch=STANCE_PROPOSAL_BRANCH,
        relpath=stance_file_relpath(ref.source_claim),
    )


def _concept_alignment_artifact(repo: Repository, ref: ConceptAlignmentRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch="proposal/concepts",
        relpath=concept_alignment_relpath(ref.slug),
    )


def _merge_manifest_artifact(repo: Repository, ref: MergeManifestRef) -> ResolvedArtifact:
    del ref
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=merge_manifest_relpath(),
    )


def _list_yaml_refs_in_directory(
    repo: Repository,
    branch: str | None,
    commit: str | None,
    *,
    subdir: str,
    ref_type: type[WorldlineRef],
) -> list[WorldlineRef]:
    from propstore.repo.branch import branch_head

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


def _list_stance_refs_in_directory(
    repo: Repository,
    branch: str | None,
    commit: str | None,
) -> list[StanceFileRef]:
    from propstore.repo.branch import branch_head

    target_commit = commit
    if repo.git is not None and target_commit is None:
        target_branch = branch or _primary_branch(repo)
        target_commit = branch_head(repo.git, target_branch)
        if target_commit is None:
            return []

    tree = repo.tree(commit=target_commit)
    directory = tree / "stances"
    if not directory.exists():
        return []

    refs: list[StanceFileRef] = []
    for entry in directory.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        refs.append(StanceFileRef(source_claim_from_stance_path(entry.name)))
    return refs


def _yaml_path_ref(path: str | Path, *, subdir: str, ref_type: type[WorldlineRef]) -> WorldlineRef:
    normalized = str(path).replace("\\", "/")
    prefix = f"{subdir}/"
    if not normalized.startswith(prefix) or not normalized.endswith(".yaml"):
        raise ValueError(f"expected {prefix}*.yaml path, got {normalized!r}")
    return ref_type(Path(normalized).stem)


def _ref_from_loaded_source_path(
    loaded: object,
    *,
    subdir: str,
    ref_type: type[WorldlineRef],
) -> WorldlineRef:
    source_path = getattr(loaded, "source_path", None)
    if source_path is None:
        raise ValueError(f"loaded artifact does not have a source_path for {subdir}")
    rendered = source_path.as_posix() if hasattr(source_path, "as_posix") else str(source_path)
    return _yaml_path_ref(rendered, subdir=subdir, ref_type=ref_type)


SOURCE_DOCUMENT_FAMILY = ArtifactFamily[SourceRef, SourceDocument](
    name="source_document",
    doc_type=SourceDocument,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, "source.yaml"),
)

SOURCE_NOTES_FAMILY = ArtifactFamily[SourceRef, str](
    name="source_notes",
    doc_type=str,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, "notes.md"),
    coerce_payload=_coerce_text_document,
    decode_bytes=_decode_text_document,
    encode_document=_encode_text_document,
    render_document=lambda document: document,
    document_payload=lambda document: document,
)

SOURCE_METADATA_FAMILY = ArtifactFamily[SourceRef, dict[str, Any]](
    name="source_metadata",
    doc_type=dict,
    resolve_ref=lambda repo, ref: _source_artifact(repo, ref, "metadata.json"),
    coerce_payload=_coerce_json_mapping,
    decode_bytes=_decode_json_mapping,
    encode_document=_encode_json_mapping,
    render_document=_render_json_mapping,
    document_payload=lambda document: document,
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
    ref_from_path=lambda path: _yaml_path_ref(path, subdir="contexts", ref_type=ContextRef),
)

FORM_FAMILY = ArtifactFamily[FormRef, FormDocument](
    name="form",
    doc_type=FormDocument,
    resolve_ref=_form_artifact,
    ref_from_path=lambda path: _yaml_path_ref(path, subdir="forms", ref_type=FormRef),
)

CANONICAL_SOURCE_FAMILY = ArtifactFamily[CanonicalSourceRef, SourceDocument](
    name="canonical_source",
    doc_type=SourceDocument,
    resolve_ref=_canonical_source_artifact,
)

CLAIMS_FILE_FAMILY = ArtifactFamily[ClaimsFileRef, ClaimsFileDocument](
    name="claims_file",
    doc_type=ClaimsFileDocument,
    resolve_ref=_claims_file_artifact,
    list_refs=lambda repo, branch, commit: _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="claims",
        ref_type=ClaimsFileRef,
    ),
    ref_from_path=lambda path: _yaml_path_ref(path, subdir="claims", ref_type=ClaimsFileRef),
    ref_from_loaded=lambda loaded: _ref_from_loaded_source_path(
        loaded,
        subdir="claims",
        ref_type=ClaimsFileRef,
    ),
)

CONCEPT_FILE_FAMILY = ArtifactFamily[ConceptFileRef, ConceptDocument](
    name="concept_file",
    doc_type=ConceptDocument,
    resolve_ref=_concept_file_artifact,
    normalize_for_write=lambda context, document, store: store.coerce(
        CONCEPT_FILE_FAMILY,
        normalize_canonical_concept_payload(
            store.payload(document),
        ),
        source=f"{context.branch}:{context.relpath}",
    ),
    list_refs=lambda repo, branch, commit: _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="concepts",
        ref_type=ConceptFileRef,
    ),
    ref_from_path=lambda path: _yaml_path_ref(path, subdir="concepts", ref_type=ConceptFileRef),
    ref_from_loaded=lambda loaded: _ref_from_loaded_source_path(
        loaded,
        subdir="concepts",
        ref_type=ConceptFileRef,
    ),
)

JUSTIFICATIONS_FILE_FAMILY = ArtifactFamily[JustificationsFileRef, SourceJustificationsDocument](
    name="justifications_file",
    doc_type=SourceJustificationsDocument,
    resolve_ref=_justifications_file_artifact,
)

STANCE_FILE_FAMILY = ArtifactFamily[StanceFileRef, StanceFileDocument](
    name="stance_file",
    doc_type=StanceFileDocument,
    resolve_ref=_stance_file_artifact,
    ref_from_path=lambda path: StanceFileRef(source_claim_from_stance_path(path)),
    list_refs=_list_stance_refs_in_directory,
)

PROPOSAL_STANCE_FAMILY = ArtifactFamily[StanceFileRef, StanceFileDocument](
    name="proposal_stance_file",
    doc_type=StanceFileDocument,
    resolve_ref=_proposal_stance_artifact,
    ref_from_path=lambda path: StanceFileRef(source_claim_from_stance_path(path)),
    list_refs=lambda repo, branch, commit: _list_stance_refs_in_directory(
        repo,
        STANCE_PROPOSAL_BRANCH if branch is None else branch,
        commit,
    ),
)

CONCEPT_ALIGNMENT_FAMILY = ArtifactFamily[ConceptAlignmentRef, ConceptAlignmentArtifactDocument](
    name="concept_alignment",
    doc_type=ConceptAlignmentArtifactDocument,
    resolve_ref=_concept_alignment_artifact,
)

MERGE_MANIFEST_FAMILY = ArtifactFamily[MergeManifestRef, MergeManifestDocument](
    name="merge_manifest",
    doc_type=MergeManifestDocument,
    resolve_ref=_merge_manifest_artifact,
)

WORLDLINE_FAMILY = ArtifactFamily[WorldlineRef, WorldlineDefinitionDocument](
    name="worldline",
    doc_type=WorldlineDefinitionDocument,
    resolve_ref=_worldline_artifact,
    ref_from_path=lambda path: _yaml_path_ref(path, subdir="worldlines", ref_type=WorldlineRef),
    list_refs=lambda repo, branch, commit: _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="worldlines",
        ref_type=WorldlineRef,
    ),
)
