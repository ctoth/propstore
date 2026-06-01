from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any


from propstore.families.concepts.declaration import (
    SourceConceptEntryDocument,
)
from propstore.families.identity.concepts import normalize_canonical_concept_payload
from propstore.parameterization_groups import build_groups
from propstore.repository import Repository


@dataclass(frozen=True)
class SourceConceptProjectionReference:
    artifact_id: str
    handles: tuple[str, ...]


def _source_concept_projection_artifact_id(
    record: SourceConceptProjectionReference,
) -> str:
    return record.artifact_id


def _source_concept_projection_handles(
    record: SourceConceptProjectionReference,
) -> tuple[str, ...]:
    return record.handles


def primary_branch_concept_match(
    repo: Repository, handle: str
) -> dict[str, str] | None:
    primary_tip = repo.require_git().branch_sha(
        repo.require_git().primary_branch_name()
    )
    if primary_tip is None:
        return None
    concept_index = repo.families.concepts.reference_index(commit=primary_tip)
    artifact_id = concept_index.resolve_id(handle)
    if artifact_id is None:
        return None
    concept = concept_index.records_by_id.get(artifact_id)
    if concept is None:
        return None
    canonical_name = concept.lexical_entry.canonical_form.written_rep
    if not isinstance(canonical_name, str) or not canonical_name:
        return None
    return {
        "artifact_id": artifact_id,
        "canonical_name": canonical_name,
    }


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

    preview_by_artifact = {
        artifact_id: copy.deepcopy(doc)
        for artifact_id, doc in primary_by_artifact.items()
    }
    for concept in projected_concepts:
        if not isinstance(concept, dict):
            continue
        artifact_id = concept.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        if artifact_id in preview_by_artifact:
            merged = copy.deepcopy(preview_by_artifact[artifact_id])
            existing_params = list(
                merged.get("parameterization_relationships", []) or []
            )
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
                    for previous_group in sorted(
                        collapsed,
                        key=lambda members: tuple(sorted(members)),
                    )
                ],
                "introduced_by": sorted(
                    member for member in group if member in parameterized_artifacts
                ),
            }
        )
    return merges


def preview_source_parameterization_group_merges(
    repo: Repository,
    concepts_doc: tuple[SourceConceptEntryDocument, ...] | None,
) -> list[dict[str, Any]]:
    primary_branch_concepts = load_primary_branch_concept_docs(repo)
    projected_concepts, parameterized_artifacts = projected_source_concepts(
        repo,
        concepts_doc,
    )
    return parameterization_group_merge_preview(
        primary_branch_concepts,
        projected_concepts,
        parameterized_artifacts=parameterized_artifacts,
    )


def _derived_concept_artifact_id(handle: str) -> str:
    artifact_id = normalize_canonical_concept_payload(
        {"canonical_name": handle},
        local_handle=_safe_source_concept_handle(handle),
    )["artifact_id"]
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("normalized concept payload did not produce an artifact_id")
    return artifact_id


def _safe_source_concept_handle(handle: str) -> str:
    cleaned = "".join(
        ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in handle.strip()
    )
    return cleaned.strip("._-") or "source"
