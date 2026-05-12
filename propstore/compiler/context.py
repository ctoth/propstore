"""Shared canonical compilation context."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping, cast

from quire.references import FamilyReferenceIndex
from quire.tree_path import TreePath as KnowledgePath, coerce_tree_path as coerce_knowledge_path
from propstore.core.conditions.registry import ConceptInfo, with_standard_synthetic_bindings
from propstore.cel_registry import build_canonical_cel_registry
from propstore.claims import ClaimFileEntry
from propstore.families.claims.references import (
    ClaimReferenceRecord,
    build_claim_file_reference_index,
)
from propstore.families.concepts.stages import (
    ConceptRecord,
    LoadedConcept,
    concept_reference_keys,
    parse_concept_record_document,
)
from propstore.families.forms.stages import (
    FormDefinition,
    load_all_forms_path,
    parse_form,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class CompilationContext:
    """Immutable symbol tables and registries for canonical semantic compilation."""

    form_registry: Mapping[str, FormDefinition]
    context_ids: frozenset[str]
    concepts_by_id: Mapping[str, ConceptRecord]
    concept_index: FamilyReferenceIndex[ConceptRecord]
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord]
    cel_registry: Mapping[str, ConceptInfo]


def _freeze_mapping(data: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(data))


def build_compiler_claim_index(
    claim_files: Sequence[ClaimFileEntry],
) -> FamilyReferenceIndex[ClaimReferenceRecord]:
    return build_claim_file_reference_index(claim_files)


def concept_form_definition(
    concept_ref: object,
    context: CompilationContext,
) -> FormDefinition | None:
    concept_id = context.concept_index.resolve_id(concept_ref)
    if concept_id is None:
        return None
    record = context.concepts_by_id.get(concept_id)
    if record is None:
        return None
    form_definition = context.form_registry.get(record.form)
    return form_definition if isinstance(form_definition, FormDefinition) else None


def compiler_concept_match_kind(
    raw_text: str,
    resolved_id: str,
    record: ConceptRecord | None,
) -> tuple[str | None, str | None]:
    if raw_text == resolved_id:
        return "artifact_id", raw_text
    if record is None:
        return None, None
    if record.canonical_name == raw_text:
        return "canonical_name", raw_text
    for logical_id in record.logical_ids:
        if logical_id.formatted == raw_text:
            return "logical_id", raw_text
        if logical_id.value == raw_text:
            return "logical_value", raw_text
    for alias in record.aliases:
        if alias.name == raw_text:
            return "alias", raw_text
    return None, None


def compiler_claim_match_kind(
    raw_text: str,
    resolved_id: str,
    record: ClaimReferenceRecord | None,
) -> tuple[str | None, str | None]:
    if raw_text == resolved_id:
        return "artifact_id", raw_text
    if record is None:
        return None, None
    for logical_id in record.claim.logical_ids:
        if logical_id.formatted == raw_text:
            return "logical_id", raw_text
        if logical_id.value == raw_text:
            return "logical_value", raw_text
    return None, None


def _concept_reference_index(
    records: Iterable[ConceptRecord],
) -> FamilyReferenceIndex[ConceptRecord]:
    return FamilyReferenceIndex.from_records(
        records,
        family="concept",
        artifact_id=lambda record: str(record.artifact_id),
        keys=(concept_reference_keys,),
    )


def _build_context_from_concepts(
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
    *,
    claim_files: Sequence[ClaimFileEntry] | None,
    context_ids: set[str] | None,
) -> CompilationContext:
    concepts_by_id: dict[str, ConceptRecord] = {}

    for concept in concepts:
        record = concept.record
        artifact_id = str(record.artifact_id)
        concepts_by_id[artifact_id] = record

    concept_index = _concept_reference_index(concepts_by_id.values())
    return CompilationContext(
        form_registry=_freeze_mapping(form_registry),
        context_ids=frozenset(context_ids or set()),
        concepts_by_id=MappingProxyType(dict(concepts_by_id)),
        concept_index=concept_index,
        claim_index=(
            build_compiler_claim_index(())
            if claim_files is None
            else build_compiler_claim_index(claim_files)
        ),
        cel_registry=_freeze_mapping(
            with_standard_synthetic_bindings(
                build_canonical_cel_registry(concept.record for concept in concepts)
            )
        ),
    )


def build_compilation_context_from_loaded(
    concepts: list[LoadedConcept],
    *,
    forms_dir: Path | KnowledgePath | None = None,
    form_registry: dict[str, FormDefinition] | None = None,
    claim_files: Sequence[ClaimFileEntry] | None = None,
    context_ids: set[str] | None = None,
) -> CompilationContext:
    resolved_form_registry = (
        dict(form_registry)
        if form_registry is not None
        else (
            {}
            if forms_dir is None
            else load_all_forms_path(coerce_knowledge_path(forms_dir))
        )
    )
    return _build_context_from_concepts(
        concepts,
        resolved_form_registry,
        claim_files=claim_files,
        context_ids=context_ids,
    )


def build_compilation_context_from_repo(
    repo: Repository | None,
    *,
    claim_files: Sequence[ClaimFileEntry] | None = None,
    context_ids: set[str] | None = None,
    commit: str | None = None,
) -> CompilationContext:
    if repo is None:
        return _build_context_from_concepts(
            [],
            {},
            claim_files=claim_files,
            context_ids=context_ids,
        )
    tree = repo.tree(commit=commit)
    concepts: list[LoadedConcept] = []
    for handle in repo.families.concepts.iter_handles(commit=commit):
        concepts.append(
            LoadedConcept(
                filename=handle.ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
        )

    form_registry: dict[str, FormDefinition] = {}
    for handle in repo.families.forms.iter_handles(commit=commit):
        document = handle.document
        form_registry[document.name] = parse_form(document.name, document)

    return _build_context_from_concepts(
        concepts,
        form_registry,
        claim_files=claim_files,
        context_ids=context_ids,
    )


def concept_registry_for_context(
    context: CompilationContext,
) -> dict[str, dict[str, Any]]:
    return concept_registry_for_context_payloads(
        context.concepts_by_id,
        context.concept_index,
        form_registry=context.form_registry,
    )


def concept_registry_for_context_payloads(
    concepts_by_id: Mapping[str, ConceptRecord],
    concept_index: FamilyReferenceIndex[ConceptRecord],
    *,
    form_registry: Mapping[str, FormDefinition] | None = None,
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    payloads_by_id: dict[str, dict[str, Any]] = {}
    for artifact_id, record in concepts_by_id.items():
        payload = record.to_payload()
        form_definition = None if form_registry is None else form_registry.get(record.form)
        if form_definition is not None:
            payload["_form_definition"] = form_definition
        payloads_by_id[artifact_id] = payload
    registry.update(payloads_by_id)
    for key, candidates in concept_index.lookup.items():
        if len(candidates) != 1:
            continue
        payload = payloads_by_id.get(candidates[0])
        if payload is None:
            continue
        registry.setdefault(key, payload)
    return registry


def build_authored_concept_registry(
    concepts: list[Any] | list[LoadedConcept],
    *,
    forms_dir: Path | KnowledgePath | None = None,
    form_registry: Mapping[str, FormDefinition] | None = None,
    require_form_definition: bool = True,
) -> dict[str, dict[str, Any]]:
    """Build the canonical authored-concept lookup used by validators/builders."""
    from propstore.families.concepts.stages import normalize_loaded_concepts
    from propstore.families.forms.stages import load_form_path

    forms_root = None if forms_dir is None else coerce_knowledge_path(forms_dir)
    typed_concepts = (
        concepts
        if all(isinstance(concept, LoadedConcept) for concept in concepts)
        else normalize_loaded_concepts(cast(Any, concepts))
    )
    registry: dict[str, dict[str, Any]] = {}
    for concept in typed_concepts:
        record = concept.record
        enriched = record.to_payload()
        cid = str(record.artifact_id)
        enriched["_storage_id"] = cid
        form_def = (
            form_registry.get(record.form)
            if form_registry is not None and record.form is not None
            else (
                None
                if forms_root is None
                else load_form_path(forms_root, record.form)
            )
        )
        if record.form:
            if form_def is None:
                if require_form_definition:
                    raise ValueError(
                        f"concept '{cid}' references missing form definition '{record.form}'"
                    )
            else:
                enriched["_form_definition"] = form_def
        registry[cid] = enriched
        if concept.source_local_id and concept.source_local_id not in registry:
            registry[concept.source_local_id] = enriched
        canonical = record.canonical_name
        if canonical not in registry:
            registry[canonical] = enriched
        for logical_id in record.logical_ids:
            if logical_id.formatted not in registry:
                registry[logical_id.formatted] = enriched
            if logical_id.value not in registry:
                registry[logical_id.value] = enriched
        for alias in record.aliases:
            if alias.name not in registry:
                registry[alias.name] = enriched
    return registry
