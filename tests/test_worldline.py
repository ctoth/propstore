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
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.identity import derive_concept_artifact_id
from propstore.sidecar.build import build_sidecar
from propstore.cli.worldline_cmds import _parse_kv_args
from propstore.knowledge_path import GitKnowledgePath
from propstore.repo import KnowledgeRepo
from propstore.world import Environment, RenderPolicy
from propstore.world.types import DerivedResult, ValueResult
from propstore.world import WorldModel
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def _concept_artifact(local_id: str) -> str:
    return derive_concept_artifact_id("propstore", local_id)


# ── Test fixtures ───────────────────────────────────────────────────


class _FakeWorldlineRepo:
    def __init__(self, worldlines_dir: Path):
        self._root = worldlines_dir.parent
        existing_worldlines = {
            f"worldlines/{path.name}": path.read_bytes()
            for path in sorted(worldlines_dir.glob("*.yaml"))
        }
        self.git = KnowledgeRepo.init(self._root)
        if existing_worldlines:
            self.git.commit_files(existing_worldlines, "Seed fake worldlines")
            self.git.sync_worktree()

    @property
    def worldlines_dir(self) -> Path:
        return self._root / "worldlines"

    def tree(self):
        return GitKnowledgePath(self.git)


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
            yaml.dump(normalize_concept_payloads([data])[0], f, default_flow_style=False)

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
        yaml.dump(normalize_claims_payload({
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
        }), f, default_flow_style=False)

    return root


@pytest.fixture(scope="module")
def physics_world(physics_knowledge):
    """Build sidecar and create WorldModel for physics knowledge."""
    from propstore.cli.repository import Repository

    repo = Repository(physics_knowledge)
    repo.sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    build_sidecar(physics_knowledge, repo.sidecar_path)
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
            yaml.dump(normalize_concept_payloads([data])[0], f, default_flow_style=False)

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
        yaml.dump(normalize_claims_payload({
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
        }), f, default_flow_style=False)

    return root


@pytest.fixture(scope="module")
def chained_physics_world(chained_physics_knowledge):
    """Build sidecar and create WorldModel for chained-derivation testing."""
    from propstore.cli.repository import Repository

    repo = Repository(chained_physics_knowledge)
    repo.sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    build_sidecar(chained_physics_knowledge, repo.sidecar_path)
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
        assert dict(wl.inputs.environment.bindings) == {"location": "earth"}
        assert wl.inputs.overrides == {"mass": 10.0}
        assert isinstance(wl.policy, RenderPolicy)
        assert isinstance(wl.inputs.environment, Environment)

    def test_worldline_definition_uses_canonical_environment_and_policy_types(self):
        """Worldlines should store the shared runtime Environment and RenderPolicy objects."""
        from propstore.worldline import WorldlineDefinition

        wl = WorldlineDefinition.from_dict({
            "id": "canonical_types",
            "targets": ["force"],
            "inputs": {
                "bindings": {"location": "earth"},
                "context_id": "ctx_physics",
            },
            "policy": {
                "strategy": "argumentation",
                "reasoning_backend": "atms",
            },
        })

        assert isinstance(wl.inputs.environment, Environment)
        assert wl.inputs.environment.context_id == "ctx_physics"
        assert isinstance(wl.policy, RenderPolicy)

    def test_worldline_definition_from_file(self, worldline_yaml_file):
        """Can load a WorldlineDefinition from a YAML file."""
        from propstore.worldline import WorldlineDefinition
        wl = WorldlineDefinition.from_file(worldline_yaml_file)
        assert wl.id == "test_wl_1"

    def test_worldline_definition_from_file_rejects_unknown_fields(self, tmp_path):
        from propstore.worldline import WorldlineDefinition

        path = tmp_path / "worldlines" / "bad.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                {
                    "id": "bad",
                    "targets": ["force"],
                    "mystery": "nope",
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="mystery"):
            WorldlineDefinition.from_file(path)

    def test_worldline_definition_roundtrip(self, worldline_yaml_question):
        """Save → load → save produces equivalent data."""
        from propstore.worldline import WorldlineDefinition
        wl = WorldlineDefinition.from_dict(worldline_yaml_question)
        exported = wl.to_dict()
        wl2 = WorldlineDefinition.from_dict(exported)
        assert wl.id == wl2.id
        assert wl.targets == wl2.targets
        assert wl.inputs.environment == wl2.inputs.environment
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

    def test_worldline_definition_rejects_unknown_reasoning_backend(self):
        """Unknown semantic backends fail during worldline parsing, not execution."""
        from propstore.worldline import WorldlineDefinition

        with pytest.raises(ValueError, match="Unknown reasoning_backend"):
            WorldlineDefinition.from_dict({
                "id": "bad_backend",
                "targets": ["force"],
                "policy": {"reasoning_backend": "not_real"},
            })

    def test_worldline_result_from_yaml(self, worldline_yaml_with_results):
        """Can parse a worldline YAML with results into a WorldlineResult."""
        from propstore.worldline import WorldlineDefinition
        wl = WorldlineDefinition.from_dict(worldline_yaml_with_results)
        assert wl.results is not None
        assert "force" in wl.results.values
        assert wl.results.values["force"].value == 98.07

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
        from propstore.worldline import run_worldline

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
        from propstore.worldline import run_worldline

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
        assert force.status == "derived"
        assert abs(force.value - 98.07) < 0.1

    def test_run_records_dependencies(self, physics_world):
        """Dependencies list all claims that contributed to results."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_deps",
            "targets": ["force"],
            "inputs": {
                "bindings": {"location": "earth"},
                "overrides": {"mass": 10.0},
            },
        })
        result = run_worldline(wl, physics_world)
        assert "g_earth" in result.dependencies.claims

    def test_run_partial_results(self, physics_world):
        """Targets that can't be determined get status=underspecified."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_partial",
            "targets": ["kinetic_energy"],  # needs velocity, which has no claims or overrides
            "inputs": {},
        })
        result = run_worldline(wl, physics_world)
        assert "kinetic_energy" in result.values
        assert result.values["kinetic_energy"].status in ("underspecified", "no_relationship")

    def test_run_override_precedence(self, physics_world):
        """Override value takes precedence over claims."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        # mass has a claim (mass_5kg = 5.0), but override says 99.0
        wl = WorldlineDefinition.from_dict({
            "id": "test_override",
            "targets": ["mass"],
            "inputs": {"overrides": {"mass": 99.0}},
        })
        result = run_worldline(wl, physics_world)
        assert result.values["mass"].value == 99.0
        assert result.values["mass"].source == "override"

    def test_run_deterministic(self, physics_world):
        """Running the same definition twice produces identical results."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

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
        from propstore.worldline import run_worldline

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
        from propstore.worldline import run_worldline
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
        if force.status == "derived" and force.formula:
            # Verify value matches formula evaluation
            inputs = {
                key: input_source.value
                for key, input_source in force.inputs_used.items()
            }
            # The formula uses concept IDs, so we verify numerically
            expected = inputs.get("concept1", inputs.get("mass", 10.0)) * inputs.get("concept2", inputs.get("acceleration", 9.807))
            assert abs(force.value - expected) < 1e-9

    def test_run_uses_world_context_scope(self):
        """inputs.environment.context_id is passed as bind environment context, not as a fake binding."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

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

            def resolve_concept(self, name):
                """Resolve canonical name or alias to concept ID."""
                resolved = self.resolve_alias(name)
                if resolved:
                    return resolved
                concept = self.get_concept(name)
                if concept:
                    return name
                # Resolve by canonical name
                if name == "target":
                    return "concept1"
                return None

            def get_claim(self, claim_id):
                return None

        wl = WorldlineDefinition.from_dict({
            "id": "test_context",
            "targets": ["target"],
            "inputs": {"context_id": "ctx_physics"},
        })
        world = FakeWorld()

        result = run_worldline(wl, world)

        assert isinstance(world.last_environment, Environment)
        assert world.last_environment.context_id == "ctx_physics"
        assert world.last_conditions == {}
        assert result.values["target"].value == 42.0

    def test_run_records_transitive_dependencies(self, chained_physics_world):
        """Two-hop derivations include the upstream claim dependency."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        wl = WorldlineDefinition.from_dict({
            "id": "test_transitive_deps",
            "targets": ["force"],
            "inputs": {"overrides": {"mass": 10.0}},
        })

        result = run_worldline(wl, chained_physics_world)

        force = result.values["force"]
        assert force.status == "derived"
        assert abs(force.value - 98.07) < 0.1
        assert "g_claim" in result.dependencies.claims
        assert force.inputs_used[_concept_artifact("concept3")].source == "derived"


# ═══════════════════════════════════════════════════════════════════
# Phase 4: Staleness detection
# ═══════════════════════════════════════════════════════════════════


class TestWorldlineStaleness:
    """Phase 4 gate tests — detecting when upstream claims change."""

    def test_fresh_worldline_not_stale(self, physics_world):
        """Immediately after run, worldline is not stale."""
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

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
        from propstore.worldline import run_worldline

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
        from propstore.worldline import run_worldline

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

        assert rerun.values["target"].value == 10.0
        assert sorted(result.dependencies.claims) == ["claim_new", "claim_old"]
        assert wl.is_stale(changed_world)

    def test_argumentation_worldline_records_stance_dependencies_and_detects_staleness(self, monkeypatch):
        """Argumentation-sensitive worldlines must record stance inputs and go stale when they flip."""
        from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

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
                return name == "relation_edge"

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
            "propstore.claim_graph.compute_claim_graph_justified_claims",
            fake_justified_claims,
        )
        monkeypatch.setattr(
            "propstore.core.analyzers.shared_analyzer_input_from_store",
            lambda world, active_claim_ids, **kwargs: world,
        )

        def fake_analyze_claim_graph(world, *, semantics="grounded", target_claim_ids=None):
            target_ids = tuple(sorted(target_claim_ids or ()))
            survivor_ids = ()
            if world._winner_id in target_ids:
                survivor_ids = (world._winner_id,)
            return AnalyzerResult(
                backend="claim_graph",
                semantics=semantics,
                extensions=(
                    ExtensionResult(
                        name=semantics,
                        accepted_claim_ids=(world._winner_id,),
                    ),
                ),
                projection=ClaimProjection(
                    target_claim_ids=target_ids,
                    survivor_claim_ids=survivor_ids,
                    witness_claim_ids=survivor_ids,
                ),
            )

        monkeypatch.setattr(
            "propstore.core.analyzers.analyze_claim_graph",
            fake_analyze_claim_graph,
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

        assert result.values["target"].value == 10.0
        assert result.dependencies.stances
        assert wl.is_stale(changed_world)

    def test_context_sensitive_worldline_detects_staleness_when_context_behavior_changes(self):
        """Context-scoped worldlines must become stale when that context resolves differently."""
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

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
            "inputs": {"context_id": "ctx_physics"},
        })
        original_world = FakeWorld(True)
        changed_world = FakeWorld(False)

        result = run_worldline(wl, original_world)
        wl.results = result

        assert result.dependencies.contexts == ("ctx_physics",)
        assert wl.is_stale(changed_world)

    def test_run_worldline_uses_world_interface_for_concept_lookup(self):
        """Worldline materialization should not require a private SQLite connection."""
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

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
        assert result.values["target"].value == 42.0


class TestSemanticCorePhase7Worldlines:
    def _graph_only_world(self):
        from propstore.core.graph_types import (
            ActiveWorldGraph,
            ClaimNode,
            CompiledWorldGraph,
            RelationEdge,
        )

        claims = {
            "claim_a": {"id": "claim_a", "concept_id": "concept1", "value": 10.0, "content_hash": "hash-a"},
            "claim_b": {"id": "claim_b", "concept_id": "concept1", "value": 20.0, "content_hash": "hash-b"},
        }
        compiled = CompiledWorldGraph(
            claims=(
                ClaimNode(
                    claim_id="claim_a",
                    concept_id="concept1",
                    claim_type="parameter",
                    scalar_value=10.0,
                    attributes={"content_hash": "hash-a"},
                ),
                ClaimNode(
                    claim_id="claim_b",
                    concept_id="concept1",
                    claim_type="parameter",
                    scalar_value=20.0,
                    attributes={"content_hash": "hash-b"},
                ),
            ),
            relations=(
                RelationEdge(
                    source_id="claim_b",
                    target_id="claim_a",
                    relation_type="rebuts",
                    attributes={"confidence": 0.8, "note": "rebuts-note"},
                ),
            ),
        )
        active_graph = ActiveWorldGraph(
            compiled=compiled,
            environment=Environment(),
            active_claim_ids=("claim_a", "claim_b"),
            inactive_claim_ids=(),
        )

        class _Bound:
            def __init__(self, claim_order):
                self._bindings = {}
                self._claims = claims
                self._claim_order = claim_order
                self._active_graph = active_graph

            def value_of(self, concept_id):
                return ValueResult(
                    concept_id=concept_id,
                    status="conflicted",
                    claims=[self._claims[claim_id] for claim_id in self._claim_order],
                )

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

            def active_claims(self, concept_id=None):
                return [self._claims[claim_id] for claim_id in self._claim_order]

        class _World:
            def __init__(self):
                self._bind_calls = 0

            def bind(self, environment=None, *, policy=None, **conditions):
                self._bind_calls += 1
                order = ["claim_a", "claim_b"] if self._bind_calls % 2 else ["claim_b", "claim_a"]
                return _Bound(order)

            def resolve_concept(self, name):
                return "concept1" if name == "target" else None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": "concept1", "canonical_name": "target"}
                return None

            def get_claim(self, claim_id):
                return claims.get(claim_id)

            def has_table(self, name):
                return name == "relation_edge"

        return _World(), active_graph

    def test_claim_graph_worldline_capture_uses_active_graph_projection_contract(
        self,
        monkeypatch,
    ):
        from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        world, active_graph = self._graph_only_world()

        def fake_shared(graph, **kwargs):
            assert graph == active_graph
            return "shared-claim-graph"

        def fake_analyze(shared, *, semantics="grounded", target_claim_ids=None):
            assert shared == "shared-claim-graph"
            target_ids = tuple(sorted(target_claim_ids or ()))
            projection = None
            if target_claim_ids is not None:
                projection = ClaimProjection(
                    target_claim_ids=target_ids,
                    survivor_claim_ids=("claim_a",),
                    witness_claim_ids=target_ids,
                )
            return AnalyzerResult(
                backend="claim_graph",
                semantics=semantics,
                extensions=(ExtensionResult(name=semantics, accepted_claim_ids=("claim_a",)),),
                projection=projection,
            )

        monkeypatch.setattr(
            "propstore.core.analyzers.shared_analyzer_input_from_active_graph",
            fake_shared,
        )
        monkeypatch.setattr(
            "propstore.core.analyzers.analyze_claim_graph",
            fake_analyze,
        )

        result = run_worldline(
            WorldlineDefinition.from_dict({
                "id": "phase7_claim_graph",
                "targets": ["target"],
                "policy": {
                    "strategy": "argumentation",
                    "reasoning_backend": "claim_graph",
                    "semantics": "grounded",
                },
            }),
            world,
        )

        assert result.values["target"].value == 10.0
        assert result.argumentation is not None
        assert result.argumentation.to_dict() == {
            "backend": "claim_graph",
            "justified": ["claim_a"],
            "defeated": ["claim_b"],
        }
        assert result.dependencies.stances

    def test_praf_worldline_capture_uses_active_graph_projection_contract(
        self,
        monkeypatch,
    ):
        from propstore.core.results import AnalyzerResult, ClaimProjection
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        world, active_graph = self._graph_only_world()

        def fake_shared(graph, **kwargs):
            assert graph == active_graph
            return "shared-praf"

        def fake_analyze(
            shared,
            *,
            semantics="grounded",
            strategy="auto",
            query_kind="argument_acceptance",
            inference_mode="credulous",
            queried_set=None,
            mc_epsilon=0.01,
            mc_confidence=0.95,
            treewidth_cutoff=12,
            rng_seed=None,
            target_claim_ids=None,
        ):
            assert shared == "shared-praf"
            assert query_kind == "argument_acceptance"
            assert inference_mode == "credulous"
            assert queried_set is None
            target_ids = tuple(sorted(target_claim_ids or ()))
            projection = None
            if target_claim_ids is not None:
                projection = ClaimProjection(
                    target_claim_ids=target_ids,
                    survivor_claim_ids=("claim_a",),
                    witness_claim_ids=target_ids,
                )
            return AnalyzerResult(
                backend="praf",
                semantics=semantics,
                projection=projection,
                metadata=(
                    ("query_kind", query_kind),
                    ("inference_mode", inference_mode),
                    ("queried_set", queried_set),
                    ("acceptance_probs", {"claim_a": 0.75, "claim_b": 0.25}),
                    ("extension_probability", None),
                    ("strategy_used", "exact_enum"),
                    ("strategy_requested", strategy),
                    ("downgraded_from", None),
                    ("samples", None),
                    ("confidence_interval_half", None),
                    ("comparison", "elitist"),
                ),
            )

        monkeypatch.setattr(
            "propstore.core.analyzers.shared_analyzer_input_from_active_graph",
            fake_shared,
        )
        monkeypatch.setattr(
            "propstore.core.analyzers.analyze_praf",
            fake_analyze,
        )

        result = run_worldline(
            WorldlineDefinition.from_dict({
                "id": "phase7_praf",
                "targets": ["target"],
                "policy": {
                    "strategy": "argumentation",
                    "reasoning_backend": "praf",
                    "semantics": "grounded",
                    "praf_strategy": "exact_enum",
                },
            }),
            world,
        )

        assert result.values["target"].value == 10.0
        assert result.argumentation is not None
        assert result.argumentation.backend == "praf"
        assert result.argumentation.acceptance_probs == {"claim_a": 0.75, "claim_b": 0.25}
        assert result.dependencies.stances

    def test_worldline_grounded_has_single_canonical_meaning(
        self,
        monkeypatch,
    ):
        from propstore.dung import ArgumentationFramework
        from propstore.grounding.bundle import GroundedRulesBundle
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        class _Bound:
            def __init__(self):
                self._claims = {
                    "claim_a": {"id": "claim_a", "concept_id": "concept1", "value": 10.0},
                    "claim_b": {"id": "claim_b", "concept_id": "concept1", "value": 20.0},
                }

            def value_of(self, concept_id):
                return ValueResult(
                    concept_id=concept_id,
                    status="determined",
                    claims=[self._claims["claim_a"]],
                )

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

            def active_claims(self, concept_id=None):
                return [self._claims["claim_a"], self._claims["claim_b"]]

        class _World:
            def bind(self, environment=None, *, policy=None, **conditions):
                return _Bound()

            def resolve_concept(self, name):
                return "concept1" if name == "target" else None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": "concept1", "canonical_name": "target"}
                return None

            def get_claim(self, claim_id):
                return None

            def has_table(self, name):
                return name == "relation_edge"

            def stances_between(self, claim_ids):
                return []

            def grounding_bundle(self):
                return GroundedRulesBundle.empty()

        projection = type(
            "FakeProjection",
            (),
            {
                "arguments": (),
                "framework": ArgumentationFramework(
                    arguments=frozenset({"arg:a", "arg:b"}),
                    defeats=frozenset(),
                    attacks=frozenset({
                        ("arg:a", "arg:b"),
                        ("arg:b", "arg:a"),
                    }),
                ),
                "claim_to_argument_ids": {
                    "claim_a": ("arg:a",),
                    "claim_b": ("arg:b",),
                },
                "argument_to_claim_id": {
                    "arg:a": "claim_a",
                    "arg:b": "claim_b",
                },
            },
        )()
        monkeypatch.setattr(
            "propstore.structured_projection.build_structured_projection",
            lambda *args, **kwargs: projection,
        )

        grounded = run_worldline(
            WorldlineDefinition.from_dict({
                "id": "phase7_structured_grounded",
                "targets": ["target"],
                "policy": {
                    "strategy": "argumentation",
                    "reasoning_backend": "aspic",
                    "semantics": "grounded",
                },
            }),
            _World(),
        )

        assert grounded.argumentation is not None
        assert grounded.argumentation.backend == "aspic"
        assert grounded.argumentation.justified == ("claim_a", "claim_b")

    def test_graph_backed_worldline_materialization_is_stable_under_repeated_execution(
        self,
        monkeypatch,
    ):
        from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
        from propstore.worldline import WorldlineDefinition, WorldlineResult
        from propstore.worldline import run_worldline

        world, active_graph = self._graph_only_world()

        monkeypatch.setattr(
            "propstore.core.analyzers.shared_analyzer_input_from_active_graph",
            lambda graph, **kwargs: active_graph,
        )
        monkeypatch.setattr(
            "propstore.core.analyzers.analyze_claim_graph",
            lambda shared, *, semantics="grounded", target_claim_ids=None: AnalyzerResult(
                backend="claim_graph",
                semantics=semantics,
                extensions=(ExtensionResult(name=semantics, accepted_claim_ids=("claim_a",)),),
                projection=(
                    None
                    if target_claim_ids is None
                    else ClaimProjection(
                        target_claim_ids=tuple(sorted(target_claim_ids)),
                        survivor_claim_ids=("claim_a",),
                        witness_claim_ids=tuple(sorted(target_claim_ids)),
                    )
                ),
            ),
        )

        definition = WorldlineDefinition.from_dict({
            "id": "phase7_stability",
            "targets": ["target"],
            "policy": {
                "strategy": "argumentation",
                "reasoning_backend": "claim_graph",
                "semantics": "grounded",
            },
        })

        result_a = run_worldline(definition, world)
        result_b = run_worldline(definition, world)
        restored = WorldlineResult.from_dict(result_a.to_dict())

        assert result_a.values == result_b.values
        assert result_a.dependencies == result_b.dependencies
        assert result_a.argumentation == result_b.argumentation
        assert result_a.content_hash == result_b.content_hash
        assert restored is not None
        assert restored.to_dict() == result_a.to_dict()


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


class TestWorldlineFailureModes:
    def test_run_algorithm_target_preserves_claim_payload(self):
        """Algorithm-only targets should preserve the claim payload instead of returning value=None."""
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        class FakeBound:
            def __init__(self):
                self._bindings = {}

            def value_of(self, concept_id):
                return ValueResult(
                    concept_id=concept_id,
                    status="determined",
                    claims=[{
                        "id": "algo1",
                        "type": "algorithm",
                        "body": "def compute(sr, ws):\n    return sr / ws\n",
                        "canonical_ast": "(sr/ws)",
                    }],
                )

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

            def active_claims(self, concept_id=None):
                return [{
                    "id": "algo1",
                    "type": "algorithm",
                    "body": "def compute(sr, ws):\n    return sr / ws\n",
                    "canonical_ast": "(sr/ws)",
                }]

        class FakeWorld:
            def bind(self, environment=None, *, policy=None, **conditions):
                return FakeBound()

            def resolve_concept(self, name):
                return "concept1" if name == "target" else None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": "concept1", "canonical_name": "target"}
                return None

            def get_claim(self, claim_id):
                return None

            def has_table(self, name):
                return False

        wl = WorldlineDefinition.from_dict({
            "id": "algorithm_target",
            "targets": ["target"],
        })

        result = run_worldline(wl, FakeWorld())

        assert result.values["target"].status == "determined"
        assert result.values["target"].claim_type == "algorithm"
        assert result.values["target"].body == "def compute(sr, ws):\n    return sr / ws\n"

    def test_run_worldline_surfaces_chain_query_failures(self):
        """Engine failures should not be reported as ordinary underspecification."""
        from propstore.world.types import DerivedResult, ValueResult
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        class FakeBound:
            def __init__(self):
                self._bindings = {}

            def value_of(self, concept_id):
                return ValueResult(concept_id=concept_id, status="no_claims")

            def derived_value(self, concept_id, override_values=None):
                return DerivedResult(concept_id=concept_id, status="no_relationship")

        class FakeWorld:
            def bind(self, environment=None, *, policy=None, **conditions):
                return FakeBound()

            def resolve_concept(self, name):
                return "concept1" if name == "target" else None

            def get_concept(self, concept_id):
                if concept_id == "concept1":
                    return {"id": "concept1", "canonical_name": "target"}
                return None

            def chain_query(self, concept_id, strategy=None, **bindings):
                raise RuntimeError("solver exploded")

        wl = WorldlineDefinition.from_dict({
            "id": "chain_failure",
            "targets": ["target"],
        })

        result = run_worldline(wl, FakeWorld())

        assert result.values["target"].status == "error"
        assert "solver exploded" in (result.values["target"].reason or "")


class TestSilentExceptionLogging:
    """Fix 7B: silent except blocks must log warnings, not swallow silently."""

    def test_sensitivity_failure_logs_warning(self, caplog):
        """When sensitivity analysis raises, a warning must be logged."""
        import logging
        from unittest.mock import patch, MagicMock
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        # Minimal fake world that returns a "derived" target
        class FakeValueResult:
            status = "no_claims"
            claims = []

        class FakeDerivedResult:
            status = "derived"
            value = 42.0
            formula = "x * 2"
            input_values = {}

        class FakeWorld:
            def bind(self, env, policy=None):
                return self

            def resolve_concept(self, name):
                if name == "target":
                    return "concept1"
                return None

            def get_concept(self, cid):
                if cid == "concept1":
                    return {"id": "concept1", "canonical_name": "target"}
                return None

            def value_of(self, cid):
                return FakeValueResult()

            def derived_value(self, cid, override_values=None):
                return FakeDerivedResult()

            def has_table(self, name):
                return False

        wl = WorldlineDefinition.from_dict({
            "id": "sensitivity_fail",
            "targets": ["target"],
        })

        with caplog.at_level(logging.WARNING, logger="propstore.worldline.runner"):
            with patch(
                "propstore.worldline.runner.analyze_sensitivity",
                side_effect=RuntimeError("sensitivity kaboom"),
                create=True,
            ):
                # The import happens inside the function, so we patch the module-level import target
                with patch(
                    "propstore.sensitivity.analyze_sensitivity",
                    side_effect=RuntimeError("sensitivity kaboom"),
                ):
                    result = run_worldline(wl, FakeWorld())

        # The worldline should still succeed (sensitivity is optional)
        assert result.values["target"].status == "derived"
        # But a warning must have been logged
        assert any(
            "sensitivity" in rec.message.lower() for rec in caplog.records
        ), f"Expected a warning about sensitivity failure, got: {[r.message for r in caplog.records]}"

    def test_argumentation_failure_logs_warning(self, caplog):
        """When argumentation capture raises, a warning must be logged."""
        import logging
        from unittest.mock import patch
        from propstore.worldline import WorldlineDefinition
        from propstore.worldline import run_worldline

        class FakeValueResult:
            status = "no_claims"
            claims = []

        class FakeDerivedResult:
            status = "derived"
            value = 42.0
            formula = "x * 2"
            input_values = {}

        class FakeWorld:
            def bind(self, env, policy=None):
                return self

            def resolve_concept(self, name):
                if name == "target":
                    return "concept1"
                return None

            def get_concept(self, cid):
                if cid == "concept1":
                    return {"id": "concept1", "canonical_name": "target"}
                return None

            def value_of(self, cid):
                return FakeValueResult()

            def derived_value(self, cid, override_values=None):
                return FakeDerivedResult()

            def has_table(self, name):
                return name == "relation_edge"

            def active_claims(self):
                raise RuntimeError("argumentation kaboom")

        wl = WorldlineDefinition.from_dict({
            "id": "arg_fail",
            "targets": ["target"],
            "policy": {
                "strategy": "argumentation",
                "reasoning_backend": "claim_graph",
                "semantics": "grounded",
            },
        })

        with caplog.at_level(logging.WARNING, logger="propstore.worldline.runner"):
            result = run_worldline(wl, FakeWorld())

        # The worldline should still succeed
        assert result.values["target"].status == "derived"
        # But a warning must have been logged
        assert any(
            "argumentation" in rec.message.lower() for rec in caplog.records
        ), f"Expected a warning about argumentation failure, got: {[r.message for r in caplog.records]}"


class TestWorldlineCLIFlags:
    """Worldline CLI must expose all reasoning backend options (Phase 6)."""

    def test_create_reasoning_backend_flag(self, tmp_path):
        """--reasoning-backend aspic must be accepted and stored in policy."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--reasoning-backend", "aspic",
        ])
        assert result.exit_code == 0, result.output

        written = yaml.safe_load((wl_dir / "test-wl.yaml").read_text())
        assert written["policy"]["reasoning_backend"] == "aspic"

    def test_create_semantics_flag(self, tmp_path):
        """--semantics preferred must be accepted and stored in policy."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--semantics", "preferred",
        ])
        assert result.exit_code == 0, result.output

        written = yaml.safe_load((wl_dir / "test-wl.yaml").read_text())
        assert written["policy"]["semantics"] == "preferred"

    def test_create_claim_graph_specific_semantics_flag(self, tmp_path):
        """Claim-graph-specific semantics like d-preferred must be CLI-selectable."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--reasoning-backend", "claim_graph",
            "--semantics", "d-preferred",
        ])
        assert result.exit_code == 0, result.output

        written = yaml.safe_load((wl_dir / "test-wl.yaml").read_text())
        assert written["policy"]["semantics"] == "d-preferred"

    def test_create_rejects_unsupported_backend_semantics_pair(self, tmp_path):
        """Structured projection must reject claim-graph-only semantics at CLI time."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--reasoning-backend", "aspic",
            "--semantics", "d-preferred",
        ])
        assert result.exit_code != 0
        assert "does not support semantics" in result.output

    def test_create_set_comparison_flag(self, tmp_path):
        """--set-comparison democratic must be accepted and stored in policy."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--set-comparison", "democratic",
        ])
        assert result.exit_code == 0, result.output

        written = yaml.safe_load((wl_dir / "test-wl.yaml").read_text())
        assert written["policy"]["comparison"] == "democratic"

    def test_create_link_principle_flag(self, tmp_path):
        """--link-principle weakest must be accepted and stored in policy."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--reasoning-backend", "aspic",
            "--link-principle", "weakest",
        ])
        assert result.exit_code == 0, result.output

        written = yaml.safe_load((wl_dir / "test-wl.yaml").read_text())
        assert written["policy"]["reasoning_backend"] == "aspic"
        assert written["policy"]["link"] == "weakest"

    def test_create_decision_criterion_flag(self, tmp_path):
        """--decision-criterion hurwicz --pessimism-index 0.3 must be stored."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--decision-criterion", "hurwicz",
            "--pessimism-index", "0.3",
        ])
        assert result.exit_code == 0, result.output

        written = yaml.safe_load((wl_dir / "test-wl.yaml").read_text())
        assert written["policy"]["decision_criterion"] == "hurwicz"
        assert written["policy"]["pessimism_index"] == pytest.approx(0.3)

    def test_create_praf_flags(self, tmp_path):
        """--praf-strategy mc --praf-epsilon 0.05 must be stored in policy."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--reasoning-backend", "praf",
            "--praf-strategy", "mc",
            "--praf-epsilon", "0.05",
            "--praf-confidence", "0.99",
            "--praf-seed", "42",
        ])
        assert result.exit_code == 0, result.output

        written = yaml.safe_load((wl_dir / "test-wl.yaml").read_text())
        assert written["policy"]["reasoning_backend"] == "praf"
        assert written["policy"]["praf_strategy"] == "mc"
        assert written["policy"]["praf_mc_epsilon"] == pytest.approx(0.05)
        assert written["policy"]["praf_mc_confidence"] == pytest.approx(0.99)
        assert written["policy"]["praf_mc_seed"] == 42

    def test_run_reasoning_backend_flag(self, tmp_path):
        """worldline run --reasoning-backend must accept the flag (parse test only)."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_run

        # We just test that the flag is accepted by the parser.
        # The run command will fail because there's no sidecar, but it should
        # NOT fail with "no such option".
        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_run, "run")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "run", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--reasoning-backend", "aspic",
            "--semantics", "preferred",
            "--set-comparison", "democratic",
            "--decision-criterion", "hurwicz",
            "--pessimism-index", "0.7",
            "--praf-strategy", "exact",
            "--praf-epsilon", "0.02",
            "--praf-confidence", "0.90",
            "--praf-seed", "123",
        ])
        # Should fail on sidecar, NOT on "no such option"
        assert "no such option" not in (result.output or "").lower(), (
            f"Flag not accepted: {result.output}"
        )

    def test_run_rejects_internal_praf_strategy_names(self, tmp_path):
        """worldline run must reject internal-only PrAF strategy names."""
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_run

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_run, "run")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "run", "test-wl",
            "--target", "concept1",
            "--strategy", "argumentation",
            "--reasoning-backend", "praf",
            "--praf-strategy", "exact_dp",
        ])

        assert result.exit_code != 0
        assert "Invalid value for '--praf-strategy'" in result.output

    def test_worldline_definition_roundtrip_preserves_link(self):
        from propstore.worldline import WorldlineDefinition

        wl = WorldlineDefinition.from_dict({
            "id": "wl_link",
            "targets": ["concept1"],
            "policy": {
                "reasoning_backend": "aspic",
                "strategy": "argumentation",
                "comparison": "democratic",
                "link": "weakest",
            },
        })

        restored = WorldlineDefinition.from_dict(wl.to_dict())

        assert restored.policy.link == "weakest"
        assert restored == wl

    def test_create_revision_flags_store_revision_query(self, tmp_path):
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_create

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_create, "create")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "create", "revision-wl",
            "--target", "concept1",
            "--revision-operation", "revise",
            "--revision-atom", '{"kind":"claim","id":"synthetic","value":9.0}',
            "--revision-conflict", "claim:synthetic=legacy",
        ])
        assert result.exit_code == 0, result.output

        written = yaml.safe_load((wl_dir / "revision-wl.yaml").read_text())
        assert written["revision"]["operation"] == "revise"
        assert written["revision"]["atom"]["id"] == "synthetic"
        assert written["revision"]["conflicts"] == {"claim:synthetic": ["legacy"]}

    def test_run_revision_flags_pass_revision_query_to_runner(self, tmp_path, monkeypatch):
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_run

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()

        seen: dict[str, object] = {}

        class _FakeWorldModel:
            def __init__(self, repo):
                self.repo = repo

            def close(self):
                return None

        def fake_run_worldline(definition, world):
            seen["revision"] = None if definition.revision is None else definition.revision.to_dict()
            from propstore.worldline import WorldlineResult

            return WorldlineResult(
                computed="2026-03-29T00:00:00Z",
                content_hash="abc123",
                values={"concept1": {"status": "determined", "value": 1.0}},
                steps=[],
                dependencies={"claims": [], "stances": [], "contexts": []},
            )

        monkeypatch.setattr("propstore.cli.worldline_cmds.WorldModel", _FakeWorldModel, raising=False)
        monkeypatch.setattr("propstore.world.WorldModel", _FakeWorldModel)
        monkeypatch.setattr("propstore.worldline.run_worldline", fake_run_worldline)

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_run, "run")

        runner = CliRunner()
        result = runner.invoke(fake_cli, [
            "run", "revision-run",
            "--target", "concept1",
            "--revision-operation", "iterated_revise",
            "--revision-atom", '{"kind":"claim","id":"new","value":9.0}',
            "--revision-conflict", "claim:new=legacy",
            "--revision-operator", "lexicographic",
        ])
        assert result.exit_code == 0, result.output
        assert seen["revision"] == {
            "operation": "iterated_revise",
            "atom": {"kind": "claim", "id": "new", "value": 9.0},
            "conflicts": {"claim:new": ["legacy"]},
            "operator": "lexicographic",
        }

    def test_show_displays_revision_query_and_result(self, tmp_path):
        import click
        from click.testing import CliRunner

        from propstore.cli.worldline_cmds import worldline_show

        wl_dir = tmp_path / "worldlines"
        wl_dir.mkdir()
        (wl_dir / "revision-show.yaml").write_text(yaml.safe_dump({
            "id": "revision-show",
            "targets": ["concept1"],
            "revision": {
                "operation": "revise",
                "atom": {"kind": "claim", "id": "synthetic", "value": 9.0},
                "conflicts": {"claim:synthetic": ["legacy"]},
            },
            "results": {
                "computed": "2026-03-29T00:00:00Z",
                "content_hash": "abc123",
                "values": {"concept1": {"status": "determined", "value": 1.0}},
                "steps": [],
                "dependencies": {"claims": [], "stances": [], "contexts": []},
                "revision": {
                    "operation": "revise",
                    "input_atom_id": "claim:synthetic",
                    "target_atom_ids": ["claim:legacy"],
                    "result": {
                        "accepted_atom_ids": ["claim:synthetic"],
                        "rejected_atom_ids": ["claim:legacy"],
                        "incision_set": ["assumption:shared_weak"],
                        "explanation": {"claim:legacy": {"reason": "support_lost"}},
                    },
                },
            },
        }), encoding="utf-8")

        @click.group()
        @click.pass_context
        def fake_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["repo"] = _FakeWorldlineRepo(wl_dir)

        fake_cli.add_command(worldline_show, "show")

        runner = CliRunner()
        result = runner.invoke(fake_cli, ["show", "revision-show"])
        assert result.exit_code == 0, result.output
        assert "Revision query: revise" in result.output
        assert "Revision result: revise" in result.output
        assert "Input atom: claim:synthetic" in result.output
        assert "Rejected atoms: claim:legacy" in result.output

