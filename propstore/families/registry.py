from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from quire.artifacts import (
    ArtifactFamily,
    BranchPlacement,
    FixedFilePlacement,
    FlatYamlPlacement,
    HashScatteredYamlPlacement,
    NestedFlatYamlPlacement,
    SingletonFilePlacement,
    SubdirFixedFilePlacement,
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
from quire.references import ForeignKeySpec, ReferenceKey
from quire.refs import single_field_ref_type, singleton_ref_type
from quire.versions import VersionId

from propstore.families.addresses import SemanticFamilyAddress
from propstore.families.claims.documents import ClaimDocument
from propstore.families.concepts.documents import ConceptDocument
from propstore.families.contexts.documents import ContextDocument
from propstore.families.forms.documents import FormDocument
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.documents.merge import MergeManifestDocument
from propstore.families.documents.micropubs import MicropublicationDocument, MicropublicationsFileDocument
from propstore.families.documents.predicates import PredicateDocument, PredicateProposalDocument
from propstore.families.documents.rules import RuleDocument, RuleProposalDocument, RuleSuperiorityDocument
from propstore.families.documents.source_alignment import ConceptAlignmentArtifactDocument
from propstore.families.documents.sources import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
)
from propstore.families.documents.stances import StanceDocument
from propstore.families.documents.worldlines import WorldlineDefinitionDocument
from propstore.families.sameas.documents import SameAsAssertionDocument
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
from propstore.families.concepts.stages import (
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


ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.27")
CONCEPT_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.04.28")
IDENTITY_POLICY_FAMILY_CONTRACT_VERSION = VersionId("2026.04.29")
WORLDLINE_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.04")
SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.02")
SOURCE_SIDE_FILE_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.02")
PROPOSAL_DECLARATION_ARTIFACT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.11")
INTENTIONAL_SET_FAMILY_CONTRACT_VERSION = VersionId("2026.05.11")
PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION = VersionId("2026.05.13")
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.05.12")
REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION = VersionId("2026.05.12")
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
    name="claim",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=ClaimDocument,
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

CANONICAL_SOURCE_FAMILY = ArtifactFamily["Repository", CanonicalSourceRef, SourceDocument](
    name="canonical_source",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=SourceDocument,
    placement=CANONICAL_SOURCE_PLACEMENT,
)


MICROPUBLICATION_FAMILY = ArtifactFamily["Repository", MicropublicationRef, MicropublicationDocument](
    name="micropublication",
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    doc_type=MicropublicationDocument,
    placement=MICROPUBLICATION_PLACEMENT,
)

CLAIM_FOREIGN_KEYS = (
    ForeignKeySpec(
        name="claim_output_concept",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CLAIMS.value,
        source_field="output_concept",
        target_family=PropstoreFamily.CONCEPTS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="claim_concepts",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CLAIMS.value,
        source_field="concepts[]",
        target_family=PropstoreFamily.CONCEPTS.value,
        many=True,
        required=False,
    ),
    ForeignKeySpec(
        name="claim_variable_concept",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CLAIMS.value,
        source_field="variables[].concept",
        target_family=PropstoreFamily.CONCEPTS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="claim_parameter_concept",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CLAIMS.value,
        source_field="parameters[].concept",
        target_family=PropstoreFamily.CONCEPTS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="claim_measurement_target_concept",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CLAIMS.value,
        source_field="target_concept",
        target_family=PropstoreFamily.CONCEPTS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="claim_stance_target",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CLAIMS.value,
        source_field="stances[].target",
        target_family=PropstoreFamily.CLAIMS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="claim_context",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CLAIMS.value,
        source_field="context.id",
        target_family=PropstoreFamily.CONTEXTS.value,
    ),
)


CONCEPT_FOREIGN_KEYS = (
    ForeignKeySpec(
        name="concept_parameterization_input",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CONCEPTS.value,
        source_field="parameterization_relationships[].inputs[]",
        target_family=PropstoreFamily.CONCEPTS.value,
        many=True,
        required=False,
    ),
    ForeignKeySpec(
        name="concept_parameterization_canonical_claim",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CONCEPTS.value,
        source_field="parameterization_relationships[].canonical_claim",
        target_family=PropstoreFamily.CLAIMS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="concept_replaced_by",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CONCEPTS.value,
        source_field="replaced_by",
        target_family=PropstoreFamily.CONCEPTS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="concept_relationship_target",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CONCEPTS.value,
        source_field="relationships[].target",
        target_family=PropstoreFamily.CONCEPTS.value,
        many=True,
        required=False,
    ),
    ForeignKeySpec(
        name="concept_form",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.CONCEPTS.value,
        source_field="lexical_entry.physical_dimension_form",
        target_family=PropstoreFamily.FORMS.value,
    ),
)


STANCE_FOREIGN_KEYS = (
    ForeignKeySpec(
        name="stance_source_claim",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.STANCES.value,
        source_field="source_claim",
        target_family=PropstoreFamily.CLAIMS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="stance_target_claim",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.STANCES.value,
        source_field="target",
        target_family=PropstoreFamily.CLAIMS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="stance_target_justification",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.STANCES.value,
        source_field="target_justification_id",
        target_family=PropstoreFamily.JUSTIFICATIONS.value,
        required=False,
    ),
)


JUSTIFICATION_FOREIGN_KEYS = (
    ForeignKeySpec(
        name="justification_conclusion",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.JUSTIFICATIONS.value,
        source_field="conclusion",
        target_family=PropstoreFamily.CLAIMS.value,
        required=False,
    ),
    ForeignKeySpec(
        name="justification_premises",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.JUSTIFICATIONS.value,
        source_field="premises[]",
        target_family=PropstoreFamily.CLAIMS.value,
        many=True,
        required=False,
    ),
)


MICROPUBLICATION_FOREIGN_KEYS = (
    ForeignKeySpec(
        name="micropub_context",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.MICROPUBS.value,
        source_field="context.id",
        target_family=PropstoreFamily.CONTEXTS.value,
    ),
    ForeignKeySpec(
        name="micropub_claims",
        contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
        source_family=PropstoreFamily.MICROPUBS.value,
        source_field="claims[]",
        target_family=PropstoreFamily.CLAIMS.value,
        many=True,
    ),
)


CLAIM_REFERENCE_KEYS = (
    ReferenceKey.field("artifact_id"),
    ReferenceKey.field("logical_ids[].formatted"),
    ReferenceKey.field("logical_ids[].value"),
)

CONCEPT_REFERENCE_KEYS = (
    ReferenceKey.field("artifact_id"),
    ReferenceKey.field("logical_ids[].value"),
    ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
    ReferenceKey.field("aliases[].name"),
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
    doc_type: type[Any],
    placement: Any,
    artifact_contract_version: VersionId | None = None,
    accessor: str | None = None,
    coerce_payload: Callable[..., Any] | None = None,
    decode_bytes: Callable[..., Any] | None = None,
    encode_document: Callable[..., Any] | None = None,
    render_document: Callable[..., Any] | None = None,
    document_payload: Callable[..., Any] | None = None,
    normalize_for_write: Callable[..., Any] | None = None,
    validate_for_write: Callable[..., Any] | None = None,
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
            name=artifact_name,
            contract_version=artifact_contract_version or contract_version,
            doc_type=doc_type,
            placement=placement,
            coerce_payload=coerce_payload,
            decode_bytes=decode_bytes,
            encode_document=encode_document,
            render_document=render_document,
            document_payload=document_payload,
            normalize_for_write=normalize_for_write,
            validate_for_write=validate_for_write,
            scan_type=scan_type,
        ),
        accessor=accessor,
        foreign_keys=foreign_keys,
        identity_policy=identity_policy,
        identity_field=identity_field,
        reference_keys=reference_keys,
        metadata=metadata,
    )


PROPSTORE_FAMILY_REGISTRY = FamilyRegistry(
    name="propstore",
    contract_version=PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION,
    families=(
        FamilyDefinition(
            key=PropstoreFamily.CLAIMS,
            name=PropstoreFamily.CLAIMS.value,
            contract_version=REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION,
            artifact_family=CLAIM_FAMILY,
            foreign_keys=CLAIM_FOREIGN_KEYS,
            identity_policy=CLAIM_IDENTITY_POLICY,
            identity_field="artifact_id",
            reference_keys=CLAIM_REFERENCE_KEYS,
            metadata=_semantic_metadata(importable=True, import_order=20),
        ),
        FamilyDefinition(
            key=PropstoreFamily.CONCEPTS,
            name=PropstoreFamily.CONCEPTS.value,
            contract_version=REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION,
            artifact_family=CONCEPT_FILE_FAMILY,
            foreign_keys=CONCEPT_FOREIGN_KEYS,
            identity_policy=CONCEPT_IDENTITY_POLICY,
            identity_field="artifact_id",
            reference_keys=CONCEPT_REFERENCE_KEYS,
            metadata=_semantic_metadata(importable=True, import_order=10),
        ),
        _family_definition(
            key=PropstoreFamily.CONTEXTS,
            name=PropstoreFamily.CONTEXTS.value,
            contract_version=REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION,
            artifact_name="context",
            artifact_contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            doc_type=ContextDocument,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.CONTEXTS.value,
                ref_factory=ContextRef,
                ref_field="name",
                branch=CURRENT_ARTIFACT_BRANCH,
            ),
            identity_field="id",
            reference_keys=(ReferenceKey.field("name"),),
            metadata=_semantic_metadata(importable=True, import_order=30),
        ),
        _family_definition(
            key=PropstoreFamily.FORMS,
            name=PropstoreFamily.FORMS.value,
            contract_version=REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION,
            artifact_name="form",
            artifact_contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            doc_type=FormDocument,
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
            contract_version=INTENTIONAL_SET_FAMILY_CONTRACT_VERSION,
            artifact_name="predicate",
            artifact_contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            doc_type=PredicateDocument,
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
            contract_version=INTENTIONAL_SET_FAMILY_CONTRACT_VERSION,
            artifact_name="rule",
            artifact_contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            doc_type=RuleDocument,
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
            contract_version=INTENTIONAL_SET_FAMILY_CONTRACT_VERSION,
            artifact_name="rule_superiority",
            artifact_contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            doc_type=RuleSuperiorityDocument,
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
            contract_version=REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION,
            artifact_name="stance",
            artifact_contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            doc_type=StanceDocument,
            placement=FlatYamlPlacement(
                namespace=PropstoreFamily.STANCES.value,
                ref_factory=StanceRef,
                ref_field="artifact_id",
                codec="colon_to_double_underscore",
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
            foreign_keys=STANCE_FOREIGN_KEYS,
            identity_field="artifact_code",
            metadata=_semantic_metadata(importable=True, import_order=60),
        ),
        _family_definition(
            key=PropstoreFamily.SAMEAS,
            name=PropstoreFamily.SAMEAS.value,
            contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="same_as_assertion",
            doc_type=SameAsAssertionDocument,
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
            contract_version=WORLDLINE_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="worldline",
            doc_type=WorldlineDefinitionDocument,
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
            contract_version=REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION,
            artifact_family=CANONICAL_SOURCE_FAMILY,
            identity_field="id",
        ),
        FamilyDefinition(
            key=PropstoreFamily.MICROPUBS,
            name=PropstoreFamily.MICROPUBS.value,
            contract_version=REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION,
            artifact_family=MICROPUBLICATION_FAMILY,
            foreign_keys=MICROPUBLICATION_FOREIGN_KEYS,
            identity_field="artifact_id",
        ),
        _family_definition(
            key=PropstoreFamily.JUSTIFICATIONS,
            name=PropstoreFamily.JUSTIFICATIONS.value,
            contract_version=REFERENCE_VALIDATED_FAMILY_CONTRACT_VERSION,
            artifact_name="justification",
            artifact_contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            doc_type=JustificationDocument,
            placement=FlatYamlPlacement(
                "justifications",
                JustificationRef,
                ref_field="artifact_id",
                codec="colon_to_double_underscore",
                branch=PRIMARY_ARTIFACT_BRANCH,
            ),
            foreign_keys=JUSTIFICATION_FOREIGN_KEYS,
            identity_field="artifact_code",
            reference_keys=(ReferenceKey.field("id"),),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_DOCUMENTS,
            name=PropstoreFamily.SOURCE_DOCUMENTS.value,
            contract_version=SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_document",
            doc_type=SourceDocument,
            placement=FixedFilePlacement("source.yaml", branch=SOURCE_BRANCH),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_NOTES,
            name=PropstoreFamily.SOURCE_NOTES.value,
            contract_version=SOURCE_SIDE_FILE_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_notes",
            doc_type=str,
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
            doc_type=dict,
            placement=FixedFilePlacement("metadata.json", branch=SOURCE_BRANCH),
            coerce_payload=coerce_json_mapping,
            decode_bytes=decode_json_mapping,
            encode_document=encode_json_mapping,
            render_document=render_json_mapping,
            document_payload=identity_json_mapping,
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_CONCEPTS,
            name=PropstoreFamily.SOURCE_CONCEPTS.value,
            contract_version=SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_concepts",
            doc_type=SourceConceptsDocument,
            placement=FixedFilePlacement("concepts.yaml", branch=SOURCE_BRANCH),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_CLAIMS,
            name=PropstoreFamily.SOURCE_CLAIMS.value,
            contract_version=SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_claims",
            doc_type=SourceClaimsDocument,
            placement=FixedFilePlacement("claims.yaml", branch=SOURCE_BRANCH),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_MICROPUBS,
            name=PropstoreFamily.SOURCE_MICROPUBS.value,
            contract_version=SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_micropubs",
            doc_type=MicropublicationsFileDocument,
            placement=FixedFilePlacement("micropubs.yaml", branch=SOURCE_BRANCH),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_JUSTIFICATIONS,
            name=PropstoreFamily.SOURCE_JUSTIFICATIONS.value,
            contract_version=SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_justifications",
            doc_type=SourceJustificationsDocument,
            placement=FixedFilePlacement("justifications.yaml", branch=SOURCE_BRANCH),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_STANCES,
            name=PropstoreFamily.SOURCE_STANCES.value,
            contract_version=SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_stances",
            doc_type=SourceStancesDocument,
            placement=FixedFilePlacement("stances.yaml", branch=SOURCE_BRANCH),
        ),
        _family_definition(
            key=PropstoreFamily.SOURCE_FINALIZE_REPORTS,
            name=PropstoreFamily.SOURCE_FINALIZE_REPORTS.value,
            contract_version=SOURCE_BRANCH_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="source_finalize_report",
            doc_type=SourceFinalizeReportDocument,
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
            contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="proposal_stance",
            doc_type=StanceDocument,
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
            contract_version=PROPOSAL_DECLARATION_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="proposal_predicates",
            doc_type=PredicateProposalDocument,
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
            contract_version=PROPOSAL_DECLARATION_ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="proposal_rules",
            doc_type=RuleProposalDocument,
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
            contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="concept_alignment",
            doc_type=ConceptAlignmentArtifactDocument,
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
            contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
            artifact_name="merge_manifest",
            doc_type=MergeManifestDocument,
            placement=SingletonFilePlacement(
                "merge/manifest.yaml",
                ref_factory=MergeManifestRef,
                branch=PRIMARY_ARTIFACT_BRANCH,
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
