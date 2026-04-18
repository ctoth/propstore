from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from quire.artifacts import ArtifactFamily, ResolvedArtifact
from quire.versions import VersionId

from propstore.artifacts.documents.micropubs import MicropublicationsFileDocument
from propstore.artifacts.refs import (
    CanonicalSourceRef,
    ConceptAlignmentRef,
    JustificationsFileRef,
    MicropubsFileRef,
    MergeManifestRef,
    SourceRef,
    StanceFileRef,
    normalize_source_slug,
)
from propstore.artifacts.semantic_families import (
    CLAIMS_FILE_FAMILY,
    CONCEPT_FILE_FAMILY,
    CONTEXT_FAMILY,
    FORM_FAMILY,
    PREDICATE_FILE_FAMILY,
    RULE_FILE_FAMILY,
    STANCE_FILE_FAMILY,
    WORLDLINE_FAMILY,
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


ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.23")
YAML_EXTENSION = ".yaml"
STANCE_PROPOSAL_BRANCH = "proposal/stances"


def _source_branch_name(name: str) -> str:
    return f"source/{normalize_source_slug(name)}"


def _source_artifact(repo: Repository, ref: SourceRef, relpath: str) -> ResolvedArtifact:
    del repo
    return ResolvedArtifact(
        branch=_source_branch_name(ref.name),
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
    return _source_artifact(repo, ref, f"merge/finalize/{normalize_source_slug(ref.name)}{YAML_EXTENSION}")


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


def _primary_branch(repo: Repository) -> str:
    if repo.git is None:
        raise ValueError("artifact operations require a git-backed repository")
    return repo.git.primary_branch_name()


@dataclass(frozen=True)
class _PrimaryYamlLayout:
    root: str
    ref_type: type
    ref_field: str = "name"
    codec: str = "stem"
    fixed_branch: str | None = None

    def relpath(self, ref: object) -> str:
        return f"{self.root}/{self._filename_stem(ref)}{YAML_EXTENSION}"

    def resolve(self, repo: Repository, ref: object) -> ResolvedArtifact:
        return ResolvedArtifact(
            branch=_primary_branch(repo),
            relpath=self.relpath(ref),
        )

    def ref_from_path(self, path: str | Path) -> object:
        rendered = path.as_posix() if hasattr(path, "as_posix") else str(path)
        normalized = rendered.replace("\\", "/")
        prefix = f"{self.root}/"
        if normalized.startswith(prefix):
            relative = normalized
        else:
            marker = f"/{prefix}"
            marker_index = normalized.rfind(marker)
            if marker_index < 0:
                raise ValueError(f"expected {self.root}/*{YAML_EXTENSION} path, got {normalized!r}")
            relative = normalized[marker_index + 1:]
        tail = relative.removeprefix(prefix)
        if "/" in tail:
            raise ValueError(f"expected {self.root}/*{YAML_EXTENSION} path, got {normalized!r}")
        if not tail.endswith(YAML_EXTENSION):
            raise ValueError(f"expected {self.root}/*{YAML_EXTENSION} path, got {normalized!r}")
        return self.ref_type(self._ref_value(tail.removesuffix(YAML_EXTENSION)))

    def ref_from_loaded(self, loaded: object) -> object:
        source_path = getattr(loaded, "source_path", None)
        if source_path is None:
            raise ValueError(f"loaded artifact does not have a source_path for {self.root}")
        return self.ref_from_path(source_path)

    def list_refs(self, repo: Repository, branch: str | None, commit: str | None) -> list[object]:
        target_commit = commit
        if repo.git is not None and target_commit is None:
            target_commit = repo.git.branch_sha(branch or self.fixed_branch or _primary_branch(repo))
            if target_commit is None:
                return []
        directory = repo.tree(commit=target_commit) / self.root
        if not directory.exists():
            return []
        return [
            self.ref_type(self._ref_value(entry.stem))
            for entry in directory.iterdir()
            if entry.is_file() and entry.suffix == YAML_EXTENSION
        ]

    def _filename_stem(self, ref: object) -> str:
        value = getattr(ref, self.ref_field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"ref field {self.ref_field!r} must be a non-empty string")
        if self.codec == "colon_to_double_underscore":
            return value.replace(":", "__")
        return value

    def _ref_value(self, stem: str) -> str:
        if self.codec == "colon_to_double_underscore":
            return stem.replace("__", ":")
        return stem


_CANONICAL_SOURCE_LAYOUT = _PrimaryYamlLayout("sources", CanonicalSourceRef)
_MICROPUBS_FILE_LAYOUT = _PrimaryYamlLayout("micropubs", MicropubsFileRef)
_JUSTIFICATIONS_FILE_LAYOUT = _PrimaryYamlLayout("justifications", JustificationsFileRef)
_PROPOSAL_STANCE_LAYOUT = _PrimaryYamlLayout(
    "stances",
    StanceFileRef,
    ref_field="source_claim",
    codec="colon_to_double_underscore",
    fixed_branch=STANCE_PROPOSAL_BRANCH,
)
_CONCEPT_ALIGNMENT_LAYOUT = _PrimaryYamlLayout("merge/concepts", ConceptAlignmentRef, ref_field="slug")


def _proposal_stance_artifact(repo: Repository, ref: StanceFileRef) -> ResolvedArtifact:
    del repo
    return ResolvedArtifact(
        branch=STANCE_PROPOSAL_BRANCH,
        relpath=_PROPOSAL_STANCE_LAYOUT.relpath(ref),
    )


def _concept_alignment_artifact(repo: Repository, ref: ConceptAlignmentRef) -> ResolvedArtifact:
    del repo
    return ResolvedArtifact(
        branch="proposal/concepts",
        relpath=_CONCEPT_ALIGNMENT_LAYOUT.relpath(ref),
    )


def _merge_manifest_artifact(repo: Repository, ref: MergeManifestRef) -> ResolvedArtifact:
    del ref
    return ResolvedArtifact(
        branch=_primary_branch(repo),
        relpath=f"merge/manifest{YAML_EXTENSION}",
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

CANONICAL_SOURCE_FAMILY = ArtifactFamily["Repository", CanonicalSourceRef, SourceDocument](
    name="canonical_source",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceDocument,
    resolve_ref=_CANONICAL_SOURCE_LAYOUT.resolve,
)


MICROPUBS_FILE_FAMILY = ArtifactFamily["Repository", MicropubsFileRef, MicropublicationsFileDocument](
    name="micropubs_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=MicropublicationsFileDocument,
    resolve_ref=_MICROPUBS_FILE_LAYOUT.resolve,
    list_refs=_MICROPUBS_FILE_LAYOUT.list_refs,
    ref_from_path=_MICROPUBS_FILE_LAYOUT.ref_from_path,
    ref_from_loaded=_MICROPUBS_FILE_LAYOUT.ref_from_loaded,
)

JUSTIFICATIONS_FILE_FAMILY = ArtifactFamily["Repository", JustificationsFileRef, SourceJustificationsDocument](
    name="justifications_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceJustificationsDocument,
    resolve_ref=_JUSTIFICATIONS_FILE_LAYOUT.resolve,
    list_refs=_JUSTIFICATIONS_FILE_LAYOUT.list_refs,
    ref_from_path=_JUSTIFICATIONS_FILE_LAYOUT.ref_from_path,
    ref_from_loaded=_JUSTIFICATIONS_FILE_LAYOUT.ref_from_loaded,
)

PROPOSAL_STANCE_FAMILY = ArtifactFamily["Repository", StanceFileRef, StanceFileDocument](
    name="proposal_stance_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=StanceFileDocument,
    resolve_ref=_proposal_stance_artifact,
    ref_from_path=_PROPOSAL_STANCE_LAYOUT.ref_from_path,
    list_refs=_PROPOSAL_STANCE_LAYOUT.list_refs,
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
