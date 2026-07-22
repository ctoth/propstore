"""propstore glue for the causal-models substrate package.

The Pearl/Halpern causal math lives in the ``causal_models`` package, which is
generic over variable-name strings and over each structural equation's
``evaluate`` callable. This module holds the *only* propstore-specific knowledge
the kernel needs: how a :class:`~propstore.core.graph_types.CompiledWorldGraph`'s
parameterization edges become structural equations, and how those equations are
evaluated.

Per the substrate boundary discipline (CLAUDE.md), this is a call, not a
conversion: propstore supplies :func:`propstore.propagation.evaluate_parameterization`
*as* the equation's ``evaluate`` argument (the generic-package rule — pass the
function, do not wrap the package's type), and uses ``causal_models``' own
:class:`~causal_models.StructuralCausalModel` directly with no propstore mirror.
"""

from __future__ import annotations

from collections.abc import Mapping

from causal_models import StructuralCausalModel, StructuralEquation, Value

from propstore.core.graph_types import CompiledWorldGraph, ParameterizationEdge
from propstore.core.id_types import ConceptId
from propstore.propagation import (
    ParameterizationEvaluationStatus,
    evaluate_parameterization,
)


def from_compiled_graph(
    graph: CompiledWorldGraph,
    *,
    exogenous_assignment: Mapping[ConceptId | str, Value] | None = None,
) -> StructuralCausalModel:
    """Build an SCM from a compiled world graph's parameterization edges.

    Each parameterization with a ``sympy`` body becomes one structural equation;
    its inputs are the SCM parents. Concept ids that are only ever inputs (never
    an output) become the exogenous variables.
    """

    equations = {
        str(edge.output_concept_id): _structural_equation_from_edge(edge)
        for edge in graph.parameterizations
        if edge.sympy
    }
    endogenous = frozenset(
        str(edge.output_concept_id) for edge in graph.parameterizations
    )
    parent_ids = frozenset(
        str(parent)
        for edge in graph.parameterizations
        for parent in edge.input_concept_ids
    )
    return StructuralCausalModel(
        exogenous=parent_ids - endogenous,
        endogenous=endogenous,
        equations=equations,
        exogenous_assignment={
            str(name): value for name, value in (exogenous_assignment or {}).items()
        },
    )


def _structural_equation_from_edge(edge: ParameterizationEdge) -> StructuralEquation:
    def evaluate(
        values: Mapping[str, Value],
        *,
        edge: ParameterizationEdge = edge,
    ) -> Value:
        result = evaluate_parameterization(
            edge.sympy or "",
            {
                str(parent): _as_float(values[str(parent)])
                for parent in edge.input_concept_ids
                if str(parent) in values
            },
            str(edge.output_concept_id),
        )
        if result.status is not ParameterizationEvaluationStatus.VALUE:
            raise ValueError(
                f"Could not evaluate structural equation for {edge.output_concept_id}"
            )
        return result.value

    return StructuralEquation(
        target=str(edge.output_concept_id),
        parents=tuple(str(parent) for parent in edge.input_concept_ids),
        evaluate=evaluate,
        provenance=None,
    )


def _as_float(value: Value) -> float:
    """Coerce a structural-equation input to ``float`` for sympy evaluation.

    The parameterization evaluator works over real-valued inputs; non-numeric
    values cannot parameterize an equation and fail loudly rather than silently.
    """

    if not isinstance(value, bool) and isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"Structural-equation input is not numeric: {value!r}")
