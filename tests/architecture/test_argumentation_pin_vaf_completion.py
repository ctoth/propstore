from __future__ import annotations

from argumentation.vaf import ValueBasedArgumentationFramework
from argumentation.vaf_completion import (
    FACT_VALUE,
    ArgumentChain,
    ArgumentLine,
    VAFArgumentStatus,
    classify_line_of_argument,
    is_skeptically_objective_under_fact_uncertainty,
    two_value_cycle_extension,
)


def test_argumentation_pin_exposes_bench_capon_line_classification() -> None:
    # Bench-Capon 2003 p. 440, Theorem 6.6: a later odd chain makes the target
    # subjectively acceptable under the theorem's stated preconditions.
    vaf = ValueBasedArgumentationFramework(
        arguments=frozenset({"a1", "a2", "b1"}),
        attacks=frozenset({("a1", "a2"), ("b1", "a1")}),
        values=frozenset({"life", "property"}),
        valuation={"a1": "life", "a2": "life", "b1": "property"},
        audience=("life", "property"),
    )
    line = ArgumentLine(
        chains=(
            ArgumentChain(arguments=("a1", "a2"), value="life"),
            ArgumentChain(arguments=("b1",), value="property"),
        ),
        target="a2",
    )

    assert classify_line_of_argument(vaf, line) is VAFArgumentStatus.SUBJECTIVE


def test_argumentation_pin_exposes_two_value_cycle_corollary() -> None:
    # Bench-Capon 2003 pp. 440-441, Corollary 6.7: the parity helper returns
    # the same extension as ordinary audience-specific preferred semantics.
    vaf = ValueBasedArgumentationFramework(
        arguments=frozenset({"a1", "a2", "b1"}),
        attacks=frozenset({("a1", "a2"), ("a2", "b1"), ("b1", "a1")}),
        values=frozenset({"a-value", "b-value"}),
        valuation={"a1": "a-value", "a2": "a-value", "b1": "b-value"},
        audience=("a-value", "b-value"),
    )

    extension = two_value_cycle_extension(
        vaf,
        (
            ArgumentChain(arguments=("a1", "a2"), value="a-value"),
            ArgumentChain(arguments=("b1",), value="b-value"),
        ),
        ("a-value", "b-value"),
    )

    assert extension == frozenset({"a1", "b1"})
    assert vaf.preferred_extensions_for_audience(("a-value", "b-value")) == [extension]


def test_argumentation_pin_exposes_fact_uncertainty_surface() -> None:
    # Bench-Capon 2003 pp. 444-447: facts outrank ordinary values, but factual
    # uncertainty can still create multiple preferred extensions.
    vaf = ValueBasedArgumentationFramework(
        arguments=frozenset({"G", "H", "K"}),
        attacks=frozenset({("G", "H"), ("H", "G")}),
        values=frozenset({FACT_VALUE, "life"}),
        valuation={"G": FACT_VALUE, "H": FACT_VALUE, "K": "life"},
        audiences=((FACT_VALUE, "life"),),
    )

    assert vaf.preferred_extensions_for_audience((FACT_VALUE, "life")) == [
        frozenset({"G", "K"}),
        frozenset({"H", "K"}),
    ]
    assert is_skeptically_objective_under_fact_uncertainty(vaf, "K")
    assert not is_skeptically_objective_under_fact_uncertainty(vaf, "G")
