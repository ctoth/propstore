"""Declarative projection contracts for materialized sidecar stores."""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, Self


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DYNAMIC_SEGMENT = re.compile(r"^[A-Za-z0-9_]+$")


class ProjectionEncoder(Protocol):
    def __call__(self, value: Any) -> Any: ...


class ProjectionDecoder(Protocol):
    def __call__(self, value: Any) -> Any: ...


def json_encoder(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def json_decoder(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"Expected JSON text, got {type(value).__name__}")
    return json.loads(value)


def _quote_identifier(identifier: str) -> str:
    if not _IDENTIFIER.fullmatch(identifier):
        raise ValueError(f"Invalid SQLite identifier: {identifier!r}")
    return f'"{identifier}"'


def _render_dynamic_name(name: str, bindings: Mapping[str, str] | None) -> str:
    if "{" not in name:
        return name
    if bindings is None:
        raise ValueError(f"Dynamic projection name {name!r} requires bindings")
    rendered = name
    for key, value in bindings.items():
        if not _DYNAMIC_SEGMENT.fullmatch(value):
            raise ValueError(f"Invalid dynamic name segment for {key}: {value!r}")
        rendered = rendered.replace("{" + key + "}", value)
    if "{" in rendered or "}" in rendered:
        raise ValueError(f"Unbound dynamic projection name segment in {name!r}")
    return rendered


@dataclass(frozen=True)
class ProjectionColumn:
    name: str
    sql_type: str
    nullable: bool = True
    primary_key: bool = False
    default_sql: str | None = None
    check_sql: str | None = None
    encoder: ProjectionEncoder | None = None
    decoder: ProjectionDecoder | None = None

    def ddl(self) -> str:
        parts = [_quote_identifier(self.name), self.sql_type]
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if not self.nullable:
            parts.append("NOT NULL")
        if self.default_sql is not None:
            parts.extend(("DEFAULT", self.default_sql))
        if self.check_sql is not None:
            parts.append(f"CHECK({self.check_sql})")
        return " ".join(parts)

    def encode(self, value: Any) -> Any:
        if self.encoder is None:
            return value
        return self.encoder(value)

    def decode(self, value: Any) -> Any:
        if self.decoder is None:
            return value
        return self.decoder(value)

    def schema_hash_material(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sql_type": self.sql_type,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "default_sql": self.default_sql,
            "check_sql": self.check_sql,
            "codec": _codec_name(self.encoder, self.decoder),
        }


@dataclass(frozen=True)
class ProjectionForeignKey:
    columns: tuple[str, ...]
    ref_table: str
    ref_columns: tuple[str, ...]

    def ddl(self) -> str:
        columns = ", ".join(_quote_identifier(column) for column in self.columns)
        ref_columns = ", ".join(_quote_identifier(column) for column in self.ref_columns)
        return (
            f"FOREIGN KEY ({columns}) REFERENCES "
            f"{_quote_identifier(self.ref_table)}({ref_columns})"
        )

    def schema_hash_material(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "ref_table": self.ref_table,
            "ref_columns": self.ref_columns,
        }


@dataclass(frozen=True)
class ProjectionIndex:
    name: str
    columns: tuple[str, ...]
    unique: bool = False
    where_sql: str | None = None

    def ddl(self, table_name: str) -> str:
        unique = "UNIQUE " if self.unique else ""
        columns = ", ".join(_quote_identifier(column) for column in self.columns)
        statement = (
            f"CREATE {unique}INDEX IF NOT EXISTS {_quote_identifier(self.name)} "
            f"ON {_quote_identifier(table_name)}({columns})"
        )
        if self.where_sql is not None:
            statement += f" WHERE {self.where_sql}"
        return statement

    def schema_hash_material(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "columns": self.columns,
            "unique": self.unique,
            "where_sql": self.where_sql,
        }


@dataclass(frozen=True)
class ProjectionRow:
    table: str
    values: Mapping[str, Any]

    def value_for(self, column: ProjectionColumn) -> Any:
        return column.encode(self.values.get(column.name))


@dataclass(frozen=True)
class ProjectionTable:
    name: str
    columns: tuple[ProjectionColumn, ...]
    primary_key: tuple[str, ...] = ()
    foreign_keys: tuple[ProjectionForeignKey, ...] = ()
    indexes: tuple[ProjectionIndex, ...] = ()
    checks: tuple[str, ...] = ()
    if_not_exists: bool = False
    row_factory: Callable[[Mapping[str, Any]], Any] | None = None

    def __post_init__(self) -> None:
        column_names = tuple(column.name for column in self.columns)
        if len(set(column_names)) != len(column_names):
            raise ValueError(f"Projection table {self.name!r} has duplicate columns")
        declared_columns = set(column_names)
        for key_column in self.primary_key:
            if key_column not in declared_columns:
                raise ValueError(f"Primary key column {key_column!r} is not declared")
        for foreign_key in self.foreign_keys:
            missing = set(foreign_key.columns) - declared_columns
            if missing:
                raise ValueError(f"Foreign key references undeclared columns: {sorted(missing)}")
        for index in self.indexes:
            missing = set(index.columns) - declared_columns
            if missing:
                raise ValueError(f"Index {index.name!r} references undeclared columns: {sorted(missing)}")

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    def table_name(self, bindings: Mapping[str, str] | None = None) -> str:
        return _render_dynamic_name(self.name, bindings)

    def create_ddl(self, bindings: Mapping[str, str] | None = None) -> str:
        table_name = self.table_name(bindings)
        exists = " IF NOT EXISTS" if self.if_not_exists else ""
        parts = [column.ddl() for column in self.columns]
        if self.primary_key:
            key_columns = ", ".join(_quote_identifier(column) for column in self.primary_key)
            parts.append(f"PRIMARY KEY ({key_columns})")
        parts.extend(foreign_key.ddl() for foreign_key in self.foreign_keys)
        parts.extend(f"CHECK({check})" for check in self.checks)
        body = ",\n    ".join(parts)
        return f"CREATE TABLE{exists} {_quote_identifier(table_name)} (\n    {body}\n)"

    def ddl_statements(
        self,
        bindings: Mapping[str, str] | None = None,
    ) -> tuple[str, ...]:
        table_name = self.table_name(bindings)
        return (self.create_ddl(bindings),) + tuple(
            index.ddl(table_name) for index in self.indexes
        )

    def insert_sql(
        self,
        *,
        or_ignore: bool = False,
        bindings: Mapping[str, str] | None = None,
    ) -> str:
        table_name = self.table_name(bindings)
        verb = "INSERT OR IGNORE" if or_ignore else "INSERT"
        columns = ", ".join(_quote_identifier(column) for column in self.column_names)
        params = ", ".join(f":{column}" for column in self.column_names)
        return f"{verb} INTO {_quote_identifier(table_name)} ({columns}) VALUES ({params})"

    def encode_row(self, values: Mapping[str, Any]) -> dict[str, Any]:
        return {column.name: column.encode(values.get(column.name)) for column in self.columns}

    def decode_row(self, row: sqlite3.Row | Mapping[str, Any]) -> Any:
        if isinstance(row, sqlite3.Row):
            row_keys = set(row.keys())
        else:
            row_keys = set(row)
        decoded = {
            column.name: column.decode(row[column.name])
            for column in self.columns
            if column.name in row_keys
        }
        if self.row_factory is not None:
            return self.row_factory(decoded)
        return ProjectionRow(table=self.name, values=decoded)

    def schema_hash_material(self) -> dict[str, Any]:
        return {
            "kind": "table",
            "name": self.name,
            "columns": tuple(column.schema_hash_material() for column in self.columns),
            "primary_key": self.primary_key,
            "foreign_keys": tuple(key.schema_hash_material() for key in self.foreign_keys),
            "indexes": tuple(index.schema_hash_material() for index in self.indexes),
            "checks": self.checks,
            "if_not_exists": self.if_not_exists,
        }


@dataclass(frozen=True)
class FtsProjection:
    table: str
    key_column: str
    columns: tuple[str, ...]
    source_query: str | None = None

    @property
    def column_names(self) -> tuple[str, ...]:
        return (self.key_column,) + self.columns

    def table_name(self, bindings: Mapping[str, str] | None = None) -> str:
        return _render_dynamic_name(self.table, bindings)

    def ddl_statements(
        self,
        bindings: Mapping[str, str] | None = None,
    ) -> tuple[str, ...]:
        table_name = self.table_name(bindings)
        columns = [_quote_identifier(self.key_column) + " UNINDEXED"]
        columns.extend(_quote_identifier(column) for column in self.columns)
        return (
            f"CREATE VIRTUAL TABLE {_quote_identifier(table_name)} "
            f"USING fts5({', '.join(columns)})",
        )

    def insert_sql(self, bindings: Mapping[str, str] | None = None) -> str:
        table_name = self.table_name(bindings)
        columns = ", ".join(_quote_identifier(column) for column in self.column_names)
        params = ", ".join(f":{column}" for column in self.column_names)
        return f"INSERT INTO {_quote_identifier(table_name)} ({columns}) VALUES ({params})"

    def schema_hash_material(self) -> dict[str, Any]:
        return {
            "kind": "fts5",
            "table": self.table,
            "key_column": self.key_column,
            "columns": self.columns,
            "source_query": self.source_query,
        }


@dataclass(frozen=True)
class VecProjection:
    table: str
    key_column: ProjectionColumn
    vector_column: ProjectionColumn
    metadata_columns: tuple[ProjectionColumn, ...] = ()

    @property
    def columns(self) -> tuple[ProjectionColumn, ...]:
        return (self.key_column, self.vector_column) + self.metadata_columns

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    def table_name(self, bindings: Mapping[str, str] | None = None) -> str:
        return _render_dynamic_name(self.table, bindings)

    def ddl_statements(
        self,
        bindings: Mapping[str, str] | None = None,
    ) -> tuple[str, ...]:
        table_name = self.table_name(bindings)
        columns = ", ".join(
            f"{_quote_identifier(column.name)} {column.sql_type}"
            for column in self.columns
        )
        return (
            f"CREATE VIRTUAL TABLE {_quote_identifier(table_name)} "
            f"USING vec0({columns})",
        )

    def insert_sql(self, bindings: Mapping[str, str] | None = None) -> str:
        table_name = self.table_name(bindings)
        columns = ", ".join(_quote_identifier(column.name) for column in self.columns)
        params = ", ".join(f":{column.name}" for column in self.columns)
        return f"INSERT INTO {_quote_identifier(table_name)} ({columns}) VALUES ({params})"

    def encode_row(self, values: Mapping[str, Any]) -> dict[str, Any]:
        return {column.name: column.encode(values.get(column.name)) for column in self.columns}

    def schema_hash_material(self) -> dict[str, Any]:
        return {
            "kind": "vec0",
            "table": self.table,
            "columns": tuple(column.schema_hash_material() for column in self.columns),
        }


SemanticProjection = ProjectionTable | FtsProjection | VecProjection


@dataclass(frozen=True)
class ProjectionSchema:
    projections: tuple[SemanticProjection, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def ddl_statements(
        self,
        bindings: Mapping[str, str] | None = None,
    ) -> tuple[str, ...]:
        statements: list[str] = []
        for projection in self.projections:
            statements.extend(projection.ddl_statements(bindings))
        return tuple(statements)

    def schema_hash_material(self) -> str:
        material = {
            "metadata": self.metadata,
            "projections": tuple(
                projection.schema_hash_material() for projection in self.projections
            ),
        }
        return json.dumps(material, sort_keys=True, separators=(",", ":"))

    def table(self, name: str) -> SemanticProjection:
        for projection in self.projections:
            projection_name = projection.name if isinstance(projection, ProjectionTable) else projection.table
            if projection_name == name:
                return projection
        raise KeyError(name)

    def validate_connection(self, conn: sqlite3.Connection) -> None:
        missing_tables: list[str] = []
        missing_columns: list[str] = []
        for projection in self.projections:
            table_name = projection.name if isinstance(projection, ProjectionTable) else projection.table
            if not _has_table(conn, table_name):
                missing_tables.append(table_name)
                continue
            for column in projection.column_names:
                if column not in _table_columns(conn, table_name):
                    missing_columns.append(f"{table_name}.{column}")
        if missing_tables:
            missing = ", ".join(sorted(missing_tables))
            raise ProjectionSchemaError(f"missing table(s) {missing}")
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ProjectionSchemaError(f"missing column(s) {missing}")


class ProjectionSchemaError(ValueError):
    pass


def create_projection_schema(
    *projections: SemanticProjection,
    metadata: Mapping[str, Any] | None = None,
) -> ProjectionSchema:
    return ProjectionSchema(
        projections=tuple(projections),
        metadata={} if metadata is None else dict(metadata),
    )


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'virtual table') AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table)})").fetchall()
    return {str(row[1]) for row in rows}


def _codec_name(
    encoder: ProjectionEncoder | None,
    decoder: ProjectionDecoder | None,
) -> str | None:
    if encoder is json_encoder and decoder is json_decoder:
        return "json"
    if encoder is None and decoder is None:
        return None
    names = (
        getattr(encoder, "__name__", encoder.__class__.__name__ if encoder else "none"),
        getattr(decoder, "__name__", decoder.__class__.__name__ if decoder else "none"),
    )
    return ":".join(names)
