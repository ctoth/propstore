"""Property tests for provenance nogood live filtering."""

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
    derivation_count,
    live,
)


_PROP_SETTINGS = settings(deadline=None)
_VARIABLES = tuple(SourceVariableId(f"ps:source:test:{name}") for name in ("a", "b", "c", "d"))


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
    for _ in range(draw(st.integers(min_value=0, max_value=6))):
        coefficient = draw(st.integers(min_value=1, max_value=3))
        variables = draw(st.lists(st.sampled_from(_VARIABLES), min_size=0, max_size=4))
        terms.append(
            PolynomialTerm(
                coefficient,
                tuple(VariablePower(variable, 1) for variable in variables),
            )
        )
    return ProvenancePolynomial(tuple(terms))


@st.composite
def nogoods(draw):
    selected = draw(st.frozensets(st.sampled_from(_VARIABLES), min_size=1, max_size=2))
    return ProvenanceNogood(
        frozenset(selected),
        NogoodWitness("test", "generated"),
        _provenance(),
    )


class TestLiveFiltering:
    @given(polynomials(), st.lists(nogoods(), min_size=0, max_size=3))
    @_PROP_SETTINGS
    def test_live_removes_every_nogood_superset(self, poly, generated_nogoods):
        result = live(poly, generated_nogoods)
        for support in result.squarefree_supports():
            assert not any(nogood.variables.issubset(support) for nogood in generated_nogoods)

    @given(polynomials(), st.lists(nogoods(), min_size=0, max_size=3))
    @_PROP_SETTINGS
    def test_live_preserves_every_non_dead_monomial(self, poly, generated_nogoods):
        result = live(poly, generated_nogoods)
        expected_terms = tuple(
            term
            for term in poly.terms
            if not any(nogood.variables.issubset(term.squarefree_support()) for nogood in generated_nogoods)
        )
        assert result == ProvenancePolynomial(expected_terms)

    def test_live_filtering_is_not_generic_homomorphism_for_counts(self):
        a = SourceVariableId("ps:source:test:a")
        b = SourceVariableId("ps:source:test:b")
        poly = ProvenancePolynomial.variable(a) + (
            ProvenancePolynomial.variable(a) * ProvenancePolynomial.variable(b)
        )
        nogood = ProvenanceNogood(
            frozenset((a, b)),
            NogoodWitness("test", "a-and-b conflict"),
            _provenance(),
        )

        raw_count = derivation_count(poly)
        live_count = derivation_count(live(poly, (nogood,)))

        assert raw_count == 2
        assert live_count == 1

    def test_empty_nogood_kills_every_monomial(self):
        a = SourceVariableId("ps:source:test:a")
        poly = ProvenancePolynomial.one() + ProvenancePolynomial.variable(a)
        nogood = ProvenanceNogood(
            frozenset(),
            NogoodWitness("test", "inconsistent empty environment"),
            _provenance(),
        )

        assert live(poly, (nogood,)) == ProvenancePolynomial.zero()
