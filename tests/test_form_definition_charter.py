"""The ``FormDefinition`` charter: projection, non-commitment, validation, algebra.

Ports the behavioral core of the reference ``test_form_dimensions`` /
``test_form_algebra`` that survives the DTO deletion: the sidecar ``form`` table
and its columns fall out of the one charter (no FormDocument/Row), every authored
form is stored regardless of consistency (non-commitment), dimensionally invalid
algebra is reported not dropped, and dimensional verification is bridgman's.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from condition_ir import KindType
from quire.sqlalchemy_schema import SqlAlchemySchema

from propstore.families.forms import (
    FormDefinition,
    FormRepository,
    validate_form_definition,
    verify_form_algebra,
)


def _physics_forms() -> list[FormDefinition]:
    return [
        FormDefinition(name="mass", kind=KindType.QUANTITY, unit_symbol="kg", dimensions={"M": 1}),
        FormDefinition(
            name="acceleration",
            kind=KindType.QUANTITY,
            unit_symbol="m/s^2",
            dimensions={"L": 1, "T": -2},
        ),
        FormDefinition(name="time", kind=KindType.QUANTITY, unit_symbol="s", dimensions={"T": 1}),
        FormDefinition(
            name="velocity",
            kind=KindType.QUANTITY,
            unit_symbol="m/s",
            dimensions={"L": 1, "T": -1},
        ),
        FormDefinition(
            name="force",
            kind=KindType.QUANTITY,
            unit_symbol="N",
            dimensions={"M": 1, "L": 1, "T": -2},
        ),
        FormDefinition(
            name="energy",
            kind=KindType.QUANTITY,
            unit_symbol="J",
            dimensions={"M": 1, "L": 2, "T": -2},
        ),
        FormDefinition(name="ratio", kind=KindType.QUANTITY, is_dimensionless=True, dimensions={}),
    ]


def _build(tmp_path: Path) -> tuple[FormRepository, Path, SqlAlchemySchema]:
    repo = FormRepository()
    for form in _physics_forms():
        repo.author(form, message=f"add {form.name}")
    sidecar = tmp_path / "forms.sqlite"
    schema = repo.build_sidecar(sidecar)
    return repo, sidecar, schema


# ── sidecar projection falls out of the charter ──────────────────────────


def test_form_table_exists_and_holds_every_form(tmp_path: Path) -> None:
    _, sidecar, _ = _build(tmp_path)
    conn = sqlite3.connect(sidecar)
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='form'"
        ).fetchall()
        assert tables == [("form",)]
        assert conn.execute("SELECT COUNT(*) FROM form").fetchone()[0] == 7
    finally:
        conn.close()


def test_form_columns_fall_out_of_charter_fields(tmp_path: Path) -> None:
    _, sidecar, _ = _build(tmp_path)
    conn = sqlite3.connect(sidecar)
    try:
        dims_row = conn.execute("SELECT dimensions FROM form WHERE name='force'").fetchone()
        assert json.loads(dims_row[0]) == {"M": 1, "L": 1, "T": -2}
        assert conn.execute("SELECT unit_symbol FROM form WHERE name='mass'").fetchone()[0] == "kg"
        assert conn.execute("SELECT kind FROM form WHERE name='force'").fetchone()[0] == "quantity"
        dimless = conn.execute(
            "SELECT is_dimensionless FROM form WHERE name='ratio'"
        ).fetchone()[0]
        assert dimless == 1
    finally:
        conn.close()


def test_render_round_trips_the_one_form_type(tmp_path: Path) -> None:
    repo, sidecar, schema = _build(tmp_path)
    by_name = {f.name: f for f in repo.render_forms(sidecar, schema)}
    assert by_name["force"].dimensions == {"M": 1, "L": 1, "T": -2}
    assert by_name["force"].kind == KindType.QUANTITY
    assert by_name["mass"].unit_symbol == "kg"
    assert by_name["ratio"].is_dimensionless is True


def test_inconsistent_form_is_stored_not_dropped(tmp_path: Path) -> None:
    # Non-commitment: a form that fails validation still lands as a row.
    repo = FormRepository()
    bad = FormDefinition(
        name="bad", kind=KindType.QUANTITY, is_dimensionless=True, dimensions={"T": -1}
    )
    assert validate_form_definition(bad)  # it IS inconsistent
    repo.author(bad, message="add bad")
    sidecar = tmp_path / "forms.sqlite"
    repo.build_sidecar(sidecar)
    conn = sqlite3.connect(sidecar)
    try:
        assert conn.execute("SELECT COUNT(*) FROM form WHERE name='bad'").fetchone()[0] == 1
    finally:
        conn.close()


# ── validation logic (diagnostics, not a storage gate) ───────────────────


def test_dimensionless_with_nonempty_dimensions_is_flagged() -> None:
    errors = validate_form_definition(
        FormDefinition(name="bad", kind=KindType.QUANTITY, is_dimensionless=True, dimensions={"T": -1})
    )
    assert errors
    assert any("dimension" in e.lower() for e in errors)


def test_nondimensionless_quantity_needs_a_dimension() -> None:
    errors = validate_form_definition(
        FormDefinition(name="bad", kind=KindType.QUANTITY, unit_symbol="Hz", dimensions={})
    )
    assert errors
    assert any("dimension" in e.lower() for e in errors)


def test_invalid_dimension_key_is_flagged() -> None:
    errors = validate_form_definition(
        FormDefinition(name="bad", kind=KindType.QUANTITY, dimensions={"123": 1})
    )
    assert any("dimension key" in e for e in errors)


def test_valid_form_has_no_errors() -> None:
    form = FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="N", dimensions={"M": 1, "L": 1, "T": -2}
    )
    assert validate_form_definition(form) == ()


# ── form algebra: dimensional verification via bridgman ──────────────────


def test_force_equals_mass_times_acceleration_verifies() -> None:
    forms = {f.name: f for f in _physics_forms()}
    assert verify_form_algebra(forms["force"], [(forms["mass"], 1), (forms["acceleration"], 1)])


def test_energy_equals_mass_times_velocity_squared_verifies() -> None:
    forms = {f.name: f for f in _physics_forms()}
    assert verify_form_algebra(forms["energy"], [(forms["mass"], 1), (forms["velocity"], 2)])


def test_dimensionally_wrong_algebra_does_not_verify() -> None:
    forms = {f.name: f for f in _physics_forms()}
    # force = mass * time is dimensionally wrong -> dim_verified is False, never fabricated True.
    assert not verify_form_algebra(forms["force"], [(forms["mass"], 1), (forms["time"], 1)])


def test_algebra_with_dimensionless_input_is_unverifiable() -> None:
    # Honest ignorance: a form without dimensions cannot verify -> False, not a guess.
    forms = {f.name: f for f in _physics_forms()}
    no_dims = FormDefinition(name="opaque", kind=KindType.QUANTITY)
    assert not verify_form_algebra(forms["force"], [(no_dims, 1)])
