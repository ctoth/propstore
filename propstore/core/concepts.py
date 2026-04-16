"""Canonical concept dataclasses and boundary conversions."""

from __future__ import annotations
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.artifacts.documents.concepts import (
    ConceptAliasDocument,
    ConceptDocument,
    ConceptFormParametersDocument,
    ConceptIdScanDocument,
    ConceptLogicalIdDocument,
    ConceptRelationshipDocument,
    ParameterizationRelationshipDocument,
)
from propstore.core.concept_status import ConceptStatus, coerce_concept_status
from propstore.core.concept_relationship_types import (
    ConceptRelationshipType,
    coerce_concept_relationship_type,
)
from propstore.artifacts.schema import load_document, to_document_builtins
from propstore.core.exactness_types import Exactness, coerce_exactness
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

def _mapping_to_builtin_dict(value: object) -> dict[str, Any] | None:
    builtins_value = to_document_builtins(value)
    if not isinstance(builtins_value, dict):
        return None
    return builtins_value


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
    relationship_type: ConceptRelationshipType
    target: ConceptId
    conditions: tuple[CelExpr, ...] = ()
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relationship_type",
            coerce_concept_relationship_type(self.relationship_type),
        )
        object.__setattr__(self, "conditions", to_cel_exprs(self.conditions))

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.relationship_type.value,
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
    exactness: Exactness | None = None
    conditions: tuple[CelExpr, ...] = ()
    source: str | None = None
    bidirectional: bool | None = None
    canonical_claim: ClaimId | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "exactness", coerce_exactness(self.exactness))
        object.__setattr__(self, "conditions", to_cel_exprs(self.conditions))

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "inputs": [str(concept_id) for concept_id in self.inputs],
        }
        if self.formula is not None:
            payload["formula"] = self.formula
        if self.sympy is not None:
            payload["sympy"] = self.sympy
        if self.exactness is not None:
            payload["exactness"] = self.exactness.value
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
    status: ConceptStatus
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", coerce_concept_status(self.status))

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
        form_parameters = _mapping_to_builtin_dict(self.form_parameters)
        payload: dict[str, Any] = {
            "artifact_id": str(self.artifact_id),
            "canonical_name": self.canonical_name,
            "status": self.status.value,
            "definition": self.definition,
            "form": self.form,
            "logical_ids": [logical_id.to_payload() for logical_id in self.logical_ids],
            "version_id": self.version_id,
        }
        if self.domain is not None:
            payload["domain"] = self.domain
        if self.definition_source is not None:
            payload["definition_source"] = self.definition_source
        if form_parameters is not None:
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
        normalized.pop("id", None)
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
    parsed_form_parameters = _mapping_to_builtin_dict(form_parameters)

    replaced_by = normalized.get("replaced_by")
    parsed_replaced_by = (
        to_concept_id(replaced_by)
        if isinstance(replaced_by, str) and replaced_by
        else None
    )

    return ConceptRecord(
        artifact_id=to_concept_id(artifact_id),
        canonical_name=canonical_name,
        status=coerce_concept_status(status),
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


def concept_document_to_payload(data: ConceptDocument) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "canonical_name": data.canonical_name,
        "status": data.status.value,
        "definition": data.definition,
        "form": data.form,
    }
    if data.artifact_id is not None:
        payload["artifact_id"] = data.artifact_id
    if data.logical_ids:
        payload["logical_ids"] = [
            {"namespace": entry.namespace, "value": entry.value}
            for entry in data.logical_ids
        ]
    if data.version_id is not None:
        payload["version_id"] = data.version_id
    if data.aliases:
        payload["aliases"] = [
            {
                key: value
                for key, value in {
                    "name": alias.name,
                    "source": alias.source,
                    "note": alias.note,
                }.items()
                if value is not None
            }
            for alias in data.aliases
        ]
    if data.created_date is not None:
        payload["created_date"] = data.created_date
    if data.definition_source is not None:
        payload["definition_source"] = data.definition_source
    if data.domain is not None:
        payload["domain"] = data.domain
    form_parameters = _mapping_to_builtin_dict(data.form_parameters)
    if form_parameters is not None:
        payload["form_parameters"] = form_parameters
    if data.last_modified is not None:
        payload["last_modified"] = data.last_modified
    if data.notes is not None:
        payload["notes"] = data.notes
    if data.parameterization_relationships:
        payload["parameterization_relationships"] = [
            {
                key: value
                for key, value in {
                    "inputs": list(parameterization.inputs),
                    "formula": parameterization.formula,
                    "exactness": parameterization.exactness,
                    "source": parameterization.source,
                    "bidirectional": parameterization.bidirectional,
                    "sympy": parameterization.sympy,
                    "conditions": list(parameterization.conditions),
                    "note": parameterization.note,
                    "canonical_claim": parameterization.canonical_claim,
                    "fit_statistics": parameterization.fit_statistics,
                }.items()
                if value not in (None, [])
            }
            for parameterization in data.parameterization_relationships
        ]
    if data.range is not None:
        payload["range"] = [data.range[0], data.range[1]]
    if data.relationships:
        payload["relationships"] = [
            {
                key: value
                for key, value in {
                    "type": relationship.type,
                    "target": relationship.target,
                    "source": relationship.source,
                    "conditions": list(relationship.conditions),
                    "note": relationship.note,
                }.items()
                if value not in (None, [])
            }
            for relationship in data.relationships
        ]
    if data.replaced_by is not None:
        payload["replaced_by"] = data.replaced_by
    return payload


def parse_concept_record_document(data: ConceptDocument) -> ConceptRecord:
    return parse_concept_record(concept_document_to_payload(data))


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
    raw_to_artifact: dict[str, str] = {}
    pending: list[tuple[LoadedDocument[ConceptDocument], dict[str, Any], str | None]] = []

    for concept in concepts:
        payload = concept_document_to_payload(concept.document)
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
                source_path=concept.source_path,
                knowledge_root=concept.knowledge_root,
                record=parse_concept_record(rewritten),
                source_local_id=raw_id,
            )
        )
    return normalized_concepts


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


def load_concepts(concepts_root: KnowledgePath | None) -> list[LoadedConcept]:
    """Load all canonical concept YAML files from a concept subtree."""

    if concepts_root is None or not concepts_root.is_dir():
        return []
    knowledge_root = concepts_root.parent if concepts_root.name else concepts_root
    loaded_documents = [
        load_document(
            entry,
            ConceptDocument,
            knowledge_root=knowledge_root,
        )
        for entry in concepts_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]
    return normalize_loaded_concepts(loaded_documents)
