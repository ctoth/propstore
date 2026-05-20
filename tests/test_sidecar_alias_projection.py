from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from quire.sqlalchemy_store import create_sqlalchemy_store
from propstore.families.concepts.declaration import (
    ConceptAlias,
    ConceptWriteModels,
)
from propstore.families.world_charters import world_sqlalchemy_schema


def test_alias_models_are_typed_and_round_trip(tmp_path) -> None:
    schema = world_sqlalchemy_schema()
    rows = ConceptWriteModels(
        form_rows=(),
        concept_rows=(),
        alias_rows=(
            ConceptAlias(
                concept_id="concept-alpha",
                alias_name="F0",
                source="Sundberg_1993",
            ),
        ),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(),
        parameterization_group_rows=(),
        form_algebra_rows=(),
    )

    db_path = tmp_path / "alias.sqlite"
    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        with Session(engine) as session:
            session.add_all(rows.alias_rows)
            session.commit()
            stored = session.execute(select(schema.model("alias"))).scalar_one()
    finally:
        engine.dispose()

    assert isinstance(stored, ConceptAlias)
    assert stored.concept_id == "concept-alpha"
    assert stored.alias_name == "F0"
    assert stored.source == "Sundberg_1993"
