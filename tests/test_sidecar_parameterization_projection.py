from __future__ import annotations

import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from quire.sqlalchemy_store import create_sqlalchemy_store
from propstore.families.concepts.declaration import (
    ConceptWriteModels,
    Parameterization,
)
from propstore.families.world_charters import world_sqlalchemy_schema


def test_parameterization_models_are_typed_and_round_trip(tmp_path) -> None:
    schema = world_sqlalchemy_schema()
    rows = ConceptWriteModels(
        form_rows=(),
        concept_rows=(),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(
            Parameterization(
                output_concept_id="concept-alpha",
                concept_ids='["concept-input"]',
                formula="x + 1",
                sympy="x + 1",
                exactness="exact",
                conditions_cel='["task == \\"speech\\""]',
                conditions_ir='{"op":"eq"}',
            ),
        ),
        parameterization_group_rows=(),
        form_algebra_rows=(),
    )

    db_path = tmp_path / "parameterization.sqlite"
    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        with Session(engine) as session:
            session.add_all(rows.parameterization_rows)
            session.commit()
            stored = session.execute(select(schema.model("parameterization"))).scalar_one()
    finally:
        engine.dispose()

    assert isinstance(stored, Parameterization)
    assert stored.output_concept_id == "concept-alpha"
    assert json.loads(stored.concept_ids) == ["concept-input"]
    assert stored.formula == "x + 1"
    assert stored.sympy == "x + 1"
    assert stored.exactness == "exact"
    assert stored.conditions_cel is not None
    assert json.loads(stored.conditions_cel) == ['task == "speech"']
    assert stored.conditions_ir == '{"op":"eq"}'
