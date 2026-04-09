"""Shared canonical compilation context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping

from propstore.cel_checker import ConceptInfo, build_cel_registry_from_concepts
from propstore.core.concepts import (
    ConceptRecord,
    LoadedConcept,
    concept_reference_keys,
    normalize_loaded_concepts as _normalize_loaded_concepts,
    parse_concept_record,
)
from propstore.form_utils import FormDefinition, load_all_forms_path
from propstore.identity import format_logical_id
from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path
from propstore.loaded import LoadedEntry
from propstore.validate import load_concepts

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


@dataclass(frozen=True)
class CompilationContext:
    """Immutable symbol tables and registries for canonical semantic compilation."""

    form_registry: Mapping[str, FormDefinition]
    context_ids: frozenset[str]
    concepts_by_id: Mapping[str, ConceptRecord]
    concept_lookup: Mapping[str, tuple[str, ...]]
    claim_lookup: Mapping[str, tuple[str, ...]]
    cel_registry: Mapping[str, ConceptInfo]


def _freeze_mapping(data: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(data))


def _extend_lookup(
    lookup: dict[str, list[str]],
    key: str | None,
    target_id: str,
) -> None:
    if not isinstance(key, str) or not key:
        return
    values = lookup.setdefault(key, [])
    if target_id not in values:
        values.append(target_id)


def _finalize_lookup(lookup: dict[str, list[str]]) -> Mapping[str, tuple[str, ...]]:
    return MappingProxyType({key: tuple(values) for key, values in lookup.items()})


def normalize_loaded_concepts(concepts: list[LoadedEntry]) -> list[LoadedConcept]:
    return _normalize_loaded_concepts(concepts)


def _build_claim_lookup(claim_files: list[LoadedEntry]) -> Mapping[str, tuple[str, ...]]:
    from propstore.identity import normalize_identity_namespace, normalize_logical_value

    lookup: dict[str, list[str]] = {}
    for claim_file in claim_files:
        source = claim_file.data.get("source")
        source_paper = (
            source.get("paper")
            if isinstance(source, dict) and isinstance(source.get("paper"), str)
            else claim_file.filename
        )
        claims = claim_file.data.get("claims")
        if not isinstance(claims, list):
            continue
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            artifact_id = claim.get("artifact_id")
            if not isinstance(artifact_id, str) or not artifact_id:
                continue
            _extend_lookup(lookup, artifact_id, artifact_id)
            raw_id = claim.get("id")
            if isinstance(raw_id, str) and raw_id:
                _extend_lookup(lookup, raw_id, artifact_id)
                _extend_lookup(
                    lookup,
                    f"{normalize_identity_namespace(str(source_paper))}:{normalize_logical_value(raw_id)}",
                    artifact_id,
                )
            logical_ids = claim.get("logical_ids")
            if not isinstance(logical_ids, list):
                continue
            for entry in logical_ids:
                if not isinstance(entry, dict):
                    continue
                formatted = format_logical_id(entry)
                if formatted:
                    _extend_lookup(lookup, formatted, artifact_id)
                value = entry.get("value")
                if isinstance(value, str) and value:
                    _extend_lookup(lookup, value, artifact_id)
    return _finalize_lookup(lookup)


def _build_context_from_concepts(
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
    *,
    claim_files: list[LoadedEntry] | None,
    context_ids: set[str] | None,
) -> CompilationContext:
    concepts_by_id: dict[str, ConceptRecord] = {}
    concept_lookup: dict[str, list[str]] = {}

    for concept in concepts:
        record = concept.record
        artifact_id = str(record.artifact_id)
        concepts_by_id[artifact_id] = record
        for key in concept_reference_keys(record):
            _extend_lookup(concept_lookup, key, artifact_id)

    finalized_lookup = _finalize_lookup(concept_lookup)
    return CompilationContext(
        form_registry=_freeze_mapping(form_registry),
        context_ids=frozenset(context_ids or set()),
        concepts_by_id=MappingProxyType(dict(concepts_by_id)),
        concept_lookup=finalized_lookup,
        claim_lookup=(
            MappingProxyType({})
            if claim_files is None
            else _build_claim_lookup(claim_files)
        ),
        cel_registry=_freeze_mapping(build_cel_registry_from_concepts(concepts)),
    )


def build_compilation_context_from_loaded(
    concepts: list[LoadedConcept],
    *,
    forms_dir: Path | KnowledgePath | None = None,
    claim_files: list[LoadedEntry] | None = None,
    context_ids: set[str] | None = None,
) -> CompilationContext:
    form_registry = (
        {}
        if forms_dir is None
        else load_all_forms_path(coerce_knowledge_path(forms_dir))
    )
    return _build_context_from_concepts(
        concepts,
        form_registry,
        claim_files=claim_files,
        context_ids=context_ids,
    )


def build_compilation_context_from_paths(
    concepts_dir: Path | KnowledgePath,
    forms_dir: Path | KnowledgePath,
    *,
    claim_files: list[LoadedEntry] | None = None,
    context_ids: set[str] | None = None,
) -> CompilationContext:
    concepts_root = coerce_knowledge_path(concepts_dir)
    concepts = normalize_loaded_concepts(load_concepts(concepts_root))
    return build_compilation_context_from_loaded(
        concepts,
        forms_dir=forms_dir,
        claim_files=claim_files,
        context_ids=context_ids,
    )


def build_compilation_context_from_repo(
    repo: Repository | None,
    *,
    claim_files: list[LoadedEntry] | None = None,
    context_ids: set[str] | None = None,
) -> CompilationContext:
    if repo is None:
        return compilation_context_from_concept_registry(
            {},
            claim_files=claim_files,
            context_ids=context_ids,
        )
    return build_compilation_context_from_paths(
        repo.tree() / "concepts",
        repo.tree() / "forms",
        claim_files=claim_files,
        context_ids=context_ids,
    )


def compilation_context_from_concept_registry(
    concept_registry: dict[str, dict[str, Any]],
    *,
    claim_files: list[LoadedEntry] | None = None,
    context_ids: set[str] | None = None,
) -> CompilationContext:
    """Adapt the old lookup-keyed concept registry into the canonical context."""

    concepts_by_id: dict[str, ConceptRecord] = {}
    concept_lookup: dict[str, list[str]] = {}
    form_registry: dict[str, FormDefinition] = {}

    for key, value in concept_registry.items():
        if not isinstance(value, dict):
            continue
        raw_form_definition = value.get("_form_definition")
        payload = dict(value)
        if not payload.get("artifact_id") and isinstance(key, str) and key:
            payload["artifact_id"] = key
        try:
            record = parse_concept_record(payload)
        except ValueError:
            continue
        artifact_id = str(record.artifact_id)
        concepts_by_id.setdefault(artifact_id, record)
        _extend_lookup(concept_lookup, key, artifact_id)
        for alias_key in concept_reference_keys(record):
            _extend_lookup(concept_lookup, alias_key, artifact_id)
        if isinstance(raw_form_definition, FormDefinition):
            form_registry.setdefault(record.form, raw_form_definition)

    finalized_lookup = _finalize_lookup(concept_lookup)
    return CompilationContext(
        form_registry=MappingProxyType(dict(form_registry)),
        context_ids=frozenset(context_ids or set()),
        concepts_by_id=MappingProxyType(dict(concepts_by_id)),
        concept_lookup=finalized_lookup,
        claim_lookup=(
            MappingProxyType({})
            if claim_files is None
            else _build_claim_lookup(claim_files)
        ),
        cel_registry=_freeze_mapping(
            build_cel_registry_from_concepts(concepts_by_id.values())
        ),
    )


def concept_registry_for_context(
    context: CompilationContext,
) -> dict[str, dict[str, Any]]:
    return concept_registry_for_context_payloads(
        context.concepts_by_id,
        context.concept_lookup,
        form_registry=context.form_registry,
    )


def concept_registry_for_context_payloads(
    concepts_by_id: Mapping[str, ConceptRecord],
    concept_lookup: Mapping[str, tuple[str, ...]],
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
    for key, candidates in concept_lookup.items():
        if len(candidates) != 1:
            continue
        payload = payloads_by_id.get(candidates[0])
        if payload is None:
            continue
        registry.setdefault(key, payload)
    return registry


def build_concept_registry_from_paths(
    concepts_dir: Path | KnowledgePath,
    forms_dir: Path | KnowledgePath,
) -> dict[str, dict[str, Any]]:
    context = build_compilation_context_from_paths(concepts_dir, forms_dir)
    return concept_registry_for_context(context)
