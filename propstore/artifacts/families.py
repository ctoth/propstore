from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from quire.artifacts import ArtifactContext, ArtifactFamily, ResolvedArtifact
from quire.family_store import DocumentFamilyStore
from quire.versions import VersionId

from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.artifacts.documents.contexts import ContextDocument
from propstore.artifacts.documents.forms import FormDocument
from propstore.artifacts.documents.micropubs import MicropublicationsFileDocument
from propstore.artifacts.documents.predicates import PredicatesFileDocument
from propstore.artifacts.documents.rules import RulesFileDocument
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
    MicropubsFileRef,
    MergeManifestRef,
    PredicateFileRef,
    RuleFileRef,
    SourceRef,
    StanceFileRef,
    STANCE_PROPOSAL_BRANCH,
    WorldlineRef,
    canonical_source_relpath,
    claims_file_relpath,
    concept_alignment_relpath,
    concept_file_relpath,
    micropubs_file_relpath,
    predicate_file_relpath,
    rule_file_relpath,
    source_branch_name,
    source_claim_from_stance_path,
    source_finalize_relpath,
    stance_file_relpath,
    merge_manifest_relpath,
    worldline_relpath,
    justifications_file_relpath,
)
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
    from propstore.repository import Repository


TYamlRef = TypeVar("TYamlRef")

ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.20")


def _source_artifact(repo: Repository, ref: SourceRef, relpath: str) -> ResolvedArtifact:
    del repo
    return ResolvedArtifact(
        branch=source_branch_name(ref.name),
        relpath=relpath,
    )


def _source_document_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, "source.yaml")


def _source_notes_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, "notes.md")


def _source_metadata_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, "metadata.json")


def _source_concepts_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, "concepts.yaml")


def _source_claims_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, "claims.yaml")


def _source_micropubs_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, "micropubs.yaml")


def _source_justifications_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, "justifications.yaml")


def _source_stances_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, "stances.yaml")


def _source_finalize_report_artifact(repo: Repository, ref: SourceRef) -> ResolvedArtifact:
    return _source_artifact(repo, ref, source_finalize_relpath(ref.name))


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


def _identity_text_document(document: str) -> str:
    return document


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


def _identity_json_mapping(document: dict[str, Any]) -> dict[str, Any]:
    return document


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


def _micropubs_file_artifact(repo: Repository, ref: MicropubsFileRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=micropubs_file_relpath(ref.name),
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


def _predicate_file_artifact(repo: Repository, ref: PredicateFileRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=predicate_file_relpath(ref.name),
    )


def _rule_file_artifact(repo: Repository, ref: RuleFileRef) -> ResolvedArtifact:
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=rule_file_relpath(ref.name),
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
    ref_type: Callable[[str], TYamlRef],
) -> list[TYamlRef]:
    target_commit = commit
    if repo.git is not None and target_commit is None:
        target_branch = branch or _default_branch(repo)
        target_commit = repo.git.branch_sha(target_branch)
        if target_commit is None:
            return []

    tree = repo.tree(commit=target_commit)
    directory = tree / subdir
    if not directory.exists():
        return []

    refs: list[TYamlRef] = []
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
    target_commit = commit
    if repo.git is not None and target_commit is None:
        target_branch = branch or _primary_branch(repo)
        target_commit = repo.git.branch_sha(target_branch)
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


def _yaml_path_ref(path: str | Path, *, subdir: str, ref_type: Callable[[str], TYamlRef]) -> TYamlRef:
    normalized = str(path).replace("\\", "/")
    prefix = f"{subdir}/"
    if not normalized.startswith(prefix) or not normalized.endswith(".yaml"):
        raise ValueError(f"expected {prefix}*.yaml path, got {normalized!r}")
    return ref_type(Path(normalized).stem)


def _ref_from_loaded_source_path(
    loaded: object,
    *,
    subdir: str,
    ref_type: Callable[[str], TYamlRef],
) -> TYamlRef:
    source_path = getattr(loaded, "source_path", None)
    if source_path is None:
        raise ValueError(f"loaded artifact does not have a source_path for {subdir}")
    rendered = source_path.as_posix() if hasattr(source_path, "as_posix") else str(source_path)
    return _yaml_path_ref(rendered, subdir=subdir, ref_type=ref_type)


def _context_ref_from_path(path: str | Path) -> ContextRef:
    return _yaml_path_ref(path, subdir="contexts", ref_type=ContextRef)


def _form_ref_from_path(path: str | Path) -> FormRef:
    return _yaml_path_ref(path, subdir="forms", ref_type=FormRef)


def _claims_file_refs(
    repo: Repository,
    branch: str | None,
    commit: str | None,
) -> list[ClaimsFileRef]:
    return _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="claims",
        ref_type=ClaimsFileRef,
    )


def _claims_file_ref_from_path(path: str | Path) -> ClaimsFileRef:
    return _yaml_path_ref(path, subdir="claims", ref_type=ClaimsFileRef)


def _claims_file_ref_from_loaded(loaded: object) -> ClaimsFileRef:
    return _ref_from_loaded_source_path(
        loaded,
        subdir="claims",
        ref_type=ClaimsFileRef,
    )


def _micropubs_file_refs(
    repo: Repository,
    branch: str | None,
    commit: str | None,
) -> list[MicropubsFileRef]:
    return _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="micropubs",
        ref_type=MicropubsFileRef,
    )


def _micropubs_file_ref_from_path(path: str | Path) -> MicropubsFileRef:
    return _yaml_path_ref(path, subdir="micropubs", ref_type=MicropubsFileRef)


def _micropubs_file_ref_from_loaded(loaded: object) -> MicropubsFileRef:
    return _ref_from_loaded_source_path(
        loaded,
        subdir="micropubs",
        ref_type=MicropubsFileRef,
    )


def _concept_file_refs(
    repo: Repository,
    branch: str | None,
    commit: str | None,
) -> list[ConceptFileRef]:
    return _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="concepts",
        ref_type=ConceptFileRef,
    )


def _concept_file_ref_from_path(path: str | Path) -> ConceptFileRef:
    return _yaml_path_ref(path, subdir="concepts", ref_type=ConceptFileRef)


def _concept_file_ref_from_loaded(loaded: object) -> ConceptFileRef:
    return _ref_from_loaded_source_path(
        loaded,
        subdir="concepts",
        ref_type=ConceptFileRef,
    )


def _predicate_file_refs(
    repo: Repository,
    branch: str | None,
    commit: str | None,
) -> list[PredicateFileRef]:
    return _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="predicates",
        ref_type=PredicateFileRef,
    )


def _predicate_file_ref_from_path(path: str | Path) -> PredicateFileRef:
    return _yaml_path_ref(path, subdir="predicates", ref_type=PredicateFileRef)


def _predicate_file_ref_from_loaded(loaded: object) -> PredicateFileRef:
    return _ref_from_loaded_source_path(
        loaded,
        subdir="predicates",
        ref_type=PredicateFileRef,
    )


def _rule_file_refs(
    repo: Repository,
    branch: str | None,
    commit: str | None,
) -> list[RuleFileRef]:
    return _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="rules",
        ref_type=RuleFileRef,
    )


def _rule_file_ref_from_path(path: str | Path) -> RuleFileRef:
    return _yaml_path_ref(path, subdir="rules", ref_type=RuleFileRef)


def _rule_file_ref_from_loaded(loaded: object) -> RuleFileRef:
    return _ref_from_loaded_source_path(
        loaded,
        subdir="rules",
        ref_type=RuleFileRef,
    )


def _stance_file_ref_from_path(path: str | Path) -> StanceFileRef:
    return StanceFileRef(source_claim_from_stance_path(path))


def _proposal_stance_refs(
    repo: Repository,
    branch: str | None,
    commit: str | None,
) -> list[StanceFileRef]:
    target_branch = STANCE_PROPOSAL_BRANCH if branch is None else branch
    return _list_stance_refs_in_directory(repo, target_branch, commit)


def _worldline_ref_from_path(path: str | Path) -> WorldlineRef:
    return _yaml_path_ref(path, subdir="worldlines", ref_type=WorldlineRef)


def _worldline_refs(
    repo: Repository,
    branch: str | None,
    commit: str | None,
) -> list[WorldlineRef]:
    return _list_yaml_refs_in_directory(
        repo,
        branch,
        commit,
        subdir="worldlines",
        ref_type=WorldlineRef,
    )


def _normalize_concept_for_write(
    context: ArtifactContext["Repository", ConceptFileRef],
    document: ConceptDocument,
    store: DocumentFamilyStore["Repository"],
) -> ConceptDocument:
    payload = store.payload(document)
    if not isinstance(payload, dict):
        raise TypeError(f"{context.branch}:{context.relpath}: expected concept payload mapping")
    return store.coerce(
        CONCEPT_FILE_FAMILY,
        normalize_canonical_concept_payload(payload),
        source=f"{context.branch}:{context.relpath}",
    )


SOURCE_DOCUMENT_FAMILY = ArtifactFamily["Repository", SourceRef, SourceDocument](
    name="source_document",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceDocument,
    resolve_ref=_source_document_artifact,
)

SOURCE_NOTES_FAMILY = ArtifactFamily["Repository", SourceRef, str](
    name="source_notes",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=str,
    resolve_ref=_source_notes_artifact,
    coerce_payload=_coerce_text_document,
    decode_bytes=_decode_text_document,
    encode_document=_encode_text_document,
    render_document=_identity_text_document,
    document_payload=_identity_text_document,
)

SOURCE_METADATA_FAMILY = ArtifactFamily["Repository", SourceRef, dict[str, Any]](
    name="source_metadata",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=dict,
    resolve_ref=_source_metadata_artifact,
    coerce_payload=_coerce_json_mapping,
    decode_bytes=_decode_json_mapping,
    encode_document=_encode_json_mapping,
    render_document=_render_json_mapping,
    document_payload=_identity_json_mapping,
)

SOURCE_CONCEPTS_FAMILY = ArtifactFamily["Repository", SourceRef, SourceConceptsDocument](
    name="source_concepts",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceConceptsDocument,
    resolve_ref=_source_concepts_artifact,
)

SOURCE_CLAIMS_FAMILY = ArtifactFamily["Repository", SourceRef, SourceClaimsDocument](
    name="source_claims",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceClaimsDocument,
    resolve_ref=_source_claims_artifact,
)


SOURCE_MICROPUBS_FAMILY = ArtifactFamily["Repository", SourceRef, MicropublicationsFileDocument](
    name="source_micropubs",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=MicropublicationsFileDocument,
    resolve_ref=_source_micropubs_artifact,
)

SOURCE_JUSTIFICATIONS_FAMILY = ArtifactFamily["Repository", SourceRef, SourceJustificationsDocument](
    name="source_justifications",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceJustificationsDocument,
    resolve_ref=_source_justifications_artifact,
)

SOURCE_STANCES_FAMILY = ArtifactFamily["Repository", SourceRef, SourceStancesDocument](
    name="source_stances",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceStancesDocument,
    resolve_ref=_source_stances_artifact,
)

SOURCE_FINALIZE_REPORT_FAMILY = ArtifactFamily["Repository", SourceRef, SourceFinalizeReportDocument](
    name="source_finalize_report",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceFinalizeReportDocument,
    resolve_ref=_source_finalize_report_artifact,
)

CONTEXT_FAMILY = ArtifactFamily["Repository", ContextRef, ContextDocument](
    name="context",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ContextDocument,
    resolve_ref=_context_artifact,
    ref_from_path=_context_ref_from_path,
)

FORM_FAMILY = ArtifactFamily["Repository", FormRef, FormDocument](
    name="form",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=FormDocument,
    resolve_ref=_form_artifact,
    ref_from_path=_form_ref_from_path,
)

CANONICAL_SOURCE_FAMILY = ArtifactFamily["Repository", CanonicalSourceRef, SourceDocument](
    name="canonical_source",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceDocument,
    resolve_ref=_canonical_source_artifact,
)

CLAIMS_FILE_FAMILY = ArtifactFamily["Repository", ClaimsFileRef, ClaimsFileDocument](
    name="claims_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ClaimsFileDocument,
    resolve_ref=_claims_file_artifact,
    list_refs=_claims_file_refs,
    ref_from_path=_claims_file_ref_from_path,
    ref_from_loaded=_claims_file_ref_from_loaded,
)


MICROPUBS_FILE_FAMILY = ArtifactFamily["Repository", MicropubsFileRef, MicropublicationsFileDocument](
    name="micropubs_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=MicropublicationsFileDocument,
    resolve_ref=_micropubs_file_artifact,
    list_refs=_micropubs_file_refs,
    ref_from_path=_micropubs_file_ref_from_path,
    ref_from_loaded=_micropubs_file_ref_from_loaded,
)


CONCEPT_FILE_FAMILY = ArtifactFamily["Repository", ConceptFileRef, ConceptDocument](
    name="concept_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ConceptDocument,
    resolve_ref=_concept_file_artifact,
    normalize_for_write=_normalize_concept_for_write,
    list_refs=_concept_file_refs,
    ref_from_path=_concept_file_ref_from_path,
    ref_from_loaded=_concept_file_ref_from_loaded,
)

JUSTIFICATIONS_FILE_FAMILY = ArtifactFamily["Repository", JustificationsFileRef, SourceJustificationsDocument](
    name="justifications_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceJustificationsDocument,
    resolve_ref=_justifications_file_artifact,
)

PREDICATE_FILE_FAMILY = ArtifactFamily["Repository", PredicateFileRef, PredicatesFileDocument](
    name="predicate_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=PredicatesFileDocument,
    resolve_ref=_predicate_file_artifact,
    list_refs=_predicate_file_refs,
    ref_from_path=_predicate_file_ref_from_path,
    ref_from_loaded=_predicate_file_ref_from_loaded,
)

RULE_FILE_FAMILY = ArtifactFamily["Repository", RuleFileRef, RulesFileDocument](
    name="rule_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=RulesFileDocument,
    resolve_ref=_rule_file_artifact,
    list_refs=_rule_file_refs,
    ref_from_path=_rule_file_ref_from_path,
    ref_from_loaded=_rule_file_ref_from_loaded,
)

STANCE_FILE_FAMILY = ArtifactFamily["Repository", StanceFileRef, StanceFileDocument](
    name="stance_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=StanceFileDocument,
    resolve_ref=_stance_file_artifact,
    ref_from_path=_stance_file_ref_from_path,
    list_refs=_list_stance_refs_in_directory,
)

PROPOSAL_STANCE_FAMILY = ArtifactFamily["Repository", StanceFileRef, StanceFileDocument](
    name="proposal_stance_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=StanceFileDocument,
    resolve_ref=_proposal_stance_artifact,
    ref_from_path=_stance_file_ref_from_path,
    list_refs=_proposal_stance_refs,
)

CONCEPT_ALIGNMENT_FAMILY = ArtifactFamily["Repository", ConceptAlignmentRef, ConceptAlignmentArtifactDocument](
    name="concept_alignment",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ConceptAlignmentArtifactDocument,
    resolve_ref=_concept_alignment_artifact,
)

MERGE_MANIFEST_FAMILY = ArtifactFamily["Repository", MergeManifestRef, MergeManifestDocument](
    name="merge_manifest",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=MergeManifestDocument,
    resolve_ref=_merge_manifest_artifact,
)

WORLDLINE_FAMILY = ArtifactFamily["Repository", WorldlineRef, WorldlineDefinitionDocument](
    name="worldline",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=WorldlineDefinitionDocument,
    resolve_ref=_worldline_artifact,
    ref_from_path=_worldline_ref_from_path,
    list_refs=_worldline_refs,
)
