"""Equation comparison for claims — composing ``eq-equiv`` directly.

When two EQUATION claims assert a relationship, deciding whether they agree,
conflict, or are undecidable is equation equivalence — owned entirely by the
``eq-equiv`` package. propstore does not parse, canonicalize, or compare
equations itself (there is no in-tree ``equation_parser`` / ``equation_comparison``
in the rewrite); it lowers a claim's authored equation text plus its
symbol→concept bindings into eq-equiv's ``BoundEquation`` and calls
``compare_equations``, returning that package's own ``EquationComparison`` /
``EquationComparisonStatus`` directly.
"""

from __future__ import annotations

from collections.abc import Iterable

from eq_equiv import (
    BoundEquation,
    DomainAssumption,
    EquationComparison,
    EquationSymbolBinding,
    compare_equations,
)


def bound_equation(
    expression: str,
    bindings: Iterable[EquationSymbolBinding],
) -> BoundEquation:
    """Lower authored equation text + symbol bindings into a ``BoundEquation``."""

    return BoundEquation(expression=expression, variables=tuple(bindings))


def compare_claim_equations(
    expression_a: str,
    expression_b: str,
    bindings: Iterable[EquationSymbolBinding],
    *,
    domain_assumptions: Iterable[DomainAssumption] = (),
) -> EquationComparison:
    """Compare two claims' equations under shared symbol bindings.

    Returns eq-equiv's ``EquationComparison`` directly: ``EQUIVALENT`` for agreeing
    orientations, ``DIFFERENT`` for a proven difference, ``UNKNOWN`` when the
    engine cannot decide (honest ignorance — never forced to a verdict).
    """

    shared = tuple(bindings)
    return compare_equations(
        bound_equation(expression_a, shared),
        bound_equation(expression_b, shared),
        domain_assumptions=tuple(domain_assumptions),
    )
