from __future__ import annotations

import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from quire.sqlalchemy_store import create_sqlalchemy_store
from propstore.families.concepts.declaration import Concept, ConceptWriteModels
from propstore.families.registry import world_schema


def test_concept_models_are_typed_and_round_trip(tmp_path) -> None:
    schema = world_schema()
    rows = ConceptWriteModels(
        form_rows=(),
        concept_rows=(
            Concept(
                id="concept-alpha",
                primary_logical_id="logical-alpha",
                logical_ids_json='[{"value":"logical-alpha"}]',
                version_id="sha256:abc",
                content_hash="abc",
                seq=1,
                canonical_name="alpha",
                status="accepted",
                domain="speech",
                definition="Alpha concept.",
                kind_type="scalar",
                form="number",
                form_parameters=None,
                range_min=None,
                range_max=None,
                is_dimensionless=1,
                unit_symbol=None,
                created_date=None,
                last_modified=None,
            ),
        ),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(),
        parameterization_group_rows=(),
        form_algebra_rows=(),
    )

    db_path = tmp_path / "concept.sqlite"
    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        with Session(engine) as session:
            session.add_all(rows.concept_rows)
            session.commit()
            stored = session.execute(select(schema.model("concept"))).scalar_one()
    finally:
        engine.dispose()

    assert isinstance(stored, Concept)
    assert stored.id == "concept-alpha"
    assert stored.concept_id == "concept-alpha"
    assert stored.primary_logical_id == "logical-alpha"
    assert stored.logical_ids_json is not None
    assert json.loads(stored.logical_ids_json) == [{"value": "logical-alpha"}]
    assert stored.canonical_name == "alpha"
    assert stored.status == "accepted"
