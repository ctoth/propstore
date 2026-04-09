"""Connected-component analysis for concept parameterization graphs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from propstore.core.concepts import ConceptRecord, LoadedConcept


ConceptGroupInput = ConceptRecord | LoadedConcept | Mapping[str, Any]


def _unwrap_concept(concept: ConceptGroupInput) -> ConceptRecord | Mapping[str, Any]:
    if isinstance(concept, LoadedConcept):
        return concept.record
    return concept


def _concept_candidates(concept: ConceptRecord | Mapping[str, Any]) -> set[str]:
    if isinstance(concept, ConceptRecord):
        return set(concept.reference_keys())

    candidates: set[str] = set()
    artifact_id = concept.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        candidates.add(artifact_id)
    canonical_name = concept.get("canonical_name")
    if isinstance(canonical_name, str) and canonical_name:
        candidates.add(canonical_name)
    for logical_id in concept.get("logical_ids", []) or []:
        if not isinstance(logical_id, Mapping):
            continue
        namespace = logical_id.get("namespace")
        value = logical_id.get("value")
        if isinstance(namespace, str) and isinstance(value, str) and namespace and value:
            candidates.add(f"{namespace}:{value}")
            candidates.add(value)
    for alias in concept.get("aliases", []) or []:
        if not isinstance(alias, Mapping):
            continue
        alias_name = alias.get("name")
        if isinstance(alias_name, str) and alias_name:
            candidates.add(alias_name)
    return candidates


def _concept_artifact_id(concept: ConceptRecord | Mapping[str, Any]) -> str | None:
    if isinstance(concept, ConceptRecord):
        return str(concept.artifact_id)
    artifact_id = concept.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        return artifact_id
    return None


def _parameterization_inputs(concept: ConceptRecord | Mapping[str, Any]) -> tuple[str, ...]:
    if isinstance(concept, ConceptRecord):
        inputs: list[str] = []
        for parameterization in concept.parameterizations:
            inputs.extend(str(input_id) for input_id in parameterization.inputs)
        return tuple(inputs)

    inputs: list[str] = []
    for parameterization in concept.get("parameterization_relationships", []) or []:
        if not isinstance(parameterization, Mapping):
            continue
        raw_inputs = parameterization.get("inputs")
        if not isinstance(raw_inputs, Sequence) or isinstance(raw_inputs, str):
            continue
        inputs.extend(
            value
            for value in raw_inputs
            if isinstance(value, str) and value
        )
    return tuple(inputs)


def build_groups(concepts: Sequence[ConceptGroupInput]) -> list[set[str]]:
    """Find connected components among concepts via parameterization relationships."""
    if not concepts:
        return []

    unwrapped = [_unwrap_concept(concept) for concept in concepts]

    all_ids: set[str] = set()
    alias_to_id: dict[str, str] = {}
    for concept in unwrapped:
        concept_id = _concept_artifact_id(concept)
        if concept_id is None:
            continue
        all_ids.add(concept_id)
        for candidate in _concept_candidates(concept):
            alias_to_id.setdefault(candidate, concept_id)

    parent: dict[str, str] = {concept_id: concept_id for concept_id in all_ids}
    rank: dict[str, int] = {concept_id: 0 for concept_id in all_ids}

    def find(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        if rank[left_root] < rank[right_root]:
            left_root, right_root = right_root, left_root
        parent[right_root] = left_root
        if rank[left_root] == rank[right_root]:
            rank[left_root] += 1

    for concept in unwrapped:
        concept_id = _concept_artifact_id(concept)
        if concept_id is None:
            continue
        for input_id in _parameterization_inputs(concept):
            resolved_input_id = alias_to_id.get(input_id, input_id)
            if resolved_input_id in all_ids:
                union(concept_id, resolved_input_id)

    components: dict[str, set[str]] = {}
    for concept_id in all_ids:
        root = find(concept_id)
        components.setdefault(root, set()).add(concept_id)

    return list(components.values())
