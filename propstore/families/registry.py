from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from quire.artifacts import (
    ArtifactFamily,
    BranchPlacement,
    FixedFilePlacement,
    FlatYamlPlacement,
    SingletonFilePlacement,
    TemplateFilePlacement,
)
from quire.families import FamilyDefinition, FamilyIdentityPolicy, FamilyRegistry
from quire.documents import (
    coerce_json_mapping,
    coerce_text_document,
    decode_json_mapping,
    decode_text_document,
    encode_json_mapping,
    encode_text_document,
    identity_json_mapping,
    identity_text_document,
    render_json_mapping,
)
from quire.references import ForeignKeySpec
from quire.refs import single_field_ref_type, singleton_ref_type
from quire.versions import VersionId

from propstore.families.addresses import SemanticFamilyAddress
from propstore.families.documents.claims import ClaimsFileDocument
from propstore.families.documents.concepts import ConceptDocument
from propstore.families.documents.contexts import ContextDocument
from propstore.families.documents.forms import FormDocument
from propstore.families.documents.merge import MergeManifestDocument
from propstore.families.documents.micropubs import MicropublicationsFileDocument
from propstore.families.documents.predicates import PredicatesFileDocument
from propstore.families.documents.rules import RulesFileDocument
from propstore.families.documents.source_alignment import ConceptAlignmentArtifactDocument
from propstore.families.documents.sources import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
)
from propstore.families.documents.stances import StanceFileDocument
from propstore.families.documents.worldlines import WorldlineDefinitionDocument
from propstore.families.identity.claims import (
    CLAIM_SOURCE_LOCAL_FIELDS,
    CLAIM_VERSION_ID_EXCLUDED_FIELDS,
    canonicalize_claim_for_version,
    compute_claim_version_id,
    derive_claim_artifact_id,
    normalize_canonical_claim_payload,
)
from propstore.families.identity.concepts import (
    CONCEPT_VERSION_ID_EXCLUDED_FIELDS,
    canonicalize_concept_for_version,
    compute_concept_version_id,
    derive_concept_artifact_id,
    normalize_canonical_concept_payload,
)
from propstore.core.concepts import (
    concept_document_to_payload,
    encode_concept_document,
    normalize_concept_document_for_write,
    render_concept_document,
)

if TYPE_CHECKING:
    from propstore.repository import Repository

    @dataclass(frozen=True)
    class SourceRef:
        name: str

    @dataclass(frozen=True)
    class ContextRef:
        name: str

    @dataclass(frozen=True)
    class FormRef:
        name: str

    @dataclass(frozen=True)
    class WorldlineRef:
        name: str

    @dataclass(frozen=True)
    class CanonicalSourceRef:
        name: str

    @dataclass(frozen=True)
    class ClaimsFileRef:
        name: str

    @dataclass(frozen=True)
    class MicropubsFileRef:
        name: str

    @dataclass(frozen=True)
    class ConceptFileRef:
        name: str

    @dataclass(frozen=True)
    class JustificationsFileRef:
        name: str

    @dataclass(frozen=True)
    class PredicateFileRef:
        name: str

    @dataclass(frozen=True)
    class RuleFileRef:
        name: str

    @dataclass(frozen=True)
    class StanceFileRef:
        source_claim: str

    @dataclass(frozen=True)
    class ConceptAlignmentRef:
        slug: str

    @dataclass(frozen=True)
    class MergeManifestRef:
        pass


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


if not TYPE_CHECKING:
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


ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.27")
CONCEPT_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.28")
IDENTITY_POLICY_FAMILY_CONTRACT_VERSION = VersionId("2026.04.29")
SOURCE_SIDE_FILE_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.28")
PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION = VersionId("2026.04.29")
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


def _callable_id(callback: object) -> str:
    module = getattr(callback, "__module__", None)
    qualname = getattr(callback, "__qualname__", None)
    if not module or not qualname:
        raise TypeError(f"identity policy callback is not named: {callback!r}")
    return f"{module}.{qualname}"


CLAIM_IDENTITY_POLICY = FamilyIdentityPolicy(
    artifact_id_function=_callable_id(derive_claim_artifact_id),
    version_id_function=_callable_id(compute_claim_version_id),
    canonical_payload_function=_callable_id(canonicalize_claim_for_version),
    normalize_payload_function=_callable_id(normalize_canonical_claim_payload),
    logical_id_fields=("logical_ids",),
    version_excluded_fields=CLAIM_VERSION_ID_EXCLUDED_FIELDS,
    source_local_fields=CLAIM_SOURCE_LOCAL_FIELDS,
)

CONCEPT_IDENTITY_POLICY = FamilyIdentityPolicy(
    artifact_id_function=_callable_id(derive_concept_artifact_id),
    version_id_function=_callable_id(compute_concept_version_id),
    canonical_payload_function=_callable_id(canonicalize_concept_for_version),
    normalize_payload_function=_callable_id(normalize_canonical_concept_payload),
    logical_id_fields=("logical_ids",),
    version_excluded_fields=CONCEPT_VERSION_ID_EXCLUDED_FIELDS,
)

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
    encode_document=encode_concept_document,
    render_document=render_concept_document,
    document_payload=concept_document_to_payload,
    normalize_for_write=normalize_concept_document_for_write,
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
    contract_version=SOURCE_SIDE_FILE_ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=str,
    placement=SOURCE_NOTES_PLACEMENT,
    coerce_payload=coerce_text_document,
    decode_bytes=decode_text_document,
    encode_document=encode_text_document,
    render_document=identity_text_document,
    document_payload=identity_text_document,
)

SOURCE_METADATA_FAMILY = ArtifactFamily["Repository", SourceRef, dict[str, Any]](
    name="source_metadata",
    contract_version=SOURCE_SIDE_FILE_ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=dict,
    placement=SOURCE_METADATA_PLACEMENT,
    coerce_payload=coerce_json_mapping,
    decode_bytes=decode_json_mapping,
    encode_document=encode_json_mapping,
    render_document=render_json_mapping,
    document_payload=identity_json_mapping,
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
            contract_version=IDENTITY_POLICY_FAMILY_CONTRACT_VERSION,
            artifact_family=CLAIMS_FILE_FAMILY,
            foreign_keys=CLAIM_FOREIGN_KEYS,
            identity_policy=CLAIM_IDENTITY_POLICY,
            metadata=_semantic_metadata(importable=True, import_order=20, collection_field="claims"),
        ),
        FamilyDefinition(
            key=PropstoreFamily.CONCEPTS,
            name=PropstoreFamily.CONCEPTS.value,
            contract_version=IDENTITY_POLICY_FAMILY_CONTRACT_VERSION,
            artifact_family=CONCEPT_FILE_FAMILY,
            foreign_keys=CONCEPT_FOREIGN_KEYS,
            identity_policy=CONCEPT_IDENTITY_POLICY,
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
    return tuple(_semantic_root(family) for family in semantic_import_families())


def semantic_import_families() -> tuple[FamilyDefinition[Any, Any, Any, Any], ...]:
    return tuple(
        sorted(
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


def semantic_address_path(name: str, repo: Repository, ref: object) -> SemanticFamilyAddress:
    family = semantic_family_by_name(name).artifact_family
    return SemanticFamilyAddress(family.address_for(repo, ref).require_path())
