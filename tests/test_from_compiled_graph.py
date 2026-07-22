"""Integration: the propstore CompiledWorldGraph -> SCM adapter.

Exercises ``propstore.world.causal.from_compiled_graph``, which supplies
``propstore.propagation.evaluate_parameterization`` as the structural equation's
``evaluate`` callable (the generic-package rule). This is the one boundary where
propstore-specific parameterization knowledge meets the generic causal-models
kernel.
"""

from __future__ import annotations

import pytest
from causal_models import CausalValueStatus, InterventionWorld
from propstore.core.graph_types import CompiledWorldGraph, ParameterizationEdge
from propstore.world import from_compiled_graph


def _sum_graph() -> CompiledWorldGraph:
    # z = x + y, with x and y exogenous (input-only) concepts.
    return CompiledWorldGraph(
        parameterizations=(
            ParameterizationEdge(
                output_concept_id="z",
                input_concept_ids=("x", "y"),
                sympy="x + y",
            ),
        ),
    )


def test_from_compiled_graph_builds_evaluable_scm() -> None:
    scm = from_compiled_graph(_sum_graph(), exogenous_assignment={"x": 2, "y": 3})

    assert scm.endogenous == frozenset({"z"})
    assert scm.exogenous == frozenset({"x", "y"})
    assert scm.evaluate()["z"] == 5.0


def test_from_compiled_graph_feeds_intervention_world() -> None:
    scm = from_compiled_graph(_sum_graph(), exogenous_assignment={"x": 2, "y": 3})

    world = InterventionWorld(scm, {"x": 10})

    derived = world.derived_value("z")
    assert derived.status is CausalValueStatus.DERIVED
    assert derived.value == 13.0


def test_from_compiled_graph_rejects_boolean_equation_input() -> None:
    scm = from_compiled_graph(_sum_graph(), exogenous_assignment={"x": True, "y": 3})

    with pytest.raises(ValueError, match="input is not numeric: True"):
        scm.evaluate()
