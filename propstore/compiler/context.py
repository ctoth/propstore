"""Shared authored-input compilation context."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping

from propstore.cel_checker import ConceptInfo, build_cel_registry
from propstore.form_utils import FormDefinition, load_all_forms_path
from propstore.identity import compute_concept_version_id, format_logical_id
from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path
from propstore.loaded import LoadedEntry
from propstore.validate import load_concepts

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


@dataclass(frozen=True)
class CompilationContext:
    """Immutable authored-input symbol tables and registries."""

    form_registry: Mapping[str, FormDefinition]
    context_ids: frozenset[str]
    concept_payloads_by_id: Mapping[str, Mapping[str, Any]]
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


def _concept_reference_keys(concept: Mapping[str, Any]) -> set[str]:
    keys: set[str] = set()
    artifact_id = concept.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        keys.add(artifact_id)
    raw_id = concept.get("id")
    if isinstance(raw_id, str) and raw_id:
        keys.add(raw_id)
    canonical_name = concept.get("canonical_name")
    if isinstance(canonical_name, str) and canonical_name:
        keys.add(canonical_name)
    logical_ids = concept.get("logical_ids")
    if isinstance(logical_ids, list):
        for logical_id in logical_ids:
            if not isinstance(logical_id, dict):
                continue
            formatted = format_logical_id(logical_id)
            if formatted:
                keys.add(formatted)
            value = logical_id.get("value")
            if isinstance(value, str) and value:
                keys.add(value)
    aliases = concept.get("aliases")
    if isinstance(aliases, list):
        for alias in aliases:
            alias_name = alias.get("name") if isinstance(alias, dict) else None
            if isinstance(alias_name, str) and alias_name:
                keys.add(alias_name)
    return keys


def _rewrite_concept_reference(
    value: Any,
    concept_ref_map: Mapping[str, str],
) -> Any:
    if not isinstance(value, str):
        return value
    return concept_ref_map.get(value, value)


def _rewrite_concept_payload_refs(
    data: Mapping[str, Any],
    *,
    concept_ref_map: Mapping[str, str],
) -> dict[str, Any]:
    rewritten = dict(data)
    replaced_by = rewritten.get("replaced_by")
    if replaced_by is not None:
        rewritten["replaced_by"] = _rewrite_concept_reference(
            replaced_by,
            concept_ref_map,
        )

    relationships = rewritten.get("relationships")
    if isinstance(relationships, list):
        updated_relationships: list[Any] = []
        for relationship in relationships:
            if not isinstance(relationship, dict):
                updated_relationships.append(relationship)
                continue
            relationship_copy = dict(relationship)
            relationship_copy["target"] = _rewrite_concept_reference(
                relationship_copy.get("target"),
                concept_ref_map,
            )
            updated_relationships.append(relationship_copy)
        rewritten["relationships"] = updated_relationships

    parameterizations = rewritten.get("parameterization_relationships")
    if isinstance(parameterizations, list):
        updated_parameterizations: list[Any] = []
        for parameterization in parameterizations:
            if not isinstance(parameterization, dict):
                updated_parameterizations.append(parameterization)
                continue
            parameterization_copy = dict(parameterization)
            inputs = parameterization_copy.get("inputs")
            if isinstance(inputs, list):
                parameterization_copy["inputs"] = [
                    _rewrite_concept_reference(input_id, concept_ref_map)
                    for input_id in inputs
                ]
            updated_parameterizations.append(parameterization_copy)
        rewritten["parameterization_relationships"] = updated_parameterizations

    rewritten["version_id"] = compute_concept_version_id(rewritten)
    return rewritten


def normalize_loaded_concepts(concepts: list[LoadedEntry]) -> list[LoadedEntry]:
    from propstore.validate import normalize_concept_record

    normalized_entries: list[tuple[LoadedEntry, dict[str, Any]]] = []
    concept_ref_map: dict[str, str] = {}

    for concept in concepts:
        normalized = normalize_concept_record(dict(concept.data))
        artifact_id = normalized.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id:
            for key in _concept_reference_keys(normalized):
                concept_ref_map.setdefault(key, artifact_id)
        normalized_entries.append((concept, normalized))

    rewritten_entries: list[LoadedEntry] = []
    for concept, normalized in normalized_entries:
        rewritten = _rewrite_concept_payload_refs(
            normalized,
            concept_ref_map=concept_ref_map,
        )
        rewritten_entries.append(
            LoadedEntry(
                filename=concept.filename,
                source_path=concept.source_path,
                knowledge_root=concept.knowledge_root,
                data=rewritten,
            )
        )

    return rewritten_entries


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
    concepts: list[LoadedEntry],
    form_registry: dict[str, FormDefinition],
    *,
    claim_files: list[LoadedEntry] | None,
    context_ids: set[str] | None,
) -> CompilationContext:
    concepts = normalize_loaded_concepts(concepts)
    concept_payloads_by_id: dict[str, Mapping[str, Any]] = {}
    concept_lookup: dict[str, list[str]] = {}

    for concept in concepts:
        enriched = dict(concept.data)
        artifact_id = enriched.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue

        form_name = enriched.get("form")
        if isinstance(form_name, str) and form_name:
            form_def = form_registry.get(form_name)
            if form_def is not None:
                enriched["_form_definition"] = form_def

        concept_payloads_by_id[artifact_id] = _freeze_mapping(copy.deepcopy(enriched))
        _extend_lookup(concept_lookup, artifact_id, artifact_id)

        raw_id = concept.data.get("id")
        if isinstance(raw_id, str) and raw_id:
            _extend_lookup(concept_lookup, raw_id, artifact_id)

        canonical_name = enriched.get("canonical_name")
        if isinstance(canonical_name, str) and canonical_name:
            _extend_lookup(concept_lookup, canonical_name, artifact_id)

        logical_ids = enriched.get("logical_ids")
        if isinstance(logical_ids, list):
            for logical_id in logical_ids:
                if not isinstance(logical_id, dict):
                    continue
                formatted = format_logical_id(logical_id)
                if formatted:
                    _extend_lookup(concept_lookup, formatted, artifact_id)
                value = logical_id.get("value")
                if isinstance(value, str) and value:
                    _extend_lookup(concept_lookup, value, artifact_id)

        aliases = enriched.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                alias_name = alias.get("name") if isinstance(alias, dict) else None
                if isinstance(alias_name, str) and alias_name:
                    _extend_lookup(concept_lookup, alias_name, artifact_id)

    finalized_lookup = _finalize_lookup(concept_lookup)
    legacy_registry = legacy_concept_registry_for_context_payloads(
        concept_payloads_by_id,
        finalized_lookup,
    )

    return CompilationContext(
        form_registry=_freeze_mapping(form_registry),
        context_ids=frozenset(context_ids or set()),
        concept_payloads_by_id=MappingProxyType(concept_payloads_by_id),
        concept_lookup=finalized_lookup,
        claim_lookup=(
            MappingProxyType({})
            if claim_files is None
            else _build_claim_lookup(claim_files)
        ),
        cel_registry=_freeze_mapping(build_cel_registry(legacy_registry)),
    )


def build_compilation_context_from_loaded(
    concepts: list[LoadedEntry],
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
    concepts = load_concepts(concepts_root)
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
        return compilation_context_from_legacy_registry({}, claim_files=claim_files, context_ids=context_ids)
    return build_compilation_context_from_paths(
        repo.tree() / "concepts",
        repo.tree() / "forms",
        claim_files=claim_files,
        context_ids=context_ids,
    )


def compilation_context_from_legacy_registry(
    concept_registry: dict[str, dict[str, Any]],
    *,
    claim_files: list[LoadedEntry] | None = None,
    context_ids: set[str] | None = None,
) -> CompilationContext:
    """Adapt the old {lookup-key: concept-dict} registry shape."""
    concept_payloads_by_id: dict[str, Mapping[str, Any]] = {}
    concept_lookup: dict[str, list[str]] = {}
    for key, value in concept_registry.items():
        if not isinstance(value, dict):
            continue
        artifact_id = value.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        concept_payloads_by_id.setdefault(
            artifact_id,
            _freeze_mapping(copy.deepcopy(value)),
        )
        _extend_lookup(concept_lookup, key, artifact_id)
        _extend_lookup(concept_lookup, artifact_id, artifact_id)
    finalized_lookup = _finalize_lookup(concept_lookup)
    legacy_registry = legacy_concept_registry_for_context_payloads(
        concept_payloads_by_id,
        finalized_lookup,
    )
    return CompilationContext(
        form_registry=MappingProxyType({}),
        context_ids=frozenset(context_ids or set()),
        concept_payloads_by_id=MappingProxyType(concept_payloads_by_id),
        concept_lookup=finalized_lookup,
        claim_lookup=(
            MappingProxyType({})
            if claim_files is None
            else _build_claim_lookup(claim_files)
        ),
        cel_registry=_freeze_mapping(build_cel_registry(legacy_registry)),
    )


def legacy_concept_registry_for_context(
    context: CompilationContext,
) -> dict[str, dict[str, Any]]:
    return legacy_concept_registry_for_context_payloads(
        context.concept_payloads_by_id,
        context.concept_lookup,
    )


def legacy_concept_registry_for_context_payloads(
    concept_payloads_by_id: Mapping[str, Mapping[str, Any]],
    concept_lookup: Mapping[str, tuple[str, ...]],
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for artifact_id, payload in concept_payloads_by_id.items():
        registry[artifact_id] = dict(payload)
    for key, candidates in concept_lookup.items():
        if len(candidates) != 1:
            continue
        payload = concept_payloads_by_id.get(candidates[0])
        if payload is None:
            continue
        registry.setdefault(key, dict(payload))
    return registry


def build_legacy_concept_registry_from_paths(
    concepts_dir: Path | KnowledgePath,
    forms_dir: Path | KnowledgePath,
) -> dict[str, dict[str, Any]]:
    context = build_compilation_context_from_paths(concepts_dir, forms_dir)
    return legacy_concept_registry_for_context(context)
