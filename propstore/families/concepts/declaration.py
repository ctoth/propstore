"""Concept family projection, row, and derived-query declaration."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ast_equiv import canonical_dump
from ast_equiv.canonicalizer import AlgorithmParseError
from quire.projections import (
    ARTIFACT_ID_FIELD,
    AUTOINCREMENT_ID_FIELD,
    CONDITIONS_CEL_FIELD,
    CONDITIONS_IR_FIELD,
    CONTENT_HASH_FIELD,
    FtsProjection,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionTable,
    LOGICAL_IDS_JSON_FIELD,
    PRIMARY_LOGICAL_ID_FIELD,
    SEQUENCE_FIELD,
    VERSION_ID_FIELD,
    family_reference_field,
    integer_field,
    real_field,
    text_field,
)
from quire.sqlite_vec_store import embedding_status_projection, rowid_vec_projection

from propstore.core.concept_status import ConceptStatus, coerce_concept_status
from propstore.core.conditions import (
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)
from propstore.core.conditions.registry import ConceptInfo, with_standard_synthetic_bindings
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.dimensions import verify_form_algebra_dimensions
from propstore.families.forms.stages import FormDefinition, kind_value_from_form_name
from propstore.families.relations.declaration import RELATION_EDGE_PROJECTION
from propstore.parameterization_groups import build_groups
from propstore.propagation import rewrite_parameterization_symbols

if TYPE_CHECKING:
    from quire.projections import ProjectionRow
    from propstore.families.concepts.stages import ConceptRecord, LoadedConcept


@dataclass(frozen=True)
class ConceptRelationshipProjectionRow:
    source_id: str
    relationship_type: str
    target_id: str
    conditions_cel: str | None
    note: str | None


@dataclass(frozen=True)
class ConceptSidecarRows:
    form_rows: tuple["ProjectionRow", ...]
    concept_rows: tuple["ProjectionRow", ...]
    alias_rows: tuple["ProjectionRow", ...]
    relationship_rows: tuple[ConceptRelationshipProjectionRow, ...]
    relation_edge_rows: tuple["ProjectionRow", ...]
    parameterization_rows: tuple["ProjectionRow", ...]
    parameterization_group_rows: tuple["ProjectionRow", ...]
    form_algebra_rows: tuple["ProjectionRow", ...]


def _concept_symbol_candidates(record: "ConceptRecord") -> tuple[str, ...]:
    return record.reference_keys()


def compile_concept_sidecar_rows(
    concepts: list["LoadedConcept"],
    form_registry: dict[str, FormDefinition],
    cel_registry: dict[str, ConceptInfo],
) -> ConceptSidecarRows:
    form_rows: list["ProjectionRow"] = []
    concept_rows: list["ProjectionRow"] = []
    alias_rows: list["ProjectionRow"] = []
    relationship_rows: list[ConceptRelationshipProjectionRow] = []
    relation_edge_rows: list["ProjectionRow"] = []
    parameterization_rows: list["ProjectionRow"] = []
    parameterization_group_rows: list["ProjectionRow"] = []
    form_algebra_rows: list["ProjectionRow"] = []

    for form_definition in form_registry.values():
        dimensions_json = (
            json.dumps(form_definition.dimensions)
            if form_definition.dimensions is not None
            else None
        )
        form_rows.append(
            FORM_PROJECTION.row(
                name=form_definition.name,
                kind=form_definition.kind.value
                if hasattr(form_definition.kind, "value")
                else str(form_definition.kind),
                unit_symbol=form_definition.unit_symbol,
                is_dimensionless=1 if form_definition.is_dimensionless else 0,
                dimensions=dimensions_json,
            )
        )

    condition_registry = with_standard_synthetic_bindings(cel_registry)

    for seq, concept in enumerate(concepts, 1):
        record = concept.record
        content_hash = record.version_id.removeprefix("sha256:")[:16]
        form_definition = form_registry.get(record.form)
        is_dimensionless = (
            1
            if form_definition is not None and form_definition.is_dimensionless
            else 0
        )
        unit_symbol = form_definition.unit_symbol if form_definition is not None else None
        form_parameters_json = (
            json.dumps(record.form_parameters)
            if record.form_parameters
            else None
        )
        range_min = None if record.range is None else record.range[0]
        range_max = None if record.range is None else record.range[1]
        concept_id = str(record.artifact_id)

        concept_rows.append(
            CONCEPT_PROJECTION.row(
                id=concept_id,
                primary_logical_id=record.primary_logical_id or "",
                logical_ids_json=json.dumps(
                    [logical_id.to_payload() for logical_id in record.logical_ids]
                ),
                version_id=record.version_id,
                content_hash=content_hash,
                seq=seq,
                canonical_name=record.canonical_name,
                status=record.status.value,
                domain=record.domain,
                definition=record.definition,
                kind_type=form_definition.kind.value
                if form_definition is not None
                else kind_value_from_form_name(record.form),
                form=record.form,
                form_parameters=form_parameters_json,
                range_min=range_min,
                range_max=range_max,
                is_dimensionless=is_dimensionless,
                unit_symbol=unit_symbol,
                created_date=record.created_date,
                last_modified=record.last_modified,
            )
        )

        for alias in record.aliases:
            alias_rows.append(
                ALIAS_PROJECTION.row(
                    concept_id=concept_id,
                    alias_name=alias.name,
                    source=alias.source,
                )
            )

        for relationship in record.relationships:
            conditions_json = (
                json.dumps(list(relationship.conditions))
                if relationship.conditions
                else None
            )
            target_id = str(relationship.target)
            relationship_rows.append(
                ConceptRelationshipProjectionRow(
                    source_id=concept_id,
                    relationship_type=relationship.relationship_type,
                    target_id=target_id,
                    conditions_cel=conditions_json,
                    note=relationship.note,
                )
            )
            relation_edge_rows.append(
                RELATION_EDGE_PROJECTION.row(
                    source_kind="concept",
                    source_id=concept_id,
                    relation_type=relationship.relationship_type,
                    target_kind="concept",
                    target_id=target_id,
                    conditions_cel=conditions_json,
                    note=relationship.note,
                )
            )

        for parameterization in record.parameterizations:
            if parameterization.formula is None:
                raise ValueError(f"Parameterization for {concept_id} is missing formula")
            if parameterization.exactness is None:
                raise ValueError(f"Parameterization for {concept_id} is missing exactness")
            inputs = [str(input_id) for input_id in parameterization.inputs]
            conditions_json = (
                json.dumps(list(parameterization.conditions))
                if parameterization.conditions
                else None
            )
            conditions_ir = (
                json.dumps(
                    checked_condition_set_to_json(
                        checked_condition_set(
                            check_condition_ir(condition, condition_registry)
                            for condition in parameterization.conditions
                        )
                    ),
                    sort_keys=True,
                )
                if parameterization.conditions
                else None
            )
            parameterization_rows.append(
                PARAMETERIZATION_PROJECTION.row(
                    output_concept_id=concept_id,
                    concept_ids=json.dumps(inputs),
                    formula=parameterization.formula,
                    sympy=parameterization.sympy,
                    exactness=str(parameterization.exactness),
                    conditions_cel=conditions_json,
                    conditions_ir=conditions_ir,
                )
            )

    groups = build_groups(concepts)
    for group_id, group_members in enumerate(sorted(groups, key=lambda group: min(group))):
        for concept_id in sorted(group_members):
            parameterization_group_rows.append(
                PARAMETERIZATION_GROUP_PROJECTION.row(
                    concept_id=concept_id,
                    group_id=group_id,
                )
            )

    form_algebra_rows.extend(_compile_form_algebra_rows(concepts, form_registry))

    return ConceptSidecarRows(
        form_rows=tuple(form_rows),
        concept_rows=tuple(concept_rows),
        alias_rows=tuple(alias_rows),
        relationship_rows=tuple(relationship_rows),
        relation_edge_rows=tuple(relation_edge_rows),
        parameterization_rows=tuple(parameterization_rows),
        parameterization_group_rows=tuple(parameterization_group_rows),
        form_algebra_rows=tuple(form_algebra_rows),
    )


def _compile_form_algebra_rows(
    concepts: list["LoadedConcept"],
    form_registry: dict[str, FormDefinition],
) -> tuple["ProjectionRow", ...]:
    if not form_registry:
        return ()

    id_to_form: dict[str, str] = {}
    id_to_symbols: dict[str, tuple[str, ...]] = {}
    for concept in concepts:
        record = concept.record
        concept_id = str(record.artifact_id)
        id_to_form[concept_id] = record.form
        id_to_symbols[concept_id] = _concept_symbol_candidates(record)

    seen: set[tuple[object, ...]] = set()
    rows: list["ProjectionRow"] = []

    for concept in concepts:
        record = concept.record
        concept_id = str(record.artifact_id)
        output_form = id_to_form.get(concept_id)
        if not output_form:
            continue

        for parameterization in record.parameterizations:
            inputs = [str(input_id) for input_id in parameterization.inputs]
            if not inputs:
                continue

            input_forms: list[str] = []
            all_resolved = True
            for input_id in inputs:
                input_form = id_to_form.get(input_id)
                if not input_form:
                    all_resolved = False
                    break
                input_forms.append(input_form)
            if not all_resolved:
                continue

            sympy_str = parameterization.sympy
            operation = ""
            if sympy_str:
                operation = rewrite_parameterization_symbols(
                    sympy_str,
                    symbol_aliases={
                        concept_id: id_to_symbols.get(concept_id, ()),
                        **{
                            input_id: id_to_symbols.get(input_id, ())
                            for input_id in inputs
                        },
                    },
                    symbol_targets={
                        concept_id: output_form,
                        **{
                            input_id: id_to_form[input_id]
                            for input_id in inputs
                        },
                    },
                )
            if not operation:
                operation = parameterization.formula or ""

            dim_verified = 1
            if sympy_str and operation:
                output_fd = form_registry.get(output_form)
                input_fd_list = [form_registry.get(form_name) for form_name in input_forms]
                if output_fd is not None and all(fd is not None for fd in input_fd_list):
                    if not verify_form_algebra_dimensions(
                        output_fd,
                        input_fd_list,  # type: ignore[arg-type]
                        operation,
                    ):
                        dim_verified = 0
                else:
                    dim_verified = 0

            try:
                canonical_operation = canonical_dump(operation, {})
            except AlgorithmParseError:
                canonical_operation = operation
            dedup_key = (output_form, tuple(sorted(input_forms)), canonical_operation)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            rows.append(
                FORM_ALGEBRA_PROJECTION.row(
                    output_form=output_form,
                    input_forms=json.dumps(input_forms),
                    operation=operation,
                    source_concept_id=concept_id,
                    source_formula=parameterization.formula or "",
                    dim_verified=dim_verified,
                )
            )

    return tuple(rows)


@dataclass(frozen=True)
class ConceptRow:
    concept_id: ConceptId
    canonical_name: str
    status: ConceptStatus | None = None
    definition: str | None = None
    kind_type: str | None = None
    form: str | None = None
    domain: str | None = None
    form_parameters: str | None = None
    primary_logical_id: str | None = None
    logical_ids_json: str | None = None
    version_id: str | None = None
    content_hash: str | None = None
    seq: int | None = None
    range_min: float | None = None
    range_max: float | None = None
    is_dimensionless: int | None = None
    unit_symbol: str | None = None
    created_date: str | None = None
    last_modified: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status is not None:
            object.__setattr__(self, "status", coerce_concept_status(self.status))
        object.__setattr__(self, "attributes", dict(self.attributes))

    def parsed_logical_ids(self) -> list[dict[str, Any]]:
        if not self.logical_ids_json:
            return []
        try:
            loaded = json.loads(self.logical_ids_json)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []

    def attribute_mapping(self) -> dict[str, Any]:
        data = dict(self.attributes)
        for key in (
            "version_id",
            "content_hash",
            "seq",
            "range_min",
            "range_max",
            "is_dimensionless",
            "unit_symbol",
            "created_date",
            "last_modified",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data

    def attribute_value(self, key: str) -> Any:
        if hasattr(self, key):
            value = getattr(self, key)
            if value is not None:
                return value
        return dict(self.attributes).get(key)


@dataclass(frozen=True)
class ConceptEmbeddingSource:
    concept: ConceptRow
    seq: int
    content_hash: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParameterizationRow:
    output_concept_id: ConceptId
    concept_ids: str
    formula: str | None = None
    sympy: str | None = None
    exactness: Exactness | None = None
    conditions_cel: str | None = None
    conditions_ir: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "exactness", coerce_exactness(self.exactness))
        object.__setattr__(self, "attributes", dict(self.attributes))


ParameterizationRowInput = ParameterizationRow | Mapping[str, Any]


ConceptRowInput = ConceptRow | Mapping[str, Any]


from propstore.families.concepts.projection_model import (  # noqa: E402
    CONCEPT_ROW_MODEL,
    PARAMETERIZATION_ROW_MODEL,
)


CONCEPT_PROJECTION = ProjectionTable(
    name="concept",
    columns=(
        ARTIFACT_ID_FIELD.column(primary_key=True),
        PRIMARY_LOGICAL_ID_FIELD.column(),
        LOGICAL_IDS_JSON_FIELD.column(),
        VERSION_ID_FIELD.column(),
        CONTENT_HASH_FIELD.column(),
        SEQUENCE_FIELD.column(),
        text_field("canonical_name", nullable=False).column(),
        text_field("status", nullable=False).column(),
        text_field("domain").column(),
        text_field("definition", nullable=False).column(),
        text_field("kind_type", nullable=False).column(),
        text_field("form", nullable=False).column(),
        text_field("form_parameters").column(),
        real_field("range_min").column(),
        real_field("range_max").column(),
        integer_field("is_dimensionless", nullable=False).column(default_sql="0"),
        text_field("unit_symbol").column(),
        text_field("created_date").column(),
        text_field("last_modified").column(),
    ),
    indexes=(ProjectionIndex("idx_concept_primary_logical_id", ("primary_logical_id",)),),
    row_factory=CONCEPT_ROW_MODEL.from_row,
)


FORM_PROJECTION = ProjectionTable(
    name="form",
    columns=(
        text_field("name").column(primary_key=True),
        text_field("kind", nullable=False).column(),
        text_field("unit_symbol").column(),
        integer_field("is_dimensionless", nullable=False).column(default_sql="0"),
        text_field("dimensions").column(),
    ),
)


FORM_ALGEBRA_PROJECTION = ProjectionTable(
    name="form_algebra",
    columns=(
        AUTOINCREMENT_ID_FIELD.column(),
        text_field("output_form", nullable=False).column(),
        text_field("input_forms", nullable=False).column(),
        text_field("operation", nullable=False).column(),
        family_reference_field("concept", role="source").column(),
        text_field("source_formula").column(),
        integer_field("dim_verified", nullable=False).column(default_sql="1"),
    ),
    foreign_keys=(ProjectionForeignKey(("output_form",), "form", ("name",)),),
    indexes=(ProjectionIndex("idx_form_algebra_output", ("output_form",)),),
)


ALIAS_PROJECTION = ProjectionTable(
    name="alias",
    columns=(
        family_reference_field("concept", nullable=False).column(),
        text_field("alias_name", nullable=False).column(),
        text_field("source", nullable=False).column(),
    ),
    foreign_keys=(ProjectionForeignKey(("concept_id",), "concept", ("id",)),),
    indexes=(
        ProjectionIndex("idx_alias_name", ("alias_name",)),
        ProjectionIndex("idx_alias_concept", ("concept_id",)),
    ),
)


PARAMETERIZATION_GROUP_PROJECTION = ProjectionTable(
    name="parameterization_group",
    columns=(
        family_reference_field("concept", nullable=False).column(),
        integer_field("group_id", nullable=False).column(),
    ),
    foreign_keys=(ProjectionForeignKey(("concept_id",), "concept", ("id",)),),
    indexes=(ProjectionIndex("idx_param_group", ("group_id",)),),
)


PARAMETERIZATION_PROJECTION = ProjectionTable(
    name="parameterization",
    columns=(
        family_reference_field("concept", role="output", nullable=False).column(),
        text_field("concept_ids", nullable=False).column(),
        text_field("formula", nullable=False).column(),
        text_field("sympy").column(),
        text_field("exactness", nullable=False).column(),
        CONDITIONS_CEL_FIELD.column(),
        CONDITIONS_IR_FIELD.column(),
    ),
    foreign_keys=(ProjectionForeignKey(("output_concept_id",), "concept", ("id",)),),
    row_factory=PARAMETERIZATION_ROW_MODEL.from_row,
)


RELATIONSHIP_PROJECTION = ProjectionTable(
    name="relationship",
    columns=(
        text_field("source_id", nullable=False).column(),
        text_field("type", nullable=False).column(),
        text_field("target_id", nullable=False).column(),
        CONDITIONS_CEL_FIELD.column(),
        text_field("note").column(),
    ),
    foreign_keys=(
        ProjectionForeignKey(("source_id",), "concept", ("id",)),
        ProjectionForeignKey(("target_id",), "concept", ("id",)),
    ),
    indexes=(
        ProjectionIndex("idx_rel_source", ("source_id",)),
        ProjectionIndex("idx_rel_target", ("target_id",)),
    ),
)


CONCEPT_FTS_PROJECTION = FtsProjection(
    table="concept_fts",
    key_column="concept_id",
    columns=("canonical_name", "aliases", "definition", "conditions"),
    source_query="""
        SELECT
            c.id AS concept_id,
            c.canonical_name AS canonical_name,
            COALESCE(
                (
                    SELECT group_concat(a.alias_name, ' ')
                    FROM alias a
                    WHERE a.concept_id = c.id
                ),
                ''
            ) AS aliases,
            c.definition AS definition,
            COALESCE(
                (
                    SELECT group_concat(value, ' ')
                    FROM (
                        SELECT rel_condition.value AS value
                        FROM relationship r, json_each(r.conditions_cel) AS rel_condition
                        WHERE r.source_id = c.id
                          AND r.conditions_cel IS NOT NULL
                        UNION ALL
                        SELECT param_condition.value AS value
                        FROM parameterization p, json_each(p.conditions_cel) AS param_condition
                        WHERE p.output_concept_id = c.id
                          AND p.conditions_cel IS NOT NULL
                    )
                ),
                ''
            ) AS conditions
        FROM concept c
        ORDER BY c.seq
    """,
)


CONCEPT_EMBEDDING_STATUS_PROJECTION = embedding_status_projection(
    name="concept_embedding_status",
    entity_id_column="concept_id",
    index_name="idx_concept_embedding_status_model_identity",
)


CONCEPT_VEC_PROJECTION = rowid_vec_projection("concept_vec_{model_identity_hash}")


def populate_concept_sidecar_rows(
    conn: sqlite3.Connection,
    rows: ConceptSidecarRows,
) -> None:
    from propstore.families.relations.declaration import RELATION_EDGE_PROJECTION

    if rows.form_rows:
        FORM_PROJECTION.insert_rows(conn, rows.form_rows)
    if rows.concept_rows:
        CONCEPT_PROJECTION.insert_rows(conn, rows.concept_rows)
    if rows.alias_rows:
        ALIAS_PROJECTION.insert_rows(conn, rows.alias_rows)

    relationship_insert_sql = RELATIONSHIP_PROJECTION.insert_sql()
    for row in rows.relationship_rows:
        conn.execute(
            relationship_insert_sql,
            {
                "source_id": row.source_id,
                "type": row.relationship_type,
                "target_id": row.target_id,
                "conditions_cel": row.conditions_cel,
                "note": row.note,
            },
        )

    if rows.relation_edge_rows:
        RELATION_EDGE_PROJECTION.insert_rows(conn, rows.relation_edge_rows)
    if rows.parameterization_rows:
        PARAMETERIZATION_PROJECTION.insert_rows(conn, rows.parameterization_rows)
    if rows.parameterization_group_rows:
        PARAMETERIZATION_GROUP_PROJECTION.insert_rows(conn, rows.parameterization_group_rows)
    if rows.form_algebra_rows:
        FORM_ALGEBRA_PROJECTION.insert_rows(conn, rows.form_algebra_rows)


class ConceptSearchQuerySyntaxError(ValueError):
    pass


def _is_concept_search_syntax_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).casefold()
    return "fts5: syntax error" in message or "unterminated string" in message


def fetch_concept_search_hits(
    conn: sqlite3.Connection,
    *,
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT "
        "COALESCE(NULLIF(concept.primary_logical_id, ''), concept.id) AS handle, "
        "concept.primary_logical_id AS logical_id, "
        "concept_fts.canonical_name AS canonical_name, "
        "concept.status AS status, "
        "concept_fts.definition AS definition "
        "FROM concept_fts JOIN concept ON concept.id = concept_fts.concept_id "
        "WHERE concept_fts MATCH ? LIMIT ?",
        (query, limit),
    ).fetchall()
    decoded: list[dict[str, Any]] = []
    for row in rows:
        try:
            decoded.append(dict(row))
        except (TypeError, ValueError):
            decoded.append(
                {
                    "handle": row[0],
                    "logical_id": row[1],
                    "canonical_name": row[2],
                    "status": row[3],
                    "definition": row[4],
                }
            )
    return decoded


def fetch_concept_search_hits_from_sidecar(
    sidecar: Path,
    *,
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    from quire.derived_runtime import connect_sqlite_store_readonly

    conn = connect_sqlite_store_readonly(sidecar)
    try:
        try:
            return fetch_concept_search_hits(conn, query=query, limit=limit)
        except sqlite3.OperationalError as exc:
            if _is_concept_search_syntax_error(exc):
                raise ConceptSearchQuerySyntaxError(query) from exc
            raise
    finally:
        conn.close()


def select_concept_by_id(conn: sqlite3.Connection, concept_id: str) -> ConceptRow | None:
    row = conn.execute("SELECT * FROM concept WHERE id = ?", (concept_id,)).fetchone()
    if row is None:
        return None
    return CONCEPT_ROW_MODEL.from_row(dict(row))


def select_all_concepts(conn: sqlite3.Connection) -> list[ConceptRow]:
    rows = conn.execute("SELECT * FROM concept").fetchall()
    return [CONCEPT_ROW_MODEL.from_row(dict(row)) for row in rows]


def select_concept_embedding_sources(
    conn: sqlite3.Connection,
    entity_ids: Sequence[str] | None = None,
) -> list[ConceptEmbeddingSource]:
    query = """
        SELECT
            id,
            seq,
            content_hash,
            canonical_name,
            definition
        FROM concept
    """
    params: tuple[str, ...] = ()
    if entity_ids:
        placeholders = ",".join("?" for _ in entity_ids)
        query += f" WHERE id IN ({placeholders})"
        params = tuple(entity_ids)
    rows = conn.execute(query, params).fetchall()
    aliases = select_aliases_by_concept_id(conn, tuple(str(row["id"]) for row in rows))
    return [
        ConceptEmbeddingSource(
            concept=CONCEPT_ROW_MODEL.from_row(dict(row)),
            seq=int(row["seq"]),
            content_hash=str(row["content_hash"]),
            aliases=aliases.get(str(row["id"]), ()),
        )
        for row in rows
    ]


def resolve_concept_embedding_entity(conn: sqlite3.Connection, entity_id: str) -> tuple[str, int]:
    row = conn.execute(
        "SELECT id, seq FROM concept WHERE id = ? OR canonical_name = ?",
        (entity_id, entity_id),
    ).fetchone()
    if row is None:
        raise ValueError(f"Concept {entity_id} not found")
    return str(row["id"]), int(row["seq"])


def select_aliases_by_concept_id(
    conn: sqlite3.Connection,
    concept_ids: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    if not concept_ids:
        return {}
    placeholders = ",".join("?" for _ in concept_ids)
    rows = conn.execute(
        f"SELECT concept_id, alias_name FROM alias WHERE concept_id IN ({placeholders})",
        tuple(concept_ids),
    ).fetchall()
    aliases: dict[str, list[str]] = {}
    for row in rows:
        aliases.setdefault(str(row["concept_id"]), []).append(str(row["alias_name"]))
    return {
        concept_id: tuple(names)
        for concept_id, names in aliases.items()
    }


def select_concept_registry_rows(conn: sqlite3.Connection) -> list[ConceptRow]:
    rows = conn.execute(
        "SELECT id, canonical_name, kind_type, form_parameters FROM concept"
    ).fetchall()
    return [CONCEPT_ROW_MODEL.from_row(dict(row)) for row in rows]


def build_concept_logical_id_index(conn: sqlite3.Connection) -> dict[str, str]:
    index: dict[str, str] = {}
    rows = conn.execute(
        "SELECT id, primary_logical_id, logical_ids_json FROM concept"
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


def resolve_concept_alias(conn: sqlite3.Connection, alias: str) -> str | None:
    row = conn.execute(
        "SELECT concept_id FROM alias WHERE alias_name = ?",
        (alias,),
    ).fetchone()
    return None if row is None else str(row["concept_id"])


def resolve_concept_id(
    conn: sqlite3.Connection,
    name: str,
    *,
    logical_id_index: Mapping[str, str] | None = None,
) -> str | None:
    resolved = resolve_concept_alias(conn, name)
    if resolved:
        return resolved

    row = conn.execute("SELECT id FROM concept WHERE id = ?", (name,)).fetchone()
    if row is not None:
        return str(row["id"])

    row = conn.execute(
        "SELECT id FROM concept WHERE primary_logical_id = ?",
        (name,),
    ).fetchone()
    if row is not None:
        return str(row["id"])

    cached = None if logical_id_index is None else logical_id_index.get(name)
    if cached is not None:
        return cached

    row = conn.execute(
        "SELECT id FROM concept WHERE canonical_name = ?",
        (name,),
    ).fetchone()
    return None if row is None else str(row["id"])


def select_concept_ids_for_group(conn: sqlite3.Connection, group_id: int) -> set[str]:
    rows = conn.execute(
        "SELECT concept_id FROM parameterization_group WHERE group_id = ?",
        (group_id,),
    ).fetchall()
    return {str(row["concept_id"]) for row in rows}


def select_parameterizations_for_output_concept(
    conn: sqlite3.Connection,
    concept_id: str,
) -> list[ParameterizationRow]:
    rows = conn.execute(
        "SELECT * FROM parameterization WHERE output_concept_id = ?",
        (concept_id,),
    ).fetchall()
    return [
        PARAMETERIZATION_ROW_MODEL.from_row(
            {
                **dict(row),
                "output_concept_id": dict(row).get("output_concept_id", concept_id),
            }
        )
        for row in rows
    ]


def select_all_parameterizations(conn: sqlite3.Connection) -> list[ParameterizationRow]:
    rows = conn.execute("SELECT * FROM parameterization").fetchall()
    return [PARAMETERIZATION_ROW_MODEL.from_row(dict(row)) for row in rows]


def select_parameterization_group_members(
    conn: sqlite3.Connection,
    concept_id: str,
) -> list[str]:
    row = conn.execute(
        "SELECT group_id FROM parameterization_group WHERE concept_id = ?",
        (concept_id,),
    ).fetchone()
    if row is None:
        return []
    rows = conn.execute(
        "SELECT concept_id FROM parameterization_group WHERE group_id = ?",
        (row["group_id"],),
    ).fetchall()
    return [str(group_row["concept_id"]) for group_row in rows]


def select_all_form_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM form").fetchall()
    return [dict(row) for row in rows]


def select_form_algebra_rows_for_output(
    conn: sqlite3.Connection,
    form_name: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM form_algebra WHERE output_form = ?",
        (form_name,),
    ).fetchall()
    return [dict(row) for row in rows]


def select_all_form_algebra_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM form_algebra").fetchall()
    return [dict(row) for row in rows]


def search_concept_ids(conn: sqlite3.Connection, query: str) -> list[dict[str, Any]]:
    try:
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH ?",
            (query,),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        if _is_concept_search_syntax_error(exc):
            raise ConceptSearchQuerySyntaxError(query) from exc
        raise
    return [dict(row) for row in rows]


def count_concepts(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM concept").fetchone()[0])


def resolve_sidecar_concept_id(conn: sqlite3.Connection, handle: str) -> str:
    conn.row_factory = sqlite3.Row
    direct = conn.execute("SELECT id FROM concept WHERE id = ?", (handle,)).fetchone()
    if direct is not None:
        return str(direct["id"])
    primary = conn.execute(
        "SELECT id FROM concept WHERE primary_logical_id = ?",
        (handle,),
    ).fetchone()
    if primary is not None:
        return str(primary["id"])
    canonical = conn.execute(
        "SELECT id FROM concept WHERE canonical_name = ?",
        (handle,),
    ).fetchone()
    if canonical is not None:
        return str(canonical["id"])
    alias = conn.execute(
        "SELECT concept_id FROM alias WHERE alias_name = ?",
        (handle,),
    ).fetchone()
    if alias is not None:
        return str(alias["concept_id"])
    raise ValueError(f"Unknown concept: {handle}")
