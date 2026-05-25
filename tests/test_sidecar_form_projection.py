from __future__ import annotations

import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from quire.sqlalchemy_store import create_sqlalchemy_store
from propstore.core.conditions.registry import KindType
from propstore.families.forms.stages import Form, FormDefinition
from propstore.families.concepts.declaration import compile_concept_sidecar_rows
from propstore.families.registry import world_schema


def test_form_models_are_typed_and_round_trip_dimensions(tmp_path) -> None:
    schema = world_schema()
    rows = compile_concept_sidecar_rows(
        concepts=[],
        form_registry={
            "length": FormDefinition(
                name="length",
                kind=KindType.QUANTITY,
                unit_symbol="m",
                dimensions={"L": 1},
            )
        },
        cel_registry={},
    )

    assert len(rows.form_rows) == 1
    form = rows.form_rows[0]
    assert isinstance(form, Form)
    assert form.name == "length"
    assert form.kind == "quantity"
    assert form.unit_symbol == "m"
    assert form.is_dimensionless == 0
    assert json.loads(form.dimensions) == {"L": 1}

    db_path = tmp_path / "forms.sqlite"
    create_sqlalchemy_store(db_path, schema)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    try:
        with Session(engine) as session:
            session.add_all(rows.form_rows)
            session.commit()
            stored = session.execute(
                select(schema.model("form")).where(schema.model("form").name == "length")
            ).scalar_one()
    finally:
        engine.dispose()

    assert stored.kind == "quantity"
    assert stored.unit_symbol == "m"
    assert stored.is_dimensionless == 0
    assert json.loads(stored.dimensions) == {"L": 1}
