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
from propstore.families.claims.declaration import ClaimDocument
from propstore.families.claims.references import (
    ImportedClaimReference,
    imported_claim_reference_index,
)
from propstore.families.registry import (
    ClaimRef,
    PROPSTORE_FAMILY_REGISTRY,
    PropstoreFamily,
    semantic_import_families,
)
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import PassResult, PipelineResult
from propstore.families.claims.lifecycle import normalize_imported_claim_artifact
from propstore.importing.stages import (
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


def _planned_claim_document_write(
    store: DocumentFamilyStore["Repository"],
    document: ClaimDocument,
    *,
    source: str,
) -> PlannedSemanticWrite:
    artifact_id = getattr(document, "artifact_id", None)
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError(
            f"Imported claim {source!r} is missing artifact_id after normalization"
        )
    family = PROPSTORE_FAMILY_REGISTRY.by_key(PropstoreFamily.CLAIMS).artifact_family
    ref = ClaimRef(artifact_id)
    address = store.address(cast(Any, family), ref)
    return PlannedSemanticWrite(
        family=family,
        ref=ref,
        document=document,
        relpath=SemanticFamilyAddress(address.require_path()),
    )


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


def _record_imported_claim_handle_ambiguities(state: SourceImportState) -> None:
    try:
        imported_claim_reference_index(state.imported_claim_handles)
    except AmbiguousReferenceError as exc:
        state.warnings.append(
            "ambiguous imported claim handle "
            f"{exc.reference!r}: {', '.join(exc.candidates)}"
        )


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
        normalizer = _SEMANTIC_IMPORT_NORMALIZERS.get(
            cast(PropstoreFamily, family.key), _normalize_passthrough_batch
        )
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
