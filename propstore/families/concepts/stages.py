"""Canonical concept dataclasses and boundary conversions."""

from __future__ import annotations
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import msgspec

from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.families.concepts.declaration import (
    ConceptAliasDocument,
    ConceptDocument,
    ConceptFormParametersDocument,
    ConceptIdScan,
    ConceptLogicalIdDocument,
    ConceptRelationshipDocument,
    ParameterizationRelationshipDocument,
)
from propstore.families.concepts.types import ConceptStatus
from propstore.families.concepts.types import ConceptRelationshipType
from quire.documents import document_to_payload, load_document_dir, to_document_builtins
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    LogicalId,
)
from propstore.families.identity.concepts import (
    compute_concept_version_id,
    derive_concept_artifact_id,
    normalize_canonical_concept_payload,
)
from propstore.families.identity.logical_ids import (
    format_logical_id,
    normalize_logical_value,
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


def parse_concept_record(data: Mapping[str, Any]) -> ConceptRecord:
    normalized = normalize_concept_payload(data)

    artifact_id = normalized.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("concept requires artifact_id")

    canonical_name = normalized.get("canonical_name")
    if not isinstance(canonical_name, str) or not canonical_name:
        raise ValueError(f"concept '{artifact_id}' requires canonical_name")

    status = normalized.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError(f"concept '{artifact_id}' requires status")

    definition = normalized.get("definition")
    if not isinstance(definition, str) or not definition:
        raise ValueError(f"concept '{artifact_id}' requires definition")

    form = normalized.get("form")
    if not isinstance(form, str) or not form:
        raise ValueError(f"concept '{artifact_id}' requires form")

    version_id = normalized.get("version_id")
    if not isinstance(version_id, str) or not version_id:
        raise ValueError(f"concept '{artifact_id}' requires version_id")

    logical_ids: list[LogicalId] = []
    for entry in normalized.get("logical_ids", []):
        if not isinstance(entry, Mapping):
            continue
        namespace = entry.get("namespace")
        value = entry.get("value")
        if (
            isinstance(namespace, str)
            and namespace
            and isinstance(value, str)
            and value
        ):
            logical_ids.append(LogicalId(namespace=namespace, value=value))
    if not logical_ids:
        raise ValueError(f"concept '{artifact_id}' requires logical_ids")

    aliases: list[ConceptAlias] = []
    for alias in normalized.get("aliases", []):
        if not isinstance(alias, Mapping):
            continue
        name = alias.get("name")
        if not isinstance(name, str) or not name:
            continue
        aliases.append(
            ConceptAlias(
                name=name,
                source=alias.get("source")
                if isinstance(alias.get("source"), str)
                else None,
                note=alias.get("note") if isinstance(alias.get("note"), str) else None,
            )
        )

    relationships: list[ConceptRelationship] = []
    for relationship in normalized.get("relationships", []):
        if not isinstance(relationship, Mapping):
            continue
        relationship_type = relationship.get("type")
        target = relationship.get("target")
        if not isinstance(relationship_type, str) or not relationship_type:
            continue
        if not isinstance(target, str) or not target:
            continue
        relationships.append(
            ConceptRelationship(
                relationship_type=ConceptRelationshipType(relationship_type),
                target=ConceptId(target),
                conditions=to_cel_exprs(_string_list(relationship.get("conditions"))),
                note=relationship.get("note")
                if isinstance(relationship.get("note"), str)
                else None,
            )
        )

    parameterizations: list[ParameterizationSpec] = []
    for parameterization in normalized.get("parameterization_relationships", []):
        if not isinstance(parameterization, Mapping):
            continue
        raw_inputs = parameterization.get("inputs")
        if not isinstance(raw_inputs, Sequence) or isinstance(raw_inputs, str):
            continue
        inputs = tuple(
            ConceptId(value) for value in raw_inputs if isinstance(value, str) and value
        )
        if not inputs:
            continue
        raw_canonical_claim = parameterization.get("canonical_claim")
        parameterizations.append(
            ParameterizationSpec(
                inputs=inputs,
                formula=parameterization.get("formula")
                if isinstance(parameterization.get("formula"), str)
                else None,
                sympy=parameterization.get("sympy")
                if isinstance(parameterization.get("sympy"), str)
                else None,
                exactness=parameterization.get("exactness")
                if isinstance(parameterization.get("exactness"), str)
                else None,
                conditions=to_cel_exprs(
                    _string_list(parameterization.get("conditions"))
                ),
                source=parameterization.get("source")
                if isinstance(parameterization.get("source"), str)
                else None,
                bidirectional=(
                    parameterization.get("bidirectional")
                    if isinstance(parameterization.get("bidirectional"), bool)
                    else None
                ),
                canonical_claim=(
                    ClaimId(raw_canonical_claim)
                    if isinstance(raw_canonical_claim, str) and raw_canonical_claim
                    else None
                ),
            )
        )

    range_value = normalized.get("range")
    parsed_range: tuple[float, float] | None = None
    if (
        isinstance(range_value, Sequence)
        and not isinstance(range_value, str)
        and len(range_value) >= 2
    ):
        start, end = range_value[0], range_value[1]
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            parsed_range = (float(start), float(end))

    form_parameters = normalized.get("form_parameters")
    parsed_form_parameters = _mapping_to_builtin_dict(form_parameters)

    replaced_by = normalized.get("replaced_by")
    parsed_replaced_by = (
        ConceptId(replaced_by) if isinstance(replaced_by, str) and replaced_by else None
    )

    return ConceptRecord(
        artifact_id=ConceptId(artifact_id),
        canonical_name=canonical_name,
        status=ConceptStatus(status),
        definition=definition,
        form=form,
        logical_ids=tuple(logical_ids),
        version_id=version_id,
        domain=normalized.get("domain")
        if isinstance(normalized.get("domain"), str)
        else None,
        definition_source=(
            normalized.get("definition_source")
            if isinstance(normalized.get("definition_source"), str)
            else None
        ),
        form_parameters=parsed_form_parameters,
        range=parsed_range,
        aliases=tuple(aliases),
        relationships=tuple(relationships),
        parameterizations=tuple(parameterizations),
        replaced_by=parsed_replaced_by,
        created_date=normalized.get("created_date")
        if isinstance(normalized.get("created_date"), str)
        else None,
        last_modified=normalized.get("last_modified")
        if isinstance(normalized.get("last_modified"), str)
        else None,
        notes=normalized.get("notes")
        if isinstance(normalized.get("notes"), str)
        else None,
    )


def render_concept_document(document: ConceptDocument) -> str:
    return encode_concept_document(document).decode("utf-8").rstrip()


def parse_concept_record_document(data: ConceptDocument) -> ConceptRecord:
    return parse_concept_record(concept_document_to_record_payload(data))


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


def normalize_loaded_concepts(
    concepts: Sequence[LoadedDocument[ConceptDocument]],
) -> list[LoadedConcept]:
    raw_to_artifact: dict[str, str] = {}
    pending: list[
        tuple[LoadedDocument[ConceptDocument], dict[str, Any], str | None]
    ] = []

    for concept in concepts:
        payload = concept_document_to_record_payload(concept.document)
        raw_id = payload.get("id") if isinstance(payload.get("id"), str) else None
        normalized = normalize_concept_payload(payload)
        artifact_id = normalized.get("artifact_id")
        if raw_id is not None and isinstance(artifact_id, str):
            raw_to_artifact[raw_id] = artifact_id
        pending.append((concept, normalized, raw_id))

    normalized_concepts: list[LoadedConcept] = []
    for concept, normalized, raw_id in pending:
        rewritten = rewrite_concept_payload_refs(
            normalized,
            concept_ref_map=raw_to_artifact,
        )
        normalized_concepts.append(
            LoadedConcept(
                filename=concept.filename,
                source_path=concept.artifact_path,
                knowledge_root=concept.store_root,
                record=parse_concept_record(rewritten),
                document=concept.document,
                source_local_id=raw_id,
            )
        )
    return normalized_concepts


def primary_logical_id(record: ConceptRecord) -> str | None:
    return record.primary_logical_id


def format_loaded_concept_logical_ids(record: ConceptRecord) -> list[dict[str, str]]:
    return [logical_id.to_payload() for logical_id in record.logical_ids]


def load_concepts(concepts_root: KnowledgePath | None) -> list[LoadedConcept]:
    """Load canonical concept artifacts from a concept subtree."""

    loaded_documents = load_document_dir(concepts_root, ConceptDocument)
    return normalize_loaded_concepts(loaded_documents)
