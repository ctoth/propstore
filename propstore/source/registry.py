from __future__ import annotations

import copy
from typing import Any

from propstore.core.concepts import parse_concept_record_document
from propstore.families.identity.concepts import normalize_canonical_concept_payload
from propstore.repository import Repository
from propstore.parameterization_groups import build_groups

from .common import normalize_source_slug
from propstore.families.documents.sources import SourceConceptsDocument


def _derived_concept_artifact_id(handle: str) -> str:
    artifact_id = normalize_canonical_concept_payload(
        {"canonical_name": handle},
        local_handle=normalize_source_slug(handle),
    )["artifact_id"]
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("normalized concept payload did not produce an artifact_id")
    return artifact_id


def load_primary_branch_concepts(repo: Repository) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    primary_tip = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
    if primary_tip is None:
        return {}, {}

    concepts_by_artifact: dict[str, dict[str, Any]] = {}
    handle_to_artifact: dict[str, str] = {}
    for ref in repo.families.concepts.iter(commit=primary_tip):
        document = repo.families.concepts.require(ref, commit=primary_tip)
        concept = dict(parse_concept_record_document(document).to_payload())
        artifact_id = concept.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        concepts_by_artifact[artifact_id] = concept
        canonical_name = concept.get("canonical_name")
        if isinstance(canonical_name, str) and canonical_name:
            handle_to_artifact[canonical_name] = artifact_id
        for alias in concept.get("aliases") or []:
            if not isinstance(alias, dict):
                continue
            alias_name = alias.get("name")
            if isinstance(alias_name, str) and alias_name:
                handle_to_artifact.setdefault(alias_name, artifact_id)
    return concepts_by_artifact, handle_to_artifact


def load_primary_branch_concept_docs(repo: Repository) -> list[dict[str, Any]]:
    primary_tip = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
    if primary_tip is None:
        return []

    docs: list[dict[str, Any]] = []
    for ref in repo.families.concepts.iter(commit=primary_tip):
        document = repo.families.concepts.require(ref, commit=primary_tip)
        docs.append(copy.deepcopy(parse_concept_record_document(document).to_payload()))
    return docs


def primary_branch_concept_match(repo: Repository, handle: str) -> dict[str, str] | None:
    concepts_by_artifact, handle_to_artifact = load_primary_branch_concepts(repo)
    artifact_id = handle_to_artifact.get(handle)
    if artifact_id is None:
        return None
    concept = concepts_by_artifact[artifact_id]
    canonical_name = concept.get("canonical_name")
    if not isinstance(canonical_name, str) or not canonical_name:
        return None
    return {
        "artifact_id": artifact_id,
        "canonical_name": canonical_name,
    }


def projected_source_concepts(
    repo: Repository,
    concepts_doc: SourceConceptsDocument | None,
) -> tuple[list[dict[str, Any]], set[str]]:
    _concepts_by_artifact, primary_handle_to_artifact = load_primary_branch_concepts(repo)
    projected: list[dict[str, Any]] = []
    local_handle_to_artifact: dict[str, str] = {}
    parameterized_artifacts: set[str] = set()
    concept_entries = () if concepts_doc is None else concepts_doc.concepts

    for entry in concept_entries:
        registry_match = entry.registry_match
        artifact_id: str | None = None
        if registry_match is not None and registry_match.artifact_id:
            artifact_id = registry_match.artifact_id
        if artifact_id is None:
            for key in ("local_name", "proposed_name"):
                handle = getattr(entry, key)
                if isinstance(handle, str) and handle in primary_handle_to_artifact:
                    artifact_id = primary_handle_to_artifact[handle]
                    break
        handle_seed = str(entry.proposed_name or entry.local_name or "concept")
        if artifact_id is None:
            artifact_id = _derived_concept_artifact_id(handle_seed)

        projected_entry = {
            "artifact_id": artifact_id,
            "canonical_name": handle_seed,
            "form": str(entry.form or "structural"),
            "parameterization_relationships": [],
        }
        projected.append(projected_entry)
        for key in ("local_name", "proposed_name"):
            handle = getattr(entry, key)
            if isinstance(handle, str) and handle:
                local_handle_to_artifact[handle] = artifact_id

    for projected_entry, raw_entry in zip(projected, concept_entries, strict=False):
        params: list[dict[str, Any]] = []
        for param in raw_entry.parameterization_relationships:
            resolved = copy.deepcopy(param.to_payload())
            inputs: list[str] = []
            for input_ref in resolved.get("inputs", []) or []:
                if not isinstance(input_ref, str) or not input_ref:
                    continue
                if input_ref.startswith("ps:concept:") or input_ref.startswith("tag:"):
                    inputs.append(input_ref)
                    continue
                artifact_id = local_handle_to_artifact.get(input_ref) or primary_handle_to_artifact.get(input_ref)
                if artifact_id is None:
                    artifact_id = _derived_concept_artifact_id(input_ref)
                inputs.append(artifact_id)
            resolved["inputs"] = inputs
            params.append(resolved)
        projected_entry["parameterization_relationships"] = params
        if params:
            parameterized_artifacts.add(str(projected_entry["artifact_id"]))

    return projected, parameterized_artifacts


def parameterization_group_merge_preview(
    primary_branch_concepts: list[dict[str, Any]],
    projected_concepts: list[dict[str, Any]],
    *,
    parameterized_artifacts: set[str],
) -> list[dict[str, Any]]:
    primary_by_artifact: dict[str, dict[str, Any]] = {}
    primary_ids: set[str] = set()
    for concept in primary_branch_concepts:
        if not isinstance(concept, dict):
            continue
        artifact_id = concept.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        primary_by_artifact[artifact_id] = copy.deepcopy(concept)
        primary_ids.add(artifact_id)

    preview_by_artifact = {artifact_id: copy.deepcopy(doc) for artifact_id, doc in primary_by_artifact.items()}
    for concept in projected_concepts:
        if not isinstance(concept, dict):
            continue
        artifact_id = concept.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        if artifact_id in preview_by_artifact:
            merged = copy.deepcopy(preview_by_artifact[artifact_id])
            existing_params = list(merged.get("parameterization_relationships", []) or [])
            for param in concept.get("parameterization_relationships", []) or []:
                if param not in existing_params:
                    existing_params.append(copy.deepcopy(param))
            merged["parameterization_relationships"] = existing_params
            preview_by_artifact[artifact_id] = merged
        else:
            preview_by_artifact[artifact_id] = copy.deepcopy(concept)

    previous_groups = build_groups(list(primary_by_artifact.values()))
    preview_groups = build_groups(list(preview_by_artifact.values()))
    previous_lookup: dict[str, frozenset[str]] = {}
    for group in previous_groups:
        frozen = frozenset(group)
        for member in group:
            previous_lookup[member] = frozen

    merges: list[dict[str, Any]] = []
    for group in sorted(preview_groups, key=lambda members: tuple(sorted(members))):
        existing_members = sorted(member for member in group if member in primary_ids)
        collapsed = {
            previous_lookup.get(member, frozenset({member}))
            for member in existing_members
        }
        if len(collapsed) < 2:
            continue
        merges.append(
            {
                "merged_group": sorted(group),
                "previous_groups": [
                    sorted(previous_group)
                    for previous_group in sorted(collapsed, key=lambda members: tuple(sorted(members)))
                ],
                "introduced_by": sorted(member for member in group if member in parameterized_artifacts),
            }
        )
    return merges


def preview_source_parameterization_group_merges(
    repo: Repository,
    concepts_doc: SourceConceptsDocument | None,
) -> list[dict[str, Any]]:
    primary_branch_concepts = load_primary_branch_concept_docs(repo)
    projected_concepts, parameterized_artifacts = projected_source_concepts(repo, concepts_doc)
    return parameterization_group_merge_preview(
        primary_branch_concepts,
        projected_concepts,
        parameterized_artifacts=parameterized_artifacts,
    )
