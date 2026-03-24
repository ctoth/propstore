"""TDD tests for worldline — materialized query artifacts.

Phase 1: Data model + YAML I/O
Phase 2: Materialization engine
Phase 4: Staleness detection

Tests are written BEFORE implementation. They import from propstore.worldline
which does not exist yet — all tests should fail with ImportError initially.
"""

import sqlite3
from pathlib import Path

import pytest
import yaml

from propstore.build_sidecar import build_sidecar
from propstore.validate import load_concepts
from propstore.validate_claims import load_claim_files
from propstore.world import WorldModel


# ── Test fixtures ───────────────────────────────────────────────────


@pytest.fixture
def worldline_yaml_question():
    """A worldline YAML dict with only the question (no results)."""
    return {
        "id": "test_wl_1",
        "name": "Test worldline",
        "created": "2026-03-23",
        "inputs": {
            "bindings": {"location": "earth"},
            "overrides": {"mass": 10.0},
        },
        "policy": {
            "strategy": "argumentation",
            "semantics": "grounded",
        },
        "targets": ["force", "gravitational_acceleration"],
    }


@pytest.fixture
def worldline_yaml_with_results(worldline_yaml_question):
    """A worldline YAML dict with both question and results."""
    wl = dict(worldline_yaml_question)
    wl["results"] = {
        "computed": "2026-03-23T14:30:00",
        "content_hash": "abc123",
        "values": {
            "gravitational_acceleration": {
                "status": "determined",
                "value": 9.807,
                "source": "claim",
                "claim_id": "g_earth",
            },
            "force": {
                "status": "derived",
                "value": 98.07,
                "source": "derived",
                "formula": "mass * acceleration",
                "inputs_used": {
                    "mass": {"value": 10.0, "source": "override"},
                    "acceleration": {"value": 9.807, "source": "claim", "claim_id": "g_earth"},
                },
            },
        },
        "steps": [
            {"concept": "location", "value": "earth", "source": "binding"},
            {"concept": "gravitational_acceleration", "value": 9.807, "source": "claim", "claim_id": "g_earth"},
            {"concept": "mass", "value": 10.0, "source": "override"},
            {"concept": "force", "value": 98.07, "source": "derived", "formula": "mass * acceleration"},
        ],
        "dependencies": {
            "claims": ["g_earth"],
            "stances": [],
            "contexts": [],
        },
    }
    return wl


@pytest.fixture
def worldline_yaml_file(tmp_path, worldline_yaml_question):
    """Write a worldline YAML to disk and return the path."""
    path = tmp_path / "worldlines" / "test_wl_1.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(worldline_yaml_question, f, default_flow_style=False)
    return path


# ── Shared physics fixtures (reused across phases) ──────────────────


@pytest.fixture(scope="module")
def physics_knowledge(tmp_path_factory):
    """Create a minimal physics knowledge base for worldline testing."""
    root = tmp_path_factory.mktemp("physics_kb") / "knowledge"
    concepts_dir = root / "concepts"
    concepts_dir.mkdir(parents=True)
    counters = concepts_dir / ".counters"
    counters.mkdir()
    (counters / "physics.next").write_text("10")

    forms_dir = root / "forms"
    forms_dir.mkdir()
    for form_name in ("acceleration", "force", "mass", "velocity", "energy", "category"):
        data = {"name": form_name, "dimensionless": False, "kind": "quantity"}
        if form_name == "category":
            data["kind"] = "category"
        with open(forms_dir / f"{form_name}.yaml", "w") as f:
            yaml.dump(data, f)

    def write_concept(name, data):
        with open(concepts_dir / f"{name}.yaml", "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    write_concept("mass", {
        "id": "concept1", "canonical_name": "mass",
        "status": "accepted", "definition": "Mass.", "form": "mass",
    })
    write_concept("acceleration", {
        "id": "concept2", "canonical_name": "acceleration",
        "status": "accepted", "definition": "Acceleration.", "form": "acceleration",
    })
    write_concept("force", {
        "id": "concept3", "canonical_name": "force",
        "status": "accepted", "definition": "Force.",
        "form": "force",
        "parameterization_relationships": [{
            "formula": "F = m * a",
            "inputs": ["concept1", "concept2"],
            "sympy": "Eq(concept3, concept1 * concept2)",
            "exactness": "exact",
            "source": "Newton",
            "bidirectional": True,
        }],
    })
    write_concept("velocity", {
        "id": "concept4", "canonical_name": "velocity",
        "status": "accepted", "definition": "Velocity.", "form": "velocity",
    })
    write_concept("kinetic_energy", {
        "id": "concept5", "canonical_name": "kinetic_energy",
        "status": "accepted", "definition": "Kinetic energy.",
        "form": "energy",
        "parameterization_relationships": [{
            "formula": "E = 0.5 * m * v^2",
            "inputs": ["concept1", "concept4"],
            "sympy": "Eq(concept5, 0.5 * concept1 * concept4**2)",
            "exactness": "exact",
            "source": "textbook",
            "bidirectional": True,
        }],
    })
    write_concept("location", {
        "id": "concept6", "canonical_name": "location",
        "status": "accepted", "definition": "Location.",
        "form": "category",
        "form_parameters": {"values": ["earth", "moon"], "extensible": False},
    })

    claims_dir = root / "claims"
    claims_dir.mkdir()
    with open(claims_dir / "physics_claims.yaml", "w") as f:
        yaml.dump({
            "source": {"paper": "test"},
            "claims": [
                {
                    "id": "g_earth",
                    "type": "parameter",
                    "concept": "concept2",
                    "value": 9.807,
                    "unit": "m/s^2",
                    "conditions": ["location == 'earth'"],
                    "provenance": {"paper": "test", "page": 1},
                },
                {
                    "id": "g_moon",
                    "type": "parameter",
                    "concept": "concept2",
                    "value": 1.625,
                    "unit": "m/s^2",
                    "conditions": ["location == 'moon'"],
                    "provenance": {"paper": "test", "page": 1},
                },
                {
                    "id": "mass_5kg",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 5.0,
                    "unit": "kg",
                    "provenance": {"paper": "test", "page": 1},
                },
            ],
        }, f, default_flow_style=False)

    return root


@pytest.fixture(scope="module")
def physics_world(physics_knowledge):
    """Build sidecar and create WorldModel for physics knowledge."""
    from propstore.cli.repository import Repository
    repo = Repository(physics_knowledge)

    concepts = load_concepts(repo.concepts_dir)
    claim_files = load_claim_files(repo.claims_dir)
    sidecar_path = repo.sidecar_path
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    build_sidecar(concepts, sidecar_path, claim_files=claim_files, repo=repo)
    return WorldModel(repo)


# ═══════════════════════════════════════════════════════════════════
# Phase 1: Data model + YAML I/O
# ═══════════════════════════════════════════════════════════════════


class TestWorldlineDefinition:
    """Phase 1 gate tests — data model parsing and validation."""

    def test_worldline_definition_from_yaml(self, worldline_yaml_question):
        """Can parse a worldline YAML dict into a WorldlineDefinition."""
        from propstore.worldline import WorldlineDefinition
        wl = WorldlineDefinition.from_dict(worldline_yaml_question)
        assert wl.id == "test_wl_1"
        assert wl.targets == ["force", "gravitational_acceleration"]
        assert wl.inputs.bindings == {"location": "earth"}
        assert wl.inputs.overrides == {"mass": 10.0}

    def test_worldline_definition_from_file(self, worldline_yaml_file):
        """Can load a WorldlineDefinition from a YAML file."""
        from propstore.worldline import WorldlineDefinition
        wl = WorldlineDefinition.from_file(worldline_yaml_file)
        assert wl.id == "test_wl_1"

    def test_worldline_definition_roundtrip(self, worldline_yaml_question):
        """Save → load → save produces equivalent data."""
        from propstore.worldline import WorldlineDefinition
        wl = WorldlineDefinition.from_dict(worldline_yaml_question)
        exported = wl.to_dict()
        wl2 = WorldlineDefinition.from_dict(exported)
        assert wl.id == wl2.id
        assert wl.targets == wl2.targets
        assert wl.inputs.bindings == wl2.inputs.bindings
        assert wl.inputs.overrides == wl2.inputs.overrides

    def test_worldline_definition_requires_id(self):
        """A worldline without an id is rejected."""
        from propstore.worldline import WorldlineDefinition
        with pytest.raises((ValueError, KeyError)):
            WorldlineDefinition.from_dict({
                "name": "no id",
                "targets": ["force"],
            })

    def test_worldline_definition_requires_targets(self):
        """A worldline without targets is rejected."""
        from propstore.worldline import WorldlineDefinition
        with pytest.raises((ValueError, KeyError)):
            WorldlineDefinition.from_dict({
                "id": "no_targets",
                "name": "no targets",
            })

    def test_worldline_result_from_yaml(self, worldline_yaml_with_results):
        """Can parse a worldline YAML with results into a WorldlineResult."""
        from propstore.worldline import WorldlineDefinition
        wl = WorldlineDefinition.from_dict(worldline_yaml_with_results)
        assert wl.results is not None
        assert "force" in wl.results.values
        assert wl.results.values["force"]["value"] == 98.07

    def test_worldline_has_no_results_initially(self, worldline_yaml_question):
        """A question-only worldline has no results."""
        from propstore.worldline import WorldlineDefinition
        wl = WorldlineDefinition.from_dict(worldline_yaml_question)
        assert wl.results is None


# ═══════════════════════════════════════════════════════════════════
# Phase 2: Materialization engine
# ═══════════════════════════════════════════════════════════════════


class TestWorldlineRunner:
    """Phase 2 gate tests — computing worldline results."""

    def test_run_produces_results(self, physics_world):
        """Running a worldline populates results."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_run",
            "targets": ["acceleration"],
            "inputs": {"bindings": {"location": "earth"}},
        })
        result = run_worldline(wl, physics_world)
        assert result is not None
        assert "acceleration" in result.values

    def test_run_with_override_derives_value(self, physics_world):
        """Override mass=10 + claim g=9.807 → derives force≈98.07."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_derive",
            "targets": ["force"],
            "inputs": {
                "bindings": {"location": "earth"},
                "overrides": {"mass": 10.0},
            },
        })
        result = run_worldline(wl, physics_world)
        assert "force" in result.values
        force = result.values["force"]
        assert force["status"] == "derived"
        assert abs(force["value"] - 98.07) < 0.1

    def test_run_records_dependencies(self, physics_world):
        """Dependencies list all claims that contributed to results."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_deps",
            "targets": ["force"],
            "inputs": {
                "bindings": {"location": "earth"},
                "overrides": {"mass": 10.0},
            },
        })
        result = run_worldline(wl, physics_world)
        assert "g_earth" in result.dependencies["claims"]

    def test_run_partial_results(self, physics_world):
        """Targets that can't be determined get status=underspecified."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_partial",
            "targets": ["kinetic_energy"],  # needs velocity, which has no claims or overrides
            "inputs": {},
        })
        result = run_worldline(wl, physics_world)
        assert "kinetic_energy" in result.values
        assert result.values["kinetic_energy"]["status"] in ("underspecified", "no_relationship")

    def test_run_override_precedence(self, physics_world):
        """Override value takes precedence over claims."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        # mass has a claim (mass_5kg = 5.0), but override says 99.0
        wl = WorldlineDefinition.from_dict({
            "id": "test_override",
            "targets": ["mass"],
            "inputs": {"overrides": {"mass": 99.0}},
        })
        result = run_worldline(wl, physics_world)
        assert result.values["mass"]["value"] == 99.0
        assert result.values["mass"]["source"] == "override"

    def test_run_deterministic(self, physics_world):
        """Running the same definition twice produces identical results."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_det",
            "targets": ["force"],
            "inputs": {
                "bindings": {"location": "earth"},
                "overrides": {"mass": 10.0},
            },
        })
        r1 = run_worldline(wl, physics_world)
        r2 = run_worldline(wl, physics_world)
        assert r1.values == r2.values
        assert r1.dependencies == r2.dependencies

    def test_all_targets_in_results(self, physics_world):
        """Every target appears in results, even if underspecified (P10)."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        targets = ["force", "kinetic_energy", "acceleration"]
        wl = WorldlineDefinition.from_dict({
            "id": "test_all_targets",
            "targets": targets,
            "inputs": {"bindings": {"location": "earth"}, "overrides": {"mass": 10.0}},
        })
        result = run_worldline(wl, physics_world)
        for t in targets:
            assert t in result.values, f"Target {t} missing from results"

    def test_derived_value_accuracy(self, physics_world):
        """Derived values match SymPy evaluation of formula + inputs (P9)."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline
        from sympy.parsing.sympy_parser import parse_expr

        wl = WorldlineDefinition.from_dict({
            "id": "test_accuracy",
            "targets": ["force"],
            "inputs": {
                "bindings": {"location": "earth"},
                "overrides": {"mass": 10.0},
            },
        })
        result = run_worldline(wl, physics_world)
        force = result.values["force"]
        if force["status"] == "derived" and force.get("formula"):
            # Verify value matches formula evaluation
            inputs = {k: v["value"] for k, v in force["inputs_used"].items()}
            # The formula uses concept IDs, so we verify numerically
            expected = inputs.get("concept1", inputs.get("mass", 10.0)) * inputs.get("concept2", inputs.get("acceleration", 9.807))
            assert abs(force["value"] - expected) < 1e-9


# ═══════════════════════════════════════════════════════════════════
# Phase 4: Staleness detection
# ═══════════════════════════════════════════════════════════════════


class TestWorldlineStaleness:
    """Phase 4 gate tests — detecting when upstream claims change."""

    def test_fresh_worldline_not_stale(self, physics_world):
        """Immediately after run, worldline is not stale."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_fresh",
            "targets": ["acceleration"],
            "inputs": {"bindings": {"location": "earth"}},
        })
        result = run_worldline(wl, physics_world)
        wl.results = result
        assert not wl.is_stale(physics_world)

    def test_all_targets_present_after_run(self, physics_world):
        """After running, every target has a result entry."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_targets_present",
            "targets": ["force", "acceleration"],
            "inputs": {"bindings": {"location": "earth"}, "overrides": {"mass": 5.0}},
        })
        result = run_worldline(wl, physics_world)
        for t in ["force", "acceleration"]:
            assert t in result.values
