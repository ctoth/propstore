from __future__ import annotations

import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from quire.sqlalchemy_store import create_sqlalchemy_store
from propstore.families.forms.stages import Form, FormAlgebra
from propstore.families.concepts.declaration import ConceptWriteModels
from propstore.families.world_charters import world_sqlalchemy_schema


def test_form_algebra_models_round_trip_with_explicit_id(tmp_path) -> None:
    schema = world_sqlalchemy_schema()
    rows = ConceptWriteModels(
        form_rows=(
            Form(
                name="force",
                kind="quantity",
                unit_symbol="N",
                is_dimensionless=0,
                dimensions='{"M": 1, "L": 1, "T": -2}',
            ),
        ),
        concept_rows=(),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(),
        parameterization_group_rows=(),
        form_algebra_rows=(
            FormAlgebra(
                id=1,
                output_form="force",
                input_forms='["mass", "acceleration"]',
                operation="mass * acceleration",
                source_concept_id="concept-force",
                source_formula="m * a",
                dim_verified=1,
            ),
        ),
    )

    db_path = tmp_path / "form-algebra.sqlite"
    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        with Session(engine) as session:
            session.add_all(rows.form_rows)
            session.add_all(rows.form_algebra_rows)
            session.commit()
            stored = session.execute(select(schema.model("form_algebra"))).scalar_one()
    finally:
        engine.dispose()

    assert stored.id == 1
    assert stored.output_form == "force"
    assert json.loads(stored.input_forms) == ["mass", "acceleration"]
    assert stored.operation == "mass * acceleration"
    assert stored.source_concept_id == "concept-force"
    assert stored.source_formula == "m * a"
    assert stored.dim_verified == 1
