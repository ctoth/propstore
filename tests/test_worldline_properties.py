"""Property-based tests for worldline invariants.

These test the formal properties that every worldline MUST satisfy,
derived from de Kleer 1986 ATMS label properties (pp.144-145).

These are NOT smoke tests. Each property test must actually probe the
invariant by constructing scenarios that would violate it if the
implementation were wrong.
"""

import sqlite3

import pytest
import yaml

from propstore.build_sidecar import build_sidecar
from propstore.validate import load_concepts
from propstore.validate_claims import load_claim_files
from propstore.world import HypotheticalWorld, WorldModel
from propstore.worldline import WorldlineDefinition
from propstore.worldline_runner import run_worldline


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def property_kb(tmp_path_factory):
    """Knowledge base designed to probe property violations.

    Structure:
    - concept1 (mass): claim mass_a=5.0, claim mass_b=10.0 (conflicted)
    - concept2 (acceleration): claim g_earth=9.807 (cond: location=earth),
                                claim g_moon=1.625 (cond: location=moon)
    - concept3 (force): parameterized F = mass * acceleration
    - concept4 (velocity): NO claims (for underspecified tests)
    - concept5 (kinetic_energy): parameterized E = 0.5 * mass * velocity^2
    - concept6 (temperature): claim temp=293.15 (unrelated to force)
    - concept7 (location): category [earth, moon]
    - concept8 (distance): claim dist=100.0 (unrelated to force)
    """
    root = tmp_path_factory.mktemp("prop_kb") / "knowledge"
    concepts_dir = root / "concepts"
    concepts_dir.mkdir(parents=True)
    (concepts_dir / ".counters").mkdir()
    (concepts_dir / ".counters" / "test.next").write_text("20")

    forms_dir = root / "forms"
    forms_dir.mkdir()
    for form_name in ("acceleration", "force", "mass", "velocity",
                       "energy", "category", "temperature", "distance"):
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
        "status": "accepted", "definition": "Force.", "form": "force",
        "parameterization_relationships": [{
            "formula": "F = m * a",
            "inputs": ["concept1", "concept2"],
            "sympy": "Eq(concept3, concept1 * concept2)",
            "exactness": "exact", "source": "test", "bidirectional": True,
        }],
    })
    write_concept("velocity", {
        "id": "concept4", "canonical_name": "velocity",
        "status": "accepted", "definition": "Velocity.", "form": "velocity",
    })
    write_concept("kinetic_energy", {
        "id": "concept5", "canonical_name": "kinetic_energy",
        "status": "accepted", "definition": "KE.", "form": "energy",
        "parameterization_relationships": [{
            "formula": "E = 0.5 * m * v^2",
            "inputs": ["concept1", "concept4"],
            "sympy": "Eq(concept5, 0.5 * concept1 * concept4**2)",
            "exactness": "exact", "source": "test", "bidirectional": True,
        }],
    })
    write_concept("temperature", {
        "id": "concept6", "canonical_name": "temperature",
        "status": "accepted", "definition": "Temp.", "form": "temperature",
    })
    write_concept("location", {
        "id": "concept7", "canonical_name": "location",
        "status": "accepted", "definition": "Location.", "form": "category",
        "form_parameters": {"values": ["earth", "moon"], "extensible": False},
    })
    write_concept("distance", {
        "id": "concept8", "canonical_name": "distance",
        "status": "accepted", "definition": "Distance.", "form": "distance",
    })

    claims_dir = root / "claims"
    claims_dir.mkdir()
    with open(claims_dir / "test_claims.yaml", "w") as f:
        yaml.dump({
            "source": {"paper": "test"},
            "claims": [
                # Acceleration: conditional on location
                {"id": "g_earth", "type": "parameter", "concept": "concept2",
                 "value": 9.807, "unit": "m/s^2",
                 "conditions": ["location == 'earth'"],
                 "provenance": {"paper": "test", "page": 1}},
                {"id": "g_moon", "type": "parameter", "concept": "concept2",
                 "value": 1.625, "unit": "m/s^2",
                 "conditions": ["location == 'moon'"],
                 "provenance": {"paper": "test", "page": 1}},
                # Temperature: unrelated to force
                {"id": "temp_room", "type": "parameter", "concept": "concept6",
                 "value": 293.15, "unit": "K",
                 "provenance": {"paper": "test", "page": 1}},
                # Distance: unrelated to force
                {"id": "dist_100", "type": "parameter", "concept": "concept8",
                 "value": 100.0, "unit": "m",
                 "provenance": {"paper": "test", "page": 1}},
            ],
        }, f, default_flow_style=False)

    return root


@pytest.fixture(scope="module")
def property_world(property_kb):
    from propstore.cli.repository import Repository
    repo = Repository(property_kb)
    concepts = load_concepts(repo.concepts_dir)
    claim_files = load_claim_files(repo.claims_dir)
    sidecar_path = repo.sidecar_path
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    build_sidecar(concepts, sidecar_path, claim_files=claim_files, repo=repo)
    return WorldModel(repo)


def _run(world, targets, bindings=None, overrides=None, strategy=None):
    """Helper: create and run a worldline."""
    d = {"id": "test", "targets": targets}
    inputs = {}
    if bindings:
        inputs["bindings"] = bindings
    if overrides:
        inputs["overrides"] = overrides
    if inputs:
        d["inputs"] = inputs
    if strategy:
        d["policy"] = {"strategy": strategy}
    wl = WorldlineDefinition.from_dict(d)
    return run_worldline(wl, world)


# ═══════════════════════════════════════════════════════════════════
# P2: SOUNDNESS — no spurious dependencies
#
# "Every claim in the dependency set actually contributes to the
#  result. Removing any single dependency must change the result."
#  (de Kleer 1986, label soundness property, p.144)
# ═══════════════════════════════════════════════════════════════════


class TestSoundness:

    def test_force_dependency_on_g_earth_is_necessary(self, property_world):
        """Force depends on g_earth. Removing g_earth must break derivation."""
        result = _run(property_world,
                      targets=["force"],
                      bindings={"location": "earth"},
                      overrides={"mass": 10.0})

        assert result.values["force"]["status"] == "derived"
        assert "g_earth" in result.dependencies["claims"]

        # Now remove g_earth and try again
        bound = property_world.bind(location="earth")
        hypo = HypotheticalWorld(bound, remove=["g_earth"])

        # With g_earth removed, acceleration has no claims under location=earth
        vr = hypo.value_of("concept2")  # acceleration
        assert vr.status != "determined", (
            "After removing g_earth, acceleration should NOT be determined"
        )

    def test_temperature_not_in_force_dependencies(self, property_world):
        """Force derivation should NOT depend on temperature claims."""
        result = _run(property_world,
                      targets=["force"],
                      bindings={"location": "earth"},
                      overrides={"mass": 10.0})

        assert "temp_room" not in result.dependencies["claims"], (
            "temp_room is a spurious dependency of force"
        )

    def test_distance_not_in_force_dependencies(self, property_world):
        """Force derivation should NOT depend on distance claims."""
        result = _run(property_world,
                      targets=["force"],
                      bindings={"location": "earth"},
                      overrides={"mass": 10.0})

        assert "dist_100" not in result.dependencies["claims"], (
            "dist_100 is a spurious dependency of force"
        )

    def test_moon_g_not_in_earth_force_dependencies(self, property_world):
        """Force on Earth should NOT depend on Moon's g value."""
        result = _run(property_world,
                      targets=["force"],
                      bindings={"location": "earth"},
                      overrides={"mass": 10.0})

        assert "g_moon" not in result.dependencies["claims"], (
            "g_moon should not appear in Earth-bound force dependencies"
        )


# ═══════════════════════════════════════════════════════════════════
# P3: COMPLETENESS — no missing dependencies
#
# "ALL claims that influenced the result are in the dependency set.
#  Modifying a claim NOT in the dependency set must NOT change the
#  result." (de Kleer 1986, label completeness property, p.145)
# ═══════════════════════════════════════════════════════════════════


class TestCompleteness:

    def test_changing_g_earth_changes_force(self, property_world):
        """g_earth is in deps. Changing its value must change force.

        We can't modify claims in the sidecar directly, but we can
        verify the dependency tracking by checking that g_earth IS in
        the dependency set and that the derived force USES g_earth's value.
        """
        result = _run(property_world,
                      targets=["force"],
                      bindings={"location": "earth"},
                      overrides={"mass": 10.0})

        assert "g_earth" in result.dependencies["claims"]

        # Verify the derived value actually used g_earth's value (9.807)
        force_val = result.values["force"]["value"]
        expected = 10.0 * 9.807  # mass * g_earth
        assert abs(force_val - expected) < 0.01, (
            f"Force {force_val} doesn't match mass*g_earth={expected}. "
            f"Was g_earth actually used?"
        )

    def test_hypothetical_g_change_changes_force(self, property_world):
        """Replacing g_earth with a different value changes force.

        This directly tests completeness: if g_earth is a real dependency,
        then a hypothetical world where g_earth has a different value must
        produce a different force.
        """
        from propstore.world import SyntheticClaim

        # Original force
        result1 = _run(property_world,
                       targets=["force"],
                       bindings={"location": "earth"},
                       overrides={"mass": 10.0})
        force1 = result1.values["force"]["value"]

        # Hypothetical: remove g_earth, add g_earth_alt=5.0
        bound = property_world.bind(location="earth")
        hypo = HypotheticalWorld(
            bound,
            remove=["g_earth"],
            add=[SyntheticClaim(
                id="g_earth_alt",
                concept_id="concept2",
                value=5.0,
            )],
        )
        dr = hypo.derived_value("concept3", override_values={"concept1": 10.0})

        assert dr.status == "derived"
        force2 = dr.value
        assert abs(force2 - 50.0) < 0.01  # 10.0 * 5.0
        assert abs(force1 - force2) > 1.0, (
            f"Changing g_earth from 9.807 to 5.0 should change force "
            f"(was {force1}, now {force2})"
        )

    def test_non_dependency_change_irrelevant(self, property_world):
        """Removing a non-dependency (temp_room) doesn't affect force."""
        # Original
        result1 = _run(property_world,
                       targets=["force"],
                       bindings={"location": "earth"},
                       overrides={"mass": 10.0})
        force1 = result1.values["force"]["value"]

        # Hypothetical: remove temp_room
        bound = property_world.bind(location="earth")
        hypo = HypotheticalWorld(bound, remove=["temp_room"])
        dr = hypo.derived_value("concept3", override_values={"concept1": 10.0})

        assert dr.status == "derived"
        assert abs(dr.value - force1) < 1e-9, (
            f"Removing non-dependency temp_room changed force: {force1} → {dr.value}"
        )


# ═══════════════════════════════════════════════════════════════════
# P5: DETERMINISM
# ═══════════════════════════════════════════════════════════════════


class TestDeterminism:

    def test_same_inputs_same_results(self, property_world):
        """Three identical runs produce identical results."""
        results = []
        for _ in range(3):
            r = _run(property_world,
                     targets=["force", "temperature"],
                     bindings={"location": "earth"},
                     overrides={"mass": 7.5})
            results.append(r)

        for i in range(1, len(results)):
            assert results[0].values == results[i].values, (
                f"Run 0 and run {i} produced different values"
            )
            assert results[0].dependencies == results[i].dependencies, (
                f"Run 0 and run {i} produced different dependencies"
            )

    def test_different_bindings_different_results(self, property_world):
        """Earth and Moon bindings produce different force values."""
        r_earth = _run(property_world,
                       targets=["force"],
                       bindings={"location": "earth"},
                       overrides={"mass": 10.0})
        r_moon = _run(property_world,
                      targets=["force"],
                      bindings={"location": "moon"},
                      overrides={"mass": 10.0})

        f_earth = r_earth.values["force"]["value"]
        f_moon = r_moon.values["force"]["value"]
        assert abs(f_earth - 98.07) < 0.1
        assert abs(f_moon - 16.25) < 0.1
        assert f_earth != f_moon


# ═══════════════════════════════════════════════════════════════════
# P6: OVERRIDE PRECEDENCE
# ═══════════════════════════════════════════════════════════════════


class TestOverridePrecedence:

    def test_override_value_returned_directly(self, property_world):
        """Overriding acceleration returns the override, not a claim."""
        # acceleration has claims (g_earth, g_moon) but override should win
        result = _run(property_world,
                      targets=["acceleration"],
                      bindings={"location": "earth"},
                      overrides={"acceleration": 42.0})

        accel = result.values["acceleration"]
        assert accel["value"] == 42.0, (
            f"Override acceleration=42.0 should win, got {accel['value']}"
        )
        assert accel["source"] == "override"

    def test_override_propagates_to_derivation(self, property_world):
        """Override mass feeds into F=ma derivation."""
        r1 = _run(property_world,
                   targets=["force"],
                   bindings={"location": "earth"},
                   overrides={"mass": 1.0})
        r2 = _run(property_world,
                   targets=["force"],
                   bindings={"location": "earth"},
                   overrides={"mass": 100.0})

        f1 = r1.values["force"]["value"]
        f2 = r2.values["force"]["value"]

        # F1 = 1.0 * 9.807 ≈ 9.807
        # F2 = 100.0 * 9.807 ≈ 980.7
        assert abs(f1 - 9.807) < 0.01
        assert abs(f2 - 980.7) < 0.1
        assert abs(f2 / f1 - 100.0) < 0.01, "Force should scale linearly with mass"


# ═══════════════════════════════════════════════════════════════════
# P9: VALUE ACCURACY
# ═══════════════════════════════════════════════════════════════════


class TestValueAccuracy:

    def test_force_equals_mass_times_acceleration(self, property_world):
        """F = m * a: derived value matches manual computation."""
        result = _run(property_world,
                      targets=["force"],
                      bindings={"location": "earth"},
                      overrides={"mass": 13.7})

        force = result.values["force"]
        assert force["status"] == "derived"
        expected = 13.7 * 9.807
        assert abs(force["value"] - expected) < 1e-6, (
            f"F = {force['value']}, expected m*a = {expected}"
        )

    def test_force_on_moon(self, property_world):
        """F = m * a with Moon's g: 25.0 * 1.625 = 40.625."""
        result = _run(property_world,
                      targets=["force"],
                      bindings={"location": "moon"},
                      overrides={"mass": 25.0})

        force = result.values["force"]
        assert force["status"] == "derived"
        expected = 25.0 * 1.625
        assert abs(force["value"] - expected) < 1e-6, (
            f"F = {force['value']}, expected m*g_moon = {expected}"
        )


# ═══════════════════════════════════════════════════════════════════
# P10: PARTIAL HONESTY
# ═══════════════════════════════════════════════════════════════════


class TestPartialHonesty:

    def test_all_targets_present_even_if_underspecified(self, property_world):
        """Every target appears in results, even if it can't be computed."""
        result = _run(property_world,
                      targets=["force", "kinetic_energy", "temperature", "distance"],
                      bindings={"location": "earth"},
                      overrides={"mass": 5.0})

        for t in ["force", "kinetic_energy", "temperature", "distance"]:
            assert t in result.values, f"Target '{t}' missing from results"

    def test_determined_vs_underspecified_correct(self, property_world):
        """Determined, derived, and underspecified statuses are accurate."""
        result = _run(property_world,
                      targets=["force", "kinetic_energy", "temperature"],
                      bindings={"location": "earth"},
                      overrides={"mass": 5.0})

        # Force: derivable (mass override + g_earth claim)
        assert result.values["force"]["status"] == "derived"

        # Temperature: determined from direct claim
        assert result.values["temperature"]["status"] == "determined"

        # Kinetic energy: underspecified (velocity has no claims/overrides)
        ke = result.values["kinetic_energy"]
        assert ke["status"] in ("underspecified", "no_relationship"), (
            f"KE should be underspecified without velocity, got {ke['status']}"
        )

    def test_underspecified_has_reason(self, property_world):
        """Underspecified results include a reason explaining why."""
        result = _run(property_world,
                      targets=["kinetic_energy"],
                      overrides={"mass": 5.0})

        ke = result.values["kinetic_energy"]
        assert ke["status"] in ("underspecified", "no_relationship")
        # Should have some explanation
        if ke["status"] == "underspecified":
            assert "reason" in ke, "Underspecified result should have a reason"
