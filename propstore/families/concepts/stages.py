"""Concept semantic stage objects."""

from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

from propstore.families.concepts.declaration import (
    ConceptDocument,
)
from propstore.families.identity.logical_ids import format_logical_id
from quire.tree_path import TreePath as KnowledgePath
from quire.documents import LoadedDocument, load_document_dir


class ConceptStage(StrEnum):
    AUTHORED = "concept.authored"
    NORMALIZED = "concept.normalized"
    BOUND = "concept.bound"
    CHECKED = "concept.checked"


@dataclass(frozen=True)
class ConceptAuthoredSet:
    concepts: tuple[LoadedDocument[ConceptDocument], ...]


@dataclass(frozen=True)
class ConceptNormalizedSet:
    concepts: tuple[LoadedDocument[ConceptDocument], ...]


@dataclass(frozen=True)
class ConceptBoundRegistry:
    concepts: tuple[LoadedDocument[ConceptDocument], ...]
    registry: dict[str, ConceptDocument]


@dataclass(frozen=True)
class ConceptCheckedRegistry:
    concepts: tuple[LoadedDocument[ConceptDocument], ...]
    registry: dict[str, ConceptDocument]


def concept_reference_keys(
    document: ConceptDocument,
) -> tuple[str, ...]:
    seen: set[str] = set()
    keys: list[str] = []

    def add(candidate: object) -> None:
        if not isinstance(candidate, str) or not candidate or candidate in seen:
            return
        seen.add(candidate)
        keys.append(candidate)

    add(document.artifact_id)
    add(document.lexical_entry.canonical_form.written_rep)
    add(document.ontology_reference.uri)
    for logical_id in document.logical_ids:
        add(logical_id.value)
        add(
            format_logical_id(
                {"namespace": logical_id.namespace, "value": logical_id.value}
            )
        )
    for alias in document.aliases:
        add(alias.name)
    for sense in document.lexical_entry.senses:
        add(sense.reference.uri)
    return tuple(keys)


def concept_symbol_candidates(document: ConceptDocument) -> tuple[str, ...]:
    return concept_reference_keys(document)


def primary_logical_id(document: ConceptDocument) -> str | None:
    if not document.logical_ids:
        return None
    logical_id = document.logical_ids[0]
    return format_logical_id(
        {"namespace": logical_id.namespace, "value": logical_id.value}
    )


def load_concepts(
    concepts_root: KnowledgePath | None,
) -> list[LoadedDocument[ConceptDocument]]:
    """Load canonical concept artifacts from a concept subtree."""
    return load_document_dir(concepts_root, ConceptDocument)
