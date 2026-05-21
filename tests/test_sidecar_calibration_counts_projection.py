from __future__ import annotations

from pathlib import Path

from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session
from propstore.families.calibration.declaration import calibration_counts_by_key
from propstore.families.world_charters import CalibrationCount, world_sqlalchemy_schema


def test_calibration_counts_use_charter_model_and_typed_query(tmp_path: Path) -> None:
    sidecar_path = tmp_path / "propstore.sqlite"
    schema = world_sqlalchemy_schema()
    create_sqlalchemy_store(sidecar_path, schema)

    table = schema.table("calibration_counts")
    assert set(table.c.keys()) == {
        "pass_number",
        "category",
        "correct_count",
        "total_count",
    }

    with writable_session(sidecar_path, schema) as derived:
        derived.session.add(
            CalibrationCount(
                pass_number=1,
                category="strong",
                correct_count=80,
                total_count=100,
            )
        )
        derived.session.commit()

    with readonly_session(sidecar_path, schema) as derived:
        assert calibration_counts_by_key(derived) == {(1, "strong"): (80, 100)}


def test_calibration_count_empty_table_returns_none(tmp_path: Path) -> None:
    sidecar_path = tmp_path / "propstore.sqlite"
    schema = world_sqlalchemy_schema()
    create_sqlalchemy_store(sidecar_path, schema)

    with readonly_session(sidecar_path, schema) as derived:
        assert calibration_counts_by_key(derived) is None
