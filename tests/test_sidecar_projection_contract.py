from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pytest

from quire.projections import (
    FtsProjection,
    ProjectionColumn,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionSchemaError,
    ProjectionTable,
    VecProjection,
    create_projection_schema,
    json_decoder,
    json_encoder,
)


def test_projection_table_generates_deterministic_ddl_and_indexes() -> None:
    table = ProjectionTable(
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
        indexes=(ProjectionIndex("idx_claim_concept_link_concept", ("concept_id",)),),
    )

    assert table.ddl_statements() == (
        'CREATE TABLE "claim_concept_link" (\n'
        '    "claim_id" TEXT NOT NULL,\n'
        '    "concept_id" TEXT NOT NULL,\n'
        '    "role" TEXT NOT NULL,\n'
        '    "ordinal" INTEGER NOT NULL,\n'
        '    "binding_name" TEXT,\n'
        '    PRIMARY KEY ("claim_id", "role", "ordinal", "concept_id"),\n'
        '    FOREIGN KEY ("claim_id") REFERENCES "claim_core"("id"),\n'
        '    FOREIGN KEY ("concept_id") REFERENCES "concept"("id")\n'
        ")",
        'CREATE INDEX IF NOT EXISTS "idx_claim_concept_link_concept" '
        'ON "claim_concept_link"("concept_id")',
    )
    assert table.create_ddl() == table.create_ddl()


def test_projection_table_generates_named_insert_and_encodes_json() -> None:
    table = ProjectionTable(
        name="source",
        columns=(
            ProjectionColumn("slug", "TEXT", nullable=False, primary_key=True),
            ProjectionColumn("quality_json", "TEXT", encoder=json_encoder, decoder=json_decoder),
        ),
    )

    assert table.insert_sql() == (
        'INSERT INTO "source" ("slug", "quality_json") '
        "VALUES (:slug, :quality_json)"
    )
    assert table.insert_sql(or_replace=True) == (
        'INSERT OR REPLACE INTO "source" ("slug", "quality_json") '
        "VALUES (:slug, :quality_json)"
    )
    with pytest.raises(ValueError, match="only one conflict policy"):
        table.insert_sql(or_ignore=True, or_replace=True)
    assert table.encode_row(
        {"slug": "paper-a", "quality_json": {"score": 0.9, "kind": "peer"}}
    ) == {
        "slug": "paper-a",
        "quality_json": '{"kind":"peer","score":0.9}',
    }


def test_projection_table_omits_non_insertable_columns_from_named_insert() -> None:
    table = ProjectionTable(
        name="form_algebra",
        columns=(
            ProjectionColumn("id", "INTEGER", primary_key=True, insertable=False),
            ProjectionColumn("output_form", "TEXT", nullable=False),
            ProjectionColumn("operation", "TEXT", nullable=False),
        ),
    )

    assert '"id" INTEGER PRIMARY KEY' in table.create_ddl()
    assert table.insert_sql() == (
        'INSERT INTO "form_algebra" ("output_form", "operation") '
        "VALUES (:output_form, :operation)"
    )


def test_projection_schema_validates_required_tables_and_columns() -> None:
    table = ProjectionTable(
        name="source",
        columns=(
            ProjectionColumn("slug", "TEXT", nullable=False, primary_key=True),
            ProjectionColumn("source_id", "TEXT", nullable=False),
        ),
    )
    schema = create_projection_schema(table)
    conn = sqlite3.connect(":memory:")

    with pytest.raises(ProjectionSchemaError, match=r"missing table\(s\) source"):
        schema.validate_connection(conn)

    conn.execute('CREATE TABLE "source" ("slug" TEXT PRIMARY KEY)')
    with pytest.raises(ProjectionSchemaError, match=r"missing column\(s\) source.source_id"):
        schema.validate_connection(conn)

    conn.close()
    conn = sqlite3.connect(":memory:")
    conn.execute(table.create_ddl())
    schema.validate_connection(conn)


@dataclass(frozen=True)
class DecodedSource:
    slug: str
    quality: dict[str, object] | None


def test_projection_table_decodes_rows_to_declared_runtime_type() -> None:
    table = ProjectionTable(
        name="source",
        columns=(
            ProjectionColumn("slug", "TEXT", nullable=False, primary_key=True),
            ProjectionColumn("quality_json", "TEXT", encoder=json_encoder, decoder=json_decoder),
        ),
        row_factory=lambda values: DecodedSource(
            slug=str(values["slug"]),
            quality=values["quality_json"],
        ),
    )
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(table.create_ddl())
    conn.execute(
        table.insert_sql(),
        table.encode_row({"slug": "paper-a", "quality_json": {"score": 1}}),
    )

    row = conn.execute('SELECT slug, quality_json FROM "source"').fetchone()

    assert table.decode_row(row) == DecodedSource(
        slug="paper-a",
        quality={"score": 1},
    )


def test_fts_projection_generates_virtual_table_and_validates_columns() -> None:
    projection = FtsProjection(
        table="concept_fts",
        key_column="concept_id",
        columns=("canonical_name", "aliases", "definition", "conditions"),
        source_query="SELECT ...",
    )
    schema = create_projection_schema(projection)
    conn = sqlite3.connect(":memory:")

    conn.execute(projection.ddl_statements()[0])

    assert projection.ddl_statements() == (
        'CREATE VIRTUAL TABLE "concept_fts" USING fts5('
        '"concept_id" UNINDEXED, "canonical_name", "aliases", "definition", "conditions")',
    )
    assert projection.insert_sql() == (
        'INSERT INTO "concept_fts" ("concept_id", "canonical_name", "aliases", '
        '"definition", "conditions") VALUES (:concept_id, :canonical_name, '
        ":aliases, :definition, :conditions)"
    )
    assert projection.population_sql() == (
        'INSERT INTO "concept_fts" ("concept_id", "canonical_name", "aliases", '
        '"definition", "conditions") SELECT ...'
    )
    assert projection.match_sql(("concept_id",), limit_param="limit") == (
        'SELECT "concept_id" FROM "concept_fts" '
        'WHERE "concept_fts" MATCH :query LIMIT :limit'
    )
    schema.validate_connection(conn)


def test_fts_projection_validates_search_columns_and_population_plan() -> None:
    projection = FtsProjection(
        table="claim_fts",
        key_column="claim_id",
        columns=("statement", "conditions", "expression"),
        row_plan="Claim FTS rows are generated from normalized claim files.",
    )

    assert projection.population_plan() == (
        "Claim FTS rows are generated from normalized claim files."
    )
    projection.validate_search_columns(("claim_id", "statement", "expression"))
    with pytest.raises(ValueError, match="does not declare search column"):
        projection.validate_search_columns(("missing",))
    with pytest.raises(ValueError, match="has no source query"):
        projection.population_sql()


def test_vec_projection_supports_dynamic_table_names() -> None:
    projection = VecProjection(
        table="claim_vec_{model_identity_hash}",
        key_column=ProjectionColumn("claim_id", "TEXT", nullable=False),
        vector_column=ProjectionColumn("embedding", "float[3]", nullable=False),
    )

    assert projection.ddl_statements({"model_identity_hash": "abc_123"}) == (
        'CREATE VIRTUAL TABLE "claim_vec_abc_123" '
        'USING vec0("claim_id" TEXT, "embedding" float[3])',
    )
    assert projection.insert_sql({"model_identity_hash": "abc_123"}) == (
        'INSERT INTO "claim_vec_abc_123" ("claim_id", "embedding") '
        "VALUES (:claim_id, :embedding)"
    )
    with pytest.raises(ValueError, match="Invalid dynamic name segment"):
        projection.ddl_statements({"model_identity_hash": "../bad"})


def test_vec_projection_supports_rowid_backed_tables() -> None:
    projection = VecProjection(
        table="claim_vec_{model_identity_hash}",
        key_column=None,
        vector_column=ProjectionColumn("embedding", "float[3]", nullable=False),
    )

    assert projection.ddl_statements({"model_identity_hash": "abc_123"}) == (
        'CREATE VIRTUAL TABLE "claim_vec_abc_123" '
        'USING vec0("embedding" float[3])',
    )
    assert projection.insert_rowid_sql({"model_identity_hash": "abc_123"}) == (
        'INSERT INTO "claim_vec_abc_123" (rowid, "embedding") '
        "VALUES (:rowid, :embedding)"
    )
    assert projection.delete_rowid_sql({"model_identity_hash": "abc_123"}) == (
        'DELETE FROM "claim_vec_abc_123" WHERE rowid = :rowid'
    )


def test_projection_schema_hash_material_is_deterministic() -> None:
    schema = create_projection_schema(
        ProjectionTable(
            name="source",
            columns=(ProjectionColumn("slug", "TEXT", nullable=False, primary_key=True),),
        ),
        metadata={"schema_version": 6},
    )

    assert schema.schema_hash_material() == schema.schema_hash_material()
    assert '"schema_version":6' in schema.schema_hash_material()
