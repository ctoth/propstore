"""Canonical semantic family registry for propstore repository artifacts."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from quire.artifacts import ArtifactFamily
from quire.family_store import DocumentFamilyStore
from quire.references import ForeignKeySpec
from quire.versions import VersionId

from propstore.artifacts.codecs import decode_yaml_mapping
from propstore.artifacts.documents.claims import ClaimsFileDocument
from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.artifacts.documents.contexts import ContextDocument
from propstore.artifacts.documents.forms import FormDocument
from propstore.artifacts.documents.predicates import PredicatesFileDocument
from propstore.artifacts.documents.rules import RulesFileDocument
from propstore.artifacts.documents.stances import StanceFileDocument
from propstore.artifacts.documents.worldlines import WorldlineDefinitionDocument
from propstore.artifacts.families import (
    CLAIMS_FILE_FAMILY,
    CONCEPT_FILE_FAMILY,
    CONTEXT_FAMILY,
    FORM_FAMILY,
    PREDICATE_FILE_FAMILY,
    RULE_FILE_FAMILY,
    STANCE_FILE_FAMILY,
    WORLDLINE_FAMILY,
)
from propstore.artifacts.identity import (
    concept_reference_keys,
    normalize_canonical_claim_payload,
    normalize_canonical_concept_payload,
    normalize_claim_file_payload,
)
from propstore.artifacts.resolution import ImportedClaimHandleIndex

if TYPE_CHECKING:
    from propstore.repository import Repository


SEMANTIC_FAMILY_CONTRACT_VERSION = VersionId("2026.04.22")
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.04.22")


@dataclass(frozen=True)
class PlannedSemanticWrite:
    """Typed artifact write planned by a semantic-family import policy."""

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
        "SemanticFamilyRegistry",
    ],
    Mapping[str, PlannedSemanticWrite],
]


@dataclass(frozen=True)
class SemanticFamilyDefinition:
    name: str
    contract_version: VersionId
    artifact_family: ArtifactFamily[Any, Any, Any]
    document_type: type[object]
    root: str
    collection_field: str | None = None
    importable: bool = False
    import_order: int = 100
    init_directory: bool = True
    foreign_keys: tuple[ForeignKeySpec, ...] = ()
    normalize_import_batch: SemanticImportBatch | None = None

    def contract_body(self) -> dict[str, object]:
        return {
            "artifact_family": self.artifact_family.name,
            "collection_field": self.collection_field,
            "document_type": f"{self.document_type.__module__}.{self.document_type.__qualname__}",
            "foreign_keys": tuple(spec.name for spec in self.foreign_keys),
            "import_order": self.import_order,
            "importable": self.importable,
            "init_directory": self.init_directory,
            "root": self.root,
        }


@dataclass(frozen=True)
class SemanticFamilyRegistry:
    families: tuple[SemanticFamilyDefinition, ...]

    def __post_init__(self) -> None:
        names = [family.name for family in self.families]
        roots = [family.root for family in self.families]
        duplicate_names = sorted({name for name in names if names.count(name) > 1})
        duplicate_roots = sorted({root for root in roots if roots.count(root) > 1})
        if duplicate_names:
            raise ValueError(f"duplicate semantic family names: {', '.join(duplicate_names)}")
        if duplicate_roots:
            raise ValueError(f"duplicate semantic family roots: {', '.join(duplicate_roots)}")

    def names(self) -> tuple[str, ...]:
        return tuple(family.name for family in self.families)

    def by_name(self, name: str) -> SemanticFamilyDefinition:
        for family in self.families:
            if family.name == name:
                return family
        raise KeyError(f"unknown semantic family: {name}")

    def by_root(self, root: str) -> SemanticFamilyDefinition:
        for family in self.families:
            if family.root == root:
                return family
        raise KeyError(f"unknown semantic family root: {root}")

    def family_for_path(self, path: str | Path) -> SemanticFamilyDefinition:
        normalized = str(path).replace("\\", "/")
        root = normalized.split("/", 1)[0]
        return self.by_root(root)

    def artifact_families(self) -> tuple[ArtifactFamily[Any, Any, Any], ...]:
        return tuple(family.artifact_family for family in self.families)

    def init_roots(self) -> tuple[str, ...]:
        return tuple(family.root for family in self.families if family.init_directory)

    def importable(self) -> tuple[SemanticFamilyDefinition, ...]:
        return tuple(
            sorted(
                (family for family in self.families if family.importable),
                key=lambda family: (family.import_order, family.name),
            )
        )

    def import_roots(self) -> tuple[str, ...]:
        return tuple(family.root for family in self.importable())

    def foreign_keys(self) -> tuple[ForeignKeySpec, ...]:
        specs = [
            spec
            for family in self.families
            for spec in family.foreign_keys
        ]
        return tuple(sorted(specs, key=lambda spec: spec.name))

    def normalize_import_writes(
        self,
        store: DocumentFamilyStore["Repository"],
        writes: Mapping[str, bytes],
        *,
        repository_name: str,
    ) -> tuple[dict[str, PlannedSemanticWrite], list[str]]:
        normalized: dict[str, PlannedSemanticWrite] = {}
        state = SemanticImportState(repository_name=repository_name)
        for family in self.importable():
            family_paths = [
                path
                for path in sorted(writes)
                if self.family_for_path(path).name == family.name
            ]
            if not family_paths:
                continue
            normalizer = family.normalize_import_batch or _normalize_passthrough_batch
            normalized.update(normalizer(store, family_paths, writes, state, self))
        return normalized, list(state.warnings)


def _decode_yaml(content: bytes, *, path: str) -> dict[str, Any]:
    return decode_yaml_mapping(content, source=path)


def _planned_write(
    store: DocumentFamilyStore["Repository"],
    registry: SemanticFamilyRegistry,
    path: str,
    payload: object,
) -> PlannedSemanticWrite:
    family = registry.family_for_path(path).artifact_family
    ref = store.ref_from_path(cast(Any, family), path)
    document = store.coerce(cast(Any, family), payload, source=path)
    return PlannedSemanticWrite(
        family=family,
        ref=ref,
        document=document,
        relpath=store.resolve(cast(Any, family), ref).relpath,
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
        rewritten["replaced_by"] = _rewrite_reference(
            rewritten.get("replaced_by"),
            concept_ref_map,
        )

    relationships = rewritten.get("relationships")
    if isinstance(relationships, list):
        updated_relationships = []
        for relationship in relationships:
            if not isinstance(relationship, dict):
                updated_relationships.append(relationship)
                continue
            copied = dict(relationship)
            copied["target"] = _rewrite_reference(copied.get("target"), concept_ref_map)
            updated_relationships.append(copied)
        rewritten["relationships"] = updated_relationships

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
                copied["inputs"] = [
                    _rewrite_reference(input_id, concept_ref_map)
                    for input_id in inputs
                ]
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
            copied["concepts"] = [
                _rewrite_reference(concept_ref, concept_ref_map)
                for concept_ref in concepts
            ]

        for field in ("variables", "parameters"):
            values = copied.get(field)
            if not isinstance(values, list):
                continue
            updated_values = []
            for value in values:
                if not isinstance(value, dict):
                    updated_values.append(value)
                    continue
                value_copy = dict(value)
                value_copy["concept"] = _rewrite_reference(
                    value_copy.get("concept"),
                    concept_ref_map,
                )
                updated_values.append(value_copy)
            copied[field] = updated_values

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
    registry: SemanticFamilyRegistry,
) -> Mapping[str, PlannedSemanticWrite]:
    seeded: dict[str, PlannedSemanticWrite] = {}
    for path in paths:
        payload = _decode_yaml(writes[path], path=path)
        canonical_name = payload.get("canonical_name")
        raw_id = payload.get("id")
        effective_name = (
            canonical_name
            if isinstance(canonical_name, str) and canonical_name
            else str(raw_id or Path(path).stem or "concept")
        )
        payload.setdefault("canonical_name", effective_name)
        payload.setdefault("status", "accepted")
        payload.setdefault("definition", effective_name)
        payload.setdefault("form", "structural")

        normalized_payload, reference_keys = _normalize_concept_payload(
            payload,
            default_domain=state.repository_name,
        )
        concept_write = _planned_write(store, registry, path, normalized_payload)
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
            registry,
            path,
            _rewrite_concept_payload_refs(
                payload,
                concept_ref_map=state.concept_ref_map,
            ),
        )
    return normalized


def _normalize_claim_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
    registry: SemanticFamilyRegistry,
) -> Mapping[str, PlannedSemanticWrite]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    for path in paths:
        payload = _decode_yaml(writes[path], path=path)
        source = payload.get("source")
        has_source = (
            isinstance(source, dict)
            and isinstance(source.get("paper"), str)
            and bool(source.get("paper"))
        )
        normalized_payload, local_map = normalize_claim_file_payload(
            payload,
            default_namespace=state.repository_name,
        )
        if not has_source:
            normalized_payload["source"] = _claim_source_from_import_path(path)
        rewritten_payload = _rewrite_claim_concept_refs(
            normalized_payload,
            concept_ref_map=state.concept_ref_map,
        )
        normalized[path] = _planned_write(store, registry, path, rewritten_payload)
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
    registry: SemanticFamilyRegistry,
) -> Mapping[str, PlannedSemanticWrite]:
    return {
        path: _planned_write(
            store,
            registry,
            path,
            state.local_handle_index.rewrite_stance_payload(
                _decode_yaml(writes[path], path=path),
                path=path,
            ),
        )
        for path in paths
    }


def _normalize_passthrough_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
    registry: SemanticFamilyRegistry,
) -> Mapping[str, PlannedSemanticWrite]:
    del state
    return {
        path: _planned_write(store, registry, path, _decode_yaml(writes[path], path=path))
        for path in paths
    }


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


SEMANTIC_FAMILIES = SemanticFamilyRegistry(
    families=(
        SemanticFamilyDefinition(
            name="claim",
            contract_version=SEMANTIC_FAMILY_CONTRACT_VERSION,
            artifact_family=CLAIMS_FILE_FAMILY,
            document_type=ClaimsFileDocument,
            root="claims",
            collection_field="claims",
            importable=True,
            import_order=20,
            foreign_keys=CLAIM_FOREIGN_KEYS,
            normalize_import_batch=_normalize_claim_batch,
        ),
        SemanticFamilyDefinition(
            name="concept",
            contract_version=SEMANTIC_FAMILY_CONTRACT_VERSION,
            artifact_family=CONCEPT_FILE_FAMILY,
            document_type=ConceptDocument,
            root="concepts",
            importable=True,
            import_order=10,
            foreign_keys=CONCEPT_FOREIGN_KEYS,
            normalize_import_batch=_normalize_concept_batch,
        ),
        SemanticFamilyDefinition(
            name="context",
            contract_version=SEMANTIC_FAMILY_CONTRACT_VERSION,
            artifact_family=CONTEXT_FAMILY,
            document_type=ContextDocument,
            root="contexts",
            importable=True,
            import_order=30,
        ),
        SemanticFamilyDefinition(
            name="form",
            contract_version=SEMANTIC_FAMILY_CONTRACT_VERSION,
            artifact_family=FORM_FAMILY,
            document_type=FormDocument,
            root="forms",
            importable=True,
            import_order=30,
        ),
        SemanticFamilyDefinition(
            name="predicate",
            contract_version=SEMANTIC_FAMILY_CONTRACT_VERSION,
            artifact_family=PREDICATE_FILE_FAMILY,
            document_type=PredicatesFileDocument,
            root="predicates",
            collection_field="predicates",
            importable=True,
            import_order=40,
        ),
        SemanticFamilyDefinition(
            name="rule",
            contract_version=SEMANTIC_FAMILY_CONTRACT_VERSION,
            artifact_family=RULE_FILE_FAMILY,
            document_type=RulesFileDocument,
            root="rules",
            collection_field="rules",
            importable=True,
            import_order=50,
        ),
        SemanticFamilyDefinition(
            name="stance",
            contract_version=SEMANTIC_FAMILY_CONTRACT_VERSION,
            artifact_family=STANCE_FILE_FAMILY,
            document_type=StanceFileDocument,
            root="stances",
            collection_field="stances",
            importable=True,
            import_order=60,
            normalize_import_batch=_normalize_stance_batch,
        ),
        SemanticFamilyDefinition(
            name="worldline",
            contract_version=SEMANTIC_FAMILY_CONTRACT_VERSION,
            artifact_family=WORLDLINE_FAMILY,
            document_type=WorldlineDefinitionDocument,
            root="worldlines",
            importable=True,
            import_order=70,
        ),
    )
)
