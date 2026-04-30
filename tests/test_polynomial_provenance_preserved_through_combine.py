from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from propstore.core.labels import Label, combine_labels
from propstore.provenance import (
    PolynomialTerm,
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
    VariablePower,
    derivation_count,
)


@given(st.integers(min_value=2, max_value=8))
def test_combine_labels_preserves_semiring_coefficients(coefficient: int) -> None:
    variable = SourceVariableId("urn:var:semiring")
    label = Label(
        support=SupportEvidence(
            ProvenancePolynomial.from_terms(
                (
                    PolynomialTerm(
                        coefficient,
                        (VariablePower(variable, 1),),
                    ),
                )
            ),
            SupportQuality.EXACT,
        )
    )

    combined = combine_labels(label, Label.empty())

    assert derivation_count(combined.support.polynomial) == coefficient
