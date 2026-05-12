from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from quire.references import FamilyReferenceIndex

from propstore.families.concepts.documents import ConceptDocument
from propstore.families.concepts.stages import parse_concept_record_document
from propstore.families.identity.concepts import normalize_canonical_concept_payload
from propstore.repository import Repository
from propstore.parameterization_groups import build_groups

from .common import normalize_source_slug
from propstore.families.documents.sources import SourceConceptsDocument


@dataclass(frozen=True)
class SourceConceptProjectionReference:
    artifact_id: str
    handles: tuple[str, ...]


def _derived_concept_artifact_id(handle: str) -> str:
    artifact_id = normalize_canonical_concept_payload(
        {"canonical_name": handle},
        local_handle=normalize_source_slug(handle),
    )["artifact_id"]
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("normalized concept payload did not produce an artifact_id")
    return artifact_id


def load_primary_branch_concepts(repo: Repository) -> dict[str, dict[str, Any]]:
    primary_tip = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
    if primary_tip is None:
        return {}

    concepts_by_artifact: dict[str, dict[str, Any]] = {}

    for handle in repo.families.concepts.iter_handles(commit=primary_tip):
        document = handle.document
        concept = dict(parse_concept_record_document(document).to_payload())
        artifact_id = concept.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        concepts_by_artifact[artifact_id] = concept
    return concepts_by_artifact


def load_primary_branch_concept_docs(repo: Repository) -> list[dict[str, Any]]:
    primary_tip = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
    if primary_tip is None:
        return []

    docs: list[dict[str, Any]] = []
    for handle in repo.families.concepts.iter_handles(commit=primary_tip):
        document = handle.document
        docs.append(copy.deepcopy(parse_concept_record_document(document).to_payload()))
    return docs


def primary_branch_concept_match(repo: Repository, handle: str) -> dict[str, str] | None:
    primary_tip = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
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


def projected_source_concepts(
    repo: Repository,
    concepts_doc: SourceConceptsDocument | None,
) -> tuple[list[dict[str, Any]], set[str]]:
    primary_tip = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
    primary_concept_index: FamilyReferenceIndex[ConceptDocument]
    if primary_tip is None:
        primary_concept_index = FamilyReferenceIndex.from_records(
            (),
            family="concepts",
            artifact_id=lambda _record: None,
        )
    else:
        primary_concept_index = repo.families.concepts.reference_index(commit=primary_tip)
    projected: list[dict[str, Any]] = []
    projected_reference_records: list[SourceConceptProjectionReference] = []
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
                if not isinstance(handle, str) or not handle:
                    continue
                resolved_artifact_id = primary_concept_index.resolve_id(handle)
                if resolved_artifact_id is not None:
                    artifact_id = resolved_artifact_id
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
        handles: list[str] = []
        for key in ("local_name", "proposed_name"):
            handle = getattr(entry, key)
            if isinstance(handle, str) and handle:
                handles.append(handle)
        projected_reference_records.append(
            SourceConceptProjectionReference(
                artifact_id=artifact_id,
                handles=tuple(handles),
            )
        )

    source_local_concept_index = FamilyReferenceIndex.from_records(
        projected_reference_records,
        family="source_concepts",
        artifact_id=lambda record: record.artifact_id,
        keys=(lambda record: record.handles,),
    )

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
                artifact_id = source_local_concept_index.resolve_id(input_ref)
                if artifact_id is None:
                    artifact_id = primary_concept_index.resolve_id(input_ref)
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
