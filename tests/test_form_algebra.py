"""TDD tests for form algebra — dimensions as first-class queryable graph structure.

Tests written BEFORE implementation. Each test class corresponds to a plan step:
- TestDimsSignature: dims_signature() utility (Step 1)
- TestFormTable: form table in sidecar (Step 2)
- TestFormAlgebra: auto-derived form algebra from concept parameterizations (Step 3)
- TestWorldModelFormQueries: WorldModel form query methods (Step 4)
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from tests.family_helpers import build_sidecar
from propstore.dimensions import dims_signature
from propstore.identity import derive_concept_artifact_id
from tests.conftest import normalize_concept_payloads


# ── Helpers ──────────────────────────────────────────────────────────


def _write_form(forms_dir: Path, name: str, **kwargs) -> None:
    """Write a form YAML file."""
    data = {"name": name, "dimensionless": kwargs.pop("dimensionless", False), **kwargs}
    (forms_dir / f"{name}.yaml").write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False)
    )


def _write_concept(concepts_dir: Path, filename: str, data: dict) -> None:
    """Write a concept YAML file."""
    normalized = normalize_concept_payloads([data])[0]
    (concepts_dir / f"{filename}.yaml").write_text(
        yaml.dump(normalized, default_flow_style=False, sort_keys=False)
    )


def _concept_artifact(local_id: str) -> str:
    return derive_concept_artifact_id("propstore", local_id)


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def physics_project(tmp_path):
    """Create a minimal physics project with forms and concepts for testing.

    Forms: mass (M), distance (L), time (T), velocity (L/T), acceleration (L/T²),
           force (MLT⁻²), energy (ML²T⁻²), ratio (dimensionless)
    Concepts: mass, distance, time, velocity, acceleration, force, energy
    Parameterizations: force = mass * acceleration, energy = mass * velocity²
    """
    knowledge = tmp_path / "knowledge"
    concepts_dir = knowledge / "concepts"
    forms_dir = knowledge / "forms"
    concepts_dir.mkdir(parents=True)
    forms_dir.mkdir(parents=True)
    counters = concepts_dir / ".counters"
    counters.mkdir()
    (counters / "physics.next").write_text("10")

    # Forms with SI dimensions
    _write_form(forms_dir, "mass", kind="quantity", unit_symbol="kg",
                dimensions={"M": 1})
    _write_form(forms_dir, "distance", kind="quantity", unit_symbol="m",
                dimensions={"L": 1})
    _write_form(forms_dir, "time", kind="quantity", unit_symbol="s",
                dimensions={"T": 1})
    _write_form(forms_dir, "velocity", kind="quantity", unit_symbol="m/s",
                dimensions={"L": 1, "T": -1})
    _write_form(forms_dir, "acceleration", kind="quantity", unit_symbol="m/s^2",
                dimensions={"L": 1, "T": -2})
    _write_form(forms_dir, "force", kind="quantity", unit_symbol="N",
                dimensions={"M": 1, "L": 1, "T": -2})
    _write_form(forms_dir, "energy", kind="quantity", unit_symbol="J",
                dimensions={"M": 1, "L": 2, "T": -2})
    _write_form(forms_dir, "ratio", dimensionless=True)

    # Concepts
    _write_concept(concepts_dir, "mass", {
        "id": "concept1", "canonical_name": "mass", "status": "accepted",
        "definition": "Inertial mass.", "domain": "physics", "form": "mass",
    })
    _write_concept(concepts_dir, "distance", {
        "id": "concept2", "canonical_name": "distance", "status": "accepted",
        "definition": "Spatial displacement.", "domain": "physics", "form": "distance",
    })
    _write_concept(concepts_dir, "time", {
        "id": "concept3", "canonical_name": "time", "status": "accepted",
        "definition": "Duration.", "domain": "physics", "form": "time",
    })
    _write_concept(concepts_dir, "velocity", {
        "id": "concept4", "canonical_name": "velocity", "status": "accepted",
        "definition": "Rate of displacement.", "domain": "physics", "form": "velocity",
    })
    _write_concept(concepts_dir, "acceleration", {
        "id": "concept5", "canonical_name": "acceleration", "status": "accepted",
        "definition": "Rate of velocity change.", "domain": "physics",
        "form": "acceleration",
    })
    _write_concept(concepts_dir, "force", {
        "id": "concept6", "canonical_name": "force", "status": "accepted",
        "definition": "Push or pull on an object.", "domain": "physics", "form": "force",
        "parameterization_relationships": [{
            "inputs": ["concept1", "concept5"],
            "formula": "F = m * a",
            "sympy": "Eq(concept6, concept1 * concept5)",
            "exactness": "exact",
        }],
    })
    _write_concept(concepts_dir, "energy", {
        "id": "concept7", "canonical_name": "energy", "status": "accepted",
        "definition": "Capacity to do work.", "domain": "physics", "form": "energy",
        "parameterization_relationships": [{
            "inputs": ["concept1", "concept4"],
            "formula": "E = m * v^2",
            "sympy": "Eq(concept7, concept1 * concept4**2)",
            "exactness": "approximate",
        }],
    })

    return tmp_path


@pytest.fixture
def sidecar_path(physics_project):
    """Build sidecar from physics_project and return the db path."""
    knowledge = physics_project / "knowledge"
    sidecar = knowledge / "sidecar" / "propstore.sqlite"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    build_sidecar(knowledge, sidecar, force=True)
    return sidecar


@pytest.fixture
def bad_dims_project(tmp_path):
    """Project where a parameterization has dimensionally invalid form mapping."""
    knowledge = tmp_path / "knowledge"
    concepts_dir = knowledge / "concepts"
    forms_dir = knowledge / "forms"
    concepts_dir.mkdir(parents=True)
    forms_dir.mkdir(parents=True)
    counters = concepts_dir / ".counters"
    counters.mkdir()
    (counters / "physics.next").write_text("5")

    _write_form(forms_dir, "mass", kind="quantity", unit_symbol="kg",
                dimensions={"M": 1})
    _write_form(forms_dir, "time", kind="quantity", unit_symbol="s",
                dimensions={"T": 1})
    # force form has M·L·T⁻² but we'll parameterize it from mass * time (wrong!)
    _write_form(forms_dir, "force", kind="quantity", unit_symbol="N",
                dimensions={"M": 1, "L": 1, "T": -2})

    _write_concept(concepts_dir, "mass", {
        "id": "concept1", "canonical_name": "mass", "status": "accepted",
        "definition": "Mass.", "domain": "physics", "form": "mass",
    })
    _write_concept(concepts_dir, "time", {
        "id": "concept2", "canonical_name": "time", "status": "accepted",
        "definition": "Time.", "domain": "physics", "form": "time",
    })
    _write_concept(concepts_dir, "force", {
        "id": "concept3", "canonical_name": "force", "status": "accepted",
        "definition": "Force.", "domain": "physics", "form": "force",
        "parameterization_relationships": [{
            "inputs": ["concept1", "concept2"],
            "formula": "F = m * t",
            "sympy": "Eq(concept3, concept1 * concept2)",
            "exactness": "exact",
        }],
    })

    return tmp_path


@pytest.fixture
def bad_dims_sidecar(bad_dims_project):
    """Build sidecar from bad_dims_project and return the db path."""
    knowledge = bad_dims_project / "knowledge"
    sidecar = knowledge / "sidecar" / "propstore.sqlite"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    build_sidecar(knowledge, sidecar, force=True)
    return sidecar


class TestFormAlgebraExceptionVisibility:
    def test_rewrite_parameterization_symbols_runtime_error_propagates(
        self,
        physics_project,
        monkeypatch,
    ):
        knowledge = physics_project / "knowledge"
        sidecar = knowledge / "sidecar" / "propstore.sqlite"
        sidecar.parent.mkdir(parents=True, exist_ok=True)

        def _boom(*_args, **_kwargs):
            raise RuntimeError("rewrite boom")

        monkeypatch.setattr("propstore.sidecar.concepts.rewrite_parameterization_symbols", _boom)

        with pytest.raises(RuntimeError, match="rewrite boom"):
            build_sidecar(knowledge, sidecar, force=True)

    def test_canonical_dump_runtime_error_propagates(
        self,
        physics_project,
        monkeypatch,
    ):
        knowledge = physics_project / "knowledge"
        sidecar = knowledge / "sidecar" / "propstore.sqlite"
        sidecar.parent.mkdir(parents=True, exist_ok=True)

        def _boom(*_args, **_kwargs):
            raise RuntimeError("canonical boom")

        monkeypatch.setattr("propstore.sidecar.concepts.canonical_dump", _boom)

        with pytest.raises(RuntimeError, match="canonical boom"):
            build_sidecar(knowledge, sidecar, force=True)


# ── Step 1: dims_signature() ────────────────────────────────────────


class TestDimsSignature:
    def test_basic(self):
        assert dims_signature({"M": 1, "L": 1, "T": -2}) == "L:1,M:1,T:-2"

    def test_none_returns_none(self):
        assert dims_signature(None) is None

    def test_empty_returns_empty_string(self):
        assert dims_signature({}) == ""

    def test_strips_zero_exponents(self):
        assert dims_signature({"M": 1, "L": 0, "T": 0}) == "M:1"

    def test_sorted_by_key(self):
        assert dims_signature({"T": -2, "M": 1}) == "M:1,T:-2"

    def test_all_zeros_returns_empty(self):
        assert dims_signature({"M": 0, "L": 0}) == ""


# ── Step 2: form table ──────────────────────────────────────────────


class TestFormTable:
    def test_form_table_exists(self, sidecar_path):
        """Sidecar has a form table after build."""
        conn = sqlite3.connect(sidecar_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='form'"
        ).fetchall()
        assert len(tables) == 1

    def test_form_table_has_all_forms(self, sidecar_path):
        """All 8 forms from the fixture are stored."""
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM form").fetchone()[0]
        assert count == 8

    def test_form_dimensions_stored_as_json(self, sidecar_path):
        """Force form dimensions stored as JSON dict."""
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT dimensions FROM form WHERE name = 'force'"
        ).fetchone()
        assert row is not None
        dims = json.loads(row[0])
        assert dims == {"M": 1, "L": 1, "T": -2}

    def test_form_unit_symbol_stored(self, sidecar_path):
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT unit_symbol FROM form WHERE name = 'mass'"
        ).fetchone()
        assert row[0] == "kg"

    def test_dimensionless_form(self, sidecar_path):
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT is_dimensionless, dimensions FROM form WHERE name = 'ratio'"
        ).fetchone()
        assert row[0] == 1

    def test_form_kind_stored(self, sidecar_path):
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT kind FROM form WHERE name = 'force'"
        ).fetchone()
        assert row[0] == "quantity"


# ── Step 3: form_algebra auto-derivation ─────────────────────────────


class TestFormAlgebra:
    def test_form_algebra_table_exists(self, sidecar_path):
        conn = sqlite3.connect(sidecar_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='form_algebra'"
        ).fetchall()
        assert len(tables) == 1

    def test_algebra_derived_from_parameterization(self, sidecar_path):
        """F=m*a concept parameterization → form_algebra: force from mass, acceleration."""
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT output_form, input_forms, operation FROM form_algebra "
            "WHERE output_form = 'force'"
        ).fetchall()
        assert len(rows) >= 1
        input_forms = json.loads(rows[0][1])
        assert set(input_forms) == {"mass", "acceleration"}

    def test_algebra_records_source_concept(self, sidecar_path):
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT source_concept_id FROM form_algebra WHERE output_form = 'force'"
        ).fetchone()
        assert row is not None
        assert row[0] == _concept_artifact("concept6")

    def test_algebra_records_source_formula(self, sidecar_path):
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT source_formula FROM form_algebra WHERE output_form = 'force'"
        ).fetchone()
        assert row is not None
        assert "F" in row[0] and "m" in row[0]

    def test_algebra_handles_powers(self, sidecar_path):
        """E=m*v² → form_algebra: energy from mass, velocity with power."""
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT operation FROM form_algebra WHERE output_form = 'energy'"
        ).fetchall()
        assert len(rows) >= 1
        # The operation should reflect the squaring
        op = rows[0][0]
        assert "**2" in op or "velocity" in op

    def test_algebra_stores_dimensionally_invalid_with_flag(self, bad_dims_sidecar):
        """Parameterization with wrong dimensions → stored with dim_verified=0."""
        conn = sqlite3.connect(bad_dims_sidecar)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM form_algebra").fetchall()
        assert len(rows) >= 1, "dimensionally invalid entries must be stored, not dropped"
        assert all(row["dim_verified"] == 0 for row in rows), (
            "dimensionally invalid entries must have dim_verified=0"
        )

    def test_algebra_deduplicates(self, tmp_path):
        """Two concepts with same form algebra → one entry."""
        knowledge = tmp_path / "knowledge"
        concepts_dir = knowledge / "concepts"
        forms_dir = knowledge / "forms"
        concepts_dir.mkdir(parents=True)
        forms_dir.mkdir(parents=True)
        counters = concepts_dir / ".counters"
        counters.mkdir()
        (counters / "physics.next").write_text("10")

        _write_form(forms_dir, "mass", kind="quantity", unit_symbol="kg",
                    dimensions={"M": 1})
        _write_form(forms_dir, "acceleration", kind="quantity", unit_symbol="m/s^2",
                    dimensions={"L": 1, "T": -2})
        _write_form(forms_dir, "force", kind="quantity", unit_symbol="N",
                    dimensions={"M": 1, "L": 1, "T": -2})

        # Two different concepts, same form algebra: force = mass * acceleration
        _write_concept(concepts_dir, "mass_a", {
            "id": "concept1", "canonical_name": "mass_a", "status": "accepted",
            "definition": "Mass A.", "domain": "physics", "form": "mass",
        })
        _write_concept(concepts_dir, "accel_a", {
            "id": "concept2", "canonical_name": "accel_a", "status": "accepted",
            "definition": "Accel A.", "domain": "physics", "form": "acceleration",
        })
        _write_concept(concepts_dir, "force_a", {
            "id": "concept3", "canonical_name": "force_a", "status": "accepted",
            "definition": "Force A.", "domain": "physics", "form": "force",
            "parameterization_relationships": [{
                "inputs": ["concept1", "concept2"],
                "formula": "F_a = m_a * a_a",
                "sympy": "Eq(concept3, concept1 * concept2)",
                "exactness": "exact",
            }],
        })
        _write_concept(concepts_dir, "mass_b", {
            "id": "concept4", "canonical_name": "mass_b", "status": "accepted",
            "definition": "Mass B.", "domain": "physics", "form": "mass",
        })
        _write_concept(concepts_dir, "accel_b", {
            "id": "concept5", "canonical_name": "accel_b", "status": "accepted",
            "definition": "Accel B.", "domain": "physics", "form": "acceleration",
        })
        _write_concept(concepts_dir, "force_b", {
            "id": "concept6", "canonical_name": "force_b", "status": "accepted",
            "definition": "Force B.", "domain": "physics", "form": "force",
            "parameterization_relationships": [{
                "inputs": ["concept4", "concept5"],
                "formula": "F_b = m_b * a_b",
                "sympy": "Eq(concept6, concept4 * concept5)",
                "exactness": "exact",
            }],
        })

        sidecar = knowledge / "sidecar" / "propstore.sqlite"
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        build_sidecar(knowledge, sidecar, force=True)

        conn = sqlite3.connect(sidecar)
        count = conn.execute(
            "SELECT COUNT(*) FROM form_algebra WHERE output_form = 'force'"
        ).fetchone()[0]
        assert count == 1  # deduped


# ── Step 4: WorldModel form queries ──────────────────────────────────


@pytest.fixture
def world_model(physics_project):
    """Build sidecar and return a WorldModel."""
    from propstore.repository import Repository
    from propstore.world import WorldModel
    knowledge = physics_project / "knowledge"
    repo = Repository(knowledge)
    build_sidecar(knowledge, repo.sidecar_path, force=True)
    return WorldModel(repo)


# ── Step 5: CLI commands (enhance existing) ─────────────────────────


class TestFormListDims:
    """pks form list --dims shows dimensions, --dims X:N filters."""

    def test_list_with_dims_flag(self, world_model):
        """pks form list --show-dims shows dimension column."""
        from click.testing import CliRunner
        from propstore.cli.form import form

        runner = CliRunner()
        result = runner.invoke(form, ["list", "--show-dims"],
                               obj={"repo": _repo_from_world(world_model)})
        assert result.exit_code == 0
        assert "force" in result.output
        assert "M" in result.output  # dimension symbol present

    def test_list_filter_by_dims(self, world_model):
        from click.testing import CliRunner
        from propstore.cli.form import form

        runner = CliRunner()
        result = runner.invoke(form, ["list", "--dims", "M:1,L:1,T:-2"],
                               obj={"repo": _repo_from_world(world_model)})
        assert result.exit_code == 0
        assert "force" in result.output
        # mass should NOT be in output (different dimensions)
        lines = [l for l in result.output.strip().split("\n") if l.strip()]
        for line in lines:
            # Every line should be a form with M·L·T⁻² dims
            assert "mass" not in line.split()[0] if line.strip() else True


class TestFormShowAlgebra:
    """pks form show <name> appends algebra when sidecar exists."""

    def test_show_includes_algebra(self, world_model):
        from click.testing import CliRunner
        from propstore.cli.form import form

        runner = CliRunner()
        result = runner.invoke(form, ["show", "force"],
                               obj={"repo": _repo_from_world(world_model)})
        assert result.exit_code == 0
        assert "mass" in result.output
        assert "acceleration" in result.output


def _repo_from_world(wm):
    """Extract the Repository from a WorldModel (it stores it internally)."""
    # WorldModel stores conn but we need the repo — reconstruct from sidecar path
    from propstore.repository import Repository
    db_path = wm._conn.execute("PRAGMA database_list").fetchone()[2]
    from pathlib import Path
    sidecar_path = Path(db_path)
    return Repository(sidecar_path.parent.parent)


class TestWorldModelFormQueries:
    def test_forms_by_dimensions(self, world_model):
        results = world_model.forms_by_dimensions({"M": 1, "L": 1, "T": -2})
        form_names = [r["name"] for r in results]
        assert "force" in form_names

    def test_forms_by_dimensions_no_match(self, world_model):
        results = world_model.forms_by_dimensions({"M": 99})
        assert results == []

    def test_forms_by_dimensions_dimensionless(self, world_model):
        results = world_model.forms_by_dimensions({})
        form_names = [r["name"] for r in results]
        assert "ratio" in form_names

    def test_form_algebra_for(self, world_model):
        results = world_model.form_algebra_for("force")
        assert len(results) >= 1
        input_forms = json.loads(results[0]["input_forms"])
        assert "mass" in input_forms

    def test_form_algebra_for_no_results(self, world_model):
        results = world_model.form_algebra_for("mass")
        # mass has no decomposition (it's a base dimension)
        assert results == []

    def test_form_algebra_using(self, world_model):
        results = world_model.form_algebra_using("mass")
        output_forms = [r["output_form"] for r in results]
        assert "force" in output_forms or "energy" in output_forms

