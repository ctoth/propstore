from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from quire.sqlalchemy_store import create_sqlalchemy_store
from propstore.families.concepts.declaration import (
    ConceptWriteModels,
    ParameterizationGroup,
)
from propstore.families.registry import world_schema


def test_parameterization_group_models_are_typed_and_round_trip(tmp_path) -> None:
    schema = world_schema()
    rows = ConceptWriteModels(
        form_rows=(),
        concept_rows=(),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(),
        parameterization_group_rows=(
            ParameterizationGroup(
                concept_id="concept-alpha",
                group_id=3,
            ),
        ),
        form_algebra_rows=(),
    )

    db_path = tmp_path / "parameterization-group.sqlite"
    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        with Session(engine) as session:
            session.add_all(rows.parameterization_group_rows)
            session.commit()
            stored = session.execute(select(schema.model("parameterization_group"))).scalar_one()
    finally:
        engine.dispose()

    assert isinstance(stored, ParameterizationGroup)
    assert stored.concept_id == "concept-alpha"
    assert stored.group_id == 3
