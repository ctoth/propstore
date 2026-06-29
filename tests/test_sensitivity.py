"""Local sensitivity analyzer tests.

The analyzer must compute partial derivatives without a direct SymPy dependency:
every output value flows through ``human-to-sympy`` via
:func:`propstore.propagation.evaluate_parameterization`, and the partials are a
central finite difference over those evaluations. The fakes here delegate
``derived_value`` to that real numeric boundary so the asserted partials are
genuinely produced through ``human-to-sympy``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

import propstore.sensitivity as sensitivity_module
from propstore.core.graph_types import ParameterizationEdge
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.propagation import evaluate_parameterization
from propstore.sensitivity import analyze_sensitivity
from propstore.world.types import DerivedResult, ValueStatus


class _FakeWorld:
    def __init__(self, param: ParameterizationEdge) -> None:
        self._param = param

    def resolve_concept(self, name: str) -> str | None:
        return name

    def parameterizations_for(
        self, concept_id: str
    ) -> Sequence[ParameterizationEdge]:
        if concept_id == str(self._param.output_concept_id):
            return (self._param,)
        return ()


class _FakeBound:
    """Bound world whose ``derived_value`` evaluates through human-to-sympy."""

    def __init__(
        self,
        param: ParameterizationEdge,
        known: Mapping[str, float],
    ) -> None:
        self._param = param
        self._known = {to_concept_id(key): float(value) for key, value in known.items()}

    def is_param_compatible(self, parameterization: ParameterizationEdge) -> bool:
        return parameterization == self._param

    def collect_known_values(
        self, variable_concepts: Sequence[ConceptId | str]
    ) -> dict[ConceptId, float]:
        wanted = {to_concept_id(concept) for concept in variable_concepts}
        return {
            concept_id: value
            for concept_id, value in self._known.items()
            if concept_id in wanted
        }

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: Mapping[str, float | str | None] | None = None,
    ) -> DerivedResult:
        output_id = to_concept_id(self._param.output_concept_id)
        if to_concept_id(concept_id) != output_id:
            return DerivedResult(
                concept_id=to_concept_id(concept_id),
                status=ValueStatus.NO_RELATIONSHIP,
            )
        bindings: dict[str, float] = {}
        for key, value in (override_values or {}).items():
            if isinstance(value, (int, float)):
                bindings[key] = float(value)
        evaluation = evaluate_parameterization(
            self._param.sympy or "",
            bindings,
            str(output_id),
        )
        if evaluation.value is None:
            return DerivedResult(concept_id=output_id, status=ValueStatus.UNDERSPECIFIED)
        return DerivedResult(
            concept_id=output_id,
            status=ValueStatus.DERIVED,
            value=evaluation.value,
        )


def _linear_param() -> ParameterizationEdge:
    # f = 2*x + y ; symbol names equal the concept ids so the numeric boundary
    # binds them directly.
    return ParameterizationEdge(
        output_concept_id="f",
        input_concept_ids=("x", "y"),
        formula="f = 2*x + y",
        sympy="2*x + y",
    )


def test_analyze_sensitivity_reports_partial_derivatives_and_elasticities() -> None:
    param = _linear_param()
    world = _FakeWorld(param)
    bound = _FakeBound(param, known={"x": 3.0, "y": 4.0})

    result = analyze_sensitivity(world, "f", bound)

    assert result is not None
    assert result.output_value == pytest.approx(10.0)  # 2*3 + 4

    by_input = {str(entry.input_concept_id): entry for entry in result.entries}
    assert by_input["x"].partial_derivative_value == pytest.approx(2.0)
    assert by_input["y"].partial_derivative_value == pytest.approx(1.0)
    # elasticity = (df/dx) * (x / f): 2*3/10 = 0.6 ; 1*4/10 = 0.4
    assert by_input["x"].elasticity == pytest.approx(0.6)
    assert by_input["y"].elasticity == pytest.approx(0.4)

    # Entries are ranked by |elasticity| descending — x dominates y.
    assert [str(entry.input_concept_id) for entry in result.entries] == ["x", "y"]


def test_analyze_sensitivity_honors_override_values() -> None:
    param = _linear_param()
    world = _FakeWorld(param)
    # No known input values; the analysis must resolve from the overrides alone.
    bound = _FakeBound(param, known={})

    result = analyze_sensitivity(
        world,
        "f",
        bound,
        override_values={"x": 5.0, "y": 1.0},
    )

    assert result is not None
    assert result.output_value == pytest.approx(11.0)  # 2*5 + 1
    by_input = {str(entry.input_concept_id): entry for entry in result.entries}
    assert by_input["x"].partial_derivative_value == pytest.approx(2.0)
    assert by_input["y"].partial_derivative_value == pytest.approx(1.0)


def test_analyze_sensitivity_returns_none_without_parameterization() -> None:
    param = _linear_param()
    world = _FakeWorld(param)
    bound = _FakeBound(param, known={"x": 3.0, "y": 4.0})

    assert analyze_sensitivity(world, "no_such_concept", bound) is None


def test_analyze_sensitivity_returns_none_when_inputs_unresolvable() -> None:
    param = _linear_param()
    world = _FakeWorld(param)
    bound = _FakeBound(param, known={"x": 3.0})  # y cannot be resolved

    assert analyze_sensitivity(world, "f", bound) is None


def test_sensitivity_module_has_no_direct_sympy_dependency() -> None:
    source = Path(sensitivity_module.__file__).read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    assert not any(
        line.startswith(("import sympy", "from sympy")) for line in import_lines
    )
