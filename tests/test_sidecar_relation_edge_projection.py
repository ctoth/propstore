from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from quire.sqlalchemy_store import create_sqlalchemy_store
from propstore.families.world_charters import world_sqlalchemy_schema


def test_relation_edge_models_round_trip_without_concept_populator(tmp_path) -> None:
    schema = world_sqlalchemy_schema()
    relation_edge_model = schema.model("relation_edge")
    relation_edge = relation_edge_model(
        source_kind="concept",
        source_id="concept-a",
        relation_type="broader",
        target_kind="concept",
        target_id="concept-b",
        conditions_cel=None,
        note="taxonomy",
    )

    db_path = tmp_path / "relation-edge.sqlite"
    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        with Session(engine) as session:
            session.add(relation_edge)
            session.commit()
            stored = session.execute(select(schema.model("relation_edge"))).scalar_one()
    finally:
        engine.dispose()

    assert isinstance(stored, relation_edge_model)
    assert getattr(stored, "source_kind") == "concept"
    assert getattr(stored, "source_id") == "concept-a"
    assert getattr(stored, "relation_type") == "broader"
    assert getattr(stored, "target_kind") == "concept"
    assert getattr(stored, "target_id") == "concept-b"
    assert getattr(stored, "conditions_cel") is None
    assert getattr(stored, "note") == "taxonomy"
