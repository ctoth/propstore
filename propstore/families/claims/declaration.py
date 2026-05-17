"""Claim-side compilation helpers for the sidecar.

Raw-id quarantine path (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): claims whose raw ``id`` never
canonicalized are still given a ``claim_core`` row with a synthetic id
and ``build_status='blocked'``, plus a ``build_diagnostics`` row
describing why. This implements discipline rule 5 (filter at render, not
at build) — no data is refused; the render layer decides what to show.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from quire.references import FamilyReferenceIndex
from quire.projections import (
    ARTIFACT_ID_FIELD,
    AUTOINCREMENT_ID_FIELD,
    CONDITIONS_CEL_FIELD,
    CONDITIONS_IR_FIELD,
    CONTENT_HASH_FIELD,
    FtsProjection,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionRow,
    ProjectionTable,
    LOGICAL_IDS_JSON_FIELD,
    PRIMARY_LOGICAL_ID_FIELD,
    PROVENANCE_JSON_FIELD,
    SEQUENCE_FIELD,
    VERSION_ID_FIELD,
    family_reference_field,
    integer_field,
    real_field,
    text_field,
)
from quire.sqlite_vec_store import embedding_status_projection, rowid_vec_projection
from propstore.claims import (
    ClaimFileEntry,
    claim_file_filename,
    claim_file_stage,
)
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
from propstore.compiler.ir import ClaimCompilationBundle
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
from propstore.families.claims.references import (
    ClaimReferenceRecord,
    build_claim_file_reference_index,
)
from propstore.families.claims.storage import (
    extract_deferred_stance_rows_with_diagnostics,
    prepare_claim_concept_link_rows,
    prepare_claim_insert_row,
)
from propstore.families.claims.stages import (
    ClaimSidecarRows,
    RawIdQuarantineRecord,
    RawIdQuarantineSidecarRows,
)
from propstore.families.diagnostics.declaration import (
    BUILD_DIAGNOSTICS_PROJECTION,
    QuarantineDiagnostic,
    delete_promotion_blocked_diagnostics,
)
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.relations.declaration import claim_stance_projection_row

if TYPE_CHECKING:
    from propstore.core.graph_types import ProvenanceRecord
    from propstore.core.justifications import CanonicalJustification


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
        object.__setattr__(self, "claim_id", to_claim_id(self.claim_id))
        object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))
        object.__setattr__(self, "role", _require_claim_concept_link_role(self.role))


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
        base = CLAIM_ROW_GENERIC_MODEL.from_row(row_map)
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
        return replace(base, source=source)

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
        data = {
            key: value
            for key, value in CLAIM_ROW_GENERIC_MODEL.to_mapping(self).items()
            if value is not None or key in {"logical_id", "logical_ids"}
        }
        source_dict = None if self.source is None or self.source.is_empty else self.source.to_dict()
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
            "source_slug": None if self.source is None else self.source.slug,
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
        }
        for key, value in optional_fields.items():
            if value is not None:
                data[key] = value
        if self.concept_links:
            data["concept_links"] = [
                {
                    key: value
                    for key, value in row.values.items()
                    if value is not None
                }
                for row in CLAIM_CONCEPT_LINKS_PATH.encode_rows(self)
            ]
        if source_dict is not None:
            data["source"] = source_dict
        if source_quality is not None:
            data["source_quality_opinion"] = source_quality
        data.update(self.attributes)
        return data


ClaimRowInput = ClaimRow | Mapping[str, Any]


from propstore.families.claims.projection_model import (  # noqa: E402
    CLAIM_CONCEPT_LINK_ROW_MODEL,
    CLAIM_CONCEPT_LINKS_PATH,
    CLAIM_ROW_GENERIC_MODEL,
)


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
        ARTIFACT_ID_FIELD.column(primary_key=True),
        PRIMARY_LOGICAL_ID_FIELD.column(),
        LOGICAL_IDS_JSON_FIELD.column(),
        VERSION_ID_FIELD.column(),
        CONTENT_HASH_FIELD.column(default_sql="''"),
        SEQUENCE_FIELD.column(),
        text_field("type", nullable=False).column(),
        text_field("target_concept").column(),
        text_field("source_slug").column(),
        text_field("source_paper", nullable=False).column(),
        integer_field("provenance_page", nullable=False).column(),
        PROVENANCE_JSON_FIELD.column(),
        family_reference_field("context").column(),
        text_field("premise_kind", nullable=False).column(default_sql="'ordinary'"),
        text_field("branch").column(),
        text_field("build_status", nullable=False).column(default_sql="'ingested'"),
        text_field("stage").column(),
        text_field("promotion_status").column(),
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
        family_reference_field("claim", nullable=False).column(),
        family_reference_field("concept", nullable=False).column(),
        text_field("role", nullable=False).column(),
        integer_field("ordinal", nullable=False).column(),
        text_field("binding_name").column(),
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
    row_factory=CLAIM_CONCEPT_LINK_ROW_MODEL.from_row,
)


CLAIM_NUMERIC_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_numeric_payload",
    columns=(
        family_reference_field("claim").column(primary_key=True),
        real_field("value").column(),
        real_field("lower_bound").column(),
        real_field("upper_bound").column(),
        real_field("uncertainty").column(),
        text_field("uncertainty_type").column(),
        integer_field("sample_size").column(),
        text_field("unit").column(),
        real_field("value_si").column(),
        real_field("lower_bound_si").column(),
        real_field("upper_bound_si").column(),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
)


CLAIM_TEXT_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_text_payload",
    columns=(
        family_reference_field("claim").column(primary_key=True),
        CONDITIONS_CEL_FIELD.column(),
        CONDITIONS_IR_FIELD.column(),
        text_field("statement").column(),
        text_field("expression").column(),
        text_field("sympy_generated").column(),
        text_field("sympy_error").column(),
        text_field("name").column(),
        text_field("measure").column(),
        text_field("listener_population").column(),
        text_field("methodology").column(),
        text_field("notes").column(),
        text_field("description").column(),
        text_field("auto_summary").column(),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
)


CLAIM_ALGORITHM_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_algorithm_payload",
    columns=(
        family_reference_field("claim").column(primary_key=True),
        text_field("body").column(),
        text_field("canonical_ast").column(),
        text_field("variables_json").column(),
        text_field("algorithm_stage").column(),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
    indexes=(ProjectionIndex("idx_claim_algorithm_stage", ("algorithm_stage",)),),
)


CONFLICT_WITNESS_PROJECTION = ProjectionTable(
    name="conflict_witness",
    columns=(
        AUTOINCREMENT_ID_FIELD.column(),
        family_reference_field("concept", nullable=False).column(),
        text_field("claim_a_id", nullable=False).column(),
        text_field("claim_b_id", nullable=False).column(),
        text_field("warning_class", nullable=False).column(),
        text_field("conditions_a").column(),
        text_field("conditions_b").column(),
        text_field("value_a").column(),
        text_field("value_b").column(),
        text_field("derivation_chain").column(),
    ),
    indexes=(ProjectionIndex("idx_conflict_witness_concept", ("concept_id",)),),
)


JUSTIFICATION_PROJECTION = ProjectionTable(
    name="justification",
    columns=(
        ARTIFACT_ID_FIELD.column(primary_key=True),
        text_field("justification_kind", nullable=False).column(),
        family_reference_field("claim", role="conclusion", nullable=False).column(),
        text_field("premise_claim_ids", nullable=False).column(),
        text_field("source_relation_type").column(),
        family_reference_field("claim", role="source").column(),
        PROVENANCE_JSON_FIELD.column(),
        text_field("rule_strength", nullable=False).column(default_sql="'defeasible'"),
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


def compile_claim_sidecar_rows(
    claim_bundle: ClaimCompilationBundle,
    concept_registry: dict,
    *,
    form_registry: dict | None = None,
) -> ClaimSidecarRows:
    claim_seq = 0
    claim_core_rows: list[ProjectionRow] = []
    numeric_payload_rows: list[ProjectionRow] = []
    text_payload_rows: list[ProjectionRow] = []
    algorithm_payload_rows: list[ProjectionRow] = []
    claim_link_rows: list[ProjectionRow] = []
    stance_rows: list[ProjectionRow] = []
    quarantine_diagnostics: list[QuarantineDiagnostic] = []
    claim_index = build_claim_file_reference_index(
        claim_bundle.normalized_claim_files
    )
    file_stage_by_filename: dict[str, str | None] = {
        claim_file_filename(claim_file): claim_file_stage(claim_file)
        for claim_file in claim_bundle.normalized_claim_files
    }

    for semantic_file in claim_bundle.semantic_files:
        file_stage = file_stage_by_filename.get(
            claim_file_filename(semantic_file.normalized_entry)
        )
        for semantic_claim in semantic_file.claims:
            claim_seq += 1
            row = prepare_claim_insert_row(
                semantic_claim,
                semantic_claim.source_paper,
                claim_seq=claim_seq,
                concept_registry=concept_registry,
                form_registry=form_registry,
            )
            if file_stage is not None:
                row["stage"] = file_stage
            claim_core_rows.append(
                CLAIM_CORE_PROJECTION.row(
                    id=row["id"],
                    primary_logical_id=row["primary_logical_id"],
                    logical_ids_json=row["logical_ids_json"],
                    version_id=row["version_id"],
                    content_hash=row.get("content_hash") or "",
                    seq=row["seq"],
                    type=row["type"],
                    target_concept=row["target_concept"],
                    source_slug=row["source_slug"],
                    source_paper=row["source_paper"],
                    provenance_page=row["provenance_page"],
                    provenance_json=row["provenance_json"],
                    context_id=row["context_id"],
                    premise_kind=row.get("premise_kind") or "ordinary",
                    branch=row.get("branch"),
                    build_status=row.get("build_status") or "ingested",
                    stage=row.get("stage"),
                    promotion_status=row.get("promotion_status"),
                )
            )
            numeric_payload_rows.append(
                CLAIM_NUMERIC_PAYLOAD_PROJECTION.row(
                    claim_id=row["id"],
                    value=row["value"],
                    lower_bound=row["lower_bound"],
                    upper_bound=row["upper_bound"],
                    uncertainty=row["uncertainty"],
                    uncertainty_type=row["uncertainty_type"],
                    sample_size=row["sample_size"],
                    unit=row["unit"],
                    value_si=row["value_si"],
                    lower_bound_si=row["lower_bound_si"],
                    upper_bound_si=row["upper_bound_si"],
                )
            )
            text_payload_rows.append(
                CLAIM_TEXT_PAYLOAD_PROJECTION.row(
                    claim_id=row["id"],
                    conditions_cel=row["conditions_cel"],
                    conditions_ir=row["conditions_ir"],
                    statement=row["statement"],
                    expression=row["expression"],
                    sympy_generated=row["sympy_generated"],
                    sympy_error=row["sympy_error"],
                    name=row["name"],
                    measure=row["measure"],
                    listener_population=row["listener_population"],
                    methodology=row["methodology"],
                    notes=row["notes"],
                    description=row["description"],
                    auto_summary=row["auto_summary"],
                )
            )
            algorithm_payload_rows.append(
                CLAIM_ALGORITHM_PAYLOAD_PROJECTION.row(
                    claim_id=row["id"],
                    body=row["body"],
                    canonical_ast=row["canonical_ast"],
                    variables_json=row["variables_json"],
                    algorithm_stage=row["algorithm_stage"],
                )
            )
            for values in prepare_claim_concept_link_rows(semantic_claim):
                claim_link_rows.append(
                    CLAIM_CONCEPT_LINK_PROJECTION.row(
                        claim_id=values[0],
                        concept_id=values[1],
                        role=values[2],
                        ordinal=values[3],
                        binding_name=values[4],
                    )
                )
            deferred_stance_rows, deferred_stance_diagnostics = (
                extract_deferred_stance_rows_with_diagnostics(
                    semantic_claim,
                    claim_index,
                )
            )
            stance_rows.extend(
                claim_stance_projection_row(values)
                for values in deferred_stance_rows
            )
            quarantine_diagnostics.extend(deferred_stance_diagnostics)

    return ClaimSidecarRows(
        claim_core_rows=tuple(claim_core_rows),
        numeric_payload_rows=tuple(numeric_payload_rows),
        text_payload_rows=tuple(text_payload_rows),
        algorithm_payload_rows=tuple(algorithm_payload_rows),
        claim_link_rows=tuple(claim_link_rows),
        stance_rows=tuple(stance_rows),
        quarantine_diagnostics=tuple(quarantine_diagnostics),
    )


def compile_authored_justification_sidecar_rows(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[ProjectionRow, ...]:
    rows, diagnostics = compile_authored_justification_sidecar_rows_with_diagnostics(
        justification_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def compile_authored_justification_sidecar_rows_with_diagnostics(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[ProjectionRow, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    rows: list[ProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, justification in justification_entries:
        justification_payload = justification.to_payload()
        justification_id = justification.id
        conclusion = claim_index.resolve_id(justification.conclusion)
        if not isinstance(justification_id, str) or not justification_id:
            raise ValueError(
                f"justification artifact {filename} missing id"
            )
        if not isinstance(conclusion, str) or conclusion not in valid_claims:
            message = (
                f"justification artifact {filename} references "
                f"nonexistent conclusion '{conclusion}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=conclusion or justification.conclusion or filename,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=message,
                    file=filename,
                )
            )
            continue
        resolved_premises: list[str] = []
        missing_premise_ref: str | None = None
        for premise in justification.premises:
            resolved_premise = claim_index.resolve_id(premise)
            if (
                not isinstance(resolved_premise, str)
                or resolved_premise not in valid_claims
            ):
                if isinstance(resolved_premise, str) and resolved_premise:
                    missing_premise_ref = resolved_premise
                elif isinstance(premise, str) and premise:
                    missing_premise_ref = premise
                else:
                    missing_premise_ref = filename
                break
            resolved_premises.append(resolved_premise)
        if missing_premise_ref is not None:
            message = (
                f"justification artifact {filename} references "
                f"nonexistent premise '{missing_premise_ref}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_premise_ref,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        provenance = justification_payload.get("provenance")
        attack_target = justification_payload.get("attack_target")
        provenance_payload: dict[str, object] = {}
        if isinstance(provenance, dict):
            provenance_payload.update(provenance)
        if isinstance(attack_target, dict):
            provenance_payload["attack_target"] = attack_target

        rows.append(
            JUSTIFICATION_PROJECTION.row(
                id=justification_id,
                justification_kind=str(justification.rule_kind or "reported_claim"),
                conclusion_claim_id=conclusion,
                premise_claim_ids=json.dumps(resolved_premises),
                source_relation_type=None,
                source_claim_id=None,
                provenance_json=json.dumps(provenance_payload)
                if provenance_payload
                else None,
                rule_strength=str(justification.rule_strength or "defeasible"),
            )
        )
    return tuple(rows), tuple(diagnostics)


def compile_raw_id_quarantine_sidecar_rows(
    records: Sequence[RawIdQuarantineRecord],
) -> RawIdQuarantineSidecarRows:
    claim_rows: list[ProjectionRow] = []
    diagnostic_rows: list[ProjectionRow] = []

    for record in records:
        claim_rows.append(
            CLAIM_CORE_PROJECTION.row(
                id=record.synthetic_id,
                primary_logical_id="",
                logical_ids_json="[]",
                version_id="",
                content_hash="",
                seq=record.seq,
                type="quarantine",
                target_concept=None,
                source_slug=record.source_paper,
                source_paper=record.source_paper,
                provenance_page=0,
                provenance_json=None,
                context_id=None,
                premise_kind="ordinary",
                branch=None,
                build_status="blocked",
                stage=None,
                promotion_status=None,
            )
        )
        diagnostic_rows.append(
            BUILD_DIAGNOSTICS_PROJECTION.row(
                claim_id=record.synthetic_id,
                source_kind="claim",
                source_ref=record.raw_id,
                diagnostic_kind="raw_id_input",
                severity="error",
                blocking=1,
                message=record.message,
                file=record.filename,
                detail_json=record.detail_json,
            )
        )

    return RawIdQuarantineSidecarRows(
        claim_rows=tuple(claim_rows),
        diagnostic_rows=tuple(diagnostic_rows),
    )


def compile_conflict_sidecar_rows(
    claim_files: Sequence[ClaimFileEntry],
    concept_registry: dict,
    cel_registry: dict,
    lifting_system=None,
) -> tuple[ProjectionRow, ...]:
    conflict_claims = conflict_claims_from_claim_files(claim_files)
    records = detect_conflicts(
        conflict_claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )
    records.extend(
        detect_transitive_conflicts(
            conflict_claims,
            concept_registry,
            lifting_system=lifting_system,
        )
    )
    return tuple(
        CONFLICT_WITNESS_PROJECTION.row(
            concept_id=record.concept_id,
            claim_a_id=record.claim_a_id,
            claim_b_id=record.claim_b_id,
            warning_class=record.warning_class.value,
            conditions_a=json.dumps(record.conditions_a),
            conditions_b=json.dumps(record.conditions_b),
            value_a=record.value_a,
            value_b=record.value_b,
            derivation_chain=record.derivation_chain,
        )
        for record in records
    )


def populate_raw_id_quarantine_records(
    conn: sqlite3.Connection,
    rows: RawIdQuarantineSidecarRows,
) -> None:
    CLAIM_CORE_PROJECTION.insert_rows(conn, (row.values for row in rows.claim_rows))
    for row in rows.diagnostic_rows:
        BUILD_DIAGNOSTICS_PROJECTION.insert_row(conn, row)


def populate_promotion_blocked_claims(
    conn: sqlite3.Connection,
    claim_rows: Sequence[ProjectionRow],
    diagnostic_rows: Sequence[ProjectionRow],
) -> None:
    if not claim_rows and not diagnostic_rows:
        return
    child_claim_tables = {
        row[0]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (
                  'claim_concept_link',
                  'claim_numeric_payload',
                  'claim_text_payload',
                  'claim_algorithm_payload',
                  'micropublication_claim'
              )
            """
        ).fetchall()
    }
    schema_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "concept" not in schema_tables:
        child_claim_tables.discard("claim_concept_link")
    claim_rows_by_id = {str(row.values["id"]): row for row in claim_rows}
    claim_ids = tuple(claim_rows_by_id)
    for claim_id in claim_ids:
        for table_name in (
            "claim_concept_link",
            "claim_numeric_payload",
            "claim_text_payload",
            "claim_algorithm_payload",
            "micropublication_claim",
        ):
            if table_name not in child_claim_tables:
                continue
            conn.execute(
                f"DELETE FROM {table_name} WHERE claim_id = ?",
                (claim_id,),
            )
        delete_claim_core_row(conn, claim_id)
        delete_promotion_blocked_diagnostics(conn, claim_id)
    CLAIM_CORE_PROJECTION.insert_rows(conn, (row.values for row in claim_rows_by_id.values()))
    for row in diagnostic_rows:
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
