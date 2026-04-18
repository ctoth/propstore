from __future__ import annotations

from enum import Enum
import json
from typing import Any

from quire.artifacts import (
    ArtifactFamily,
    BranchPlacement,
    FixedFilePlacement,
    FlatYamlPlacement,
    SingletonFilePlacement,
    TemplateFilePlacement,
)
from quire.families import FamilyDefinition, FamilyRegistry
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
)
from propstore.artifacts.semantic_families import (
    CLAIM_FOREIGN_KEYS,
    CLAIMS_FILE_FAMILY,
    CONCEPT_FOREIGN_KEYS,
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

ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.23")
YAML_EXTENSION = ".yaml"
PRIMARY_ARTIFACT_BRANCH = BranchPlacement(policy="primary")
SOURCE_BRANCH = BranchPlacement(
    policy="template",
    template="source/{stem}",
    ref_field="name",
    codec="safe_slug",
)
PROPOSAL_STANCE_BRANCH = BranchPlacement(policy="fixed", fixed_branch="proposal/stances")
PROPOSAL_CONCEPT_BRANCH = BranchPlacement(policy="fixed", fixed_branch="proposal/concepts")

SOURCE_DOCUMENT_PLACEMENT = FixedFilePlacement["Repository", SourceRef]("source.yaml", branch=SOURCE_BRANCH)
SOURCE_NOTES_PLACEMENT = FixedFilePlacement["Repository", SourceRef]("notes.md", branch=SOURCE_BRANCH)
SOURCE_METADATA_PLACEMENT = FixedFilePlacement["Repository", SourceRef]("metadata.json", branch=SOURCE_BRANCH)
SOURCE_CONCEPTS_PLACEMENT = FixedFilePlacement["Repository", SourceRef]("concepts.yaml", branch=SOURCE_BRANCH)
SOURCE_CLAIMS_PLACEMENT = FixedFilePlacement["Repository", SourceRef]("claims.yaml", branch=SOURCE_BRANCH)
SOURCE_MICROPUBS_PLACEMENT = FixedFilePlacement["Repository", SourceRef]("micropubs.yaml", branch=SOURCE_BRANCH)
SOURCE_JUSTIFICATIONS_PLACEMENT = FixedFilePlacement["Repository", SourceRef]("justifications.yaml", branch=SOURCE_BRANCH)
SOURCE_STANCES_PLACEMENT = FixedFilePlacement["Repository", SourceRef]("stances.yaml", branch=SOURCE_BRANCH)
SOURCE_FINALIZE_REPORT_PLACEMENT = TemplateFilePlacement["Repository", SourceRef](
    "merge/finalize/{stem}.yaml",
    ref_field="name",
    codec="safe_slug",
    branch=SOURCE_BRANCH,
)
CANONICAL_SOURCE_PLACEMENT = FlatYamlPlacement["Repository", CanonicalSourceRef](
    "sources",
    CanonicalSourceRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
MICROPUBS_FILE_PLACEMENT = FlatYamlPlacement["Repository", MicropubsFileRef](
    "micropubs",
    MicropubsFileRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
JUSTIFICATIONS_FILE_PLACEMENT = FlatYamlPlacement["Repository", JustificationsFileRef](
    "justifications",
    JustificationsFileRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
PROPOSAL_STANCE_PLACEMENT = FlatYamlPlacement["Repository", StanceFileRef](
    "stances",
    StanceFileRef,
    ref_field="source_claim",
    codec="colon_to_double_underscore",
    branch=PROPOSAL_STANCE_BRANCH,
)
CONCEPT_ALIGNMENT_PLACEMENT = FlatYamlPlacement["Repository", ConceptAlignmentRef](
    "merge/concepts",
    ConceptAlignmentRef,
    ref_field="slug",
    branch=PROPOSAL_CONCEPT_BRANCH,
)
MERGE_MANIFEST_PLACEMENT = SingletonFilePlacement["Repository", MergeManifestRef](
    "merge/manifest.yaml",
    ref_factory=MergeManifestRef,
    branch=PRIMARY_ARTIFACT_BRANCH,
)


class PropstoreFamily(str, Enum):
    CLAIMS = "claims"
    CONCEPTS = "concepts"
    CONTEXTS = "contexts"
    FORMS = "forms"
    PREDICATES = "predicates"
    RULES = "rules"
    STANCES = "stances"
    WORLDLINES = "worldlines"
    SOURCES = "sources"
    MICROPUBS = "micropubs"
    JUSTIFICATIONS = "justifications"
    SOURCE_DOCUMENTS = "source_documents"
    SOURCE_NOTES = "source_notes"
    SOURCE_METADATA = "source_metadata"
    SOURCE_CONCEPTS = "source_concepts"
    SOURCE_CLAIMS = "source_claims"
    SOURCE_MICROPUBS = "source_micropubs"
    SOURCE_JUSTIFICATIONS = "source_justifications"
    SOURCE_STANCES = "source_stances"
    SOURCE_FINALIZE_REPORTS = "source_finalize_reports"
    PROPOSAL_STANCES = "proposal_stances"
    CONCEPT_ALIGNMENTS = "concept_alignments"
    MERGE_MANIFESTS = "merge_manifests"


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


SOURCE_DOCUMENT_FAMILY = ArtifactFamily["Repository", SourceRef, SourceDocument](
    name="source_document",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceDocument,
    placement=SOURCE_DOCUMENT_PLACEMENT,
)

SOURCE_NOTES_FAMILY = ArtifactFamily["Repository", SourceRef, str](
    name="source_notes",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=str,
    placement=SOURCE_NOTES_PLACEMENT,
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
    placement=SOURCE_METADATA_PLACEMENT,
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
    placement=SOURCE_CONCEPTS_PLACEMENT,
)

SOURCE_CLAIMS_FAMILY = ArtifactFamily["Repository", SourceRef, SourceClaimsDocument](
    name="source_claims",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceClaimsDocument,
    placement=SOURCE_CLAIMS_PLACEMENT,
)


SOURCE_MICROPUBS_FAMILY = ArtifactFamily["Repository", SourceRef, MicropublicationsFileDocument](
    name="source_micropubs",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=MicropublicationsFileDocument,
    placement=SOURCE_MICROPUBS_PLACEMENT,
)

SOURCE_JUSTIFICATIONS_FAMILY = ArtifactFamily["Repository", SourceRef, SourceJustificationsDocument](
    name="source_justifications",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceJustificationsDocument,
    placement=SOURCE_JUSTIFICATIONS_PLACEMENT,
)

SOURCE_STANCES_FAMILY = ArtifactFamily["Repository", SourceRef, SourceStancesDocument](
    name="source_stances",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceStancesDocument,
    placement=SOURCE_STANCES_PLACEMENT,
)

SOURCE_FINALIZE_REPORT_FAMILY = ArtifactFamily["Repository", SourceRef, SourceFinalizeReportDocument](
    name="source_finalize_report",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceFinalizeReportDocument,
    placement=SOURCE_FINALIZE_REPORT_PLACEMENT,
)

CANONICAL_SOURCE_FAMILY = ArtifactFamily["Repository", CanonicalSourceRef, SourceDocument](
    name="canonical_source",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceDocument,
    placement=CANONICAL_SOURCE_PLACEMENT,
)


MICROPUBS_FILE_FAMILY = ArtifactFamily["Repository", MicropubsFileRef, MicropublicationsFileDocument](
    name="micropubs_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=MicropublicationsFileDocument,
    placement=MICROPUBS_FILE_PLACEMENT,
)

JUSTIFICATIONS_FILE_FAMILY = ArtifactFamily["Repository", JustificationsFileRef, SourceJustificationsDocument](
    name="justifications_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceJustificationsDocument,
    placement=JUSTIFICATIONS_FILE_PLACEMENT,
)

PROPOSAL_STANCE_FAMILY = ArtifactFamily["Repository", StanceFileRef, StanceFileDocument](
    name="proposal_stance_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=StanceFileDocument,
    placement=PROPOSAL_STANCE_PLACEMENT,
)

CONCEPT_ALIGNMENT_FAMILY = ArtifactFamily["Repository", ConceptAlignmentRef, ConceptAlignmentArtifactDocument](
    name="concept_alignment",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ConceptAlignmentArtifactDocument,
    placement=CONCEPT_ALIGNMENT_PLACEMENT,
)

MERGE_MANIFEST_FAMILY = ArtifactFamily["Repository", MergeManifestRef, MergeManifestDocument](
    name="merge_manifest",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=MergeManifestDocument,
    placement=MERGE_MANIFEST_PLACEMENT,
)


PROPSTORE_FAMILY_REGISTRY = FamilyRegistry(
    name="propstore",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    families=(
        FamilyDefinition(
            key=PropstoreFamily.CLAIMS,
            name=PropstoreFamily.CLAIMS.value,
            contract_version=CLAIMS_FILE_FAMILY.contract_version,
            artifact_family=CLAIMS_FILE_FAMILY,
            foreign_keys=CLAIM_FOREIGN_KEYS,
        ),
        FamilyDefinition(
            key=PropstoreFamily.CONCEPTS,
            name=PropstoreFamily.CONCEPTS.value,
            contract_version=CONCEPT_FILE_FAMILY.contract_version,
            artifact_family=CONCEPT_FILE_FAMILY,
            foreign_keys=CONCEPT_FOREIGN_KEYS,
        ),
        FamilyDefinition(
            key=PropstoreFamily.CONTEXTS,
            name=PropstoreFamily.CONTEXTS.value,
            contract_version=CONTEXT_FAMILY.contract_version,
            artifact_family=CONTEXT_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.FORMS,
            name=PropstoreFamily.FORMS.value,
            contract_version=FORM_FAMILY.contract_version,
            artifact_family=FORM_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.PREDICATES,
            name=PropstoreFamily.PREDICATES.value,
            contract_version=PREDICATE_FILE_FAMILY.contract_version,
            artifact_family=PREDICATE_FILE_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.RULES,
            name=PropstoreFamily.RULES.value,
            contract_version=RULE_FILE_FAMILY.contract_version,
            artifact_family=RULE_FILE_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.STANCES,
            name=PropstoreFamily.STANCES.value,
            contract_version=STANCE_FILE_FAMILY.contract_version,
            artifact_family=STANCE_FILE_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.WORLDLINES,
            name=PropstoreFamily.WORLDLINES.value,
            contract_version=WORLDLINE_FAMILY.contract_version,
            artifact_family=WORLDLINE_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCES,
            name=PropstoreFamily.SOURCES.value,
            contract_version=CANONICAL_SOURCE_FAMILY.contract_version,
            artifact_family=CANONICAL_SOURCE_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.MICROPUBS,
            name=PropstoreFamily.MICROPUBS.value,
            contract_version=MICROPUBS_FILE_FAMILY.contract_version,
            artifact_family=MICROPUBS_FILE_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.JUSTIFICATIONS,
            name=PropstoreFamily.JUSTIFICATIONS.value,
            contract_version=JUSTIFICATIONS_FILE_FAMILY.contract_version,
            artifact_family=JUSTIFICATIONS_FILE_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_DOCUMENTS,
            name=PropstoreFamily.SOURCE_DOCUMENTS.value,
            contract_version=SOURCE_DOCUMENT_FAMILY.contract_version,
            artifact_family=SOURCE_DOCUMENT_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_NOTES,
            name=PropstoreFamily.SOURCE_NOTES.value,
            contract_version=SOURCE_NOTES_FAMILY.contract_version,
            artifact_family=SOURCE_NOTES_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_METADATA,
            name=PropstoreFamily.SOURCE_METADATA.value,
            contract_version=SOURCE_METADATA_FAMILY.contract_version,
            artifact_family=SOURCE_METADATA_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_CONCEPTS,
            name=PropstoreFamily.SOURCE_CONCEPTS.value,
            contract_version=SOURCE_CONCEPTS_FAMILY.contract_version,
            artifact_family=SOURCE_CONCEPTS_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_CLAIMS,
            name=PropstoreFamily.SOURCE_CLAIMS.value,
            contract_version=SOURCE_CLAIMS_FAMILY.contract_version,
            artifact_family=SOURCE_CLAIMS_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_MICROPUBS,
            name=PropstoreFamily.SOURCE_MICROPUBS.value,
            contract_version=SOURCE_MICROPUBS_FAMILY.contract_version,
            artifact_family=SOURCE_MICROPUBS_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_JUSTIFICATIONS,
            name=PropstoreFamily.SOURCE_JUSTIFICATIONS.value,
            contract_version=SOURCE_JUSTIFICATIONS_FAMILY.contract_version,
            artifact_family=SOURCE_JUSTIFICATIONS_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_STANCES,
            name=PropstoreFamily.SOURCE_STANCES.value,
            contract_version=SOURCE_STANCES_FAMILY.contract_version,
            artifact_family=SOURCE_STANCES_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_FINALIZE_REPORTS,
            name=PropstoreFamily.SOURCE_FINALIZE_REPORTS.value,
            contract_version=SOURCE_FINALIZE_REPORT_FAMILY.contract_version,
            artifact_family=SOURCE_FINALIZE_REPORT_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.PROPOSAL_STANCES,
            name=PropstoreFamily.PROPOSAL_STANCES.value,
            contract_version=PROPOSAL_STANCE_FAMILY.contract_version,
            artifact_family=PROPOSAL_STANCE_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.CONCEPT_ALIGNMENTS,
            name=PropstoreFamily.CONCEPT_ALIGNMENTS.value,
            contract_version=CONCEPT_ALIGNMENT_FAMILY.contract_version,
            artifact_family=CONCEPT_ALIGNMENT_FAMILY,
        ),
        FamilyDefinition(
            key=PropstoreFamily.MERGE_MANIFESTS,
            name=PropstoreFamily.MERGE_MANIFESTS.value,
            contract_version=MERGE_MANIFEST_FAMILY.contract_version,
            artifact_family=MERGE_MANIFEST_FAMILY,
        ),
    ),
)
