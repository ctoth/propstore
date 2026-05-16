"""Claim-side compilation helpers for the sidecar.

Raw-id quarantine path (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): claims whose raw ``id`` never
canonicalized are still given a ``claim_core`` row with a synthetic id
and ``build_status='blocked'``, plus a ``build_diagnostics`` row
describing why. This implements discipline rule 5 (filter at render, not
at build) — no data is refused; the render layer decides what to show.
"""

from __future__ import annotations

import contextlib
import json
import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from quire.projections import (
    FtsProjection,
    ProjectionColumn,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionRow,
    ProjectionTable,
)
from quire.sqlite_vec_store import embedding_status_projection, rowid_vec_projection
from propstore.core.algorithm_stage import AlgorithmStage, coerce_algorithm_stage
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.core.claim_values import (
    ClaimProvenance,
    ClaimSource,
    SourceOrigin,
    SourceTrust,
)
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    ContextId,
    LogicalId,
    to_claim_id,
    to_concept_id,
    to_context_id,
)
from propstore.core.relations import (
    ClaimConceptLinkRole,
    coerce_claim_concept_link_role,
)
from propstore.core.source_types import coerce_source_kind, coerce_source_origin_type

if TYPE_CHECKING:
    from propstore.core.graph_types import ProvenanceRecord
    from propstore.core.justifications import CanonicalJustification
    from propstore.families.claims.stages import (
        ClaimSidecarRows,
        RawIdQuarantineSidecarRows,
    )


def _require_claim_type(value: object) -> ClaimType:
    claim_type = coerce_claim_type(value)
    if claim_type is None:
        raise KeyError('claim_type')
    return claim_type


def _require_claim_concept_link_role(value: object) -> ClaimConceptLinkRole:
    role = coerce_claim_concept_link_role(value)
    if role is None:
        raise KeyError('role')
    return role


@dataclass(frozen=True)
class ClaimConceptLinkRow:
    claim_id: ClaimId
    concept_id: ConceptId
    role: ClaimConceptLinkRole
    ordinal: int = 0
    binding_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _require_claim_concept_link_role(self.role))

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> ClaimConceptLinkRow:
        return cls(
            claim_id=to_claim_id(row_map["claim_id"]),
            concept_id=to_concept_id(row_map["concept_id"]),
            role=_require_claim_concept_link_role(row_map["role"]),
            ordinal=0 if row_map.get("ordinal") is None else int(row_map["ordinal"]),
            binding_name=(
                None if row_map.get("binding_name") is None else str(row_map["binding_name"])
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_id": self.claim_id,
            "concept_id": self.concept_id,
            "role": self.role.value,
            "ordinal": self.ordinal,
        }
        if self.binding_name is not None:
            data["binding_name"] = self.binding_name
        return data


@dataclass(frozen=True)
class ClaimRow:
    claim_id: ClaimId
    artifact_id: str
    claim_type: ClaimType | None = None
    concept_links: tuple[ClaimConceptLinkRow, ...] = field(default_factory=tuple)
    target_concept: ConceptId | None = None
    logical_ids: tuple[LogicalId, ...] = field(default_factory=tuple)
    version_id: str | None = None
    seq: int | None = None
    value: Any = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    uncertainty: float | None = None
    uncertainty_type: str | None = None
    sample_size: int | None = None
    unit: str | None = None
    conditions_cel: str | None = None
    conditions_ir: str | None = None
    statement: str | None = None
    expression: str | None = None
    sympy_generated: str | None = None
    sympy_error: str | None = None
    name: str | None = None
    measure: str | None = None
    listener_population: str | None = None
    methodology: str | None = None
    notes: str | None = None
    description: str | None = None
    auto_summary: str | None = None
    body: str | None = None
    canonical_ast: str | None = None
    variables_json: str | None = None
    algorithm_stage: AlgorithmStage | None = None
    source: ClaimSource | None = None
    provenance: ClaimProvenance | None = None
    value_si: float | None = None
    lower_bound_si: float | None = None
    upper_bound_si: float | None = None
    context_id: ContextId | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))
        object.__setattr__(self, "concept_links", tuple(self.concept_links))
        if self.claim_type is not None:
            object.__setattr__(self, "claim_type", coerce_claim_type(self.claim_type))
        if self.algorithm_stage is not None:
            object.__setattr__(
                self, "algorithm_stage", coerce_algorithm_stage(self.algorithm_stage)
            )

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> ClaimRow:
        known = {
            "id",
            "artifact_id",
            "type",
            "claim_type",
            "concept_links",
            "target_concept",
            "primary_logical_id",
            "logical_id",
            "logical_ids",
            "logical_ids_json",
            "version_id",
            "seq",
            "value",
            "lower_bound",
            "upper_bound",
            "uncertainty",
            "uncertainty_type",
            "sample_size",
            "unit",
            "conditions_cel",
            "conditions_ir",
            "statement",
            "expression",
            "sympy_generated",
            "sympy_error",
            "name",
            "measure",
            "listener_population",
            "methodology",
            "notes",
            "description",
            "auto_summary",
            "body",
            "canonical_ast",
            "variables_json",
            "algorithm_stage",
            "source_slug",
            "source_quality_opinion",
            "source_paper",
            "source_id",
            "source_kind",
            "source_origin_type",
            "source_origin_value",
            "source_origin_retrieved",
            "source_origin_content_ref",
            "source_prior_base_rate",
            "source_quality_json",
            "source_derived_from_json",
            "provenance_page",
            "provenance_json",
            "value_si",
            "lower_bound_si",
            "upper_bound_si",
            "context_id",
            "source",
        }
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in known and value is not None
        }
        artifact_id = row_map.get("artifact_id", row_map.get("id"))
        if artifact_id is None:
            raise KeyError("id")
        logical_id_entries = row_map.get("logical_ids")
        logical_ids_json = row_map.get("logical_ids_json")
        if logical_id_entries is None and isinstance(logical_ids_json, str) and logical_ids_json:
            try:
                logical_id_entries = json.loads(logical_ids_json)
            except json.JSONDecodeError:
                logical_id_entries = None
        logical_ids: list[LogicalId] = []
        if isinstance(logical_id_entries, list):
            for entry in logical_id_entries:
                if not isinstance(entry, Mapping):
                    continue
                namespace = entry.get("namespace")
                value = entry.get("value")
                if isinstance(namespace, str) and isinstance(value, str) and namespace and value:
                    logical_ids.append(LogicalId(namespace=namespace, value=value))
        primary_logical_id = row_map.get("primary_logical_id", row_map.get("logical_id"))
        if not logical_ids and isinstance(primary_logical_id, str) and ":" in primary_logical_id:
            namespace, value = primary_logical_id.split(":", 1)
            if namespace and value:
                logical_ids.append(LogicalId(namespace=namespace, value=value))
        concept_link_entries = row_map.get("concept_links")
        concept_links: list[ClaimConceptLinkRow] = []
        if isinstance(concept_link_entries, list | tuple):
            for entry in concept_link_entries:
                if not isinstance(entry, Mapping):
                    continue
                concept_links.append(ClaimConceptLinkRow.from_mapping(entry))

        nested_source = row_map.get("source") if isinstance(row_map.get("source"), Mapping) else None
        quality_trust = (
            SourceTrust.from_mapping(
                {"quality": row_map.get("source_quality_json") or row_map.get("source_quality_opinion")}
            )
            if row_map.get("source_quality_json") is not None
            or row_map.get("source_quality_opinion") is not None
            else None
        )
        derived_from_trust = (
            SourceTrust.from_mapping(
                {"derived_from": row_map.get("source_derived_from_json")}
            )
            if row_map.get("source_derived_from_json") is not None
            else None
        )
        flat_source = ClaimSource(
            source_id=(None if row_map.get("source_id") is None else str(row_map["source_id"])),
            kind=(
                None
                if row_map.get("source_kind") is None
                else coerce_source_kind(row_map["source_kind"])
            ),
            slug=(None if row_map.get("source_slug") is None else str(row_map["source_slug"])),
            origin=SourceOrigin(
                origin_type=(
                    None
                    if row_map.get("source_origin_type") is None
                    else coerce_source_origin_type(row_map["source_origin_type"])
                ),
                value=(
                    None
                    if row_map.get("source_origin_value") is None
                    else str(row_map["source_origin_value"])
                ),
                retrieved=(
                    None
                    if row_map.get("source_origin_retrieved") is None
                    else str(row_map["source_origin_retrieved"])
                ),
                content_ref=(
                    None
                    if row_map.get("source_origin_content_ref") is None
                    else str(row_map["source_origin_content_ref"])
                ),
            ),
            trust=SourceTrust.from_mapping(
                {
                    "prior_base_rate": row_map.get("source_prior_base_rate"),
                    "quality": row_map.get("source_quality_json"),
                    "derived_from": row_map.get("source_derived_from_json"),
                }
            ),
        )
        source = ClaimSource.from_mapping(nested_source, slug=flat_source.slug)
        if source is None and not flat_source.is_empty:
            source = ClaimSource(
                source_id=flat_source.source_id,
                kind=flat_source.kind,
                slug=flat_source.slug,
                origin=None if flat_source.origin is None or flat_source.origin.is_empty else flat_source.origin,
                trust=None if flat_source.trust is None or flat_source.trust.is_empty else flat_source.trust,
            )
        elif source is not None:
            source = ClaimSource(
                source_id=source.source_id if source.source_id is not None else flat_source.source_id,
                kind=source.kind if source.kind is not None else flat_source.kind,
                slug=source.slug if source.slug is not None else flat_source.slug,
                origin=source.origin if source.origin is not None else (
                    None if flat_source.origin is None or flat_source.origin.is_empty else flat_source.origin
                ),
                trust=source.trust if source.trust is not None else (
                    None if flat_source.trust is None or flat_source.trust.is_empty else flat_source.trust
                ),
            )
        provenance = ClaimProvenance.from_components(
            paper=(
                None if row_map.get("source_paper") is None else str(row_map["source_paper"])
            ),
            page=(
                None if row_map.get("provenance_page") is None else int(row_map["provenance_page"])
            ),
            provenance_json=row_map.get("provenance_json"),
        )
        return cls(
            claim_id=to_claim_id(row_map["id"]),
            artifact_id=str(artifact_id),
            claim_type=(
                None
                if row_map.get("type", row_map.get("claim_type")) is None
                else _require_claim_type(row_map.get("type", row_map.get("claim_type")))
            ),
            concept_links=tuple(concept_links),
            target_concept=(
                None
                if row_map.get("target_concept") is None
                else to_concept_id(row_map["target_concept"])
            ),
            logical_ids=tuple(logical_ids),
            version_id=None if row_map.get("version_id") is None else str(row_map["version_id"]),
            seq=None if row_map.get("seq") is None else int(row_map["seq"]),
            value=row_map.get("value"),
            lower_bound=(
                None if row_map.get("lower_bound") is None else float(row_map["lower_bound"])
            ),
            upper_bound=(
                None if row_map.get("upper_bound") is None else float(row_map["upper_bound"])
            ),
            uncertainty=(
                None if row_map.get("uncertainty") is None else float(row_map["uncertainty"])
            ),
            uncertainty_type=(
                None if row_map.get("uncertainty_type") is None else str(row_map["uncertainty_type"])
            ),
            sample_size=(
                None if row_map.get("sample_size") is None else int(row_map["sample_size"])
            ),
            unit=None if row_map.get("unit") is None else str(row_map["unit"]),
            conditions_cel=(
                None if row_map.get("conditions_cel") is None else str(row_map["conditions_cel"])
            ),
            conditions_ir=(
                None if row_map.get("conditions_ir") is None else str(row_map["conditions_ir"])
            ),
            statement=None if row_map.get("statement") is None else str(row_map["statement"]),
            expression=None if row_map.get("expression") is None else str(row_map["expression"]),
            sympy_generated=(
                None if row_map.get("sympy_generated") is None else str(row_map["sympy_generated"])
            ),
            sympy_error=(
                None if row_map.get("sympy_error") is None else str(row_map["sympy_error"])
            ),
            name=None if row_map.get("name") is None else str(row_map["name"]),
            measure=None if row_map.get("measure") is None else str(row_map["measure"]),
            listener_population=(
                None
                if row_map.get("listener_population") is None
                else str(row_map["listener_population"])
            ),
            methodology=(
                None if row_map.get("methodology") is None else str(row_map["methodology"])
            ),
            notes=None if row_map.get("notes") is None else str(row_map["notes"]),
            description=(
                None if row_map.get("description") is None else str(row_map["description"])
            ),
            auto_summary=(
                None if row_map.get("auto_summary") is None else str(row_map["auto_summary"])
            ),
            body=None if row_map.get("body") is None else str(row_map["body"]),
            canonical_ast=(
                None if row_map.get("canonical_ast") is None else str(row_map["canonical_ast"])
            ),
            variables_json=(
                None if row_map.get("variables_json") is None else str(row_map["variables_json"])
            ),
            algorithm_stage=coerce_algorithm_stage(row_map.get("algorithm_stage")),
            source=source,
            provenance=provenance,
            value_si=None if row_map.get("value_si") is None else float(row_map["value_si"]),
            lower_bound_si=(
                None if row_map.get("lower_bound_si") is None else float(row_map["lower_bound_si"])
            ),
            upper_bound_si=(
                None if row_map.get("upper_bound_si") is None else float(row_map["upper_bound_si"])
            ),
            context_id=(
                None if row_map.get("context_id") is None else to_context_id(row_map["context_id"])
            ),
            attributes=attributes,
        )

    @property
    def primary_logical_id(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].formatted

    @property
    def primary_logical_value(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].value

    @property
    def source_paper(self) -> str | None:
        return None if self.provenance is None else self.provenance.paper

    @property
    def provenance_page(self) -> int | None:
        return None if self.provenance is None else self.provenance.page

    @property
    def source_slug(self) -> str | None:
        return None if self.source is None else self.source.slug

    def concept_ids_for_role(self, role: ClaimConceptLinkRole) -> tuple[ConceptId, ...]:
        return tuple(
            link.concept_id
            for link in self.concept_links
            if link.role is role
        )

    @property
    def output_concept_id(self) -> ConceptId | None:
        concept_ids = self.concept_ids_for_role(ClaimConceptLinkRole.OUTPUT)
        return concept_ids[0] if concept_ids else None

    @property
    def value_concept_id(self) -> ConceptId | None:
        return self.output_concept_id or self.target_concept

    @property
    def about_concept_ids(self) -> tuple[ConceptId, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.ABOUT)

    @property
    def input_concept_ids(self) -> tuple[ConceptId, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.INPUT)

    @property
    def target_concept_ids(self) -> tuple[ConceptId, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.TARGET)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.claim_id,
            "artifact_id": self.artifact_id,
        }
        logical_ids_payload = [logical_id.to_payload() for logical_id in self.logical_ids]
        logical_ids_json = json.dumps(logical_ids_payload) if logical_ids_payload else None
        source_dict = None if self.source is None or self.source.is_empty else self.source.to_dict()
        provenance_json = None if self.provenance is None else self.provenance.to_json()
        provenance_page = None if self.provenance is None else self.provenance.page
        source_paper = None if self.provenance is None else self.provenance.paper
        source_quality = (
            None
            if self.source is None or self.source.trust is None
            else self.source.trust.quality_dict()
        )
        source_prior_base_rate = (
            None
            if self.source is None or self.source.trust is None
            else self.source.trust.prior_base_rate_dict()
        )
        source_derived_from = (
            None
            if self.source is None or self.source.trust is None or not self.source.trust.derived_from
            else json.dumps(list(self.source.trust.derived_from))
        )
        optional_fields = {
            "primary_logical_id": self.primary_logical_id,
            "version_id": self.version_id,
            "seq": self.seq,
            "type": self.claim_type,
            "target_concept": self.target_concept,
            "value": self.value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "uncertainty": self.uncertainty,
            "uncertainty_type": self.uncertainty_type,
            "sample_size": self.sample_size,
            "unit": self.unit,
            "conditions_cel": self.conditions_cel,
            "conditions_ir": self.conditions_ir,
            "statement": self.statement,
            "expression": self.expression,
            "sympy_generated": self.sympy_generated,
            "sympy_error": self.sympy_error,
            "name": self.name,
            "measure": self.measure,
            "listener_population": self.listener_population,
            "methodology": self.methodology,
            "notes": self.notes,
            "description": self.description,
            "auto_summary": self.auto_summary,
            "body": self.body,
            "canonical_ast": self.canonical_ast,
            "variables_json": self.variables_json,
            "algorithm_stage": (
                None if self.algorithm_stage is None else str(self.algorithm_stage)
            ),
            "source_slug": None if self.source is None else self.source.slug,
            "source_paper": source_paper,
            "source_id": None if self.source is None else self.source.source_id,
            "source_kind": (
                None
                if self.source is None or self.source.kind is None
                else self.source.kind.value
            ),
            "source_origin_type": (
                None
                if self.source is None
                or self.source.origin is None
                or self.source.origin.origin_type is None
                else self.source.origin.origin_type.value
            ),
            "source_origin_value": (
                None
                if self.source is None or self.source.origin is None
                else self.source.origin.value
            ),
            "source_origin_retrieved": (
                None
                if self.source is None or self.source.origin is None
                else self.source.origin.retrieved
            ),
            "source_origin_content_ref": (
                None
                if self.source is None or self.source.origin is None
                else self.source.origin.content_ref
            ),
            "source_prior_base_rate": (
                source_prior_base_rate
            ),
            "source_quality_json": (
                None if source_quality is None else json.dumps(source_quality)
            ),
            "source_derived_from_json": source_derived_from,
            "provenance_page": provenance_page,
            "provenance_json": provenance_json,
            "value_si": self.value_si,
            "lower_bound_si": self.lower_bound_si,
            "upper_bound_si": self.upper_bound_si,
            "context_id": self.context_id,
        }
        for key, value in optional_fields.items():
            if value is not None:
                data[key] = value
        data["logical_id"] = self.primary_logical_id
        data["logical_ids"] = logical_ids_payload
        if self.concept_links:
            data["concept_links"] = [link.to_dict() for link in self.concept_links]
        if source_dict is not None:
            data["source"] = source_dict
        if source_quality is not None:
            data["source_quality_opinion"] = source_quality
        data.update(self.attributes)
        return data


ClaimRowInput = ClaimRow | Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class SourcePromotionClaimRow:
    claim_id: str
    promotion_status: str


def coerce_claim_row(row: ClaimRowInput) -> ClaimRow:
    if isinstance(row, ClaimRow):
        return row
    return ClaimRow.from_mapping(row)


def claim_select_sql() -> str:
    return """
        SELECT
            core.id,
            core.id AS artifact_id,
            core.primary_logical_id,
            core.logical_ids_json,
            core.version_id,
            core.seq,
            core.type,
            core.target_concept,
            num.value,
            num.lower_bound,
            num.upper_bound,
            num.uncertainty,
            num.uncertainty_type,
            num.sample_size,
            num.unit,
            txt.conditions_cel,
            txt.conditions_ir,
            txt.statement,
            txt.expression,
            txt.sympy_generated,
            txt.sympy_error,
            txt.name,
            txt.measure,
            txt.listener_population,
            txt.methodology,
            txt.notes,
            txt.description,
            txt.auto_summary,
            alg.body,
            alg.canonical_ast,
            alg.variables_json,
            alg.algorithm_stage,
            core.source_slug,
            core.source_paper,
            src.source_id AS source_id,
            src.kind AS source_kind,
            src.origin_type AS source_origin_type,
            src.origin_value AS source_origin_value,
            src.origin_retrieved AS source_origin_retrieved,
            src.origin_content_ref AS source_origin_content_ref,
            src.prior_base_rate AS source_prior_base_rate,
            src.quality_json AS source_quality_json,
            src.derived_from_json AS source_derived_from_json,
            core.provenance_page,
            core.provenance_json,
            num.value_si,
            num.lower_bound_si,
            num.upper_bound_si,
            core.context_id,
            core.branch,
            core.build_status,
            core.stage,
            core.promotion_status
        FROM claim_core AS core
        LEFT JOIN claim_numeric_payload AS num ON num.claim_id = core.id
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        LEFT JOIN claim_algorithm_payload AS alg ON alg.claim_id = core.id
        LEFT JOIN source AS src ON src.slug = core.source_slug
    """


def select_claim_rows(
    conn: sqlite3.Connection,
    where_sql: str = "",
    params: tuple[Any, ...] = (),
) -> list[ClaimRow]:
    rows = conn.execute(
        f"{claim_select_sql()} {where_sql}",
        params,
    ).fetchall()
    row_dicts = [dict(row) for row in rows]
    if not row_dicts:
        return []
    claim_ids = [
        str(row_dict["id"])
        for row_dict in row_dicts
        if isinstance(row_dict.get("id"), str)
    ]
    links_by_claim_id = select_claim_concept_links_by_claim_id(conn, claim_ids)
    for row_dict in row_dicts:
        row_dict["concept_links"] = links_by_claim_id.get(str(row_dict["id"]), [])
    return [ClaimRow.from_mapping(row_dict) for row_dict in row_dicts]


def select_claim_rows_linked_to_concept(
    conn: sqlite3.Connection,
    concept_id: str | None,
    *,
    roles: tuple[str, ...] | None = None,
) -> list[ClaimRow]:
    where_sql, params = _claim_concept_link_where_sql(concept_id, roles=roles)
    return select_claim_rows(conn, where_sql + "ORDER BY core.id", params)


def select_claim_rows_with_visibility(
    conn: sqlite3.Connection,
    *,
    concept_id: str | None,
    include_drafts: bool,
    include_blocked: bool,
) -> list[ClaimRow]:
    clauses: list[str] = []
    bound: list[Any] = []
    concept_clause, concept_params = _claim_concept_link_where_sql(concept_id)
    if concept_clause:
        clauses.append(concept_clause.removeprefix("WHERE ").strip())
        bound.extend(concept_params)
    if not include_drafts:
        clauses.append("(core.stage IS NULL OR core.stage != 'draft')")
    if not include_blocked:
        clauses.append("(core.build_status IS NULL OR core.build_status != 'blocked')")
        clauses.append(
            "(core.promotion_status IS NULL OR core.promotion_status != 'blocked')"
        )
    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses) + " "
    return select_claim_rows(conn, where_sql + "ORDER BY core.id", tuple(bound))


def _claim_concept_link_where_sql(
    concept_id: str | None,
    *,
    roles: tuple[str, ...] | None = None,
) -> tuple[str, tuple[Any, ...]]:
    if concept_id is None:
        return "", ()
    predicates = [
        "link.claim_id = core.id",
        "link.concept_id = ?",
    ]
    params: list[Any] = [concept_id]
    if roles:
        placeholders = ",".join("?" for _ in roles)
        predicates.append(f"link.role IN ({placeholders})")
        params.extend(roles)
    where_sql = (
        "WHERE EXISTS ("
        "SELECT 1 FROM claim_concept_link AS link "
        f"WHERE {' AND '.join(predicates)}"
        ") "
    )
    return where_sql, tuple(params)


def select_claim_concept_links_by_claim_id(
    conn: sqlite3.Connection,
    claim_ids: Sequence[str],
) -> dict[str, list[dict[str, Any]]]:
    if not claim_ids:
        return {}
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT claim_id, concept_id, role, ordinal, binding_name
        FROM claim_concept_link
        WHERE claim_id IN ({placeholders})
        ORDER BY claim_id, ordinal, concept_id
        """,
        tuple(claim_ids),
    ).fetchall()
    links_by_claim_id: dict[str, list[dict[str, Any]]] = {
        claim_id: [] for claim_id in claim_ids
    }
    for row in rows:
        links_by_claim_id.setdefault(str(row["claim_id"]), []).append(dict(row))
    return links_by_claim_id


def build_claim_logical_id_index(conn: sqlite3.Connection) -> dict[str, str]:
    index: dict[str, str] = {}
    rows = conn.execute(
        "SELECT id, primary_logical_id, logical_ids_json FROM claim_core"
    ).fetchall()
    for row in rows:
        artifact_id = row["id"]
        primary_logical_id = row["primary_logical_id"]
        if isinstance(primary_logical_id, str) and primary_logical_id:
            index.setdefault(primary_logical_id, artifact_id)
        logical_ids_json = row["logical_ids_json"]
        if not isinstance(logical_ids_json, str) or not logical_ids_json:
            continue
        try:
            logical_ids = json.loads(logical_ids_json)
        except json.JSONDecodeError:
            continue
        if not isinstance(logical_ids, list):
            continue
        for entry in logical_ids:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if isinstance(namespace, str) and isinstance(value, str):
                index.setdefault(f"{namespace}:{value}", artifact_id)
                index.setdefault(value, artifact_id)
    return index


def resolve_claim_id(
    conn: sqlite3.Connection,
    name: str,
    *,
    logical_id_index: Mapping[str, str] | None = None,
) -> str | None:
    row = conn.execute(
        "SELECT id FROM claim_core WHERE id = ?",
        (name,),
    ).fetchone()
    if row is not None:
        return str(row["id"])

    row = conn.execute(
        "SELECT id FROM claim_core WHERE primary_logical_id = ?",
        (name,),
    ).fetchone()
    if row is not None:
        return str(row["id"])

    return None if logical_id_index is None else logical_id_index.get(name)


def count_claims(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0])


def select_authored_justifications(
    conn: sqlite3.Connection,
) -> tuple[CanonicalJustification, ...]:
    rows = conn.execute(
        """
        SELECT id, justification_kind, conclusion_claim_id,
               premise_claim_ids, source_relation_type, source_claim_id,
               provenance_json, rule_strength
        FROM justification
        ORDER BY id
        """
    ).fetchall()
    return tuple(_canonical_justification_from_row(row) for row in rows)


def count_authored_justifications(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM justification").fetchone()[0])


def _canonical_justification_from_row(
    row: sqlite3.Row,
) -> CanonicalJustification:
    from propstore.core.justifications import CanonicalJustification

    justification_id = str(row["id"])
    premise_claim_ids = _decode_justification_premises(
        row["premise_claim_ids"],
        justification_id=justification_id,
    )
    provenance = _decode_justification_provenance(
        row["provenance_json"],
        justification_id=justification_id,
    )
    attributes = tuple(
        (key, row[key])
        for key in ("source_relation_type", "source_claim_id")
        if row[key] is not None
    )
    return CanonicalJustification(
        justification_id=justification_id,
        conclusion_claim_id=str(row["conclusion_claim_id"]),
        premise_claim_ids=premise_claim_ids,
        rule_kind=str(row["justification_kind"]),
        rule_strength=str(row["rule_strength"] or "defeasible"),
        provenance=provenance,
        attributes=attributes,
    )


def _decode_justification_premises(
    value: object,
    *,
    justification_id: str,
) -> tuple[str, ...]:
    if not isinstance(value, str):
        raise ValueError(
            f"justification {justification_id!r} premise_claim_ids must be JSON text"
        )
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        raise ValueError(
            f"justification {justification_id!r} premise_claim_ids must decode to a list"
        )
    return tuple(str(item) for item in loaded)


def _decode_justification_provenance(
    value: object,
    *,
    justification_id: str,
) -> ProvenanceRecord | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(
            f"justification {justification_id!r} provenance_json must be JSON text"
        )
    loaded = json.loads(value)
    if not isinstance(loaded, Mapping):
        raise ValueError(
            f"justification {justification_id!r} provenance_json must decode to a mapping"
        )
    from propstore.core.graph_types import ProvenanceRecord

    return ProvenanceRecord.from_mapping(loaded)


def has_claim_core_table(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='claim_core'"
    ).fetchone()
    return row is not None


def delete_claim_core_row(conn: sqlite3.Connection, claim_id: str) -> None:
    conn.execute("DELETE FROM claim_core WHERE id = ?", (claim_id,))


def select_claim_embedding_rows(
    conn: sqlite3.Connection,
    entity_ids: Sequence[str] | None = None,
) -> list[ClaimRow]:
    query = """
        SELECT
            core.id,
            core.id AS artifact_id,
            core.seq,
            core.content_hash,
            txt.auto_summary,
            txt.statement,
            txt.expression,
            txt.name
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
    """
    params: tuple[str, ...] = ()
    if entity_ids:
        placeholders = ",".join("?" for _ in entity_ids)
        query += f" WHERE core.id IN ({placeholders})"
        params = tuple(entity_ids)
    return [ClaimRow.from_mapping(dict(row)) for row in conn.execute(query, params).fetchall()]


def resolve_claim_embedding_entity(conn: sqlite3.Connection, entity_id: str) -> tuple[str, int]:
    row = conn.execute(
        "SELECT id, seq FROM claim_core WHERE id = ?",
        (entity_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Claim {entity_id} not found")
    return str(row["id"]), int(row["seq"])


def embed_claims_for_request(
    sidecar: Path,
    *,
    claim_id: str | None,
    embed_all: bool,
    model: str,
    batch_size: int,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> list[tuple[str, Any]]:
    if not claim_id and not embed_all:
        raise ValueError("provide a claim ID or request all claims")

    from propstore.families.embeddings.declaration import (
        embed_claims,
        get_registered_models,
        load_vec_extension,
    )
    from quire.derived_runtime import connect_sqlite_store

    ids = [claim_id] if claim_id else None
    reports: list[tuple[str, Any]] = []
    conn = connect_sqlite_store(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        load_vec_extension(conn)
        if model == "all":
            models = get_registered_models(conn)
            if not models:
                raise LookupError("no models registered")
            for model_row in models:
                model_name = str(model_row["model_name"])
                result = embed_claims(
                    conn,
                    model_name,
                    claim_ids=ids,
                    batch_size=batch_size,
                    on_progress=(
                        None
                        if on_progress is None
                        else lambda done, total, model_name=model_name: on_progress(
                            model_name,
                            done,
                            total,
                        )
                    ),
                )
                reports.append((model_name, result))
        else:
            result = embed_claims(
                conn,
                model,
                claim_ids=ids,
                batch_size=batch_size,
                on_progress=(
                    None
                    if on_progress is None
                    else lambda done, total: on_progress(model, done, total)
                ),
            )
            reports.append((model, result))
        conn.commit()
    return reports


def find_similar_claim_rows(
    sidecar: Path,
    *,
    claim_id: str,
    model: str | None,
    top_k: int,
    agree: bool = False,
    disagree: bool = False,
) -> list[dict[str, Any]]:
    from propstore.families.embeddings.declaration import (
        find_similar,
        find_similar_agree,
        find_similar_disagree,
        get_registered_models,
        load_vec_extension,
    )
    from quire.derived_runtime import connect_sqlite_store

    conn = connect_sqlite_store(sidecar)
    conn.row_factory = sqlite3.Row
    load_vec_extension(conn)

    try:
        if agree:
            rows = find_similar_agree(conn, claim_id, top_k=top_k)
        elif disagree:
            rows = find_similar_disagree(conn, claim_id, top_k=top_k)
        else:
            selected_model = model
            if selected_model is None:
                models = get_registered_models(conn)
                if not models:
                    raise LookupError("no embeddings found")
                selected_model = str(models[0]["model_name"])
            rows = find_similar(conn, claim_id, selected_model, top_k=top_k)
    finally:
        conn.close()

    return [dict(row) for row in rows]


class SidecarClaimRelationStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def load_embedding_extension(self) -> None:
        from propstore.families.embeddings.declaration import load_vec_extension

        load_vec_extension(self._conn)

    def get_registered_models(self) -> list[dict]:
        from propstore.families.embeddings.declaration import get_registered_models

        return get_registered_models(self._conn)

    def get_claim_text(self, claim_id: str) -> dict[str, Any] | None:
        return select_claim_text(self._conn, claim_id)

    def get_claim_texts(self, claim_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
        return select_claim_texts(self._conn, claim_ids)

    def all_claim_ids(self) -> list[str]:
        return select_all_claim_ids(self._conn)

    def find_similar(
        self,
        claim_id: str,
        model_name: str,
        *,
        top_k: int,
    ) -> list[dict[str, Any]]:
        from propstore.families.embeddings.declaration import find_similar

        return find_similar(self._conn, claim_id, model_name, top_k=top_k)


def relate_claim_from_sidecar(
    sidecar: Path,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    from quire.derived_runtime import connect_sqlite_store
    from propstore.heuristic.relate import relate_claim

    conn = connect_sqlite_store(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        return relate_claim(
            SidecarClaimRelationStore(conn),
            claim_id,
            model_name,
            embedding_model,
            top_k,
        )


def relate_all_from_sidecar(
    sidecar: Path,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
    concurrency: int = 20,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    from quire.derived_runtime import connect_sqlite_store
    from propstore.heuristic.relate import relate_all

    conn = connect_sqlite_store(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        return relate_all(
            SidecarClaimRelationStore(conn),
            model_name,
            embedding_model,
            top_k,
            concurrency=concurrency,
            on_progress=on_progress,
        )


def select_claim_text(conn: sqlite3.Connection, claim_id: str) -> dict[str, Any] | None:
    rows = select_claim_texts(conn, [claim_id])
    return rows.get(claim_id)


def select_claim_texts(
    conn: sqlite3.Connection,
    claim_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    if not claim_ids:
        return {}
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT core.id, txt.auto_summary, txt.statement, txt.expression, core.source_paper
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        WHERE core.id IN ({placeholders})
        """,
        tuple(claim_ids),
    ).fetchall()
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        decoded = dict(row)
        decoded["text"] = (
            decoded.get("auto_summary")
            or decoded.get("statement")
            or decoded.get("expression")
            or decoded["id"]
        )
        result[str(decoded["id"])] = decoded
    return result


def select_all_claim_ids(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT id FROM claim_core").fetchall()
    return [str(row["id"]) for row in rows]


def select_source_promotion_claim_rows(
    conn: sqlite3.Connection,
    branch: str,
) -> list[SourcePromotionClaimRow]:
    rows = conn.execute(
        """
        SELECT id, promotion_status
        FROM claim_core
        WHERE branch = ? AND promotion_status IS NOT NULL
        ORDER BY id
        """,
        (branch,),
    ).fetchall()
    return [
        SourcePromotionClaimRow(
            claim_id=str(row[0]),
            promotion_status=str(row[1]),
        )
        for row in rows
    ]


CLAIM_EMBEDDING_JOIN_SOURCE = """
    (
        SELECT
            core.id,
            core.seq,
            core.type,
            core.source_paper,
            COALESCE(output_link.concept_id, target_link.concept_id, core.target_concept) AS concept_id,
            txt.auto_summary,
            txt.statement
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        LEFT JOIN claim_concept_link AS output_link
            ON output_link.claim_id = core.id AND output_link.role = 'output'
        LEFT JOIN claim_concept_link AS target_link
            ON target_link.claim_id = core.id AND target_link.role = 'target'
    )
"""


CLAIM_EMBEDDING_JOIN_COLUMNS = (
    "c.id, c.type, c.auto_summary, c.statement, c.source_paper, c.concept_id"
)


CLAIM_CORE_PROJECTION = ProjectionTable(
    name="claim_core",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("primary_logical_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("logical_ids_json", "TEXT", nullable=False, default_sql="'[]'"),
        ProjectionColumn("version_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("content_hash", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("seq", "INTEGER", nullable=False),
        ProjectionColumn("type", "TEXT", nullable=False),
        ProjectionColumn("target_concept", "TEXT"),
        ProjectionColumn("source_slug", "TEXT"),
        ProjectionColumn("source_paper", "TEXT", nullable=False),
        ProjectionColumn("provenance_page", "INTEGER", nullable=False),
        ProjectionColumn("provenance_json", "TEXT"),
        ProjectionColumn("context_id", "TEXT"),
        ProjectionColumn("premise_kind", "TEXT", nullable=False, default_sql="'ordinary'"),
        ProjectionColumn("branch", "TEXT"),
        ProjectionColumn("build_status", "TEXT", nullable=False, default_sql="'ingested'"),
        ProjectionColumn("stage", "TEXT"),
        ProjectionColumn("promotion_status", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("context_id",), "context", ("id",)),),
    indexes=(
        ProjectionIndex("idx_claim_core_target", ("target_concept",)),
        ProjectionIndex("idx_claim_core_type", ("type",)),
        ProjectionIndex("idx_claim_core_primary_logical_id", ("primary_logical_id",)),
        ProjectionIndex("idx_claim_core_build_status", ("build_status",)),
        ProjectionIndex("idx_claim_core_stage", ("stage",)),
        ProjectionIndex("idx_claim_core_promotion_status", ("promotion_status",)),
    ),
)


CLAIM_CONCEPT_LINK_PROJECTION = ProjectionTable(
    name="claim_concept_link",
    columns=(
        ProjectionColumn("claim_id", "TEXT", nullable=False),
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("role", "TEXT", nullable=False),
        ProjectionColumn("ordinal", "INTEGER", nullable=False),
        ProjectionColumn("binding_name", "TEXT"),
    ),
    primary_key=("claim_id", "role", "ordinal", "concept_id"),
    foreign_keys=(
        ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),
        ProjectionForeignKey(("concept_id",), "concept", ("id",)),
    ),
    indexes=(
        ProjectionIndex("idx_claim_concept_link_claim", ("claim_id",)),
        ProjectionIndex("idx_claim_concept_link_concept", ("concept_id",)),
        ProjectionIndex("idx_claim_concept_link_role", ("role",)),
    ),
)


CLAIM_NUMERIC_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_numeric_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("value", "REAL"),
        ProjectionColumn("lower_bound", "REAL"),
        ProjectionColumn("upper_bound", "REAL"),
        ProjectionColumn("uncertainty", "REAL"),
        ProjectionColumn("uncertainty_type", "TEXT"),
        ProjectionColumn("sample_size", "INTEGER"),
        ProjectionColumn("unit", "TEXT"),
        ProjectionColumn("value_si", "REAL"),
        ProjectionColumn("lower_bound_si", "REAL"),
        ProjectionColumn("upper_bound_si", "REAL"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
)


CLAIM_TEXT_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_text_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("conditions_ir", "TEXT"),
        ProjectionColumn("statement", "TEXT"),
        ProjectionColumn("expression", "TEXT"),
        ProjectionColumn("sympy_generated", "TEXT"),
        ProjectionColumn("sympy_error", "TEXT"),
        ProjectionColumn("name", "TEXT"),
        ProjectionColumn("measure", "TEXT"),
        ProjectionColumn("listener_population", "TEXT"),
        ProjectionColumn("methodology", "TEXT"),
        ProjectionColumn("notes", "TEXT"),
        ProjectionColumn("description", "TEXT"),
        ProjectionColumn("auto_summary", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
)


CLAIM_ALGORITHM_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_algorithm_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("body", "TEXT"),
        ProjectionColumn("canonical_ast", "TEXT"),
        ProjectionColumn("variables_json", "TEXT"),
        ProjectionColumn("algorithm_stage", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
    indexes=(ProjectionIndex("idx_claim_algorithm_stage", ("algorithm_stage",)),),
)


CONFLICT_WITNESS_PROJECTION = ProjectionTable(
    name="conflict_witness",
    columns=(
        ProjectionColumn("id", "INTEGER PRIMARY KEY AUTOINCREMENT", insertable=False),
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("claim_a_id", "TEXT", nullable=False),
        ProjectionColumn("claim_b_id", "TEXT", nullable=False),
        ProjectionColumn("warning_class", "TEXT", nullable=False),
        ProjectionColumn("conditions_a", "TEXT"),
        ProjectionColumn("conditions_b", "TEXT"),
        ProjectionColumn("value_a", "TEXT"),
        ProjectionColumn("value_b", "TEXT"),
        ProjectionColumn("derivation_chain", "TEXT"),
    ),
    indexes=(ProjectionIndex("idx_conflict_witness_concept", ("concept_id",)),),
)


JUSTIFICATION_PROJECTION = ProjectionTable(
    name="justification",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("justification_kind", "TEXT", nullable=False),
        ProjectionColumn("conclusion_claim_id", "TEXT", nullable=False),
        ProjectionColumn("premise_claim_ids", "TEXT", nullable=False),
        ProjectionColumn("source_relation_type", "TEXT"),
        ProjectionColumn("source_claim_id", "TEXT"),
        ProjectionColumn("provenance_json", "TEXT"),
        ProjectionColumn("rule_strength", "TEXT", nullable=False, default_sql="'defeasible'"),
    ),
)


CLAIM_FTS_PROJECTION = FtsProjection(
    table="claim_fts",
    key_column="claim_id",
    columns=("statement", "conditions", "expression"),
    source_query="""
        SELECT
            c.id AS claim_id,
            COALESCE(t.statement, '') AS statement,
            COALESCE(
                (
                    SELECT group_concat(value, ' ')
                    FROM json_each(t.conditions_cel)
                ),
                ''
            ) AS conditions,
            COALESCE(t.expression, '') AS expression
        FROM claim_core c
        JOIN claim_text_payload t ON t.claim_id = c.id
        ORDER BY c.seq
    """,
)


CLAIM_EMBEDDING_STATUS_PROJECTION = embedding_status_projection(
    name="embedding_status",
    entity_id_column="claim_id",
    index_name="idx_embedding_status_model_identity",
)


CLAIM_VEC_PROJECTION = rowid_vec_projection("claim_vec_{model_identity_hash}")


def populate_raw_id_quarantine_records(
    conn: sqlite3.Connection,
    rows: RawIdQuarantineSidecarRows,
) -> None:
    from propstore.families.diagnostics.declaration import BUILD_DIAGNOSTICS_PROJECTION

    CLAIM_CORE_PROJECTION.insert_rows(conn, (row.values for row in rows.claim_rows))
    for row in rows.diagnostic_rows:
        BUILD_DIAGNOSTICS_PROJECTION.insert_row(conn, row)


def populate_claims(
    conn: sqlite3.Connection,
    rows: ClaimSidecarRows,
) -> None:
    """Populate normalized claim storage from compiled sidecar rows.

    Schema-v3 behavior (``reviews/2026-04-16-code-review/workstreams/
    ws-z-render-gates.md`` finding 3.2): the file-level ``stage`` marker
    (e.g. ``'draft'``) is threaded from the claim-file document onto each
    ``claim_core`` row. Drafts populate normally; render-policy filtering
    (phase 4) decides visibility.

    ``artifact_id is the logical id`` for a claim. ``version_id`` is the
    content identity. Duplicate rows with the same ``artifact_id`` and
    same ``version_id`` are idempotent; duplicate logical ids with
    different versions emit a blocking ``claim_version_conflict``
    diagnostic instead of silently taking the first writer.
    """

    from propstore.families.relations.declaration import RELATION_EDGE_PROJECTION

    seen_claim_versions: dict[str, str] = {}
    emitted_conflicts: set[tuple[str, str, str]] = set()
    payloads_by_claim_id = {
        numeric_row.values["claim_id"]: (numeric_row, text_row, algorithm_row)
        for numeric_row, text_row, algorithm_row in zip(
            rows.numeric_payload_rows,
            rows.text_payload_rows,
            rows.algorithm_payload_rows,
            strict=True,
        )
    }
    for row in rows.claim_core_rows:
        claim_id = row.values.get("id")
        version_id = row.values.get("version_id")
        if isinstance(claim_id, str) and claim_id in seen_claim_versions:
            existing_version = seen_claim_versions[claim_id]
            new_version = str(version_id or "")
            if existing_version == new_version:
                continue
            conflict_key = (claim_id, existing_version, new_version)
            if conflict_key not in emitted_conflicts:
                _insert_claim_version_conflict(
                    conn,
                    claim_id=claim_id,
                    existing_version=existing_version,
                    new_version=new_version,
                    source_ref=str(row.values.get("primary_logical_id") or claim_id),
                )
                emitted_conflicts.add(conflict_key)
            continue
        CLAIM_CORE_PROJECTION.insert_row(conn, row.values)
        numeric_row, text_row, algorithm_row = payloads_by_claim_id[claim_id]
        CLAIM_NUMERIC_PAYLOAD_PROJECTION.insert_row(conn, numeric_row.values)
        CLAIM_TEXT_PAYLOAD_PROJECTION.insert_row(conn, text_row.values)
        CLAIM_ALGORITHM_PAYLOAD_PROJECTION.insert_row(conn, algorithm_row.values)
        if isinstance(claim_id, str):
            seen_claim_versions[claim_id] = str(version_id or "")
    seen_link_keys: set[tuple[object, object, object, object]] = set()
    for row in rows.claim_link_rows:
        key = (
            row.values["claim_id"],
            row.values["role"],
            row.values["ordinal"],
            row.values["concept_id"],
        )
        if key in seen_link_keys:
            continue
        seen_link_keys.add(key)
        CLAIM_CONCEPT_LINK_PROJECTION.insert_row(conn, row)
    if rows.stance_rows:
        RELATION_EDGE_PROJECTION.insert_rows(conn, (stance_row.values for stance_row in rows.stance_rows))


def _insert_claim_version_conflict(
    conn: sqlite3.Connection,
    *,
    claim_id: str,
    existing_version: str,
    new_version: str,
    source_ref: str,
) -> None:
    from propstore.families.diagnostics.declaration import BUILD_DIAGNOSTICS_PROJECTION

    BUILD_DIAGNOSTICS_PROJECTION.insert_row(
        conn,
        BUILD_DIAGNOSTICS_PROJECTION.row(
            claim_id=claim_id,
            source_kind="claim",
            source_ref=source_ref,
            diagnostic_kind="claim_version_conflict",
            severity="error",
            blocking=1,
            message=f"Claim logical id {claim_id!r} appears with multiple version_id values",
            file=None,
            detail_json=json.dumps(
                {
                    "existing_version_id": existing_version,
                    "new_version_id": new_version,
                },
                sort_keys=True,
            ),
        ),
    )


def populate_stances(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    from propstore.families.relations.declaration import RELATION_EDGE_PROJECTION

    RELATION_EDGE_PROJECTION.insert_rows(conn, (row.values for row in rows))


def populate_authored_justifications(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    JUSTIFICATION_PROJECTION.insert_rows(conn, rows, or_ignore=True)


def populate_conflicts(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    CONFLICT_WITNESS_PROJECTION.insert_rows(conn, rows)
