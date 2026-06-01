from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from typing import TYPE_CHECKING, Any

from quire.charters import FamilyCharter, charter_catalog
from quire.schema_catalog import SchemaCatalog
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.artifacts import (
    ArtifactFamily,
    BlobRefPlacement,
    BranchPlacement,
    FixedFilePlacement,
    FlatYamlPlacement,
    HashScatteredYamlPlacement,
    NestedFlatYamlPlacement,
    SingletonFilePlacement,
    SubdirFixedFilePlacement,
    TemplateFilePlacement,
    batch_artifact_family,
)
from quire import ContractManifest
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
from quire.references import ForeignKeySpec, ReferenceKey
from quire.refs import RefName, single_field_ref_type, singleton_ref_type
from quire.versions import VersionId

from propstore.contracts import decode_schema_manifest, encode_schema_manifest
from propstore.families.addresses import SemanticFamilyAddress
from propstore.families.claims.declaration import (
    AUTHORED_CLAIM_CHARTER,
    AUTHORED_CLAIM_FAMILY_CONTRACT_VERSION,
    ClaimDocument,
    JUSTIFICATION_CHARTER,
    SOURCE_CLAIM_BATCH_SPEC,
    SOURCE_JUSTIFICATION_BATCH_SPEC,
    SourceClaimDocument,
    SourceJustificationDocument,
)
from propstore.families.concepts.declaration import (
    AUTHORED_CONCEPT_CHARTER,
    AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
    ConceptDocument,
    SOURCE_CONCEPT_BATCH_SPEC,
    SourceConceptEntryDocument,
)
from propstore.families.contexts.declaration import CONTEXT_CHARTER
from propstore.families.forms.models import FORM_CHARTER
from propstore.families.merge.declaration import (
    MERGE_MANIFEST_FAMILY_CONTRACT_VERSION,
    MergeManifestDocument,
)
from propstore.families.micropublications.declaration import (
    MICROPUBLICATION_CHARTER,
    SOURCE_MICROPUBLICATION_BATCH_SPEC,
    MicropublicationDocument,
)
from propstore.families.predicates.declaration import (
    PREDICATE_FAMILY_CONTRACT_VERSION,
    PredicateDocument,
    PredicateProposalArtifact,
)
from propstore.families.rules.declaration import (
    AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
    AuthoredRuleProposalArtifact,
    RuleDocument,
    RuleSuperiorityDocument,
)
from propstore.families.sameas.declaration import SameAsAssertionDocument
from propstore.families.source_alignment.declaration import (
    SOURCE_ALIGNMENT_FAMILY_CONTRACT_VERSION,
    ConceptAlignmentArtifactDocument,
)
from propstore.families.sources.declaration import SourceFinalizeReportDocument
from propstore.families.stances.declaration import (
    SOURCE_STANCE_BATCH_SPEC,
    STANCE_CHARTER,
    SourceStanceEntryDocument,
    StanceDocument,
)
from propstore.families.worldlines.declaration import (
    WORLDLINES_FAMILY_CONTRACT_VERSION,
    WorldlineDefinitionDocument,
)
from propstore.families.identity.claims import (
    CLAIM_SOURCE_LOCAL_FIELDS,
    CLAIM_VERSION_ID_EXCLUDED_FIELDS,
    canonicalize_claim_for_version,
    compute_claim_version_id,
    derive_claim_artifact_id,
    normalize_canonical_claim_payload,
)
from propstore.families.sources.declaration import (
    SourceDocument,
    encode_source_document,
    render_source_document,
    source_document_payload,
)
from propstore.families.identity.concepts import (
    CONCEPT_VERSION_ID_EXCLUDED_FIELDS,
    canonicalize_concept_for_version,
    compute_concept_version_id,
    derive_concept_artifact_id,
    normalize_canonical_concept_payload,
)
from propstore.families.concepts.stages import (
    encode_concept_document,
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
    class ClaimRef:
        artifact_id: str

    @dataclass(frozen=True)
    class MicropublicationRef:
        artifact_id: str

    @dataclass(frozen=True)
    class ConceptFileRef:
        name: str

    @dataclass(frozen=True)
    class JustificationRef:
        artifact_id: str

    @dataclass(frozen=True)
    class PredicateRef:
        predicate_id: str

    @dataclass(frozen=True)
    class RuleRef:
        rule_id: str

    @dataclass(frozen=True)
    class RuleSuperiorityRef:
        artifact_id: str

    @dataclass(frozen=True)
    class PredicateProposalRef:
        source_paper: str

    @dataclass(frozen=True)
    class RuleProposalRef:
        source_paper: str
        rule_id: str

    @dataclass(frozen=True)
    class StanceRef:
        artifact_id: str

    @dataclass(frozen=True)
    class SameAsAssertionRef:
        artifact_id: str

    @dataclass(frozen=True)
    class ConceptAlignmentRef:
        slug: str

    @dataclass(frozen=True)
    class MergeManifestRef:
        pass

    @dataclass(frozen=True)
    class SchemaRef:
        pass


class PropstoreFamily(str, Enum):
    CLAIMS = "claims"
    CONCEPTS = "concepts"
    CONTEXTS = "contexts"
    FORMS = "forms"
    PREDICATES = "predicates"
    RULES = "rules"
    RULE_SUPERIORITY = "rule_superiority"
    STANCES = "stances"
    SAMEAS = "sameas"
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
    PROPOSAL_PREDICATES = "proposal_predicates"
    PROPOSAL_RULES = "proposal_rules"
    CONCEPT_ALIGNMENTS = "concept_alignments"
    MERGE_MANIFESTS = "merge_manifests"
    SCHEMA = "schema"


if not TYPE_CHECKING:
    SourceRef = single_field_ref_type("SourceRef", "name", module=__name__)
    ContextRef = single_field_ref_type("ContextRef", "name", module=__name__)
    FormRef = single_field_ref_type("FormRef", "name", module=__name__)
    WorldlineRef = single_field_ref_type("WorldlineRef", "name", module=__name__)
    CanonicalSourceRef = single_field_ref_type("CanonicalSourceRef", "name", module=__name__)
    ClaimRef = single_field_ref_type("ClaimRef", "artifact_id", module=__name__)
    MicropublicationRef = single_field_ref_type("MicropublicationRef", "artifact_id", module=__name__)
    ConceptFileRef = single_field_ref_type("ConceptFileRef", "name", module=__name__)
    JustificationRef = single_field_ref_type("JustificationRef", "artifact_id", module=__name__)
    PredicateRef = single_field_ref_type("PredicateRef", "predicate_id", module=__name__)
    RuleRef = single_field_ref_type("RuleRef", "rule_id", module=__name__)
    RuleSuperiorityRef = single_field_ref_type("RuleSuperiorityRef", "artifact_id", module=__name__)

    @dataclass(frozen=True)
    class PredicateProposalRef:
        source_paper: str

    @dataclass(frozen=True)
    class RuleProposalRef:
        source_paper: str
        rule_id: str

    StanceRef = single_field_ref_type("StanceRef", "artifact_id", module=__name__)
    SameAsAssertionRef = single_field_ref_type("SameAsAssertionRef", "artifact_id", module=__name__)
    ConceptAlignmentRef = single_field_ref_type("ConceptAlignmentRef", "slug", module=__name__)
    MergeManifestRef = singleton_ref_type("MergeManifestRef", module=__name__)
    SchemaRef = singleton_ref_type("SchemaRef", module=__name__)


ARTIFACT_FAMILY_CONTRACT_VERSION = AUTHORED_CLAIM_FAMILY_CONTRACT_VERSION
CLAIM_FAMILY_CONTRACT_VERSION = AUTHORED_CLAIM_FAMILY_CONTRACT_VERSION
SAMEAS_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
STANCE_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
CONCEPT_ARTIFACT_FAMILY_CONTRACT_VERSION = AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION
IDENTITY_POLICY_FAMILY_CONTRACT_VERSION = VersionId("2026.04.29")
SOURCE_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
SOURCE_DOCUMENT_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.02")
SOURCE_BATCH_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.26")
SOURCE_SIDE_FILE_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.02")
PROPOSAL_DECLARATION_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.11")
INTENTIONAL_SET_FAMILY_CONTRACT_VERSION = VersionId("2026.05.11")
MICROPUBLICATION_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
MICROPUBLICATION_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
SOURCE_MICROPUBLICATION_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.26")
PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION = VersionId("2026.05.25")
REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION = VersionId("2026.05.21")
SOURCE_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
SOURCE_BATCH_FAMILY_CONTRACT_VERSION = VersionId("2026.05.26")
FORM_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
FORM_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
CONTEXT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
CONTEXT_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
JUSTIFICATION_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
JUSTIFICATION_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
SCHEMA_FAMILY_CONTRACT_VERSION = VersionId("2026.05.29")

PROPSTORE_SCHEMA_REF = RefName("refs/propstore/schema")

CONTEXT_DOCUMENT_TYPE = CONTEXT_CHARTER.generated_document()
FORM_DOCUMENT_TYPE = FORM_CHARTER.generated_document()
JustificationDocument = getattr(
    import_module("propstore.families.claims.declaration"),
    "JustificationDocument",
)
PRIMARY_ARTIFACT_BRANCH = BranchPlacement(policy="primary")
CURRENT_ARTIFACT_BRANCH = BranchPlacement(policy="current")


SOURCE_BRANCH = BranchPlacement(
    policy="template",
    template="source/{stem}",
    ref_field="name",
    codec="safe_slug",
    collision_suffix="sha256",
)
PROPOSAL_STANCE_BRANCH = BranchPlacement(policy="fixed", fixed_branch="proposal/stances")
PROPOSAL_PREDICATE_BRANCH = BranchPlacement(policy="fixed", fixed_branch="proposal/predicates")
PROPOSAL_RULE_BRANCH = BranchPlacement(policy="fixed", fixed_branch="proposal/rules")
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

CLAIM_PLACEMENT = FlatYamlPlacement["Repository", ClaimRef](
    namespace=PropstoreFamily.CLAIMS.value,
    ref_factory=ClaimRef,
    ref_field="artifact_id",
    codec="colon_to_double_underscore",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
CONCEPT_PLACEMENT = FlatYamlPlacement["Repository", ConceptFileRef](
    namespace=PropstoreFamily.CONCEPTS.value,
    ref_factory=ConceptFileRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
CANONICAL_SOURCE_PLACEMENT = FlatYamlPlacement["Repository", CanonicalSourceRef](
    "sources",
    CanonicalSourceRef,
    ref_field="name",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
MICROPUBLICATION_PLACEMENT = HashScatteredYamlPlacement["Repository", MicropublicationRef](
    "micropubs",
    MicropublicationRef,
    ref_field="artifact_id",
    codec="base64url",
    filename_mode="encoded_ref",
    branch=PRIMARY_ARTIFACT_BRANCH,
)
CLAIM_FAMILY = ArtifactFamily["Repository", ClaimRef, ClaimDocument](
    "claim",
    ARTIFACT_FAMILY_CONTRACT_VERSION,
    ClaimDocument,
    CLAIM_PLACEMENT,
)

CONCEPT_FILE_FAMILY = ArtifactFamily["Repository", ConceptFileRef, ConceptDocument](
    "concept_file",
    CONCEPT_ARTIFACT_FAMILY_CONTRACT_VERSION,
    ConceptDocument,
    CONCEPT_PLACEMENT,
    encode_document=encode_concept_document,
    render_document=render_concept_document,
)

CANONICAL_SOURCE_FAMILY = ArtifactFamily["Repository", CanonicalSourceRef, SourceDocument](
    "canonical_source",
    SOURCE_ARTIFACT_FAMILY_CONTRACT_VERSION,
    SourceDocument,
    CANONICAL_SOURCE_PLACEMENT,
    encode_document=encode_source_document,
    render_document=render_source_document,
    document_payload=source_document_payload,
)


MICROPUBLICATION_FAMILY = ArtifactFamily["Repository", MicropublicationRef, MicropublicationDocument](
    "micropublication",
    MICROPUBLICATION_ARTIFACT_FAMILY_CONTRACT_VERSION,
    MicropublicationDocument,
    MICROPUBLICATION_PLACEMENT,
)

def _semantic_metadata(
    *,
    importable: bool = False,
    import_order: int = 100,
    init_directory: bool = True,
    collection_field: str | None = None,
    aggregate_decision: str | None = None,
    aggregate_reason: str | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "semantic": True,
        "importable": importable,
        "import_order": import_order,
        "init_directory": init_directory,
        "collection_field": collection_field,
    }
    if aggregate_decision is not None:
        metadata["aggregate_decision"] = aggregate_decision
    if aggregate_reason is not None:
        metadata["aggregate_reason"] = aggregate_reason
    return metadata


def _family_definition(
    *,
    key: PropstoreFamily,
    name: str,
    contract_version: VersionId,
    artifact_name: str,
    document_type: type[Any],
    placement: Any,
    artifact_contract_version: VersionId | None = None,
    accessor: str | None = None,
    coerce_payload: Callable[..., Any] | None = None,
    decode_bytes: Callable[..., Any] | None = None,
    encode_document: Callable[..., Any] | None = None,
    render_document: Callable[..., Any] | None = None,
    document_payload: Callable[..., Any] | None = None,
    scan_type: type[Any] | None = None,
    foreign_keys: tuple[ForeignKeySpec, ...] = (),
    identity_policy: FamilyIdentityPolicy | None = None,
    identity_field: str | None = None,
    reference_keys: tuple[ReferenceKey, ...] = (),
    metadata: Mapping[str, object] | None = None,
) -> FamilyDefinition[Any, PropstoreFamily, Any, Any]:
    return FamilyDefinition(
        key=key,
        name=name,
        contract_version=contract_version,
        artifact_family=ArtifactFamily(
            artifact_name,
            artifact_contract_version or contract_version,
            document_type,
            placement,
            coerce_payload=coerce_payload,
            decode_bytes=decode_bytes,
            encode_document=encode_document,
            render_document=render_document,
            document_payload=document_payload,
            scan_type=scan_type,
        ),
        accessor=accessor,
        foreign_keys=foreign_keys,
        identity_policy=identity_policy,
        identity_field=identity_field,
        reference_keys=reference_keys,
        metadata=metadata,
    )


def _charter_foreign_keys(charter: FamilyCharter) -> tuple[ForeignKeySpec, ...]:
    specs: list[ForeignKeySpec] = []
    for field in charter.fields:
        if field.foreign_key is not None:
            specs.append(field.foreign_key)
        specs.extend(field.foreign_keys)
    return tuple(specs)


def _charter_reference_keys(charter: FamilyCharter) -> tuple[ReferenceKey, ...]:
    return charter.family.reference_keys


PROPSTORE_FAMILY_REGISTRY = FamilyRegistry(
    name="propstore",
    contract_version=PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION,
    families=(
        FamilyDefinition(
            key=PropstoreFamily.CLAIMS,
            name=PropstoreFamily.CLAIMS.value,
            contract_version=CLAIM_FAMILY_CONTRACT_VERSION,
            artifact_family=CLAIM_FAMILY,
            foreign_keys=_charter_foreign_keys(AUTHORED_CLAIM_CHARTER),
            identity_policy=CLAIM_IDENTITY_POLICY,
            identity_field="artifact_id",
            reference_keys=_charter_reference_keys(AUTHORED_CLAIM_CHARTER),
            metadata=_semantic_metadata(importable=True, import_order=20),
        ),
        FamilyDefinition(
            key=PropstoreFamily.CONCEPTS,
            name=PropstoreFamily.CONCEPTS.value,
            contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
            artifact_family=CONCEPT_FILE_FAMILY,
            foreign_keys=_charter_foreign_keys(AUTHORED_CONCEPT_CHARTER),
            identity_policy=CONCEPT_IDENTITY_POLICY,
            identity_field="artifact_id",
            reference_keys=_charter_reference_keys(AUTHORED_CONCEPT_CHARTER),
            metadata=_semantic_metadata(importable=True, import_order=10),
        ),
        _family_definition(
            key=PropstoreFamily.CONTEXTS,
            name=PropstoreFamily.CONTEXTS.value,
            contract_version=CONTEXT_FAMILY_CONTRACT_VERSION,
            artifact_name="context",
            artifact_contract_version=CONTEXT_ARTIFACT_FAMILY_CONTRACT_VERSION,
            document_type=CONTEXT_DOCUMENT_TYPE,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.CONTEXTS.value,
                ref_factory=ContextRef,
                ref_field="name",
                branch=CURRENT_ARTIFACT_BRANCH,
            ),
            identity_field="id",
            reference_keys=_charter_reference_keys(CONTEXT_CHARTER),
            metadata=_semantic_metadata(importable=True, import_order=30),
        ),
        _family_definition(
            key=PropstoreFamily.FORMS,
            name=PropstoreFamily.FORMS.value,
            contract_version=FORM_FAMILY_CONTRACT_VERSION,
            artifact_name="form",
            artifact_contract_version=FORM_ARTIFACT_FAMILY_CONTRACT_VERSION,
            document_type=FORM_DOCUMENT_TYPE,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.FORMS.value,
                ref_factory=FormRef,
                ref_field="name",
                branch=CURRENT_ARTIFACT_BRANCH,
            ),
            identity_field="name",
            metadata=_semantic_metadata(importable=True, import_order=30),
        ),
        _family_definition(
            key=PropstoreFamily.PREDICATES,
            name=PropstoreFamily.PREDICATES.value,
            contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
            artifact_name="predicate",
            document_type=PredicateDocument,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.PREDICATES.value,
                ref_factory=PredicateRef,
                ref_field="predicate_id",
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
            metadata=_semantic_metadata(
                importable=True,
                import_order=40,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.RULES,
            name=PropstoreFamily.RULES.value,
            contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
            artifact_name="rule",
            artifact_contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
            document_type=RuleDocument,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.RULES.value,
                ref_factory=RuleRef,
                ref_field="rule_id",
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
            metadata=_semantic_metadata(
                importable=True,
                import_order=50,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.RULE_SUPERIORITY,
            name=PropstoreFamily.RULE_SUPERIORITY.value,
            contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
            artifact_name="rule_superiority",
            artifact_contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
            document_type=RuleSuperiorityDocument,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.RULE_SUPERIORITY.value,
                ref_factory=RuleSuperiorityRef,
                ref_field="artifact_id",
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
            metadata=_semantic_metadata(
                importable=True,
                import_order=55,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.STANCES,
            name=PropstoreFamily.STANCES.value,
            contract_version=STANCE_FAMILY_CONTRACT_VERSION,
            artifact_name="stance",
            artifact_contract_version=STANCE_FAMILY_CONTRACT_VERSION,
            document_type=StanceDocument,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.STANCES.value,
                ref_factory=StanceRef,
                ref_field="artifact_id",
                codec="colon_to_double_underscore",
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
            foreign_keys=_charter_foreign_keys(STANCE_CHARTER),
            identity_field="artifact_code",
            metadata=_semantic_metadata(importable=True, import_order=60),
        ),
        _family_definition(
            key=PropstoreFamily.SAMEAS,
            name=PropstoreFamily.SAMEAS.value,
            contract_version=SAMEAS_FAMILY_CONTRACT_VERSION,
            artifact_name="same_as_assertion",
            document_type=SameAsAssertionDocument,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.SAMEAS.value,
                ref_factory=SameAsAssertionRef,
                ref_field="artifact_id",
                codec="colon_to_double_underscore",
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
            metadata=_semantic_metadata(importable=True, import_order=65),
        ),
        _family_definition(
            key=PropstoreFamily.WORLDLINES,
            name=PropstoreFamily.WORLDLINES.value,
            contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
            artifact_name="worldline",
            artifact_contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
            document_type=WorldlineDefinitionDocument,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.WORLDLINES.value,
                ref_factory=WorldlineRef,
                ref_field="name",
                branch=CURRENT_ARTIFACT_BRANCH,
            ),
            metadata={
                **_semantic_metadata(importable=True, import_order=70),
                "trajectory_field": "journal",
            },
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCES,
            name=PropstoreFamily.SOURCES.value,
            contract_version=SOURCE_FAMILY_CONTRACT_VERSION,
            artifact_family=CANONICAL_SOURCE_FAMILY,
            identity_field="id",
        ),
        FamilyDefinition(
            key=PropstoreFamily.MICROPUBS,
            name=PropstoreFamily.MICROPUBS.value,
            contract_version=MICROPUBLICATION_FAMILY_CONTRACT_VERSION,
            artifact_family=MICROPUBLICATION_FAMILY,
            foreign_keys=_charter_foreign_keys(MICROPUBLICATION_CHARTER),
            identity_field="artifact_id",
        ),
        _family_definition(
            key=PropstoreFamily.JUSTIFICATIONS,
            name=PropstoreFamily.JUSTIFICATIONS.value,
            contract_version=JUSTIFICATION_FAMILY_CONTRACT_VERSION,
            artifact_name="justification",
            artifact_contract_version=JUSTIFICATION_ARTIFACT_FAMILY_CONTRACT_VERSION,
            document_type=JustificationDocument,
            placement=FlatYamlPlacement(
                "justifications",
                JustificationRef,
                ref_field="artifact_id",
                codec="colon_to_double_underscore",
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
            foreign_keys=_charter_foreign_keys(JUSTIFICATION_CHARTER),
            identity_field="artifact_code",
            reference_keys=_charter_reference_keys(JUSTIFICATION_CHARTER),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_DOCUMENTS,
            name=PropstoreFamily.SOURCE_DOCUMENTS.value,
            contract_version=SOURCE_DOCUMENT_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_document",
            document_type=SourceDocument,
            placement=FixedFilePlacement("source.yaml", branch=SOURCE_BRANCH),
            encode_document=encode_source_document,
            render_document=render_source_document,
            document_payload=source_document_payload,
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_NOTES,
            name=PropstoreFamily.SOURCE_NOTES.value,
            contract_version=SOURCE_SIDE_FILE_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_notes",
            document_type=str,
            placement=FixedFilePlacement("notes.md", branch=SOURCE_BRANCH),
            coerce_payload=coerce_text_document,
            decode_bytes=decode_text_document,
            encode_document=encode_text_document,
            render_document=identity_text_document,
            document_payload=identity_text_document,
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_METADATA,
            name=PropstoreFamily.SOURCE_METADATA.value,
            contract_version=SOURCE_SIDE_FILE_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_metadata",
            document_type=dict,
            placement=FixedFilePlacement("metadata.json", branch=SOURCE_BRANCH),
            coerce_payload=coerce_json_mapping,
            decode_bytes=decode_json_mapping,
            encode_document=encode_json_mapping,
            render_document=render_json_mapping,
            document_payload=identity_json_mapping,
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_CONCEPTS,
            name=PropstoreFamily.SOURCE_CONCEPTS.value,
            contract_version=SOURCE_BATCH_FAMILY_CONTRACT_VERSION,
            artifact_family=batch_artifact_family(
                name="source_concepts",
                contract_version=SOURCE_BATCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
                placement=FixedFilePlacement("concepts.yaml", branch=SOURCE_BRANCH),
                batch_spec=SOURCE_CONCEPT_BATCH_SPEC,
            ),
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_CLAIMS,
            name=PropstoreFamily.SOURCE_CLAIMS.value,
            contract_version=SOURCE_BATCH_FAMILY_CONTRACT_VERSION,
            artifact_family=batch_artifact_family(
                name="source_claims",
                contract_version=SOURCE_BATCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
                placement=FixedFilePlacement("claims.yaml", branch=SOURCE_BRANCH),
                batch_spec=SOURCE_CLAIM_BATCH_SPEC,
            ),
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_MICROPUBS,
            name=PropstoreFamily.SOURCE_MICROPUBS.value,
            contract_version=SOURCE_MICROPUBLICATION_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_family=batch_artifact_family(
                name="source_micropubs",
                contract_version=SOURCE_MICROPUBLICATION_ARTIFACT_FAMILY_CONTRACT_VERSION,
                placement=FixedFilePlacement("micropubs.yaml", branch=SOURCE_BRANCH),
                batch_spec=SOURCE_MICROPUBLICATION_BATCH_SPEC,
            ),
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_JUSTIFICATIONS,
            name=PropstoreFamily.SOURCE_JUSTIFICATIONS.value,
            contract_version=SOURCE_BATCH_FAMILY_CONTRACT_VERSION,
            artifact_family=batch_artifact_family(
                name="source_justifications",
                contract_version=SOURCE_BATCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
                placement=FixedFilePlacement("justifications.yaml", branch=SOURCE_BRANCH),
                batch_spec=SOURCE_JUSTIFICATION_BATCH_SPEC,
            ),
        ),
        FamilyDefinition(
            key=PropstoreFamily.SOURCE_STANCES,
            name=PropstoreFamily.SOURCE_STANCES.value,
            contract_version=SOURCE_BATCH_FAMILY_CONTRACT_VERSION,
            artifact_family=batch_artifact_family(
                name="source_stances",
                contract_version=SOURCE_BATCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
                placement=FixedFilePlacement("stances.yaml", branch=SOURCE_BRANCH),
                batch_spec=SOURCE_STANCE_BATCH_SPEC,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_FINALIZE_REPORTS,
            name=PropstoreFamily.SOURCE_FINALIZE_REPORTS.value,
            contract_version=SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_finalize_report",
            document_type=SourceFinalizeReportDocument,
            placement=TemplateFilePlacement(
                "merge/finalize/{stem}.yaml",
                ref_field="name",
                codec="safe_slug",
                branch=SOURCE_BRANCH,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.PROPOSAL_STANCES,
            name=PropstoreFamily.PROPOSAL_STANCES.value,
            contract_version=STANCE_FAMILY_CONTRACT_VERSION,
            artifact_name="proposal_stance",
            document_type=StanceDocument,
            placement=FlatYamlPlacement(
                "stances",
                StanceRef,
                ref_field="artifact_id",
                codec="colon_to_double_underscore",
                branch=PROPOSAL_STANCE_BRANCH,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.PROPOSAL_PREDICATES,
            name=PropstoreFamily.PROPOSAL_PREDICATES.value,
            contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
            artifact_name="proposal_predicates",
            artifact_contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
            document_type=PredicateProposalArtifact,
            placement=SubdirFixedFilePlacement(
                namespace="predicates",
                filename="declarations.yaml",
                ref_factory=PredicateProposalRef,
                ref_field="source_paper",
                branch=PROPOSAL_PREDICATE_BRANCH,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.PROPOSAL_RULES,
            name=PropstoreFamily.PROPOSAL_RULES.value,
            contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
            artifact_name="proposal_rules",
            artifact_contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
            document_type=AuthoredRuleProposalArtifact,
            placement=NestedFlatYamlPlacement(
                namespace="rules",
                ref_factory=RuleProposalRef,
                dir_ref_field="source_paper",
                stem_ref_field="rule_id",
                branch=PROPOSAL_RULE_BRANCH,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.CONCEPT_ALIGNMENTS,
            name=PropstoreFamily.CONCEPT_ALIGNMENTS.value,
            contract_version=SOURCE_ALIGNMENT_FAMILY_CONTRACT_VERSION,
            artifact_name="concept_alignment",
            artifact_contract_version=SOURCE_ALIGNMENT_FAMILY_CONTRACT_VERSION,
            document_type=ConceptAlignmentArtifactDocument,
            placement=FlatYamlPlacement(
                "merge/concepts",
                ConceptAlignmentRef,
                ref_field="slug",
                branch=PROPOSAL_CONCEPT_BRANCH,
            ),
        ),
        _family_definition(
            key=PropstoreFamily.MERGE_MANIFESTS,
            name=PropstoreFamily.MERGE_MANIFESTS.value,
            contract_version=MERGE_MANIFEST_FAMILY_CONTRACT_VERSION,
            artifact_name="merge_manifest",
            document_type=MergeManifestDocument,
            placement=SingletonFilePlacement(
                "merge/manifest.yaml",
                ref_factory=MergeManifestRef,
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
        ),
        FamilyDefinition(
            key=PropstoreFamily.SCHEMA,
            name=PropstoreFamily.SCHEMA.value,
            contract_version=SCHEMA_FAMILY_CONTRACT_VERSION,
            artifact_family=ArtifactFamily["Repository", "SchemaRef", ContractManifest](
                "schema",
                SCHEMA_FAMILY_CONTRACT_VERSION,
                ContractManifest,
                BlobRefPlacement(PROPSTORE_SCHEMA_REF, ref_factory=SchemaRef),
                encode_document=encode_schema_manifest,
                decode_bytes=decode_schema_manifest,
            ),
        ),
    ),
)


def _semantic_import_order(family: FamilyDefinition[Any, Any, Any, Any]) -> int:
    value = family.metadata_value("import_order", 100)
    return value if isinstance(value, int) else 100


def _semantic_init_directory(family: FamilyDefinition[Any, Any, Any, Any]) -> bool:
    return family.metadata_value("init_directory") is not False


def _semantic_importable(family: FamilyDefinition[Any, Any, Any, Any]) -> bool:
    return family.metadata_value("importable") is True


def semantic_families() -> tuple[FamilyDefinition[Any, Any, Any, Any], ...]:
    return PROPSTORE_FAMILY_REGISTRY.select_by_metadata("semantic", True)


def semantic_family_by_name(name: str) -> FamilyDefinition[Any, Any, Any, Any]:
    family = PROPSTORE_FAMILY_REGISTRY.by_name(name)
    if family.metadata_value("semantic") is not True:
        raise KeyError(f"not a semantic family: {name}")
    return family


def semantic_init_roots() -> tuple[str, ...]:
    return tuple(family.storage_root() for family in semantic_families() if _semantic_init_directory(family))


def semantic_import_roots() -> tuple[str, ...]:
    return tuple(family.storage_root() for family in semantic_import_families())


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


def semantic_address_path(name: str, repo: Repository, ref: object) -> SemanticFamilyAddress:
    family = semantic_family_by_name(name).artifact_family
    return SemanticFamilyAddress(family.address_for(repo, ref).require_path())


def world_charters() -> tuple[FamilyCharter, ...]:
    calibration = import_module("propstore.families.calibration.declaration")
    claims = import_module("propstore.families.claims.declaration")
    concepts = import_module("propstore.families.concepts.declaration")
    contexts = import_module("propstore.families.contexts.declaration")
    diagnostics = import_module("propstore.families.diagnostics.declaration")
    embeddings = import_module("propstore.families.embeddings.declaration")
    forms = import_module("propstore.families.forms.models")
    meta = import_module("propstore.families.meta.declaration")
    micropublications = import_module("propstore.families.micropublications.declaration")
    merge = import_module("propstore.families.merge.declaration")
    predicates = import_module("propstore.families.predicates.declaration")
    relations = import_module("propstore.families.relations.declaration")
    rules = import_module("propstore.families.rules.declaration")
    sameas = import_module("propstore.families.sameas.declaration")
    source_alignment = import_module("propstore.families.source_alignment.declaration")
    sources = import_module("propstore.families.sources.declaration")
    stances = import_module("propstore.families.stances.declaration")
    worldlines = import_module("propstore.families.worldlines.declaration")

    relation_charters = relations.RELATIONS_CHARTERS
    return (
        meta.WORLD_META_CHARTER,
        sources.SOURCE_CHARTER,
        AUTHORED_CONCEPT_CHARTER,
        *concepts.CONCEPT_CHARTERS,
        relation_charters[0],
        *forms.FORMS_CHARTERS,
        *contexts.CONTEXT_CHARTERS,
        AUTHORED_CLAIM_CHARTER,
        claims.CLAIM_CORE_CHARTER,
        claims.CLAIM_CONCEPT_LINK_CHARTER,
        *claims.CLAIM_PAYLOAD_CHARTERS,
        claims.CLAIM_SOURCE_ASSERTION_CHARTER,
        relation_charters[1],
        *predicates.PREDICATE_CHARTERS,
        *rules.AUTHORED_RULE_CHARTERS,
        *rules.RULES_CHARTERS,
        claims.JUSTIFICATION_CHARTER,
        sameas.SAMEAS_CHARTER,
        stances.STANCE_CHARTER,
        source_alignment.CONCEPT_ALIGNMENT_ARTIFACT_CHARTER,
        *worldlines.WORLDLINE_CHARTERS,
        merge.MERGE_MANIFEST_CHARTER,
        *micropublications.MICROPUBLICATION_CHARTERS,
        calibration.CALIBRATION_CHARTER,
        *embeddings.EMBEDDING_CHARTERS,
        diagnostics.DIAGNOSTICS_CHARTER,
    )


@lru_cache(maxsize=1)
def world_catalog() -> SchemaCatalog:
    meta = import_module("propstore.families.meta.declaration")
    return charter_catalog(
        *world_charters(),
        metadata={
            "projection": "propstore.world",
            "schema_version": meta.PROPSTORE_WORLD_SCHEMA_VERSION,
        },
    )


@lru_cache(maxsize=1)
def world_schema() -> SqlAlchemySchema:
    return build_sqlalchemy_schema(world_catalog())
