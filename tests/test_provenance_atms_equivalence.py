"""Equivalence tests between ATMS labels and provenance polynomial support."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.labels import (
    EnvironmentKey,
    Label,
    NogoodSet,
    combine_labels,
    label_to_polynomial,
    merge_labels,
    polynomial_to_label,
)
from propstore.provenance import live


_PROP_SETTINGS = settings(deadline=None)
_ASSUMPTION_IDS = st.text(alphabet="abcd", min_size=1, max_size=3)
_CONTEXT_IDS = st.text(alphabet="wxyz", min_size=1, max_size=3).map(lambda text: f"ctx_{text}")


@st.composite
def environment_keys(draw):
    assumptions = draw(st.frozensets(_ASSUMPTION_IDS, min_size=0, max_size=3))
    contexts = draw(st.frozensets(_CONTEXT_IDS, min_size=0, max_size=3))
    return EnvironmentKey(tuple(assumptions), context_ids=tuple(contexts))


@st.composite
def labels(draw):
    environments = draw(st.lists(environment_keys(), min_size=0, max_size=5))
    return Label(tuple(environments))


class TestLabelPolynomialEquivalence:
    @pytest.mark.property
    @given(labels())
    @_PROP_SETTINGS
    def test_label_to_polynomial_to_label_round_trips(self, label):
        assert polynomial_to_label(label_to_polynomial(label)) == label

    @pytest.mark.property
    @given(environment_keys())
    @_PROP_SETTINGS
    def test_assumptions_and_contexts_survive_projection_separately(self, environment):
        label = Label((environment,))
        projected = polynomial_to_label(label_to_polynomial(label))

        assert projected.environments == label.environments
        if environment.assumption_ids or environment.context_ids:
            assert projected.environments[0].assumption_ids == environment.assumption_ids
            assert projected.environments[0].context_ids == environment.context_ids

    @pytest.mark.property
    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_combine_labels_uses_polynomial_multiplication_projection(self, left, right):
        combined = combine_labels(left, right)
        expected = polynomial_to_label(label_to_polynomial(left) * label_to_polynomial(right))

        assert combined == expected

    @pytest.mark.property
    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_merge_labels_uses_polynomial_addition_projection(self, left, right):
        merged = merge_labels([left, right])
        expected = polynomial_to_label(label_to_polynomial(left) + label_to_polynomial(right))

        assert merged == expected

    @pytest.mark.property
    @given(labels(), labels(), environment_keys())
    @_PROP_SETTINGS
    def test_nogood_pruning_matches_polynomial_projection(self, left, right, nogood):
        nogoods = NogoodSet((nogood,))
        merged = merge_labels([left, right], nogoods=nogoods)

        assert all(not nogoods.excludes(env) for env in merged.environments)

    @pytest.mark.property
    @given(labels(), environment_keys())
    @_PROP_SETTINGS
    def test_nogood_set_projects_to_live_filtering(self, label, nogood):
        nogoods = NogoodSet((nogood,))
        filtered = merge_labels([label], nogoods=nogoods)
        expected = polynomial_to_label(
            live(label_to_polynomial(label), nogoods.provenance_nogoods)
        )

        assert filtered.environments == expected.environments
