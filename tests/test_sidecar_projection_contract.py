from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, insert, inspect, select, text
from sqlalchemy.orm import Session

from quire.sqlalchemy_store import create_sqlalchemy_store, validate_sqlalchemy_store

from propstore.families.world_charters import (
    world_sqlalchemy_schema,
)
from propstore.families.sources.declaration import Source, SourceTrust


def test_world_charter_generates_deterministic_tables_and_indexes() -> None:
    schema = world_sqlalchemy_schema()
    table = schema.table("claim_concept_link")

    assert tuple(table.primary_key.columns.keys()) == (
        "claim_id",
        "concept_id",
        "role",
        "ordinal",
    )
    assert tuple(table.c.keys()) == (
        "claim_id",
        "concept_id",
        "role",
        "ordinal",
        "binding_name",
    )
    assert {
        index.name: tuple(column.name for column in index.columns)
        for index in table.indexes
    } == {
        "idx_claim_concept_link_claim": ("claim_id",),
        "idx_claim_concept_link_concept": ("concept_id",),
        "idx_claim_concept_link_role": ("role",),
    }


def test_world_charter_maps_models_and_round_trips_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "world.sqlite"
    schema = world_sqlalchemy_schema()

    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                insert(schema.table("source")),
                [
                    {
                        "slug": "paper-a",
                        "source_id": "source:paper-a",
                        "kind": "paper",
                        "trust": SourceTrust(status="stated"),
                    }
                ],
            )
        with Session(engine) as session:
            row = session.execute(select(schema.model("source"))).scalar_one()
    finally:
        engine.dispose()

    assert isinstance(row, Source)
    assert row.slug == "paper-a"
    assert row.source_id == "source:paper-a"
    assert row.kind == "paper"
    assert row.trust == SourceTrust(status="stated")


def test_world_charter_store_validation_reports_missing_tables_and_columns(tmp_path: Path) -> None:
    schema = world_sqlalchemy_schema()
    db_path = tmp_path / "world.sqlite"

    create_sqlalchemy_store(db_path, schema)
    validate_sqlalchemy_store(db_path, schema)

    missing_table = tmp_path / "missing-table.sqlite"
    sqlite3.connect(missing_table).close()
    with pytest.raises(ValueError, match=r"missing table 'meta'"):
        validate_sqlalchemy_store(missing_table, schema)

    missing_column = tmp_path / "missing-column.sqlite"
    conn = sqlite3.connect(missing_column)
    try:
        conn.execute('CREATE TABLE "meta" ("key" TEXT PRIMARY KEY)')
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(ValueError, match=r"table 'meta' missing column\(s\) schema_version"):
        validate_sqlalchemy_store(missing_column, schema)


def test_world_charter_fts_indexes_are_generated_from_source_queries() -> None:
    schema = world_sqlalchemy_schema()
    concept_fts = schema.fts_index("concept_fts")
    claim_fts = schema.fts_index("claim_fts")

    assert concept_fts.entity_id_field == "concept_id"
    assert concept_fts.fields == ("canonical_name", "aliases", "definition", "conditions")
    assert concept_fts.source_query is not None
    assert "FROM concept c" in concept_fts.source_query
    assert tuple(schema.fts_table("concept_fts").c.keys())[1:] == (
        "concept_id",
        "canonical_name",
        "aliases",
        "definition",
        "conditions",
    )

    assert claim_fts.entity_id_field == "claim_id"
    assert claim_fts.fields == ("statement", "conditions", "expression")
    assert claim_fts.source_query is not None
    assert "FROM claim_core c" in claim_fts.source_query
    assert tuple(schema.fts_table("claim_fts").c.keys())[1:] == (
        "claim_id",
        "statement",
        "conditions",
        "expression",
    )


def test_world_charter_schema_hash_material_is_deterministic() -> None:
    schema = world_sqlalchemy_schema()

    assert schema.catalog.schema_hash() == schema.catalog.schema_hash()
    assert schema.catalog_hash == schema.catalog.schema_hash()
    assert schema.catalog.payload()["metadata"] == {
        "projection": "propstore.world",
        "schema_version": 6,
    }


def test_world_charter_maps_no_database_primary_key_tables() -> None:
    schema = world_sqlalchemy_schema()
    table = schema.table("relationship")
    model = schema.model("relationship")

    assert not table.primary_key.columns
    assert model.__name__ == "ConceptRelationship"
    assert schema.model("claim_concept_link").__name__ == "ClaimConceptLink"


def test_world_charter_store_creates_schema_catalog(tmp_path: Path) -> None:
    db_path = tmp_path / "world.sqlite"
    schema = world_sqlalchemy_schema()

    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        inspector = inspect(engine)
        assert "quire_schema_catalog" in inspector.get_table_names()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT schema_hash FROM quire_schema_catalog WHERE key = 'default'")
            ).first()
    finally:
        engine.dispose()

    assert row == (schema.catalog_hash,)


def test_world_charter_schema_catalog_hash_is_persisted(tmp_path: Path) -> None:
    db_path = tmp_path / "world.sqlite"
    schema = world_sqlalchemy_schema()

    create_sqlalchemy_store(db_path, schema)
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT schema_hash FROM quire_schema_catalog WHERE key = 'default'"
        ).fetchone()
    finally:
        conn.close()

    assert row == (schema.catalog_hash,)
