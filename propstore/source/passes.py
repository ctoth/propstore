"""Normalize semantic family writes during committed repository imports."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from quire.documents import decode_yaml_mapping
from quire.family_store import DocumentFamilyStore
from quire.families import FamilyRegistry
from quire.references import AmbiguousReferenceError

from propstore.families.addresses import SemanticFamilyAddress
from propstore.families.claims.documents import ClaimDocument
from propstore.families.registry import (
    ClaimRef,
    PROPSTORE_FAMILY_REGISTRY,
    PropstoreFamily,
    semantic_import_families,
)
from propstore.families.identity.concepts import (
    concept_reference_keys,
    normalize_canonical_concept_payload,
)
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import PassResult, PipelineResult
from propstore.source.claim_concepts import normalize_imported_claim_artifact
from propstore.source.reference_indexes import (
    ImportedClaimHandle,
    imported_claim_handle_index,
)
from propstore.source.stages import (
    PlannedSemanticWrite,
    SourceImportAuthoredWrites,
    SourceImportNormalizedWrites,
    SourceImportState,
    SourceStage,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


SemanticImportBatch = Callable[
    [
        DocumentFamilyStore["Repository"],
        Sequence[str],
        Mapping[str, bytes],
        SourceImportState,
    ],
    Mapping[str, PlannedSemanticWrite],
]


def _semantic_import_registry() -> FamilyRegistry["Repository", PropstoreFamily]:
    return FamilyRegistry(
        name="propstore-semantic-import",
        contract_version=PROPSTORE_FAMILY_REGISTRY.contract_version,
        families=semantic_import_families(),
        validate_foreign_keys=False,
    )


def _decode_yaml(content: bytes, *, path: str) -> dict[str, Any]:
    return decode_yaml_mapping(content, source=path)


def _planned_write(
    store: DocumentFamilyStore["Repository"],
    path: str,
    payload: object,
) -> PlannedSemanticWrite:
    family = _semantic_import_registry().family_for_path(path).artifact_family
    ref = store.ref_from_path(cast(Any, family), path)
    document = store.coerce(cast(Any, family), payload, source=path)
    address = store.address(cast(Any, family), ref)
    return PlannedSemanticWrite(
        family=family,
        ref=ref,
        document=document,
        relpath=SemanticFamilyAddress(address.require_path()),
    )


def _planned_claim_document_write(
    store: DocumentFamilyStore["Repository"],
    document: ClaimDocument,
    *,
    source: str,
) -> PlannedSemanticWrite:
    artifact_id = getattr(document, "artifact_id", None)
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError(f"Imported claim {source!r} is missing artifact_id after normalization")
    family = PROPSTORE_FAMILY_REGISTRY.by_key(PropstoreFamily.CLAIMS).artifact_family
    ref = ClaimRef(artifact_id)
    address = store.address(cast(Any, family), ref)
    return PlannedSemanticWrite(
        family=family,
        ref=ref,
        document=document,
        relpath=SemanticFamilyAddress(address.require_path()),
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


def _rewrite_indexed_reference(value: Any, index) -> Any:
    if not isinstance(value, str):
        return value
    return index.resolve_id(value) or value


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
    state: SourceImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    seeded: dict[str, PlannedSemanticWrite] = {}
    for path in paths:
        payload = _decode_yaml(writes[path], path=path)
        canonical_name = payload.get("canonical_name")
        raw_id = payload.get("id")
        effective_name = canonical_name if isinstance(canonical_name, str) and canonical_name else str(raw_id or Path(path).stem or "concept")
        payload.setdefault("canonical_name", effective_name)
        payload.setdefault("status", "proposed")
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
    state: SourceImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    for path in paths:
        payload = _decode_yaml(writes[path], path=path)
        if isinstance(payload.get("claims"), list):
            raise ValueError(
                f"Imported claim path {path!r} is an aggregate; "
                "canonical repository imports require one claim artifact per file"
            )
        normalized_claim = normalize_imported_claim_artifact(
            payload,
            default_namespace=state.repository_name,
            default_source=_claim_source_from_import_path(path),
            concept_map=state.concept_ref_map,
            source=path,
        )
        planned_write = _planned_claim_document_write(store, normalized_claim.document, source=path)
        normalized[planned_write.relpath] = planned_write
        for local_id, artifact_id in normalized_claim.local_handle_map.items():
            state.imported_claim_handles.append(
                ImportedClaimHandle(handle=local_id, artifact_id=artifact_id)
            )
    return normalized


def _record_imported_claim_handle_ambiguities(state: SourceImportState) -> None:
    try:
        imported_claim_handle_index(state.imported_claim_handles)
    except AmbiguousReferenceError as exc:
        state.warnings.append(
            "ambiguous imported claim handle "
            f"{exc.reference!r}: {', '.join(exc.candidates)}"
        )


def _normalize_stance_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SourceImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    claim_index = imported_claim_handle_index(state.imported_claim_handles)
    for path in paths:
        payload = dict(_decode_yaml(writes[path], path=path))
        payload["source_claim"] = _rewrite_indexed_reference(
            payload.get("source_claim"),
            claim_index,
        )
        raw_stances = payload.get("stances")
        if isinstance(raw_stances, list):
            payload["stances"] = [
                (
                    {
                        **stance,
                        "target": _rewrite_indexed_reference(
                            stance.get("target"),
                            claim_index,
                        ),
                    }
                    if isinstance(stance, dict)
                    else stance
                )
                for stance in raw_stances
            ]
        if isinstance(payload.get("target"), str):
            payload["target"] = _rewrite_indexed_reference(
                payload.get("target"),
                claim_index,
            )
        normalized[path] = _planned_write(store, path, payload)
    return normalized


def _normalize_passthrough_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SourceImportState,
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


def _normalize_semantic_import_writes(
    store: DocumentFamilyStore["Repository"],
    writes: Mapping[str, bytes],
    *,
    repository_name: str,
) -> SourceImportNormalizedWrites:
    normalized: dict[str, PlannedSemanticWrite] = {}
    state = SourceImportState(repository_name=repository_name)
    import_registry = _semantic_import_registry()
    for family in semantic_import_families():
        family_paths = [
            path
            for path in sorted(writes)
            if import_registry.family_for_path(path).name == family.name
        ]
        if not family_paths:
            continue
        normalizer = _SEMANTIC_IMPORT_NORMALIZERS.get(cast(PropstoreFamily, family.key), _normalize_passthrough_batch)
        normalized.update(normalizer(store, family_paths, writes, state))
        if family.key is PropstoreFamily.CLAIMS:
            _record_imported_claim_handle_ambiguities(state)
    return SourceImportNormalizedWrites(
        writes=normalized,
        warnings=tuple(state.warnings),
    )


class SourceImportNormalizePass:
    family = PropstoreFamily.SOURCES
    name = "source.import.normalize"
    input_stage = SourceStage.IMPORT_AUTHORED
    output_stage = SourceStage.IMPORT_NORMALIZED

    def run(
        self,
        value: SourceImportAuthoredWrites,
        context: object,
    ) -> PassResult[SourceImportNormalizedWrites]:
        del context
        return PassResult(
            output=_normalize_semantic_import_writes(
                value.store,
                value.writes,
                repository_name=value.repository_name,
            )
        )


def register_source_import_pipeline(registry: PipelineRegistry) -> None:
    registry.register(SourceImportNormalizePass, family=PropstoreFamily.SOURCES)


def run_source_import_pipeline(
    authored: SourceImportAuthoredWrites,
) -> PipelineResult[object]:
    registry = PipelineRegistry()
    register_source_import_pipeline(registry)
    return run_pipeline(
        authored,
        family=PropstoreFamily.SOURCES,
        start_stage=SourceStage.IMPORT_AUTHORED,
        target_stage=SourceStage.IMPORT_NORMALIZED,
        registry=registry,
        context=None,
    )
