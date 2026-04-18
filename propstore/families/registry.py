from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import msgspec
from quire.artifacts import (
    ArtifactContext,
    ArtifactFamily,
    BranchPlacement,
    FixedFilePlacement,
    FlatYamlPlacement,
    SingletonFilePlacement,
    TemplateFilePlacement,
)
from quire.families import FamilyDefinition, FamilyRegistry
from quire.family_store import DocumentFamilyStore
from quire.documents import decode_yaml_mapping
from quire.references import ForeignKeySpec
from quire.refs import single_field_ref_type, singleton_ref_type
from quire.versions import VersionId

from propstore.artifacts.documents.claims import ClaimsFileDocument
from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.artifacts.documents.contexts import ContextDocument
from propstore.artifacts.documents.forms import FormDocument
from propstore.artifacts.documents.merge import MergeManifestDocument
from propstore.artifacts.documents.micropubs import MicropublicationsFileDocument
from propstore.artifacts.documents.predicates import PredicatesFileDocument
from propstore.artifacts.documents.rules import RulesFileDocument
from propstore.artifacts.documents.source_alignment import ConceptAlignmentArtifactDocument
from propstore.artifacts.documents.sources import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
)
from propstore.artifacts.documents.stances import StanceFileDocument
from propstore.artifacts.documents.worldlines import WorldlineDefinitionDocument
from propstore.core.concepts import concept_document_to_payload
from propstore.identity import (
    concept_reference_keys,
    normalize_canonical_claim_payload,
    normalize_canonical_concept_payload,
    normalize_claim_file_payload,
)
from propstore.claim_references import ImportedClaimHandleIndex

if TYPE_CHECKING:
    from propstore.repository import Repository


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


SourceRef = single_field_ref_type("SourceRef", "name", module=__name__)
ContextRef = single_field_ref_type("ContextRef", "name", module=__name__)
FormRef = single_field_ref_type("FormRef", "name", module=__name__)
WorldlineRef = single_field_ref_type("WorldlineRef", "name", module=__name__)
CanonicalSourceRef = single_field_ref_type("CanonicalSourceRef", "name", module=__name__)
ClaimsFileRef = single_field_ref_type("ClaimsFileRef", "name", module=__name__)
MicropubsFileRef = single_field_ref_type("MicropubsFileRef", "name", module=__name__)
ConceptFileRef = single_field_ref_type("ConceptFileRef", "name", module=__name__)
JustificationsFileRef = single_field_ref_type("JustificationsFileRef", "name", module=__name__)
PredicateFileRef = single_field_ref_type("PredicateFileRef", "name", module=__name__)
RuleFileRef = single_field_ref_type("RuleFileRef", "name", module=__name__)
StanceFileRef = single_field_ref_type("StanceFileRef", "source_claim", module=__name__)
ConceptAlignmentRef = single_field_ref_type("ConceptAlignmentRef", "slug", module=__name__)
MergeManifestRef = singleton_ref_type("MergeManifestRef", module=__name__)


ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.24")
CONCEPT_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.25")
PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION = VersionId("2026.04.25")
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.04.22")
PRIMARY_ARTIFACT_BRANCH = BranchPlacement(policy="primary")
CURRENT_ARTIFACT_BRANCH = BranchPlacement(policy="current")
SOURCE_BRANCH = BranchPlacement(
    policy="template",
    template="source/{stem}",
    ref_field="name",
    codec="safe_slug",
)
PROPOSAL_STANCE_BRANCH = BranchPlacement(policy="fixed", fixed_branch="proposal/stances")
PROPOSAL_CONCEPT_BRANCH = BranchPlacement(policy="fixed", fixed_branch="proposal/concepts")

CLAIM_PLACEMENT = FlatYamlPlacement["Repository", ClaimsFileRef](
    namespace=PropstoreFamily.CLAIMS.value,
    ref_factory=ClaimsFileRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
CONCEPT_PLACEMENT = FlatYamlPlacement["Repository", ConceptFileRef](
    namespace=PropstoreFamily.CONCEPTS.value,
    ref_factory=ConceptFileRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
CONTEXT_PLACEMENT = FlatYamlPlacement["Repository", ContextRef](
    namespace=PropstoreFamily.CONTEXTS.value,
    ref_factory=ContextRef,
    ref_field="name",
    branch=CURRENT_ARTIFACT_BRANCH,
)
FORM_PLACEMENT = FlatYamlPlacement["Repository", FormRef](
    namespace=PropstoreFamily.FORMS.value,
    ref_factory=FormRef,
    ref_field="name",
    branch=CURRENT_ARTIFACT_BRANCH,
)
PREDICATE_PLACEMENT = FlatYamlPlacement["Repository", PredicateFileRef](
    namespace=PropstoreFamily.PREDICATES.value,
    ref_factory=PredicateFileRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
RULE_PLACEMENT = FlatYamlPlacement["Repository", RuleFileRef](
    namespace=PropstoreFamily.RULES.value,
    ref_factory=RuleFileRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
STANCE_PLACEMENT = FlatYamlPlacement["Repository", StanceFileRef](
    namespace=PropstoreFamily.STANCES.value,
    ref_factory=StanceFileRef,
    ref_field="source_claim",
    codec="colon_to_double_underscore",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
WORLDLINE_PLACEMENT = FlatYamlPlacement["Repository", WorldlineRef](
    namespace=PropstoreFamily.WORLDLINES.value,
    ref_factory=WorldlineRef,
    ref_field="name",
    branch=CURRENT_ARTIFACT_BRANCH,
)
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


def _concept_document_payload(document: ConceptDocument) -> dict[str, Any]:
    return concept_document_to_payload(document)


def _encode_concept_document(document: ConceptDocument) -> bytes:
    return msgspec.yaml.encode(_concept_document_payload(document))


def _render_concept_document(document: ConceptDocument) -> str:
    return _encode_concept_document(document).decode("utf-8").rstrip()


def _normalize_concept_for_write(
    context: ArtifactContext["Repository", ConceptFileRef],
    document: ConceptDocument,
    store: DocumentFamilyStore["Repository"],
) -> ConceptDocument:
    payload = store.payload(document)
    source = f"{context.branch}:{context.require_path()}"
    if not isinstance(payload, dict):
        raise TypeError(f"{source}: expected concept payload mapping")
    return store.coerce(
        CONCEPT_FILE_FAMILY,
        normalize_canonical_concept_payload(payload),
        source=source,
    )


CONTEXT_FAMILY = ArtifactFamily["Repository", ContextRef, ContextDocument](
    name="context",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ContextDocument,
    placement=CONTEXT_PLACEMENT,
)

FORM_FAMILY = ArtifactFamily["Repository", FormRef, FormDocument](
    name="form",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=FormDocument,
    placement=FORM_PLACEMENT,
)

CLAIMS_FILE_FAMILY = ArtifactFamily["Repository", ClaimsFileRef, ClaimsFileDocument](
    name="claims_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ClaimsFileDocument,
    placement=CLAIM_PLACEMENT,
)

CONCEPT_FILE_FAMILY = ArtifactFamily["Repository", ConceptFileRef, ConceptDocument](
    name="concept_file",
    contract_version=CONCEPT_ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ConceptDocument,
    placement=CONCEPT_PLACEMENT,
    encode_document=_encode_concept_document,
    render_document=_render_concept_document,
    document_payload=_concept_document_payload,
    normalize_for_write=_normalize_concept_for_write,
)

PREDICATE_FILE_FAMILY = ArtifactFamily["Repository", PredicateFileRef, PredicatesFileDocument](
    name="predicate_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=PredicatesFileDocument,
    placement=PREDICATE_PLACEMENT,
)

RULE_FILE_FAMILY = ArtifactFamily["Repository", RuleFileRef, RulesFileDocument](
    name="rule_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=RulesFileDocument,
    placement=RULE_PLACEMENT,
)

STANCE_FILE_FAMILY = ArtifactFamily["Repository", StanceFileRef, StanceFileDocument](
    name="stance_file",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=StanceFileDocument,
    placement=STANCE_PLACEMENT,
)

WORLDLINE_FAMILY = ArtifactFamily["Repository", WorldlineRef, WorldlineDefinitionDocument](
    name="worldline",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=WorldlineDefinitionDocument,
    placement=WORLDLINE_PLACEMENT,
)


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


CLAIM_FOREIGN_KEYS = (
    ForeignKeySpec(
        name="claim_concept",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="concept",
        target_family="concept",
    ),
    ForeignKeySpec(
        name="claim_concepts",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="concepts",
        target_family="concept",
        many=True,
    ),
    ForeignKeySpec(
        name="claim_variable_concept",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="variables[].concept",
        target_family="concept",
    ),
    ForeignKeySpec(
        name="claim_parameter_concept",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="parameters[].concept",
        target_family="concept",
    ),
    ForeignKeySpec(
        name="claim_measurement_target_concept",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="target_concept",
        target_family="concept",
    ),
    ForeignKeySpec(
        name="claim_stance_target",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="stances[].target",
        target_family="claim",
    ),
    ForeignKeySpec(
        name="claim_context",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="context",
        target_family="context",
    ),
)


CONCEPT_FOREIGN_KEYS = (
    ForeignKeySpec(
        name="concept_parameterization_input",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="parameterization_relationships[].inputs[]",
        target_family="concept",
        many=True,
    ),
    ForeignKeySpec(
        name="concept_parameterization_canonical_claim",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="parameterization_relationships[].canonical_claim",
        target_family="claim",
        required=False,
    ),
    ForeignKeySpec(
        name="concept_replaced_by",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="replaced_by",
        target_family="concept",
        required=False,
    ),
    ForeignKeySpec(
        name="concept_relationship_target",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="relationships[].target",
        target_family="concept",
        many=True,
    ),
    ForeignKeySpec(
        name="concept_form",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="form",
        target_family="form",
    ),
)


@dataclass(frozen=True)
class PlannedSemanticWrite:
    family: ArtifactFamily[Any, Any, Any]
    ref: object
    document: object
    relpath: str


@dataclass
class SemanticImportState:
    repository_name: str
    concept_ref_map: dict[str, str] = field(default_factory=dict)
    local_handle_index: ImportedClaimHandleIndex = field(default_factory=ImportedClaimHandleIndex)
    warnings: list[str] = field(default_factory=list)


SemanticImportBatch = Callable[
    [
        DocumentFamilyStore["Repository"],
        Sequence[str],
        Mapping[str, bytes],
        SemanticImportState,
    ],
    Mapping[str, PlannedSemanticWrite],
]


def _semantic_metadata(
    *,
    importable: bool = False,
    import_order: int = 100,
    init_directory: bool = True,
    collection_field: str | None = None,
) -> dict[str, object]:
    return {
        "semantic": True,
        "importable": importable,
        "import_order": import_order,
        "init_directory": init_directory,
        "collection_field": collection_field,
    }


PROPSTORE_FAMILY_REGISTRY = FamilyRegistry(
    name="propstore",
    contract_version=PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION,
    families=(
        FamilyDefinition(
            key=PropstoreFamily.CLAIMS,
            name=PropstoreFamily.CLAIMS.value,
            contract_version=CLAIMS_FILE_FAMILY.contract_version,
            artifact_family=CLAIMS_FILE_FAMILY,
            foreign_keys=CLAIM_FOREIGN_KEYS,
            metadata=_semantic_metadata(importable=True, import_order=20, collection_field="claims"),
        ),
        FamilyDefinition(
            key=PropstoreFamily.CONCEPTS,
            name=PropstoreFamily.CONCEPTS.value,
            contract_version=CONCEPT_FILE_FAMILY.contract_version,
            artifact_family=CONCEPT_FILE_FAMILY,
            foreign_keys=CONCEPT_FOREIGN_KEYS,
            metadata=_semantic_metadata(importable=True, import_order=10),
        ),
        FamilyDefinition(
            key=PropstoreFamily.CONTEXTS,
            name=PropstoreFamily.CONTEXTS.value,
            contract_version=CONTEXT_FAMILY.contract_version,
            artifact_family=CONTEXT_FAMILY,
            metadata=_semantic_metadata(importable=True, import_order=30),
        ),
        FamilyDefinition(
            key=PropstoreFamily.FORMS,
            name=PropstoreFamily.FORMS.value,
            contract_version=FORM_FAMILY.contract_version,
            artifact_family=FORM_FAMILY,
            metadata=_semantic_metadata(importable=True, import_order=30),
        ),
        FamilyDefinition(
            key=PropstoreFamily.PREDICATES,
            name=PropstoreFamily.PREDICATES.value,
            contract_version=PREDICATE_FILE_FAMILY.contract_version,
            artifact_family=PREDICATE_FILE_FAMILY,
            metadata=_semantic_metadata(importable=True, import_order=40, collection_field="predicates"),
        ),
        FamilyDefinition(
            key=PropstoreFamily.RULES,
            name=PropstoreFamily.RULES.value,
            contract_version=RULE_FILE_FAMILY.contract_version,
            artifact_family=RULE_FILE_FAMILY,
            metadata=_semantic_metadata(importable=True, import_order=50, collection_field="rules"),
        ),
        FamilyDefinition(
            key=PropstoreFamily.STANCES,
            name=PropstoreFamily.STANCES.value,
            contract_version=STANCE_FILE_FAMILY.contract_version,
            artifact_family=STANCE_FILE_FAMILY,
            metadata=_semantic_metadata(importable=True, import_order=60, collection_field="stances"),
        ),
        FamilyDefinition(
            key=PropstoreFamily.WORLDLINES,
            name=PropstoreFamily.WORLDLINES.value,
            contract_version=WORLDLINE_FAMILY.contract_version,
            artifact_family=WORLDLINE_FAMILY,
            metadata=_semantic_metadata(importable=True, import_order=70),
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


def _metadata(family: FamilyDefinition[Any, Any, Any, Any]) -> Mapping[str, object]:
    return family.metadata or {}


def _is_semantic_family(family: FamilyDefinition[Any, Any, Any, Any]) -> bool:
    return _metadata(family).get("semantic") is True


def _semantic_import_order(family: FamilyDefinition[Any, Any, Any, Any]) -> int:
    value = _metadata(family).get("import_order", 100)
    return value if isinstance(value, int) else 100


def _semantic_init_directory(family: FamilyDefinition[Any, Any, Any, Any]) -> bool:
    return _metadata(family).get("init_directory") is not False


def _semantic_importable(family: FamilyDefinition[Any, Any, Any, Any]) -> bool:
    return _metadata(family).get("importable") is True


def _semantic_root(family: FamilyDefinition[Any, Any, Any, Any]) -> str:
    placement_body = family.artifact_family.placement.contract_body()
    namespace = placement_body.get("namespace")
    if not isinstance(namespace, str) or not namespace:
        raise ValueError(f"family {family.name!r} does not use a namespace placement")
    return namespace


def semantic_families() -> tuple[FamilyDefinition[Any, Any, Any, Any], ...]:
    return tuple(family for family in PROPSTORE_FAMILY_REGISTRY.families if _is_semantic_family(family))


def semantic_family_names() -> tuple[str, ...]:
    return tuple(family.name for family in semantic_families())


def semantic_family_by_name(name: str) -> FamilyDefinition[Any, Any, Any, Any]:
    family = PROPSTORE_FAMILY_REGISTRY.by_name(name)
    if not _is_semantic_family(family):
        raise KeyError(f"not a semantic family: {name}")
    return family


def semantic_family_by_root(root: str) -> FamilyDefinition[Any, Any, Any, Any]:
    for family in semantic_families():
        if _semantic_root(family) == root:
            return family
    raise KeyError(f"unknown semantic family root: {root}")


def semantic_family_for_path(path: str | Path) -> FamilyDefinition[Any, Any, Any, Any]:
    normalized = str(path).replace("\\", "/")
    return semantic_family_by_root(normalized.split("/", 1)[0])


def semantic_init_roots() -> tuple[str, ...]:
    return tuple(_semantic_root(family) for family in semantic_families() if _semantic_init_directory(family))


def semantic_import_roots() -> tuple[str, ...]:
    return tuple(
        _semantic_root(family)
        for family in sorted(
            (family for family in semantic_families() if _semantic_importable(family)),
            key=lambda item: (_semantic_import_order(item), item.name),
        )
    )


def semantic_foreign_keys() -> tuple[ForeignKeySpec, ...]:
    specs = [spec for family in semantic_families() for spec in family.foreign_keys]
    return tuple(sorted(specs, key=lambda spec: spec.name))


def semantic_root_path(name: str, tree_or_repo: object) -> Path:
    root = _semantic_root(semantic_family_by_name(name))
    if isinstance(tree_or_repo, Path):
        return tree_or_repo / root
    repo_root = getattr(tree_or_repo, "root", None)
    if isinstance(repo_root, Path):
        return repo_root / root
    raise TypeError(f"cannot resolve semantic root for {type(tree_or_repo).__name__}")


def semantic_address_path(name: str, repo: Repository, ref: object) -> str:
    family = semantic_family_by_name(name).artifact_family
    return family.address_for(repo, ref).require_path()


def _decode_yaml(content: bytes, *, path: str) -> dict[str, Any]:
    return decode_yaml_mapping(content, source=path)


def _planned_write(
    store: DocumentFamilyStore["Repository"],
    path: str,
    payload: object,
) -> PlannedSemanticWrite:
    family = semantic_family_for_path(path).artifact_family
    ref = store.ref_from_path(cast(Any, family), path)
    document = store.coerce(cast(Any, family), payload, source=path)
    address = store.address(cast(Any, family), ref)
    return PlannedSemanticWrite(
        family=family,
        ref=ref,
        document=document,
        relpath=address.require_path(),
    )


def _document_payload(
    store: DocumentFamilyStore["Repository"],
    write: PlannedSemanticWrite,
) -> object:
    return store.payload(write.document, cast(Any, write.family))


def _claim_source_from_import_path(path: str) -> dict[str, str]:
    return {"paper": Path(path).stem}


def _rewrite_reference(value: Any, reference_map: Mapping[str, str]) -> Any:
    if not isinstance(value, str):
        return value
    return reference_map.get(value, value)


def _rewrite_concept_payload_refs(
    data: dict[str, Any],
    *,
    concept_ref_map: Mapping[str, str],
) -> dict[str, Any]:
    rewritten = dict(data)
    if "replaced_by" in rewritten:
        rewritten["replaced_by"] = _rewrite_reference(rewritten.get("replaced_by"), concept_ref_map)

    relationships = rewritten.get("relationships")
    if isinstance(relationships, list):
        rewritten["relationships"] = [
            (
                {**relationship, "target": _rewrite_reference(relationship.get("target"), concept_ref_map)}
                if isinstance(relationship, dict)
                else relationship
            )
            for relationship in relationships
        ]

    parameterizations = rewritten.get("parameterization_relationships")
    if isinstance(parameterizations, list):
        updated_parameterizations = []
        for parameterization in parameterizations:
            if not isinstance(parameterization, dict):
                updated_parameterizations.append(parameterization)
                continue
            copied = dict(parameterization)
            inputs = copied.get("inputs")
            if isinstance(inputs, list):
                copied["inputs"] = [_rewrite_reference(input_id, concept_ref_map) for input_id in inputs]
            updated_parameterizations.append(copied)
        rewritten["parameterization_relationships"] = updated_parameterizations

    return normalize_canonical_concept_payload(rewritten)


def _rewrite_claim_concept_refs(
    data: dict[str, Any],
    *,
    concept_ref_map: Mapping[str, str],
) -> dict[str, Any]:
    rewritten = dict(data)
    claims = rewritten.get("claims")
    if not isinstance(claims, list):
        return rewritten

    updated_claims: list[Any] = []
    for claim in claims:
        if not isinstance(claim, dict):
            updated_claims.append(claim)
            continue
        copied = dict(claim)
        if "concept" in copied:
            copied["concept"] = _rewrite_reference(copied.get("concept"), concept_ref_map)
        if "target_concept" in copied:
            copied["target_concept"] = _rewrite_reference(copied.get("target_concept"), concept_ref_map)
        concepts = copied.get("concepts")
        if isinstance(concepts, list):
            copied["concepts"] = [_rewrite_reference(concept_ref, concept_ref_map) for concept_ref in concepts]
        for field_name in ("variables", "parameters"):
            values = copied.get(field_name)
            if not isinstance(values, list):
                continue
            copied[field_name] = [
                (
                    {**value, "concept": _rewrite_reference(value.get("concept"), concept_ref_map)}
                    if isinstance(value, dict)
                    else value
                )
                for value in values
            ]
        updated_claims.append(normalize_canonical_claim_payload(copied))

    rewritten["claims"] = updated_claims
    return rewritten


def _normalize_concept_payload(
    data: dict[str, Any],
    *,
    default_domain: str,
) -> tuple[dict[str, Any], set[str]]:
    raw_id = data.get("id")
    normalized = normalize_canonical_concept_payload(
        dict(data),
        default_domain=str(default_domain or "propstore"),
    )
    return normalized, concept_reference_keys(
        normalized,
        raw_id=raw_id if isinstance(raw_id, str) else None,
    )


def _normalize_concept_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    seeded: dict[str, PlannedSemanticWrite] = {}
    for path in paths:
        payload = _decode_yaml(writes[path], path=path)
        canonical_name = payload.get("canonical_name")
        raw_id = payload.get("id")
        effective_name = canonical_name if isinstance(canonical_name, str) and canonical_name else str(raw_id or Path(path).stem or "concept")
        payload.setdefault("canonical_name", effective_name)
        payload.setdefault("status", "accepted")
        payload.setdefault("definition", effective_name)
        payload.setdefault("form", "structural")

        normalized_payload, reference_keys = _normalize_concept_payload(payload, default_domain=state.repository_name)
        concept_write = _planned_write(store, path, normalized_payload)
        seeded[path] = concept_write
        artifact_id = getattr(concept_write.document, "artifact_id", None)
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ValueError(f"Imported concept {path!r} is missing artifact_id after normalization")
        for reference_key in reference_keys:
            state.concept_ref_map[str(reference_key)] = artifact_id

    normalized: dict[str, PlannedSemanticWrite] = {}
    for path, concept_write in seeded.items():
        payload = _document_payload(store, concept_write)
        if not isinstance(payload, dict):
            raise TypeError(f"Imported concept {path!r} did not render to a mapping payload")
        normalized[path] = _planned_write(
            store,
            path,
            _rewrite_concept_payload_refs(payload, concept_ref_map=state.concept_ref_map),
        )
    return normalized


def _normalize_claim_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    for path in paths:
        payload = _decode_yaml(writes[path], path=path)
        source = payload.get("source")
        has_source = isinstance(source, dict) and isinstance(source.get("paper"), str) and bool(source.get("paper"))
        normalized_payload, local_map = normalize_claim_file_payload(payload, default_namespace=state.repository_name)
        if not has_source:
            normalized_payload["source"] = _claim_source_from_import_path(path)
        rewritten_payload = _rewrite_claim_concept_refs(normalized_payload, concept_ref_map=state.concept_ref_map)
        normalized[path] = _planned_write(store, path, rewritten_payload)
        for local_id, artifact_id in local_map.items():
            if state.local_handle_index.record(local_id, artifact_id):
                state.warnings.append(
                    f"ambiguous imported claim handle {local_id!r}; stance files must use artifact IDs"
                )
    return normalized


def _normalize_stance_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    return {
        path: _planned_write(
            store,
            path,
            state.local_handle_index.rewrite_stance_payload(_decode_yaml(writes[path], path=path), path=path),
        )
        for path in paths
    }


def _normalize_passthrough_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    del state
    return {
        path: _planned_write(store, path, _decode_yaml(writes[path], path=path))
        for path in paths
    }


_SEMANTIC_IMPORT_NORMALIZERS: Mapping[PropstoreFamily, SemanticImportBatch] = {
    PropstoreFamily.CONCEPTS: _normalize_concept_batch,
    PropstoreFamily.CLAIMS: _normalize_claim_batch,
    PropstoreFamily.STANCES: _normalize_stance_batch,
}


def normalize_semantic_import_writes(
    store: DocumentFamilyStore["Repository"],
    writes: Mapping[str, bytes],
    *,
    repository_name: str,
) -> tuple[dict[str, PlannedSemanticWrite], list[str]]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    state = SemanticImportState(repository_name=repository_name)
    importable = sorted(
        (family for family in semantic_families() if _semantic_importable(family)),
        key=lambda item: (_semantic_import_order(item), item.name),
    )
    for family in importable:
        family_paths = [
            path
            for path in sorted(writes)
            if semantic_family_for_path(path).name == family.name
        ]
        if not family_paths:
            continue
        normalizer = _SEMANTIC_IMPORT_NORMALIZERS.get(cast(PropstoreFamily, family.key), _normalize_passthrough_batch)
        normalized.update(normalizer(store, family_paths, writes, state))
    return normalized, list(state.warnings)
