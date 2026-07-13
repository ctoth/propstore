"""Normalize committed repository snapshots onto isolated import branches.

The input is a source repository's committed canonical semantic tree.  Every
document is decoded through its registered family and rewritten only where the
destination branch needs local identities.  Imported concepts are namespaced by
repository origin and source artifact identity; canonical names never reconcile
or merge concepts.  Claims and stances then rewrite their typed references
through the identities established earlier in the same import pass.

Each import branch therefore remains a self-contained snapshot.  Repeating an
import of the same source snapshot produces the same semantic documents, while
an equally named concept from another repository remains independently
addressable.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

import msgspec
from quire.documents import decode_yaml_mapping
from quire.families import BoundFamilyRegistry
from quire.family_store import DocumentFamilyStore
from quire.references import AmbiguousReferenceError

from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.identity.claims import derive_claim_artifact_id
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.families.identity.stances import derive_stance_artifact_id
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    PropstoreFamily,
    semantic_import_families,
)
from propstore.families.relations import Stance
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import PassResult, PipelineResult
from propstore.source.common import normalize_source_slug
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


SemanticImportBatch = Callable[
    [
        "BoundFamilyRegistry[object, object]",
        str,
        Sequence[str],
        Mapping[str, bytes],
        SourceImportState,
    ],
    "Mapping[str, PlannedSemanticWrite]",
]


def _bound_registry(
    store: DocumentFamilyStore[object],
) -> BoundFamilyRegistry[object, object]:
    """Bind the canonical registry to the destination import store."""

    return PROPSTORE_FAMILY_REGISTRY.bind(store.owner, store)


def _decode(content: bytes, *, path: str) -> dict[str, object]:
    """Decode one YAML document at the import IO boundary."""

    return decode_yaml_mapping(content, source=path)


def _remap(reference_map: Mapping[str, str], value: str | None) -> str | None:
    if value is None:
        return None
    return reference_map.get(value, value)


def _planned_write(
    bound: BoundFamilyRegistry[object, object],
    family_name: str,
    ref: object,
    document: object,
) -> PlannedSemanticWrite:
    relpath = bound.by_name(family_name).address(ref).require_path()
    return PlannedSemanticWrite(
        family=bound.registry.by_name(family_name).artifact_family,
        ref=ref,
        document=document,
        relpath=relpath,
    )


def _normalize_concept_batch(
    bound: BoundFamilyRegistry[object, object],
    family_name: str,
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SourceImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    coercer = bound.by_name(family_name)
    repository_identity = normalize_source_slug(state.repository_name)
    for path in paths:
        concept: Concept = coercer.coerce(_decode(writes[path], path=path), source=path)
        source_identity = normalize_source_slug(concept.concept_id)
        new_id = derive_concept_artifact_id(
            f"{repository_identity}_{source_identity}"
        )
        state.concept_ref_map[concept.concept_id] = new_id
        rekeyed = msgspec.structs.replace(concept, concept_id=new_id)
        planned = _planned_write(bound, family_name, new_id, rekeyed)
        normalized[planned.relpath] = planned
    return normalized


def _normalize_claim_batch(
    bound: BoundFamilyRegistry[object, object],
    family_name: str,
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SourceImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    coercer = bound.by_name(family_name)
    for path in paths:
        claim: Claim = coercer.coerce(_decode(writes[path], path=path), source=path)
        new_id = derive_claim_artifact_id(state.repository_name, claim.claim_id)
        rekeyed = msgspec.structs.replace(
            claim,
            claim_id=new_id,
            concepts=tuple(
                _remap(state.concept_ref_map, concept) or concept
                for concept in claim.concepts
            ),
            variables=tuple(
                msgspec.structs.replace(
                    variable,
                    concept=_remap(state.concept_ref_map, variable.concept)
                    or variable.concept,
                )
                for variable in claim.variables
            ),
            output_concept=_remap(state.concept_ref_map, claim.output_concept),
            target_concept=_remap(state.concept_ref_map, claim.target_concept),
        )
        state.imported_claim_handles.append(
            ImportedClaimHandle(handle=claim.claim_id, artifact_id=new_id)
        )
        planned = _planned_write(bound, family_name, new_id, rekeyed)
        normalized[planned.relpath] = planned
    _record_imported_claim_handle_ambiguities(state)
    return normalized


def _record_imported_claim_handle_ambiguities(state: SourceImportState) -> None:
    try:
        imported_claim_handle_index(state.imported_claim_handles)
    except AmbiguousReferenceError as exc:
        state.warnings.append(
            f"ambiguous imported claim handle {exc.reference!r}: "
            f"{', '.join(exc.candidates)}"
        )


def _normalize_stance_batch(
    bound: BoundFamilyRegistry[object, object],
    family_name: str,
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SourceImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    coercer = bound.by_name(family_name)
    claim_index = imported_claim_handle_index(state.imported_claim_handles)
    for path in paths:
        stance: Stance = coercer.coerce(_decode(writes[path], path=path), source=path)
        source_claim_id = (
            claim_index.resolve_id(stance.source_claim_id) or stance.source_claim_id
        )
        target_claim_id = (
            claim_index.resolve_id(stance.target_claim_id) or stance.target_claim_id
        )
        stance_type = None if stance.stance_type is None else stance.stance_type.value
        new_id = derive_stance_artifact_id(
            source_claim_id=source_claim_id,
            target_claim_id=target_claim_id,
            stance_type=stance_type,
        )
        rekeyed = msgspec.structs.replace(
            stance,
            stance_id=new_id,
            source_claim_id=source_claim_id,
            target_claim_id=target_claim_id,
        )
        planned = _planned_write(bound, family_name, new_id, rekeyed)
        normalized[planned.relpath] = planned
    return normalized


def _normalize_passthrough_batch(
    bound: BoundFamilyRegistry[object, object],
    family_name: str,
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SourceImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    del state
    normalized: dict[str, PlannedSemanticWrite] = {}
    coercer = bound.by_name(family_name)
    for path in paths:
        document = coercer.coerce(_decode(writes[path], path=path), source=path)
        ref = coercer.ref_from_path(path)
        planned = _planned_write(bound, family_name, ref, document)
        normalized[planned.relpath] = planned
    return normalized


_SEMANTIC_IMPORT_NORMALIZERS: Mapping[str, SemanticImportBatch] = {
    PropstoreFamily.CONCEPT.value: _normalize_concept_batch,
    PropstoreFamily.CLAIM.value: _normalize_claim_batch,
    PropstoreFamily.STANCE.value: _normalize_stance_batch,
}


def _normalize_semantic_import_writes(
    store: DocumentFamilyStore[object],
    writes: Mapping[str, bytes],
    *,
    repository_name: str,
) -> SourceImportNormalizedWrites:
    bound = _bound_registry(store)
    state = SourceImportState(repository_name=repository_name)
    normalized: dict[str, PlannedSemanticWrite] = {}
    for family in semantic_import_families():
        family_paths = [
            path
            for path in sorted(writes)
            if bound.registry.family_for_path(path).name == family.name
        ]
        if not family_paths:
            continue
        normalizer = _SEMANTIC_IMPORT_NORMALIZERS.get(
            family.name, _normalize_passthrough_batch
        )
        normalized.update(normalizer(bound, family.name, family_paths, writes, state))
    return SourceImportNormalizedWrites(
        writes=normalized,
        warnings=tuple(state.warnings),
    )


class SourceImportNormalizePass:
    """Rewrite a committed snapshot into isolated planned import writes."""

    family = PropstoreFamily.CONCEPT
    name = "import.snapshot.normalize"
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
    registry.register(SourceImportNormalizePass, family=PropstoreFamily.CONCEPT)


def run_source_import_pipeline(
    authored: SourceImportAuthoredWrites,
) -> PipelineResult[object]:
    """Run committed-snapshot normalization through the semantic-pass runner."""

    registry = PipelineRegistry()
    register_source_import_pipeline(registry)
    return run_pipeline(
        authored,
        family=PropstoreFamily.CONCEPT,
        start_stage=SourceStage.IMPORT_AUTHORED,
        target_stage=SourceStage.IMPORT_NORMALIZED,
        registry=registry,
        context=None,
    )
