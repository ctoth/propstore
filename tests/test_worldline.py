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
from propstore.cli.worldline_cmds import _parse_kv_args
from propstore.validate import load_concepts
from propstore.validate_claims import load_claim_files
from propstore.world import Environment
from propstore.world.types import DerivedResult, ValueResult
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


@pytest.fixture(scope="module")
def chained_physics_knowledge(tmp_path_factory):
    """Create a minimal physics KB with a two-hop derivation chain."""
    root = tmp_path_factory.mktemp("chained_physics_kb") / "knowledge"
    concepts_dir = root / "concepts"
    concepts_dir.mkdir(parents=True)
    counters = concepts_dir / ".counters"
    counters.mkdir()
    (counters / "physics.next").write_text("10")

    forms_dir = root / "forms"
    forms_dir.mkdir()
    for form_name in ("acceleration", "force", "mass"):
        data = {"name": form_name, "dimensionless": False, "kind": "quantity"}
        with open(forms_dir / f"{form_name}.yaml", "w", encoding="utf-8") as f:
            yaml.dump(data, f)

    def write_concept(name, data):
        with open(concepts_dir / f"{name}.yaml", "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)

    write_concept("mass", {
        "id": "concept1", "canonical_name": "mass",
        "status": "accepted", "definition": "Mass.", "form": "mass",
    })
    write_concept("gravitational_source", {
        "id": "concept2", "canonical_name": "gravitational_source",
        "status": "accepted", "definition": "Source gravity.", "form": "acceleration",
    })
    write_concept("acceleration", {
        "id": "concept3", "canonical_name": "acceleration",
        "status": "accepted", "definition": "Acceleration.", "form": "acceleration",
        "parameterization_relationships": [{
            "formula": "a = g",
            "inputs": ["concept2"],
            "sympy": "Eq(concept3, concept2)",
            "exactness": "exact",
            "source": "test",
            "bidirectional": True,
        }],
    })
    write_concept("force", {
        "id": "concept4", "canonical_name": "force",
        "status": "accepted", "definition": "Force.", "form": "force",
        "parameterization_relationships": [{
            "formula": "F = m * a",
            "inputs": ["concept1", "concept3"],
            "sympy": "Eq(concept4, concept1 * concept3)",
            "exactness": "exact",
            "source": "test",
            "bidirectional": True,
        }],
    })

    claims_dir = root / "claims"
    claims_dir.mkdir()
    with open(claims_dir / "physics_claims.yaml", "w", encoding="utf-8") as f:
        yaml.dump({
            "source": {"paper": "test"},
            "claims": [
                {
                    "id": "g_claim",
                    "type": "parameter",
                    "concept": "concept2",
                    "value": 9.807,
                    "unit": "m/s^2",
                    "provenance": {"paper": "test", "page": 1},
                },
            ],
        }, f, default_flow_style=False)

    return root


@pytest.fixture(scope="module")
def chained_physics_world(chained_physics_knowledge):
    """Build sidecar and create WorldModel for chained-derivation testing."""
    from propstore.cli.repository import Repository

    repo = Repository(chained_physics_knowledge)
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

    def test_run_uses_world_context_scope(self):
        """inputs.context is passed as bind environment context, not as a fake binding."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        class FakeBound:
            def __init__(self, context_id):
                self._context_id = context_id

            def value_of(self, concept_id):
                if self._context_id == "ctx_physics":
                    return ValueResult(
                        concept_id=concept_id,
                        status="determined",
                        claims=[{"id": "ctx_claim", "value": 42.0}],
                    )
                return ValueResult(concept_id=concept_id, status="no_claims")

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

        class FakeWorld:
            def __init__(self):
                self.last_environment = None
                self.last_conditions = None

            def bind(self, environment=None, *, policy=None, **conditions):
                self.last_environment = environment
                self.last_conditions = conditions
                context_id = environment.context_id if environment is not None else None
                return FakeBound(context_id)

            def resolve_alias(self, name):
                return None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": concept_id, "canonical_name": "target"}
                return None

            def get_claim(self, claim_id):
                return None

            @property
            def _conn(self):
                class FakeConn:
                    @staticmethod
                    def execute(*args, **kwargs):
                        class FakeCursor:
                            @staticmethod
                            def fetchone():
                                return {"id": "concept1"}
                        return FakeCursor()
                return FakeConn()

        wl = WorldlineDefinition.from_dict({
            "id": "test_context",
            "targets": ["target"],
            "inputs": {"context": "ctx_physics"},
        })
        world = FakeWorld()

        result = run_worldline(wl, world)

        assert isinstance(world.last_environment, Environment)
        assert world.last_environment.context_id == "ctx_physics"
        assert world.last_conditions == {}
        assert result.values["target"]["value"] == 42.0

    def test_run_records_transitive_dependencies(self, chained_physics_world):
        """Two-hop derivations include the upstream claim dependency."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_transitive_deps",
            "targets": ["force"],
            "inputs": {"overrides": {"mass": 10.0}},
        })

        result = run_worldline(wl, chained_physics_world)

        force = result.values["force"]
        assert force["status"] == "derived"
        assert abs(force["value"] - 98.07) < 0.1
        assert "g_claim" in result.dependencies["claims"]
        assert force["inputs_used"]["concept3"]["source"] == "derived"


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


class TestWorldlineDependencyLiveness:
    def test_resolved_worldline_tracks_all_candidate_claims_for_staleness(self):
        """A resolved result must stay live to all candidate claims, not just the winner."""
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        class FakeBound:
            def __init__(self, claims):
                self._claims = claims
                self._bindings = {}

            def value_of(self, concept_id):
                return ValueResult(concept_id=concept_id, status="conflicted", claims=self._claims)

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

            def active_claims(self, concept_id=None):
                return list(self._claims)

        class FakeWorld:
            def __init__(self, older_claim_date):
                self._claims = {
                    "claim_old": {
                        "id": "claim_old",
                        "value": 10.0,
                        "provenance_json": f'{{"date": "{older_claim_date}"}}',
                        "content_hash": f"old-{older_claim_date}",
                    },
                    "claim_new": {
                        "id": "claim_new",
                        "value": 20.0,
                        "provenance_json": '{"date": "2025-01-01"}',
                        "content_hash": "new-2025-01-01",
                    },
                }

            def bind(self, environment=None, *, policy=None, **conditions):
                claims = [self._claims["claim_old"], self._claims["claim_new"]]
                return FakeBound(claims)

            def resolve_concept(self, name):
                return "concept1" if name == "target" else None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": concept_id, "canonical_name": "target"}
                return None

            def get_claim(self, claim_id):
                return self._claims.get(claim_id)

            def has_table(self, name):
                return False

        wl = WorldlineDefinition.from_dict({
            "id": "recency_liveness",
            "targets": ["target"],
            "policy": {"strategy": "recency"},
        })
        original_world = FakeWorld("2024-01-01")
        changed_world = FakeWorld("2026-01-01")

        result = run_worldline(wl, original_world)
        wl.results = result
        rerun = run_worldline(wl, changed_world)

        assert rerun.values["target"]["value"] == 10.0
        assert sorted(result.dependencies["claims"]) == ["claim_new", "claim_old"]
        assert wl.is_stale(changed_world)

    def test_argumentation_worldline_records_stance_dependencies_and_detects_staleness(self, monkeypatch):
        """Argumentation-sensitive worldlines must record stance inputs and go stale when they flip."""
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        class FakeBound:
            def __init__(self, claims):
                self._claims = claims
                self._bindings = {}

            def value_of(self, concept_id):
                return ValueResult(concept_id=concept_id, status="conflicted", claims=self._claims)

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

            def active_claims(self, concept_id=None):
                return list(self._claims)

        class FakeWorld:
            def __init__(self, winner_id, stance_type):
                self._winner_id = winner_id
                self._stance_type = stance_type
                self._claims = {
                    "claim_a": {"id": "claim_a", "value": 10.0, "content_hash": "hash-a"},
                    "claim_b": {"id": "claim_b", "value": 20.0, "content_hash": "hash-b"},
                }

            def bind(self, environment=None, *, policy=None, **conditions):
                claims = [self._claims["claim_a"], self._claims["claim_b"]]
                return FakeBound(claims)

            def resolve_concept(self, name):
                return "concept1" if name == "target" else None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": concept_id, "canonical_name": "target"}
                return None

            def get_claim(self, claim_id):
                return self._claims.get(claim_id)

            def has_table(self, name):
                return name == "claim_stance"

            def claims_by_ids(self, claim_ids):
                return {cid: self._claims[cid] for cid in claim_ids if cid in self._claims}

            def stances_between(self, claim_ids):
                if {"claim_a", "claim_b"}.issubset(claim_ids):
                    return [{
                        "claim_id": "claim_b",
                        "target_claim_id": "claim_a",
                        "stance_type": self._stance_type,
                        "confidence": 1.0,
                        "note": f"{self._stance_type}-note",
                    }]
                return []

        def fake_justified_claims(world, active_claim_ids, **kwargs):
            return frozenset({world._winner_id}) & frozenset(active_claim_ids)

        monkeypatch.setattr(
            "propstore.argumentation.compute_justified_claims",
            fake_justified_claims,
        )

        wl = WorldlineDefinition.from_dict({
            "id": "argumentation_liveness",
            "targets": ["target"],
            "policy": {"strategy": "argumentation"},
        })
        original_world = FakeWorld("claim_a", "rebuts")
        changed_world = FakeWorld("claim_b", "supports")

        result = run_worldline(wl, original_world)
        wl.results = result

        assert result.values["target"]["value"] == 10.0
        assert result.dependencies["stances"]
        assert wl.is_stale(changed_world)

    def test_context_sensitive_worldline_detects_staleness_when_context_behavior_changes(self):
        """Context-scoped worldlines must become stale when that context resolves differently."""
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        class FakeBound:
            def __init__(self, context_id, active):
                self._context_id = context_id
                self._active = active
                self._bindings = {}

            def value_of(self, concept_id):
                if self._context_id == "ctx_physics" and self._active:
                    return ValueResult(
                        concept_id=concept_id,
                        status="determined",
                        claims=[{"id": "ctx_claim", "value": 42.0, "content_hash": "ctx-live"}],
                    )
                return ValueResult(concept_id=concept_id, status="no_claims")

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

            def active_claims(self, concept_id=None):
                if self._context_id == "ctx_physics" and self._active:
                    return [{"id": "ctx_claim", "value": 42.0, "content_hash": "ctx-live"}]
                return []

        class FakeWorld:
            def __init__(self, active):
                self._active = active

            def bind(self, environment=None, *, policy=None, **conditions):
                context_id = environment.context_id if environment is not None else None
                return FakeBound(context_id, self._active)

            def resolve_concept(self, name):
                return "concept1" if name == "target" else None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": concept_id, "canonical_name": "target"}
                return None

            def get_claim(self, claim_id):
                if self._active and claim_id == "ctx_claim":
                    return {"id": "ctx_claim", "value": 42.0, "content_hash": "ctx-live"}
                return None

            def has_table(self, name):
                return False

        wl = WorldlineDefinition.from_dict({
            "id": "context_liveness",
            "targets": ["target"],
            "inputs": {"context": "ctx_physics"},
        })
        original_world = FakeWorld(True)
        changed_world = FakeWorld(False)

        result = run_worldline(wl, original_world)
        wl.results = result

        assert result.dependencies["contexts"] == ["ctx_physics"]
        assert wl.is_stale(changed_world)

    def test_run_worldline_uses_world_interface_for_concept_lookup(self):
        """Worldline materialization should not require a private SQLite connection."""
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline_runner import run_worldline

        class MinimalBound:
            def __init__(self):
                self._bindings = {}

            def value_of(self, concept_id):
                return ValueResult(
                    concept_id=concept_id,
                    status="determined",
                    claims=[{"id": "claim1", "value": 42.0, "content_hash": "claim-1"}],
                )

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

            def active_claims(self, concept_id=None):
                return [{"id": "claim1", "value": 42.0, "content_hash": "claim-1"}]

        class MinimalWorld:
            def bind(self, environment=None, *, policy=None, **conditions):
                return MinimalBound()

            def resolve_concept(self, name):
                return "concept1" if name == "target" else None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": "concept1", "canonical_name": "target"}
                return None

            def get_claim(self, claim_id):
                if claim_id == "claim1":
                    return {"id": "claim1", "value": 42.0, "content_hash": "claim-1"}
                return None

            def has_table(self, name):
                return False

        wl = WorldlineDefinition.from_dict({
            "id": "interface_lookup",
            "targets": ["target"],
        })

        result = run_worldline(wl, MinimalWorld())
        assert result.values["target"]["value"] == 42.0


class TestWorldlineCliParsing:
    def test_parse_kv_args_coerces_scalar_bindings(self):
        """CLI bindings preserve basic scalar types instead of stringifying all input."""
        parsed = _parse_kv_args(("count=10", "enabled=true", "place=earth", "ratio=0.5"))

        assert parsed == {
            "count": 10,
            "enabled": True,
            "place": "earth",
            "ratio": 0.5,
        }
