"""Canonical concept dataclasses and boundary conversions."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


from propstore.cel_types import to_cel_exprs
from propstore.families.concepts.declaration import (
    ConceptDocument,
)
from propstore.families.concepts.types import ConceptStatus
from propstore.families.concepts.types import ConceptRelationshipType
from quire.documents import load_document_dir, to_document_builtins
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    LogicalId,
)
from quire.tree_path import TreePath as KnowledgePath
from quire.documents import LoadedDocument


class ConceptStage(StrEnum):
    AUTHORED = "concept.authored"
    NORMALIZED = "concept.normalized"
    BOUND = "concept.bound"
    CHECKED = "concept.checked"


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _mapping_to_builtin_dict(value: object) -> dict[str, Any] | None:
    builtins_value = to_document_builtins(value)
    if not isinstance(builtins_value, dict):
        return None
    pruned = _prune_none_values(builtins_value)
    return pruned if isinstance(pruned, dict) else None


def _prune_none_values(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            key: _prune_none_values(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_prune_none_values(item) for item in value]
    if isinstance(value, tuple):
        return [_prune_none_values(item) for item in value]
    return value


@dataclass(frozen=True)
class LoadedConcept:
    filename: str
    source_path: KnowledgePath | None
    knowledge_root: KnowledgePath | None
    document: ConceptDocument
    source_local_id: str | None = None


@dataclass(frozen=True)
class ConceptAuthoredSet:
    concepts: tuple[LoadedConcept, ...]


@dataclass(frozen=True)
class ConceptNormalizedSet:
    concepts: tuple[LoadedConcept, ...]


@dataclass(frozen=True)
class ConceptBoundRegistry:
    concepts: tuple[LoadedConcept, ...]
    registry: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ConceptCheckedRegistry:
    concepts: tuple[LoadedConcept, ...]
    registry: dict[str, dict[str, Any]]


def render_concept_document(document: ConceptDocument) -> str:
    return encode_concept_document(document).decode("utf-8").rstrip()


def concept_reference_keys(
    record: ConceptRecord,
    *,
    source_local_id: str | None = None,
) -> tuple[str, ...]:
    seen: set[str] = set()
    keys: list[str] = []

    def add(candidate: object) -> None:
        if not isinstance(candidate, str) or not candidate or candidate in seen:
            return
        seen.add(candidate)
        keys.append(candidate)

    add(source_local_id)
    for key in record.reference_keys():
        add(key)
    return tuple(keys)


def concept_symbol_candidates(record: ConceptRecord) -> tuple[str, ...]:
    return record.reference_keys()


def _rewrite_concept_reference(
    value: object,
    concept_ref_map: Mapping[str, str],
) -> object:
    if not isinstance(value, str):
        return value
    return concept_ref_map.get(value, value)


def primary_logical_id(record: ConceptRecord) -> str | None:
    return record.primary_logical_id


def load_concepts(concepts_root: KnowledgePath | None) -> list[LoadedConcept]:
    """Load canonical concept artifacts from a concept subtree."""

    loaded_documents = load_document_dir(concepts_root, ConceptDocument)
    return normalize_loaded_concepts(loaded_documents)
