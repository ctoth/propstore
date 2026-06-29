"""Equivalence between propstore ATMS labels and provenance-semiring polynomials.

The carved ``provenance_semiring`` package owns the label / environment / nogood
algebra; ``propstore.core.labels`` is the propstore door that re-exports those
canonical types directly (CLAUDE.md substrate boundary: one spelling per thing,
no ``label_to_polynomial`` / ``polynomial_to_label`` mirror). The label *is* the
polynomial — ``Label.support.polynomial`` is the polynomial and
``Label.environments`` projects it back to its squarefree supports. These tests
confirm the ATMS-facing operations (``combine_labels`` / ``merge_labels`` /
``NogoodSet`` pruning) the engine consumes are exactly the polynomial product,
sum, and ``live`` filtering, and that propstore's assumption-vs-context variable
meaning survives the projection.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from provenance_semiring import ProvenancePolynomial, SupportEvidence, live

import propstore.core.labels as ps_labels
from propstore.core.labels import (
    EnvironmentKey,
    Label,
    NogoodSet,
    SupportQuality,
    combine_labels,
    environment_assumption_ids,
    environment_context_ids,
    make_environment_key,
    merge_labels,
)

_PROP_SETTINGS = settings(deadline=None)
_ASSUMPTION_IDS = st.text(alphabet="abcd", min_size=1, max_size=3)
_CONTEXT_IDS = st.text(alphabet="wxyz", min_size=1, max_size=3).map(lambda text: f"ctx_{text}")


@st.composite
def environment_keys(draw: st.DrawFn) -> EnvironmentKey:
    assumptions = draw(st.frozensets(_ASSUMPTION_IDS, min_size=0, max_size=3))
    contexts = draw(st.frozensets(_CONTEXT_IDS, min_size=0, max_size=3))
    return make_environment_key(
        assumption_ids=tuple(sorted(assumptions)),
        context_ids=tuple(sorted(contexts)),
    )


@st.composite
def labels(draw: st.DrawFn) -> Label:
    environments = draw(st.lists(environment_keys(), min_size=0, max_size=5))
    return Label(tuple(environments))


def _project(polynomial: ProvenancePolynomial) -> tuple[EnvironmentKey, ...]:
    """Read a polynomial back as the antichain of environments a Label exposes."""

    return Label(support=SupportEvidence(polynomial, SupportQuality.EXACT)).environments


class TestLabelPolynomialEquivalence:
    def test_propstore_label_door_is_the_carved_algebra(self) -> None:
        """No mirror: the propstore door re-exports the package's own functions."""

        import provenance_semiring as ps

        assert ps_labels.Label is ps.Label
        assert ps_labels.EnvironmentKey is ps.EnvironmentKey
        assert ps_labels.NogoodSet is ps.NogoodSet
        assert ps_labels.combine_labels is ps.combine_labels
        assert ps_labels.merge_labels is ps.merge_labels

    @pytest.mark.property
    @given(environment_keys())
    @_PROP_SETTINGS
    def test_assumption_and_context_meaning_survives_projection(
        self, environment: EnvironmentKey
    ) -> None:
        label = Label((environment,))
        projected = label.environments

        assert projected == (environment,)
        assert environment_assumption_ids(projected[0]) == environment_assumption_ids(environment)
        assert environment_context_ids(projected[0]) == environment_context_ids(environment)

    @pytest.mark.property
    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_combine_labels_uses_polynomial_multiplication_projection(
        self, left: Label, right: Label
    ) -> None:
        combined = combine_labels(left, right)
        expected = _project(left.support.polynomial * right.support.polynomial)

        assert combined.environments == expected

    @pytest.mark.property
    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_merge_labels_uses_polynomial_addition_projection(
        self, left: Label, right: Label
    ) -> None:
        merged = merge_labels([left, right])
        expected = _project(left.support.polynomial + right.support.polynomial)

        assert merged.environments == expected

    @pytest.mark.property
    @given(labels(), labels(), environment_keys())
    @_PROP_SETTINGS
    def test_nogood_pruning_matches_live_projection(
        self, left: Label, right: Label, nogood: EnvironmentKey
    ) -> None:
        nogoods = NogoodSet((nogood,))
        merged = merge_labels([left, right], nogoods=nogoods)

        assert all(not nogoods.excludes(env) for env in merged.environments)
        expected = _project(
            live(
                left.support.polynomial + right.support.polynomial,
                nogoods.provenance_nogoods,
            )
        )
        assert merged.environments == expected
