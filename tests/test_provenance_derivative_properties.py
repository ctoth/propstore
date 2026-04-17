"""Property tests for provenance polynomial derivatives."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.provenance import (
    NogoodWitness,
    PolynomialTerm,
    Provenance,
    ProvenanceNogood,
    ProvenancePolynomial,
    ProvenanceStatus,
    ProvenanceWitness,
    SourceVariableId,
    VariablePower,
    live,
    partial_derivative,
)


_PROP_SETTINGS = settings(deadline=None)
_VARIABLES = tuple(SourceVariableId(f"ps:source:test:{name}") for name in ("a", "b", "c"))


def _provenance() -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(
            ProvenanceWitness(
                asserter="test",
                timestamp="2026-04-17T00:00:00Z",
                source_artifact_code="test",
                method="test",
            ),
        ),
    )


@st.composite
def polynomials(draw):
    terms = []
    for _ in range(draw(st.integers(min_value=0, max_value=5))):
        coefficient = draw(st.integers(min_value=1, max_value=3))
        variables = draw(st.lists(st.sampled_from(_VARIABLES), min_size=0, max_size=3))
        terms.append(
            PolynomialTerm(
                coefficient,
                tuple(VariablePower(variable, 1) for variable in variables),
            )
        )
    return ProvenancePolynomial(tuple(terms))


class TestPolynomialDerivative:
    @given(polynomials(), polynomials(), st.sampled_from(_VARIABLES))
    @_PROP_SETTINGS
    def test_derivative_of_sum(self, left, right, variable):
        assert partial_derivative(left + right, variable) == (
            partial_derivative(left, variable) + partial_derivative(right, variable)
        )

    @given(polynomials(), polynomials(), st.sampled_from(_VARIABLES))
    @_PROP_SETTINGS
    def test_derivative_product_rule(self, left, right, variable):
        assert partial_derivative(left * right, variable) == (
            partial_derivative(left, variable) * right
            + left * partial_derivative(right, variable)
        )

    def test_dead_monomials_do_not_contribute_to_live_derivative(self):
        a = SourceVariableId("ps:source:test:a")
        b = SourceVariableId("ps:source:test:b")
        poly = ProvenancePolynomial.variable(a) * ProvenancePolynomial.variable(b)
        nogood = ProvenanceNogood(
            frozenset((a, b)),
            NogoodWitness("test", "dead support"),
            _provenance(),
        )

        assert partial_derivative(live(poly, (nogood,)), a) == ProvenancePolynomial.zero()

    def test_source_removal_affects_only_monomials_containing_source(self):
        a = SourceVariableId("ps:source:test:a")
        b = SourceVariableId("ps:source:test:b")
        c = SourceVariableId("ps:source:test:c")
        poly = (
            ProvenancePolynomial.variable(a) * ProvenancePolynomial.variable(b)
            + ProvenancePolynomial.variable(c)
        )

        derivative = partial_derivative(poly, a)

        assert derivative == ProvenancePolynomial.variable(b)
