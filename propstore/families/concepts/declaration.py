"""Concept family projection, row, and derived-query declaration."""

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
    ProjectionTable,
)
from quire.sqlite_vec_store import embedding_status_projection, rowid_vec_projection

from propstore.core.concept_status import ConceptStatus, coerce_concept_status
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.id_types import ConceptId, to_concept_id

if TYPE_CHECKING:
    from propstore.sidecar.stages import ConceptSidecarRows


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
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status is not None:
            object.__setattr__(self, "status", coerce_concept_status(self.status))
        object.__setattr__(self, "attributes", dict(self.attributes))

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> ConceptRow:
        known = {
            "id",
            "canonical_name",
            "status",
            "definition",
            "kind_type",
            "form",
            "domain",
            "form_parameters",
            "primary_logical_id",
            "logical_ids_json",
        }
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in known and value is not None
        }
        return cls(
            concept_id=to_concept_id(row_map["id"]),
            canonical_name=str(row_map["canonical_name"]),
            status=None if row_map.get("status") is None else coerce_concept_status(row_map["status"]),
            definition=None if row_map.get("definition") is None else str(row_map["definition"]),
            kind_type=None if row_map.get("kind_type") is None else str(row_map["kind_type"]),
            form=None if row_map.get("form") is None else str(row_map["form"]),
            domain=None if row_map.get("domain") is None else str(row_map["domain"]),
            form_parameters=None if row_map.get("form_parameters") is None else str(row_map["form_parameters"]),
            primary_logical_id=None if row_map.get("primary_logical_id") is None else str(row_map["primary_logical_id"]),
            logical_ids_json=None if row_map.get("logical_ids_json") is None else str(row_map["logical_ids_json"]),
            attributes=attributes,
        )

    def parsed_logical_ids(self) -> list[dict[str, Any]]:
        if not self.logical_ids_json:
            return []
        try:
            loaded = json.loads(self.logical_ids_json)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.concept_id,
            "canonical_name": self.canonical_name,
        }
        if self.status is not None:
            data["status"] = self.status.value
        if self.definition is not None:
            data["definition"] = self.definition
        if self.kind_type is not None:
            data["kind_type"] = self.kind_type
        if self.form is not None:
            data["form"] = self.form
        if self.domain is not None:
            data["domain"] = self.domain
        if self.form_parameters is not None:
            data["form_parameters"] = self.form_parameters
        if self.primary_logical_id is not None:
            data["primary_logical_id"] = self.primary_logical_id
            data["logical_id"] = self.primary_logical_id
        if self.logical_ids_json is not None:
            data["logical_ids_json"] = self.logical_ids_json
        data["logical_ids"] = self.parsed_logical_ids()
        data.update(self.attributes)
        return data


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

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "output_concept_id": self.output_concept_id,
            "concept_ids": self.concept_ids,
        }
        if self.formula is not None:
            data["formula"] = self.formula
        if self.sympy is not None:
            data["sympy"] = self.sympy
        if self.exactness is not None:
            data["exactness"] = self.exactness.value
        if self.conditions_cel is not None:
            data["conditions_cel"] = self.conditions_cel
        if self.conditions_ir is not None:
            data["conditions_ir"] = self.conditions_ir
        data.update(self.attributes)
        return data

    @classmethod
    def from_mapping(
        cls,
        row_map: Mapping[str, Any],
        *,
        output_concept_id: ConceptId | str | None = None,
    ) -> "ParameterizationRow":
        known = {
            "output_concept_id",
            "concept_ids",
            "formula",
            "sympy",
            "exactness",
            "conditions_cel",
            "conditions_ir",
        }
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in known and value is not None
        }
        resolved_output_concept_id = row_map.get("output_concept_id", output_concept_id)
        if resolved_output_concept_id is None:
            raise KeyError("output_concept_id")
        return cls(
            output_concept_id=to_concept_id(resolved_output_concept_id),
            concept_ids=str(row_map["concept_ids"]),
            formula=None if row_map.get("formula") is None else str(row_map["formula"]),
            sympy=None if row_map.get("sympy") is None else str(row_map["sympy"]),
            exactness=coerce_exactness(row_map.get("exactness")),
            conditions_cel=(
                None
                if row_map.get("conditions_cel") is None
                else str(row_map["conditions_cel"])
            ),
            conditions_ir=(
                None
                if row_map.get("conditions_ir") is None
                else str(row_map["conditions_ir"])
            ),
            attributes=attributes,
        )


ParameterizationRowInput = ParameterizationRow | Mapping[str, Any]


def coerce_parameterization_row(
    row: ParameterizationRowInput,
    *,
    output_concept_id: ConceptId | str | None = None,
) -> ParameterizationRow:
    if isinstance(row, ParameterizationRow):
        return row
    return ParameterizationRow.from_mapping(
        row,
        output_concept_id=output_concept_id,
    )


ConceptRowInput = ConceptRow | Mapping[str, Any]


def coerce_concept_row(row: ConceptRowInput) -> ConceptRow:
    if isinstance(row, ConceptRow):
        return row
    return ConceptRow.from_mapping(row)


CONCEPT_PROJECTION = ProjectionTable(
    name="concept",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("primary_logical_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("logical_ids_json", "TEXT", nullable=False, default_sql="'[]'"),
        ProjectionColumn("version_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("content_hash", "TEXT", nullable=False),
        ProjectionColumn("seq", "INTEGER", nullable=False),
        ProjectionColumn("canonical_name", "TEXT", nullable=False),
        ProjectionColumn("status", "TEXT", nullable=False),
        ProjectionColumn("domain", "TEXT"),
        ProjectionColumn("definition", "TEXT", nullable=False),
        ProjectionColumn("kind_type", "TEXT", nullable=False),
        ProjectionColumn("form", "TEXT", nullable=False),
        ProjectionColumn("form_parameters", "TEXT"),
        ProjectionColumn("range_min", "REAL"),
        ProjectionColumn("range_max", "REAL"),
        ProjectionColumn("is_dimensionless", "INTEGER", nullable=False, default_sql="0"),
        ProjectionColumn("unit_symbol", "TEXT"),
        ProjectionColumn("created_date", "TEXT"),
        ProjectionColumn("last_modified", "TEXT"),
    ),
    indexes=(ProjectionIndex("idx_concept_primary_logical_id", ("primary_logical_id",)),),
    row_factory=ConceptRow.from_mapping,
)


FORM_PROJECTION = ProjectionTable(
    name="form",
    columns=(
        ProjectionColumn("name", "TEXT", primary_key=True),
        ProjectionColumn("kind", "TEXT", nullable=False),
        ProjectionColumn("unit_symbol", "TEXT"),
        ProjectionColumn("is_dimensionless", "INTEGER", nullable=False, default_sql="0"),
        ProjectionColumn("dimensions", "TEXT"),
    ),
)


FORM_ALGEBRA_PROJECTION = ProjectionTable(
    name="form_algebra",
    columns=(
        ProjectionColumn("id", "INTEGER PRIMARY KEY AUTOINCREMENT", insertable=False),
        ProjectionColumn("output_form", "TEXT", nullable=False),
        ProjectionColumn("input_forms", "TEXT", nullable=False),
        ProjectionColumn("operation", "TEXT", nullable=False),
        ProjectionColumn("source_concept_id", "TEXT"),
        ProjectionColumn("source_formula", "TEXT"),
        ProjectionColumn("dim_verified", "INTEGER", nullable=False, default_sql="1"),
    ),
    foreign_keys=(ProjectionForeignKey(("output_form",), "form", ("name",)),),
    indexes=(ProjectionIndex("idx_form_algebra_output", ("output_form",)),),
)


ALIAS_PROJECTION = ProjectionTable(
    name="alias",
    columns=(
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("alias_name", "TEXT", nullable=False),
        ProjectionColumn("source", "TEXT", nullable=False),
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
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("group_id", "INTEGER", nullable=False),
    ),
    foreign_keys=(ProjectionForeignKey(("concept_id",), "concept", ("id",)),),
    indexes=(ProjectionIndex("idx_param_group", ("group_id",)),),
)


PARAMETERIZATION_PROJECTION = ProjectionTable(
    name="parameterization",
    columns=(
        ProjectionColumn("output_concept_id", "TEXT", nullable=False),
        ProjectionColumn("concept_ids", "TEXT", nullable=False),
        ProjectionColumn("formula", "TEXT", nullable=False),
        ProjectionColumn("sympy", "TEXT"),
        ProjectionColumn("exactness", "TEXT", nullable=False),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("conditions_ir", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("output_concept_id",), "concept", ("id",)),),
    row_factory=ParameterizationRow.from_mapping,
)


RELATIONSHIP_PROJECTION = ProjectionTable(
    name="relationship",
    columns=(
        ProjectionColumn("source_id", "TEXT", nullable=False),
        ProjectionColumn("type", "TEXT", nullable=False),
        ProjectionColumn("target_id", "TEXT", nullable=False),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("note", "TEXT"),
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
    from propstore.sidecar.sqlite import connect_sidecar_readonly

    conn = connect_sidecar_readonly(sidecar)
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
    return ConceptRow.from_mapping(dict(row))


def select_all_concepts(conn: sqlite3.Connection) -> list[ConceptRow]:
    rows = conn.execute("SELECT * FROM concept").fetchall()
    return [ConceptRow.from_mapping(dict(row)) for row in rows]


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
            concept=ConceptRow.from_mapping(dict(row)),
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
    return [ConceptRow.from_mapping(dict(row)) for row in rows]


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


def search_concept_ids(conn: sqlite3.Connection, query: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH ?",
        (query,),
    ).fetchall()
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


def embed_concepts_for_request(
    sidecar: Path,
    *,
    concept_id: str | None,
    embed_all: bool,
    model: str,
    batch_size: int,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> list[tuple[str, Any]]:
    if not concept_id and not embed_all:
        raise ValueError("provide a concept ID or request all concepts")

    from propstore.heuristic.embed import (
        _load_vec_extension,
        embed_concepts,
        get_registered_models,
    )
    from propstore.sidecar.sqlite import connect_sidecar

    reports: list[tuple[str, Any]] = []
    conn = connect_sidecar(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        _load_vec_extension(conn)
        ids = [resolve_sidecar_concept_id(conn, concept_id)] if concept_id else None

        if model == "all":
            models = get_registered_models(conn)
            if not models:
                raise LookupError("no models registered")
            for model_row in models:
                model_name = str(model_row["model_name"])
                result = embed_concepts(
                    conn,
                    model_name,
                    concept_ids=ids,
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
            result = embed_concepts(
                conn,
                model,
                concept_ids=ids,
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


def find_similar_concept_rows(
    sidecar: Path,
    *,
    concept_id: str,
    model: str | None,
    top_k: int,
    agree: bool = False,
    disagree: bool = False,
) -> list[dict[str, Any]]:
    from propstore.heuristic.embed import (
        _load_vec_extension,
        find_similar_concepts,
        find_similar_concepts_agree,
        find_similar_concepts_disagree,
        get_registered_models,
    )
    from propstore.sidecar.sqlite import connect_sidecar

    conn = connect_sidecar(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)

    try:
        resolved_id = resolve_sidecar_concept_id(conn, concept_id)
        if agree:
            rows = find_similar_concepts_agree(conn, resolved_id, top_k=top_k)
        elif disagree:
            rows = find_similar_concepts_disagree(conn, resolved_id, top_k=top_k)
        else:
            selected_model = model
            if selected_model is None:
                models = get_registered_models(conn)
                if not models:
                    raise LookupError("no embeddings found")
                selected_model = str(models[0]["model_name"])
            rows = find_similar_concepts(
                conn,
                resolved_id,
                selected_model,
                top_k=top_k,
            )
    finally:
        conn.close()

    return [dict(row) for row in rows]
