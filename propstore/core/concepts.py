"""Canonical concept dataclasses and boundary conversions."""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import msgspec

from propstore.document_schema import DocumentStruct
from propstore.core.id_types import ClaimId, ConceptId, LogicalId, to_claim_id, to_concept_id
from propstore.identity import (
    compute_concept_version_id,
    derive_concept_artifact_id,
    format_logical_id,
    normalize_logical_value,
)
from propstore.knowledge_path import KnowledgePath
from propstore.loaded import LoadedDocument, LoadedEntry


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


class ConceptLogicalIdDocument(DocumentStruct):
    namespace: str
    value: str


class ConceptAliasDocument(DocumentStruct):
    name: str
    source: str | None = None
    note: str | None = None


class ConceptRelationshipDocument(DocumentStruct):
    type: str
    target: str
    source: str | None = None
    conditions: tuple[str, ...] = ()
    note: str | None = None


class ConceptFormParametersDocument(DocumentStruct):
    construction: str | None = None
    extensible: bool | None = None
    note: str | None = None
    reference: str | None = None
    values: tuple[str, ...] | None = None


class ParameterizationRelationshipDocument(DocumentStruct):
    inputs: tuple[str, ...]
    formula: str | None = None
    exactness: str | None = None
    source: str | None = None
    bidirectional: bool | None = None
    sympy: str | None = None
    conditions: tuple[str, ...] = ()
    note: str | None = None
    canonical_claim: str | None = None
    fit_statistics: str | None = None


class ConceptDocument(DocumentStruct):
    artifact_id: str
    logical_ids: tuple[ConceptLogicalIdDocument, ...]
    version_id: str
    canonical_name: str
    status: str
    definition: str
    form: str
    aliases: tuple[ConceptAliasDocument, ...] = ()
    created_date: str | None = None
    definition_source: str | None = None
    domain: str | None = None
    form_parameters: ConceptFormParametersDocument | None = None
    last_modified: str | None = None
    notes: str | None = None
    parameterization_relationships: tuple[ParameterizationRelationshipDocument, ...] = ()
    range: tuple[float, float] | None = None
    relationships: tuple[ConceptRelationshipDocument, ...] = ()
    replaced_by: str | None = None


class ConceptIdScanDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=False):
    """Partial concept projection for ID scans over repo-controlled files."""

    id: str | None = None
    artifact_id: str | None = None
    logical_ids: tuple[ConceptLogicalIdDocument, ...] = ()

@dataclass(frozen=True)
class ConceptAlias:
    name: str
    source: str | None = None
    note: str | None = None

    def to_payload(self) -> dict[str, str]:
        payload: dict[str, str] = {"name": self.name}
        if self.source is not None:
            payload["source"] = self.source
        if self.note is not None:
            payload["note"] = self.note
        return payload


@dataclass(frozen=True)
class ConceptRelationship:
    relationship_type: str
    target: ConceptId
    conditions: tuple[str, ...] = ()
    note: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.relationship_type,
            "target": str(self.target),
        }
        if self.conditions:
            payload["conditions"] = list(self.conditions)
        if self.note is not None:
            payload["note"] = self.note
        return payload


@dataclass(frozen=True)
class ParameterizationSpec:
    inputs: tuple[ConceptId, ...]
    formula: str | None = None
    sympy: str | None = None
    exactness: str | None = None
    conditions: tuple[str, ...] = ()
    source: str | None = None
    bidirectional: bool | None = None
    canonical_claim: ClaimId | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "inputs": [str(concept_id) for concept_id in self.inputs],
        }
        if self.formula is not None:
            payload["formula"] = self.formula
        if self.sympy is not None:
            payload["sympy"] = self.sympy
        if self.exactness is not None:
            payload["exactness"] = self.exactness
        if self.conditions:
            payload["conditions"] = list(self.conditions)
        if self.source is not None:
            payload["source"] = self.source
        if self.bidirectional is not None:
            payload["bidirectional"] = self.bidirectional
        if self.canonical_claim is not None:
            payload["canonical_claim"] = str(self.canonical_claim)
        return payload


@dataclass(frozen=True)
class ConceptRecord:
    artifact_id: ConceptId
    canonical_name: str
    status: str
    definition: str
    form: str
    logical_ids: tuple[LogicalId, ...]
    version_id: str
    domain: str | None = None
    definition_source: str | None = None
    form_parameters: dict[str, Any] | None = None
    range: tuple[float, float] | None = None
    aliases: tuple[ConceptAlias, ...] = ()
    relationships: tuple[ConceptRelationship, ...] = ()
    parameterizations: tuple[ParameterizationSpec, ...] = ()
    replaced_by: ConceptId | None = None
    created_date: str | None = None
    last_modified: str | None = None
    notes: str | None = None

    @property
    def primary_logical_id(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].formatted

    def reference_keys(self) -> tuple[str, ...]:
        seen: set[str] = set()
        keys: list[str] = []

        def add(candidate: object) -> None:
            if not isinstance(candidate, str) or not candidate or candidate in seen:
                return
            seen.add(candidate)
            keys.append(candidate)

        add(self.artifact_id)
        add(self.canonical_name)
        for logical_id in self.logical_ids:
            add(logical_id.formatted)
            add(logical_id.value)
        for alias in self.aliases:
            add(alias.name)
        return tuple(keys)

    def to_payload(self) -> dict[str, Any]:
        form_parameters = None
        if self.form_parameters is not None:
            form_parameters = msgspec.to_builtins(self.form_parameters)
        payload: dict[str, Any] = {
            "artifact_id": str(self.artifact_id),
            "canonical_name": self.canonical_name,
            "status": self.status,
            "definition": self.definition,
            "form": self.form,
            "logical_ids": [logical_id.to_payload() for logical_id in self.logical_ids],
            "version_id": self.version_id,
        }
        if self.domain is not None:
            payload["domain"] = self.domain
        if self.definition_source is not None:
            payload["definition_source"] = self.definition_source
        if form_parameters:
            payload["form_parameters"] = form_parameters
        if self.range is not None:
            payload["range"] = [self.range[0], self.range[1]]
        if self.aliases:
            payload["aliases"] = [alias.to_payload() for alias in self.aliases]
        if self.relationships:
            payload["relationships"] = [
                relationship.to_payload()
                for relationship in self.relationships
            ]
        if self.parameterizations:
            payload["parameterization_relationships"] = [
                parameterization.to_payload()
                for parameterization in self.parameterizations
            ]
        if self.replaced_by is not None:
            payload["replaced_by"] = str(self.replaced_by)
        if self.created_date is not None:
            payload["created_date"] = self.created_date
        if self.last_modified is not None:
            payload["last_modified"] = self.last_modified
        if self.notes is not None:
            payload["notes"] = self.notes
        return payload


@dataclass(frozen=True)
class LoadedConcept:
    filename: str
    source_path: KnowledgePath | None
    knowledge_root: KnowledgePath | None
    record: ConceptRecord
    source_local_id: str | None = None

    @property
    def data(self) -> dict[str, Any]:
        return self.record.to_payload()

    def to_loaded_entry(self) -> LoadedEntry:
        return LoadedEntry(
            filename=self.filename,
            source_path=self.source_path,
            knowledge_root=self.knowledge_root,
            data=self.record.to_payload(),
        )


def normalize_concept_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(data)

    local_seed = str(
        normalized.get("id")
        or normalized.get("canonical_name")
        or normalized.get("artifact_id")
        or "concept"
    )
    canonical_name = normalized.get("canonical_name")
    primary_namespace = str(normalized.get("domain") or "propstore")
    primary_value = normalize_logical_value(str(canonical_name or local_seed))

    logical_ids = normalized.get("logical_ids")
    normalized_logical_ids: list[dict[str, str]] = []
    if isinstance(logical_ids, list):
        for entry in logical_ids:
            if not isinstance(entry, Mapping):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if isinstance(namespace, str) and namespace and isinstance(value, str) and value:
                normalized_logical_ids.append({"namespace": namespace, "value": value})

    if not normalized_logical_ids:
        normalized_logical_ids = [{"namespace": primary_namespace, "value": primary_value}]
        propstore_local = normalize_logical_value(local_seed)
        if primary_namespace != "propstore" or propstore_local != primary_value:
            normalized_logical_ids.append({"namespace": "propstore", "value": propstore_local})
    normalized["logical_ids"] = normalized_logical_ids

    artifact_id = normalized.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        normalized["artifact_id"] = derive_concept_artifact_id(
            "propstore",
            normalize_logical_value(local_seed),
        )

    version_id = normalized.get("version_id")
    if not isinstance(version_id, str) or not version_id:
        version_payload = {
            key: value
            for key, value in normalized.items()
            if not str(key).startswith("_")
        }
        normalized["version_id"] = compute_concept_version_id(version_payload)

    return normalized


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
        if isinstance(namespace, str) and namespace and isinstance(value, str) and value:
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
                source=alias.get("source") if isinstance(alias.get("source"), str) else None,
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
                relationship_type=relationship_type,
                target=to_concept_id(target),
                conditions=_string_list(relationship.get("conditions")),
                note=relationship.get("note") if isinstance(relationship.get("note"), str) else None,
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
            to_concept_id(value)
            for value in raw_inputs
            if isinstance(value, str) and value
        )
        if not inputs:
            continue
        raw_canonical_claim = parameterization.get("canonical_claim")
        parameterizations.append(
            ParameterizationSpec(
                inputs=inputs,
                formula=parameterization.get("formula") if isinstance(parameterization.get("formula"), str) else None,
                sympy=parameterization.get("sympy") if isinstance(parameterization.get("sympy"), str) else None,
                exactness=parameterization.get("exactness") if isinstance(parameterization.get("exactness"), str) else None,
                conditions=_string_list(parameterization.get("conditions")),
                source=parameterization.get("source") if isinstance(parameterization.get("source"), str) else None,
                bidirectional=(
                    parameterization.get("bidirectional")
                    if isinstance(parameterization.get("bidirectional"), bool)
                    else None
                ),
                canonical_claim=(
                    to_claim_id(raw_canonical_claim)
                    if isinstance(raw_canonical_claim, str) and raw_canonical_claim
                    else None
                ),
            )
        )

    range_value = normalized.get("range")
    parsed_range: tuple[float, float] | None = None
    if isinstance(range_value, Sequence) and not isinstance(range_value, str) and len(range_value) >= 2:
        start, end = range_value[0], range_value[1]
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            parsed_range = (float(start), float(end))

    form_parameters = normalized.get("form_parameters")
    parsed_form_parameters = copy.deepcopy(form_parameters) if isinstance(form_parameters, Mapping) else None

    replaced_by = normalized.get("replaced_by")
    parsed_replaced_by = (
        to_concept_id(replaced_by)
        if isinstance(replaced_by, str) and replaced_by
        else None
    )

    return ConceptRecord(
        artifact_id=to_concept_id(artifact_id),
        canonical_name=canonical_name,
        status=status,
        definition=definition,
        form=form,
        logical_ids=tuple(logical_ids),
        version_id=version_id,
        domain=normalized.get("domain") if isinstance(normalized.get("domain"), str) else None,
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
        created_date=normalized.get("created_date") if isinstance(normalized.get("created_date"), str) else None,
        last_modified=normalized.get("last_modified") if isinstance(normalized.get("last_modified"), str) else None,
        notes=normalized.get("notes") if isinstance(normalized.get("notes"), str) else None,
    )


def parse_concept_record_document(data: ConceptDocument) -> ConceptRecord:
    form_parameters = None
    if data.form_parameters is not None:
        form_parameters = {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in msgspec.to_builtins(data.form_parameters).items()
            if value is not None
        }

    return ConceptRecord(
        artifact_id=to_concept_id(data.artifact_id),
        canonical_name=data.canonical_name,
        status=data.status,
        definition=data.definition,
        form=data.form,
        logical_ids=tuple(
            LogicalId(namespace=entry.namespace, value=entry.value)
            for entry in data.logical_ids
        ),
        version_id=data.version_id,
        domain=data.domain,
        definition_source=data.definition_source,
        form_parameters=form_parameters,
        range=None if data.range is None else (float(data.range[0]), float(data.range[1])),
        aliases=tuple(
            ConceptAlias(name=alias.name, source=alias.source, note=alias.note)
            for alias in data.aliases
        ),
        relationships=tuple(
            ConceptRelationship(
                relationship_type=relationship.type,
                target=to_concept_id(relationship.target),
                conditions=tuple(relationship.conditions),
                note=relationship.note,
            )
            for relationship in data.relationships
        ),
        parameterizations=tuple(
            ParameterizationSpec(
                inputs=tuple(to_concept_id(value) for value in parameterization.inputs),
                formula=parameterization.formula,
                sympy=parameterization.sympy,
                exactness=parameterization.exactness,
                conditions=tuple(parameterization.conditions),
                source=parameterization.source,
                bidirectional=parameterization.bidirectional,
                canonical_claim=(
                    None
                    if parameterization.canonical_claim is None
                    else to_claim_id(parameterization.canonical_claim)
                ),
            )
            for parameterization in data.parameterization_relationships
        ),
        replaced_by=(
            None if data.replaced_by is None else to_concept_id(data.replaced_by)
        ),
        created_date=data.created_date,
        last_modified=data.last_modified,
        notes=data.notes,
    )


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


def _rewrite_concept_reference(
    value: object,
    concept_ref_map: Mapping[str, str],
) -> object:
    if not isinstance(value, str):
        return value
    return concept_ref_map.get(value, value)


def rewrite_concept_payload_refs(
    data: Mapping[str, Any],
    *,
    concept_ref_map: Mapping[str, str],
) -> dict[str, Any]:
    rewritten = dict(data)

    replaced_by = rewritten.get("replaced_by")
    if replaced_by is not None:
        rewritten["replaced_by"] = _rewrite_concept_reference(replaced_by, concept_ref_map)

    relationships = rewritten.get("relationships")
    if isinstance(relationships, list):
        updated_relationships: list[Any] = []
        for relationship in relationships:
            if not isinstance(relationship, Mapping):
                updated_relationships.append(relationship)
                continue
            updated = dict(relationship)
            updated["target"] = _rewrite_concept_reference(updated.get("target"), concept_ref_map)
            updated_relationships.append(updated)
        rewritten["relationships"] = updated_relationships

    parameterizations = rewritten.get("parameterization_relationships")
    if isinstance(parameterizations, list):
        updated_parameterizations: list[Any] = []
        for parameterization in parameterizations:
            if not isinstance(parameterization, Mapping):
                updated_parameterizations.append(parameterization)
                continue
            updated = dict(parameterization)
            inputs = updated.get("inputs")
            if isinstance(inputs, Sequence) and not isinstance(inputs, str):
                updated["inputs"] = [
                    _rewrite_concept_reference(input_value, concept_ref_map)
                    for input_value in inputs
                ]
            updated_parameterizations.append(updated)
        rewritten["parameterization_relationships"] = updated_parameterizations

    rewritten["version_id"] = compute_concept_version_id(rewritten)
    return rewritten


def normalize_loaded_concepts(
    concepts: Sequence[LoadedDocument[ConceptDocument]],
) -> list[LoadedConcept]:
    return [
        LoadedConcept(
            filename=concept.filename,
            source_path=concept.source_path,
            knowledge_root=concept.knowledge_root,
            record=parse_concept_record_document(concept.document),
        )
        for concept in concepts
    ]


def concept_payload_registry(
    concepts: Iterable[LoadedConcept],
    *,
    include_source_local_ids: bool = False,
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for concept in concepts:
        payload = concept.record.to_payload()
        registry[str(concept.record.artifact_id)] = payload
        for key in concept.record.reference_keys():
            registry.setdefault(key, payload)
        if include_source_local_ids and concept.source_local_id is not None:
            registry.setdefault(concept.source_local_id, payload)
    return registry


def primary_logical_id(record: ConceptRecord) -> str | None:
    return record.primary_logical_id


def format_loaded_concept_logical_ids(record: ConceptRecord) -> list[dict[str, str]]:
    return [logical_id.to_payload() for logical_id in record.logical_ids]
