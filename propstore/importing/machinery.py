"""Typed import contract machinery.

This module deliberately stops at machinery: it compiles one explicit authored
import form into one situated assertion plus provenance metadata. Bulk import
workflows can call this later, but semantic guessing and identity closure do
not belong here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Literal

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import ConditionId, ContextId, ProvenanceGraphId
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet
from propstore.provenance.records import (
    ExternalInferenceProvenanceRecord,
    ExternalStatementAttitude,
    ExternalStatementProvenanceRecord,
    ImportRunProvenanceRecord,
    LicenseProvenanceRecord,
    SourceVersionProvenanceRecord,
)

EquivalenceWitnessStatus = Literal["asserted", "derived_unresolved"]

_URI_PREFIXES = ("urn:", "ni://", "http://", "https://")


@dataclass(frozen=True, order=True)
class SurfaceRoleBinding:
    role: str
    value: str

    def __post_init__(self) -> None:
        role = _require_non_empty(self.role, "role")
        value = _require_non_empty(self.value, "role value")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "value", value)


@dataclass(frozen=True)
class ExternalInferenceSurface:
    inference_id: str
    engine: str
    inferred_at: str
    premise_statement_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "inference_id", _require_uri(self.inference_id, "inference_id")
        )
        object.__setattr__(self, "engine", _require_non_empty(self.engine, "engine"))
        object.__setattr__(
            self, "inferred_at", _require_non_empty(self.inferred_at, "inferred_at")
        )
        object.__setattr__(
            self,
            "premise_statement_ids",
            _canonical_uri_tuple(self.premise_statement_ids, "premise statement"),
        )


@dataclass(frozen=True)
class AuthoredAssertionSurface:
    """Non-NL authored surface consumed by the import lens."""

    source_id: str
    source_label: str
    source_version_id: str
    source_content_hash: str
    retrieval_uri: str | None
    license_id: str
    license_label: str
    license_uri: str | None
    import_run_id: str
    importer_id: str
    imported_at: str
    external_statement_id: str
    external_statement_locator: str
    external_inference: ExternalInferenceSurface | None
    mapping_policy_id: str
    mapping_policy_label: str
    relation_id: str
    role_bindings: tuple[SurfaceRoleBinding, ...]
    context_id: str
    microtheory_id: str
    lifting_rule_id: str | None
    condition_id: str
    condition_registry_fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _require_uri(self.source_id, "source_id"))
        object.__setattr__(
            self, "source_label", _require_non_empty(self.source_label, "source_label")
        )
        object.__setattr__(
            self,
            "source_version_id",
            _require_non_empty(self.source_version_id, "source_version_id"),
        )
        object.__setattr__(
            self,
            "source_content_hash",
            _require_content_hash(self.source_content_hash),
        )
        if self.retrieval_uri is not None:
            object.__setattr__(
                self,
                "retrieval_uri",
                _require_uri(self.retrieval_uri, "retrieval_uri"),
            )
        object.__setattr__(
            self, "license_id", _require_uri(self.license_id, "license_id")
        )
        object.__setattr__(
            self,
            "license_label",
            _require_non_empty(self.license_label, "license_label"),
        )
        if self.license_uri is not None:
            object.__setattr__(
                self,
                "license_uri",
                _require_uri(self.license_uri, "license_uri"),
            )
        object.__setattr__(
            self, "import_run_id", _require_uri(self.import_run_id, "import_run_id")
        )
        object.__setattr__(
            self, "importer_id", _require_uri(self.importer_id, "importer_id")
        )
        object.__setattr__(
            self, "imported_at", _require_non_empty(self.imported_at, "imported_at")
        )
        object.__setattr__(
            self,
            "external_statement_id",
            _require_uri(self.external_statement_id, "external_statement_id"),
        )
        object.__setattr__(
            self,
            "external_statement_locator",
            _require_non_empty(
                self.external_statement_locator, "external_statement_locator"
            ),
        )
        object.__setattr__(
            self,
            "mapping_policy_id",
            _require_uri(self.mapping_policy_id, "mapping_policy_id"),
        )
        object.__setattr__(
            self,
            "mapping_policy_label",
            _require_non_empty(self.mapping_policy_label, "mapping_policy_label"),
        )
        object.__setattr__(
            self, "relation_id", _require_non_empty(self.relation_id, "relation_id")
        )
        role_bindings = tuple(self.role_bindings)
        if not role_bindings:
            raise ValueError("role bindings must be non-empty")
        object.__setattr__(self, "role_bindings", role_bindings)
        object.__setattr__(
            self, "context_id", _require_non_empty(self.context_id, "context_id")
        )
        object.__setattr__(
            self,
            "microtheory_id",
            _require_non_empty(self.microtheory_id, "microtheory_id"),
        )
        if self.lifting_rule_id is not None:
            object.__setattr__(
                self,
                "lifting_rule_id",
                _require_uri(self.lifting_rule_id, "lifting_rule_id"),
            )
        object.__setattr__(
            self, "condition_id", _require_non_empty(self.condition_id, "condition_id")
        )
        object.__setattr__(
            self,
            "condition_registry_fingerprint",
            _require_non_empty(
                self.condition_registry_fingerprint,
                "condition_registry_fingerprint",
            ),
        )

    def with_mapping(
        self,
        *,
        relation_id: str,
        context_id: str,
        microtheory_id: str,
        role_bindings: tuple[SurfaceRoleBinding, ...],
    ) -> AuthoredAssertionSurface:
        return replace(
            self,
            relation_id=relation_id,
            context_id=context_id,
            microtheory_id=microtheory_id,
            role_bindings=role_bindings,
        )


@dataclass(frozen=True, order=True)
class ExternalSourceIdentity:
    source_id: str
    label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _require_uri(self.source_id, "source_id"))
        object.__setattr__(
            self, "label", _require_non_empty(self.label, "source label")
        )


@dataclass(frozen=True, order=True)
class MappingPolicy:
    policy_id: str
    label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", _require_uri(self.policy_id, "policy_id"))
        object.__setattr__(
            self, "label", _require_non_empty(self.label, "mapping policy label")
        )


@dataclass(frozen=True, order=True)
class ContextMicrotheoryMapping:
    context: ContextReference
    microtheory_id: str
    mapping_policy_id: str
    lifting_rule_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.context, ContextReference):
            raise TypeError("context must be ContextReference")
        object.__setattr__(
            self,
            "microtheory_id",
            _require_non_empty(self.microtheory_id, "microtheory_id"),
        )
        object.__setattr__(
            self,
            "mapping_policy_id",
            _require_uri(self.mapping_policy_id, "mapping_policy_id"),
        )
        if self.lifting_rule_id is not None:
            object.__setattr__(
                self,
                "lifting_rule_id",
                _require_uri(self.lifting_rule_id, "lifting_rule_id"),
            )


@dataclass(frozen=True)
class AuthoredAssertionForm:
    source_identity: ExternalSourceIdentity
    source: SourceVersionProvenanceRecord
    license: LicenseProvenanceRecord
    import_run: ImportRunProvenanceRecord
    external_statement: ExternalStatementProvenanceRecord
    external_inference: ExternalInferenceProvenanceRecord | None
    mapping_policy: MappingPolicy
    context_mapping: ContextMicrotheoryMapping
    relation: RelationConceptRef
    role_bindings: RoleBindingSet
    condition: ConditionRef


@dataclass(frozen=True)
class ImportMetadata:
    source_identity: ExternalSourceIdentity
    source: SourceVersionProvenanceRecord
    license: LicenseProvenanceRecord
    import_run: ImportRunProvenanceRecord
    external_statement: ExternalStatementProvenanceRecord
    external_inference: ExternalInferenceProvenanceRecord | None
    mapping_policy: MappingPolicy
    context_mapping: ContextMicrotheoryMapping


@dataclass(frozen=True)
class CompiledImportAssertion:
    assertion: SituatedAssertion
    import_metadata: ImportMetadata


class ImportAuthoredFormLens:
    """Lens between non-NL surface records and structural import forms."""

    def get(self, surface: AuthoredAssertionSurface) -> AuthoredAssertionForm:
        source_identity = ExternalSourceIdentity(
            source_id=surface.source_id,
            label=surface.source_label,
        )
        source = SourceVersionProvenanceRecord(
            source_id=surface.source_id,
            version_id=surface.source_version_id,
            content_hash=surface.source_content_hash,
            retrieval_uri=surface.retrieval_uri,
        )
        license_record = LicenseProvenanceRecord(
            license_id=surface.license_id,
            label=surface.license_label,
            uri=surface.license_uri,
        )
        import_run = ImportRunProvenanceRecord(
            run_id=surface.import_run_id,
            importer_id=surface.importer_id,
            imported_at=surface.imported_at,
            source=source,
            license=license_record,
        )
        external_statement = ExternalStatementProvenanceRecord(
            statement_id=surface.external_statement_id,
            source=source,
            locator=surface.external_statement_locator,
            attitude=ExternalStatementAttitude.ASSERTED,
        )
        external_inference = _external_inference_from_surface(
            surface.external_inference,
            conclusion_statement_id=surface.external_statement_id,
        )
        mapping_policy = MappingPolicy(
            policy_id=surface.mapping_policy_id,
            label=surface.mapping_policy_label,
        )
        context_mapping = ContextMicrotheoryMapping(
            context=ContextReference(ContextId(surface.context_id)),
            microtheory_id=surface.microtheory_id,
            mapping_policy_id=surface.mapping_policy_id,
            lifting_rule_id=surface.lifting_rule_id,
        )
        return AuthoredAssertionForm(
            source_identity=source_identity,
            source=source,
            license=license_record,
            import_run=import_run,
            external_statement=external_statement,
            external_inference=external_inference,
            mapping_policy=mapping_policy,
            context_mapping=context_mapping,
            relation=RelationConceptRef(surface.relation_id),
            role_bindings=RoleBindingSet(
                tuple(
                    RoleBinding(binding.role, binding.value)
                    for binding in surface.role_bindings
                )
            ),
            condition=ConditionRef(
                id=ConditionId(surface.condition_id),
                registry_fingerprint=surface.condition_registry_fingerprint,
            ),
        )


@dataclass(frozen=True, order=True)
class EquivalenceWitness:
    witness_id: str
    candidate_ids: tuple[str, str]
    mapping_policy_id: str
    evidence_statement_ids: tuple[str, ...]
    status: EquivalenceWitnessStatus
    source_witness_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "witness_id", _require_uri(self.witness_id, "witness_id")
        )
        candidates = _canonical_candidate_pair(
            self.candidate_ids[0], self.candidate_ids[1]
        )
        object.__setattr__(self, "candidate_ids", candidates)
        object.__setattr__(
            self,
            "mapping_policy_id",
            _require_uri(self.mapping_policy_id, "mapping_policy_id"),
        )
        object.__setattr__(
            self,
            "evidence_statement_ids",
            _canonical_uri_tuple(self.evidence_statement_ids, "evidence statement"),
        )
        object.__setattr__(
            self,
            "source_witness_ids",
            _canonical_uri_tuple(self.source_witness_ids, "source witness")
            if self.source_witness_ids
            else (),
        )
        if self.status not in ("asserted", "derived_unresolved"):
            raise ValueError("unsupported equivalence witness status")


class EquivalenceWitnessStore:
    """Explicit witness index with no sameAs-style identity closure."""

    def __init__(self) -> None:
        self._witnesses: dict[str, EquivalenceWitness] = {}

    def record_witness(
        self,
        first_candidate_id: str,
        second_candidate_id: str,
        *,
        mapping_policy_id: str,
        evidence_statement_ids: tuple[str, ...],
    ) -> EquivalenceWitness:
        return self._record(
            first_candidate_id,
            second_candidate_id,
            mapping_policy_id=mapping_policy_id,
            evidence_statement_ids=evidence_statement_ids,
            status="asserted",
            source_witness_ids=(),
        )

    def compose(
        self,
        first_witness_id: str,
        second_witness_id: str,
    ) -> EquivalenceWitness | None:
        first = self._witnesses[first_witness_id]
        second = self._witnesses[second_witness_id]
        if first.mapping_policy_id != second.mapping_policy_id:
            return None
        shared = set(first.candidate_ids).intersection(second.candidate_ids)
        if len(shared) != 1:
            return None
        endpoints = (
            set(first.candidate_ids).union(second.candidate_ids).difference(shared)
        )
        if len(endpoints) != 2:
            return None
        left, right = tuple(sorted(endpoints))
        return self._record(
            left,
            right,
            mapping_policy_id=first.mapping_policy_id,
            evidence_statement_ids=first.evidence_statement_ids
            + second.evidence_statement_ids,
            status="derived_unresolved",
            source_witness_ids=(first.witness_id, second.witness_id),
        )

    def witnesses_for(self, candidate_id: str) -> tuple[EquivalenceWitness, ...]:
        candidate = _require_uri(candidate_id, "candidate_id")
        return tuple(
            witness
            for witness in self._witnesses.values()
            if candidate in witness.candidate_ids
        )

    def identity_for(self, candidate_id: str) -> str:
        return _require_uri(candidate_id, "candidate_id")


def _external_inference_from_surface(
    surface: ExternalInferenceSurface | None,
    *,
    conclusion_statement_id: str,
) -> ExternalInferenceProvenanceRecord | None:
    if surface is None:
        return None
    return ExternalInferenceProvenanceRecord(
        inference_id=surface.inference_id,
        engine=surface.engine,
        inferred_at=surface.inferred_at,
        premise_statement_ids=surface.premise_statement_ids,
        conclusion_statement_id=conclusion_statement_id,
    )


def _surface_from_external_inference(
    record: ExternalInferenceProvenanceRecord | None,
) -> ExternalInferenceSurface | None:
    if record is None:
        return None
    return ExternalInferenceSurface(
        inference_id=record.inference_id,
        engine=record.engine,
        inferred_at=record.inferred_at,
        premise_statement_ids=record.premise_statement_ids,
    )


def _canonical_candidate_pair(left: str, right: str) -> tuple[str, str]:
    left_id = _require_uri(left, "candidate_id")
    right_id = _require_uri(right, "candidate_id")
    if left_id == right_id:
        raise ValueError("equivalence witness requires distinct candidates")
    first, second = sorted((left_id, right_id))
    return (first, second)


def _canonical_uri_tuple(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    result = tuple(sorted({_require_uri(value, label) for value in values}))
    if not result:
        raise ValueError(f"{label} set must be non-empty")
    return result


def _require_non_empty(value: str, label: str) -> str:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{label} must be non-empty")
    return text


def _require_uri(value: str, label: str) -> str:
    text = _require_non_empty(value, label)
    if not text.startswith(_URI_PREFIXES):
        raise ValueError(f"{label} must be a URI")
    return text


def _require_content_hash(value: str) -> str:
    text = _require_non_empty(value, "source content hash")
    if ":" not in text:
        raise ValueError("source content hash must name the hash algorithm")
    return text


def _digest(value: object) -> str:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()
