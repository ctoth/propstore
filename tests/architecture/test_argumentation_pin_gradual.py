from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import fields
from pathlib import Path

import pytest

from argumentation import dfquad, equational, gradual, gradual_principles, matt_toni
from argumentation.dung import ArgumentationFramework
from argumentation.gradual import GradualStrengthResult, WeightedBipolarGraph


def test_argumentation_pin_exposes_gradual_public_surface() -> None:
    assert hasattr(dfquad, "dfquad_strengths")
    assert hasattr(dfquad, "dfquad_bipolar_strengths")
    assert hasattr(matt_toni, "matt_toni_strengths")
    assert hasattr(equational, "equational_fixpoint")
    assert hasattr(gradual_principles, "PRINCIPLE_COMPLIANCE")
    assert hasattr(gradual, "quadratic_energy_strengths_continuous")
    assert "integration_method" in {field.name for field in fields(GradualStrengthResult)}


def test_argumentation_pin_gradual_behaviour_matches_paper_gates() -> None:
    graph = WeightedBipolarGraph(
        arguments=frozenset({"supporter", "attacker", "target"}),
        initial_weights={"supporter": 0.7, "attacker": 0.7, "target": 0.4},
        supports=frozenset({("supporter", "target")}),
        attacks=frozenset({("attacker", "target")}),
    )
    assert dfquad.dfquad_strengths(graph).strengths["target"] == pytest.approx(0.4)

    supported = WeightedBipolarGraph(
        arguments=frozenset({"source", "target"}),
        initial_weights={"source": 0.7, "target": 0.5},
        supports=frozenset({("source", "target")}),
    )
    attacked = WeightedBipolarGraph(
        arguments=frozenset({"source", "target"}),
        initial_weights={"source": 0.7, "target": 0.5},
        attacks=frozenset({("source", "target")}),
    )
    assert dfquad.dfquad_bipolar_strengths(supported).strengths["target"] - 0.5 == pytest.approx(
        0.5 - dfquad.dfquad_bipolar_strengths(attacked).strengths["target"]
    )

    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )
    assert matt_toni.matt_toni_strengths(framework) == pytest.approx({"a": 1.0, "b": 0.25})

    continuous = gradual.quadratic_energy_strengths(supported)
    assert continuous.integration_method == "rk4_adaptive"
    assert "enable_continuous_integration" not in inspect.signature(
        gradual.quadratic_energy_strengths
    ).parameters

    equational_result = equational.equational_fixpoint(
        WeightedBipolarGraph(
            arguments=frozenset({"a", "b"}),
            initial_weights={"a": 1.0, "b": 1.0},
            attacks=frozenset({("a", "b")}),
        ),
        scheme="max",
    )
    assert equational_result.strengths == pytest.approx({"a": 1.0, "b": 0.0})


def test_deleted_dfquad_path_and_propstore_importers_are_absent() -> None:
    with pytest.raises((AttributeError, ImportError)):
        module = importlib.import_module("argumentation.probabilistic_dfquad")
        getattr(module, "compute_dfquad_strengths")

    propstore_root = Path(__file__).resolve().parents[2] / "propstore"
    offenders: list[str] = []
    for path in propstore_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "argumentation.probabilistic_dfquad":
                offenders.append(str(path.relative_to(propstore_root)))
    assert offenders == []


def test_argumentation_dependency_uses_remote_git_source() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")

    assert '"formal-argumentation",' in text
    assert 'formal-argumentation = { git = "https://github.com/ctoth/argumentation.git", rev = "' in text
    assert "formal-argumentation @" not in text
    assert "file:" not in text
    assert "../argumentation" not in text
