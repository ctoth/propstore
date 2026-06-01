from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_type_hints

import msgspec
import quire.contracts as quire_contracts
from quire.artifacts import ArtifactFamily
from quire.contracts import ContractEntry, ContractManifest
from quire.references import ForeignKeySpec
from quire.versions import VersionId

if TYPE_CHECKING:
    from propstore.families.claims.declaration import ClaimTypeContract

PROPSTORE_REGISTRY_CONTRACT_VERSION = VersionId("2026.05.02")
SEMANTIC_PASS_CONTRACT_VERSION = VersionId("2026.04.20")


def encode_schema_manifest(manifest: ContractManifest) -> bytes:
    """Encode the contract manifest as the schema family's blob bytes."""
    return manifest.to_yaml()


def decode_schema_manifest(raw: bytes, source: str) -> ContractManifest:
    """Decode the schema family's blob bytes back into a contract manifest."""
    return ContractManifest.from_yaml(raw)


def iter_artifact_families() -> tuple[ArtifactFamily[Any, Any, Any], ...]:
    from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY

    discovered = {
        family.artifact_family.name: family.artifact_family
        for family in PROPSTORE_FAMILY_REGISTRY.families
    }
    return tuple(sorted(discovered.values(), key=lambda family: family.name))


def iter_semantic_foreign_keys() -> tuple[ForeignKeySpec, ...]:
    from propstore.families.registry import semantic_foreign_keys

    return semantic_foreign_keys()


def iter_claim_type_contracts() -> tuple["ClaimTypeContract", ...]:
    from propstore.families.claims.declaration import (
        iter_claim_type_contracts as iter_contracts,
    )

    return iter_contracts()


def iter_semantic_pass_classes() -> tuple[type[Any], ...]:
    from propstore.families.claims.passes import register_claim_pipeline
    from propstore.families.concepts.passes import register_concept_pipeline
    from propstore.families.contexts.passes import register_context_pipeline
    from propstore.families.forms.passes import register_form_pipeline
    from propstore.semantic_passes.registry import PipelineRegistry

    registry = PipelineRegistry()
    register_claim_pipeline(registry)
    register_concept_pipeline(registry)
    register_context_pipeline(registry)
    register_form_pipeline(registry)
    return registry.registered_passes()


def iter_semantic_stage_contracts() -> tuple[tuple[str, str, type[Any], tuple[str, ...]], ...]:
    from propstore.families.claims.stages import (
        ClaimAuthoredFiles,
        ClaimCheckedBundle,
        ClaimStage,
    )
    from propstore.families.concepts.stages import (
        ConceptAuthoredSet,
        ConceptBoundRegistry,
        ConceptCheckedRegistry,
        ConceptNormalizedSet,
        ConceptStage,
    )
    from propstore.families.contexts.stages import (
        ContextAuthoredSet,
        ContextBoundGraph,
        ContextCheckedGraph,
        ContextNormalizedSet,
        ContextStage,
    )
    from propstore.families.forms.stages import (
        FormAuthoredSet,
        FormCheckedRegistry,
        FormNormalizedRegistry,
        FormStage,
    )

    return (
        (ClaimStage.AUTHORED.value, "claims", ClaimAuthoredFiles, ()),
        (ClaimStage.CHECKED.value, "claims", ClaimCheckedBundle, ()),
        (ConceptStage.AUTHORED.value, "concepts", ConceptAuthoredSet, ()),
        (ConceptStage.NORMALIZED.value, "concepts", ConceptNormalizedSet, ()),
        (ConceptStage.BOUND.value, "concepts", ConceptBoundRegistry, ()),
        (ConceptStage.CHECKED.value, "concepts", ConceptCheckedRegistry, ()),
        (ContextStage.AUTHORED.value, "contexts", ContextAuthoredSet, ()),
        (ContextStage.NORMALIZED.value, "contexts", ContextNormalizedSet, ()),
        (ContextStage.BOUND.value, "contexts", ContextBoundGraph, ()),
        (ContextStage.CHECKED.value, "contexts", ContextCheckedGraph, ()),
        (FormStage.AUTHORED.value, "forms", FormAuthoredSet, ()),
        (FormStage.NORMALIZED.value, "forms", FormNormalizedRegistry, ()),
        (FormStage.CHECKED.value, "forms", FormCheckedRegistry, ()),
    )


def _iter_charter_document_schemas() -> tuple[tuple[type[msgspec.Struct], VersionId], ...]:
    from propstore.families.registry import world_charters

    document_schemas: dict[str, tuple[type[msgspec.Struct], VersionId]] = {}
    for charter in world_charters():
        document_type = charter.generated_document()
        key = f"{document_type.__module__}.{document_type.__name__}"
        version = (
            VersionId(str(charter.document_contract_version), allow_placeholder=False)
            if charter.document_contract_version is not None
            else charter.family.contract_version
        )
        document_schemas[key] = (document_type, version)
    return tuple(
        item
        for _, item in sorted(document_schemas.items(), key=lambda entry: entry[0])
    )


def build_propstore_contract_manifest() -> ContractManifest:
    contracts: list[ContractEntry] = []
    contracts.extend(
        _document_contract(document_type, contract_version=contract_version)
        for document_type, contract_version in _iter_charter_document_schemas()
    )
    from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY

    contracts.extend(PROPSTORE_FAMILY_REGISTRY.contract_entries())
    contracts.extend(_family_contract(family) for family in iter_artifact_families())
    contracts.extend(_foreign_key_contract(spec) for spec in iter_semantic_foreign_keys())
    contracts.extend(_claim_type_contract(contract) for contract in iter_claim_type_contracts())
    contracts.extend(_semantic_stage_contract(*contract) for contract in iter_semantic_stage_contracts())
    contracts.extend(_semantic_pass_contract(pass_class) for pass_class in iter_semantic_pass_classes())
    return ContractManifest(
        format_version=1,
        package_name="propstore",
        package_version="0.1.0",
        registry_name=PROPSTORE_FAMILY_REGISTRY.name,
        registry_contract_version=PROPSTORE_FAMILY_REGISTRY.contract_version,
        contracts=tuple(contracts),
        compatible_changes=(
            quire_contracts.CompatibilityMarker(
                contract="family-registry:propstore",
                contract_version=PROPSTORE_FAMILY_REGISTRY.contract_version,
                reason=(
                    "Context family document ownership moved to generated "
                    "declaration types with context family and artifact "
                    "contracts version-bumped in the same registry version."
                ),
            ),
            quire_contracts.CompatibilityMarker(
                contract="document_schema:JustificationDocument",
                contract_version=VersionId("2026.05.25"),
                reason=(
                    "Claim family cutover moved justification nested document "
                    "types into the claim declaration module without changing "
                    "the authored YAML fields."
                ),
            ),
            quire_contracts.CompatibilityMarker(
                contract="document_schema:MicropublicationDocument",
                contract_version=VersionId("2026.05.25"),
                reason=(
                    "Claim family cutover moved claim provenance document "
                    "ownership into the claim declaration module without "
                    "changing the micropublication YAML fields."
                ),
            ),
            quire_contracts.CompatibilityMarker(
                contract="family:claims",
                contract_version=VersionId("2026.05.25"),
                reason=(
                    "Claim foreign-key and source batch declarations moved "
                    "from registry tables onto claim family charter metadata "
                    "without changing authored claim YAML fields."
                ),
            ),
            quire_contracts.CompatibilityMarker(
                contract="family:concepts",
                contract_version=VersionId("2026.05.25"),
                reason=(
                    "Concept foreign-key and source batch declarations moved "
                    "from registry tables onto concept family charter metadata "
                    "without changing authored concept YAML fields."
                ),
            ),
            quire_contracts.CompatibilityMarker(
                contract="family:contexts",
                contract_version=VersionId("2026.05.25"),
                reason=(
                    "Context reference-key declaration moved from registry "
                    "construction onto context family metadata without "
                    "changing authored context YAML fields."
                ),
            ),
            quire_contracts.CompatibilityMarker(
                contract="artifact_family:proposal_predicates",
                contract_version=VersionId("2026.05.25"),
                reason=(
                    "Predicate proposal container moved to a generated "
                    "charter artifact type without changing proposal YAML "
                    "fields or placement."
                ),
            ),
            quire_contracts.CompatibilityMarker(
                contract="family:proposal_predicates",
                contract_version=VersionId("2026.05.25"),
                reason=(
                    "Predicate proposal family now uses the generated "
                    "charter artifact type for the same proposal YAML "
                    "fields and placement."
                ),
            ),
            *_required_relaxation_markers(),
        ),
    )


# Correcting the manifest `required` computation (it compared a field name
# against a tuple of default VALUES, so every field was recorded required)
# relaxes `required: true` -> `required: false` on every field that actually
# carries a default. A relaxation is backward compatible: any reader that
# previously treated a field as required still accepts documents that now mark
# it optional. The bytewise contract checker cannot tell a relaxation from a
# breaking change, so each affected `document_schema` body change needs a
# compatibility marker at its current contract version.
_REQUIRED_RELAXATION_MARKERS: tuple[tuple[str, str], ...] = (
    ("document_schema:AuthoredRuleProposalArtifact", "2026.05.25"),
    ("document_schema:ClaimDocument", "2026.05.25"),
    ("document_schema:ContextDocument", "2026.05.25"),
    ("document_schema:Context_lifting_ruleDocument", "2026.05.25"),
    ("document_schema:FormDocument", "2026.05.20"),
    ("document_schema:JustificationDocument", "2026.05.20"),
    ("document_schema:MicropublicationDocument", "2026.05.20"),
    ("document_schema:PredicateDocument", "2026.05.25"),
    ("document_schema:PredicateProposalArtifact", "2026.05.25"),
    ("document_schema:Relation_edgeDocument", "2026.05.20"),
    ("document_schema:RuleDocument", "2026.05.25"),
    ("document_schema:RuleSuperiorityDocument", "2026.05.25"),
    ("document_schema:SameAsAssertionDocument", "2026.05.25"),
    ("document_schema:SourceDocument", "2026.05.25"),
    ("document_schema:WorldlineDefinitionDocument", "2026.05.25"),
    ("document_schema:WorldlineJournalDocument", "2026.05.25"),
    ("document_schema:WorldlineResultDocument", "2026.05.25"),
    ("document_schema:WorldlineRevisionStateDocument", "2026.05.25"),
    (
        "document_schema:propstore.families.stances.declaration.StanceDocument",
        "2026.05.25",
    ),
)


def _required_relaxation_markers() -> tuple[quire_contracts.CompatibilityMarker, ...]:
    return tuple(
        quire_contracts.CompatibilityMarker(
            contract=contract,
            contract_version=VersionId(version),
            reason=(
                "Corrected manifest `required` computation to real per-field "
                "optionality (msgspec FieldInfo.required); fields that carry a "
                "default flip required:true -> required:false. A relaxation, "
                "backward compatible with prior required readers."
            ),
        )
        for contract, version in _REQUIRED_RELAXATION_MARKERS
    )


def _document_contract(
    document_type: type[msgspec.Struct],
    *,
    contract_version: VersionId,
) -> ContractEntry:
    fields = []
    # Resolve string annotations (PEP 563) and strip `Annotated[...]` charter_field
    # metadata to the base type, so the serialized contract records the public type
    # (e.g. `builtins.str`), not the raw declarative annotation. include_extras=False
    # drops the Annotated wrapper; the old defstruct documents already had clean types.
    annotations = get_type_hints(document_type)
    # A field is required iff msgspec reports it has no default (neither a
    # `default` nor a `default_factory`). The old `name not in
    # __struct_defaults__` test compared a field NAME against a tuple of default
    # VALUES, so it was true for essentially every field and recorded every
    # field as required. `msgspec.structs.fields(...)` exposes the real
    # per-field `.required` optionality.
    required_by_name = {
        info.name: info.required for info in msgspec.structs.fields(document_type)
    }
    for name in getattr(document_type, "__struct_fields__", ()):
        fields.append({
            "name": name,
            "type": _render_type(annotations.get(name, object)),
            "required": required_by_name.get(name, True),
        })
    return ContractEntry(
        kind="document_schema",
        name=_document_contract_name(document_type),
        contract_version=contract_version,
        body={
            "module": document_type.__module__,
            "fields": tuple(fields),
        },
    )


def _document_contract_name(document_type: type[msgspec.Struct]) -> str:
    if (
        document_type.__module__ == "propstore.families.stances.declaration"
        and document_type.__name__ == "StanceDocument"
    ):
        return f"{document_type.__module__}.{document_type.__name__}"
    return document_type.__name__


def _family_contract(family: ArtifactFamily[Any, Any, Any]) -> ContractEntry:
    return ContractEntry(
        kind="artifact_family",
        name=family.name,
        contract_version=family.contract_version,
        body={
            **family.contract_body(),
            "coerce_payload": _callback_id(family.coerce_payload),
            "decode_bytes": _callback_id(family.decode_bytes),
            "encode_document": _callback_id(family.encode_document),
            "render_document": _callback_id(family.render_document),
            "document_payload": _callback_id(family.document_payload),
            "scan_type": (
                None
                if family.scan_type is None
                else f"{family.scan_type.__module__}.{family.scan_type.__qualname__}"
            ),
        },
    )


def _foreign_key_contract(spec: ForeignKeySpec) -> ContractEntry:
    return ContractEntry(
        kind="foreign_key",
        name=spec.name,
        contract_version=spec.contract_version,
        body=spec.contract_body(),
    )


def _claim_type_contract(contract: "ClaimTypeContract") -> ContractEntry:
    return ContractEntry(
        kind="claim_type_contract",
        name=contract.claim_type.value,
        contract_version=contract.contract_version,
        body=contract.contract_body(),
    )


def _semantic_stage_contract(
    name: str,
    family: str,
    stage_class: type[Any],
    invariants: tuple[str, ...],
) -> ContractEntry:
    return ContractEntry(
        kind="semantic_stage",
        name=name,
        contract_version=SEMANTIC_PASS_CONTRACT_VERSION,
        body={
            "family": family,
            "class": f"{stage_class.__module__}.{stage_class.__qualname__}",
            "invariants": invariants,
        },
    )


def _semantic_pass_contract(pass_class: type[Any]) -> ContractEntry:
    return ContractEntry(
        kind="semantic_pass",
        name=pass_class.name,
        contract_version=SEMANTIC_PASS_CONTRACT_VERSION,
        body={
            "family": pass_class.family.value,
            "input_stage": pass_class.input_stage.value,
            "output_stage": pass_class.output_stage.value,
            "class": f"{pass_class.__module__}.{pass_class.__qualname__}",
            "diagnostic_codes": (),
            "required_context": (),
        },
    )


def _callback_id(callback: object) -> str | None:
    if callback is None:
        return None
    module = getattr(callback, "__module__", None)
    qualname = getattr(callback, "__qualname__", None)
    if module and qualname:
        return f"{module}.{qualname}"
    return repr(callback)


def _render_type(value: object) -> str:
    module = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None)
    if module and qualname:
        return f"{module}.{qualname}"
    return str(value).replace("typing.", "")
