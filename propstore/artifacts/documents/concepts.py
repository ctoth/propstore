from __future__ import annotations

from typing import Any

import msgspec

from propstore.cel_types import CelExpr
from propstore.core.concept_status import ConceptStatus
from propstore.core.concept_relationship_types import ConceptRelationshipType
from propstore.core.exactness_types import Exactness
from propstore.artifacts.schema import DocumentStruct


class ConceptLogicalIdDocument(DocumentStruct):
    namespace: str
    value: str


class ConceptAliasDocument(DocumentStruct):
    name: str
    source: str | None = None
    note: str | None = None


class ConceptRelationshipDocument(DocumentStruct):
    type: ConceptRelationshipType
    target: str
    source: str | None = None
    conditions: tuple[CelExpr, ...] = ()
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
    exactness: Exactness | None = None
    source: str | None = None
    bidirectional: bool | None = None
    sympy: str | None = None
    conditions: tuple[CelExpr, ...] = ()
    note: str | None = None
    canonical_claim: str | None = None
    fit_statistics: str | None = None


class ConceptDocument(DocumentStruct):
    canonical_name: str
    status: ConceptStatus
    definition: str
    form: str
    artifact_id: str | None = None
    logical_ids: tuple[ConceptLogicalIdDocument, ...] = ()
    version_id: str | None = None
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
    id: str | None = None
    artifact_id: str | None = None
    logical_ids: tuple[ConceptLogicalIdDocument, ...] = ()
