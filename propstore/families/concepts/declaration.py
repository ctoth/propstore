"""Concept family projection, row, and derived-query declaration."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import json
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
from propstore.families.forms.stages import (
    Form,
    FormAlgebra,
    FormDefinition,
    compile_form_algebra,
    compile_form_models,
    kind_value_from_form_name,
)
from propstore.parameterization_groups import build_groups

if TYPE_CHECKING:
    from propstore.families.concepts.stages import ConceptRecord, LoadedConcept


@dataclass(frozen=True)
class ConceptWriteModels:
    form_rows: tuple[Form, ...]
    concept_rows: tuple["Concept", ...]
    alias_rows: tuple["ConceptAlias", ...]
    relationship_rows: tuple["ConceptRelationship", ...]
    relation_edge_rows: tuple[object, ...]
    parameterization_rows: tuple["Parameterization", ...]
    parameterization_group_rows: tuple["ParameterizationGroup", ...]
    form_algebra_rows: tuple[FormAlgebra, ...]


def compile_concept_sidecar_rows(
    concepts: list["LoadedConcept"],
    form_registry: dict[str, FormDefinition],
    cel_registry: dict[str, ConceptInfo],
) -> ConceptWriteModels:
    from propstore.families.relations.declaration import (
        CONCEPT_RELATIONSHIP_DISCRIMINATORS,
        CONCEPT_RELATIONSHIP_STORAGE_MODEL,
        RelationshipRow,
        RELATION_EDGE_TABLE,
    )

    form_rows = compile_form_models(form_registry)
    concept_rows: list[Concept] = []
    alias_rows: list[ConceptAlias] = []
    relationship_rows: list[ConceptRelationship] = []
    relation_edge_rows: list[object] = []
    parameterization_rows: list[Parameterization] = []
    parameterization_group_rows: list[ParameterizationGroup] = []
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
            Concept(
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
                ConceptAlias(
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
                ConceptRelationship(
                    source_id=concept_id,
                    type=relationship.relationship_type,
                    target_id=target_id,
                    conditions_cel=conditions_json,
                    note=relationship.note,
                )
            )
            relationship_row = RelationshipRow(
                source_id=concept_id,
                relation_type=relationship.relationship_type,
                target_id=target_id,
                conditions_cel=conditions_json,
                note=relationship.note,
            )
            row_values: dict[str, object] = {}
            for discriminator in CONCEPT_RELATIONSHIP_DISCRIMINATORS:
                row_values.update(discriminator.row_values())
            row_values.update(CONCEPT_RELATIONSHIP_STORAGE_MODEL.to_row(relationship_row))
            relation_edge_rows.append(
                RELATION_EDGE_TABLE.row(**row_values)
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
                Parameterization(
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
                ParameterizationGroup(
                    concept_id=concept_id,
                    group_id=group_id,
                )
            )

    return ConceptWriteModels(
        form_rows=form_rows,
        concept_rows=tuple(concept_rows),
        alias_rows=tuple(alias_rows),
        relationship_rows=tuple(relationship_rows),
        relation_edge_rows=tuple(relation_edge_rows),
        parameterization_rows=tuple(parameterization_rows),
        parameterization_group_rows=tuple(parameterization_group_rows),
        form_algebra_rows=compile_form_algebra(concepts, form_registry),
    )


class Concept:
    def __init__(
        self,
        concept_id: ConceptId | str | None = None,
        canonical_name: str = "",
        *,
        id: str | None = None,
        status: ConceptStatus | str | None = None,
        definition: str | None = None,
        kind_type: str | None = None,
        form: str | None = None,
        domain: str | None = None,
        form_parameters: str | None = None,
        primary_logical_id: str | None = None,
        logical_ids_json: str | None = None,
        version_id: str | None = None,
        content_hash: str | None = None,
        seq: int | None = None,
        range_min: float | None = None,
        range_max: float | None = None,
        is_dimensionless: int | None = None,
        unit_symbol: str | None = None,
        created_date: str | None = None,
        last_modified: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> None:
        concept_key = str(id or concept_id or "")
        self.id = concept_key
        self.canonical_name = canonical_name
        self.status = None if status is None else coerce_concept_status(status)
        self.definition = definition
        self.kind_type = kind_type
        self.form = form
        self.domain = domain
        self.form_parameters = form_parameters
        self.primary_logical_id = primary_logical_id
        self.logical_ids_json = logical_ids_json
        self.version_id = version_id
        self.content_hash = content_hash
        self.seq = seq
        self.range_min = range_min
        self.range_max = range_max
        self.is_dimensionless = is_dimensionless
        self.unit_symbol = unit_symbol
        self.created_date = created_date
        self.last_modified = last_modified
        self.attributes = dict(attributes or {})

    @property
    def concept_id(self) -> ConceptId:
        return to_concept_id(self.id)

    @classmethod
    def from_row_mapping(cls, row: Mapping[str, Any]) -> "Concept":
        payload = dict(row)
        concept_id = payload.pop("concept_id", None) or payload.pop("id", None)
        known = {
            "canonical_name",
            "status",
            "definition",
            "kind_type",
            "form",
            "domain",
            "form_parameters",
            "primary_logical_id",
            "logical_ids_json",
            "version_id",
            "content_hash",
            "seq",
            "range_min",
            "range_max",
            "is_dimensionless",
            "unit_symbol",
            "created_date",
            "last_modified",
        }
        values = {key: payload.pop(key, None) for key in known}
        values["attributes"] = payload
        return cls(concept_id=concept_id, **values)

    @classmethod
    def coerce(cls, value: "Concept | Mapping[str, Any]") -> "Concept":
        if isinstance(value, Concept):
            return value
        return cls.from_row_mapping(value)

    def to_row_mapping(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "concept_id": self.concept_id,
            "canonical_name": self.canonical_name,
            "status": self.status,
            "definition": self.definition,
            "kind_type": self.kind_type,
            "form": self.form,
            "domain": self.domain,
            "form_parameters": self.form_parameters,
            "primary_logical_id": self.primary_logical_id,
            "logical_ids_json": self.logical_ids_json,
            "version_id": self.version_id,
            "content_hash": self.content_hash,
            "seq": self.seq,
            "range_min": self.range_min,
            "range_max": self.range_max,
            "is_dimensionless": self.is_dimensionless,
            "unit_symbol": self.unit_symbol,
            "created_date": self.created_date,
            "last_modified": self.last_modified,
        }
        data.update(self.attributes)
        return data

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


class ConceptAlias:
    def __init__(
        self,
        concept_id: ConceptId | str,
        alias_name: str,
        source: str | None = None,
    ) -> None:
        self.concept_id = to_concept_id(concept_id)
        self.alias_name = alias_name
        self.source = source


class ConceptRelationship:
    def __init__(
        self,
        source_id: ConceptId | str,
        type: object,
        target_id: ConceptId | str,
        *,
        conditions_cel: str | None = None,
        note: str | None = None,
    ) -> None:
        self.source_id = to_concept_id(source_id)
        self.type = str(type)
        self.target_id = to_concept_id(target_id)
        self.conditions_cel = conditions_cel
        self.note = note

    @property
    def relationship_type(self) -> str:
        return self.type


@dataclass(frozen=True)
class ConceptEmbeddingSource:
    concept: Concept
    seq: int
    content_hash: str
    aliases: tuple[str, ...] = ()


class Parameterization:
    def __init__(
        self,
        output_concept_id: ConceptId | str,
        concept_ids: str,
        *,
        formula: str | None = None,
        sympy: str | None = None,
        exactness: Exactness | str | None = None,
        conditions_cel: str | None = None,
        conditions_ir: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> None:
        self.output_concept_id = to_concept_id(output_concept_id)
        self.concept_ids = concept_ids
        self.formula = formula
        self.sympy = sympy
        self.exactness = coerce_exactness(exactness)
        self.conditions_cel = conditions_cel
        self.conditions_ir = conditions_ir
        self.attributes = dict(attributes or {})

    @classmethod
    def from_row_mapping(cls, row: Mapping[str, Any]) -> "Parameterization":
        payload = dict(row)
        known = {
            "output_concept_id",
            "concept_ids",
            "formula",
            "sympy",
            "exactness",
            "conditions_cel",
            "conditions_ir",
        }
        values = {key: payload.pop(key, None) for key in known}
        values["attributes"] = payload
        return cls(**values)

    @classmethod
    def coerce(cls, value: "Parameterization | Mapping[str, Any]") -> "Parameterization":
        if isinstance(value, Parameterization):
            return value
        return cls.from_row_mapping(value)

    def to_row_mapping(self) -> dict[str, Any]:
        data = {
            "output_concept_id": self.output_concept_id,
            "concept_ids": self.concept_ids,
            "formula": self.formula,
            "sympy": self.sympy,
            "exactness": self.exactness,
            "conditions_cel": self.conditions_cel,
            "conditions_ir": self.conditions_ir,
        }
        data.update(self.attributes)
        return data


class ParameterizationGroup:
    def __init__(self, concept_id: ConceptId | str, group_id: int) -> None:
        self.concept_id = to_concept_id(concept_id)
        self.group_id = int(group_id)


ParameterizationInput = Parameterization | Mapping[str, Any]


ConceptInput = Concept | Mapping[str, Any]


CONCEPT_EMBEDDING_STATUS_PROJECTION = embedding_status_projection(
    name="concept_embedding_status",
    entity_id_column="concept_id",
    index_name="idx_concept_embedding_status_model_identity",
)


CONCEPT_VEC_PROJECTION = rowid_vec_projection("concept_vec_{model_identity_hash}")


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


def select_concept_by_id(conn: sqlite3.Connection, concept_id: str) -> Concept | None:
    row = conn.execute("SELECT * FROM concept WHERE id = ?", (concept_id,)).fetchone()
    if row is None:
        return None
    return Concept.from_row_mapping(dict(row))


def select_all_concepts(conn: sqlite3.Connection) -> list[Concept]:
    rows = conn.execute("SELECT * FROM concept").fetchall()
    return [Concept.from_row_mapping(dict(row)) for row in rows]


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
            concept=Concept.from_row_mapping(dict(row)),
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


def select_concept_registry_rows(conn: sqlite3.Connection) -> list[Concept]:
    rows = conn.execute(
        "SELECT id, canonical_name, kind_type, form_parameters FROM concept"
    ).fetchall()
    return [Concept.from_row_mapping(dict(row)) for row in rows]


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
) -> list[Parameterization]:
    rows = conn.execute(
        "SELECT * FROM parameterization WHERE output_concept_id = ?",
        (concept_id,),
    ).fetchall()
    return [
        Parameterization.from_row_mapping(
            {
                **dict(row),
                "output_concept_id": dict(row).get("output_concept_id", concept_id),
            }
        )
        for row in rows
    ]


def select_all_parameterizations(conn: sqlite3.Connection) -> list[Parameterization]:
    rows = conn.execute("SELECT * FROM parameterization").fetchall()
    return [Parameterization.from_row_mapping(dict(row)) for row in rows]


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
