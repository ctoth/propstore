"""Tests for parameterization group connected-component analysis.

Verifies that concepts connected via parameterization_relationships
are grouped into the correct connected components.
"""

import pytest

from compiler.parameterization_groups import build_groups


def _concept(cid, param_inputs=None):
    """Build a minimal concept dict with optional parameterization inputs."""
    c = {"id": cid, "canonical_name": f"concept_{cid}"}
    if param_inputs is not None:
        c["parameterization_relationships"] = [
            {"formula": "x = y", "inputs": param_inputs, "exactness": "exact",
             "source": "Test", "bidirectional": True}
        ]
    return c


class TestBuildGroups:
    def test_five_connected_concepts_one_group(self):
        """5 concepts all connected via parameterizations form 1 group."""
        # Chain: a->b->c, a->d->e (all connected through a)
        concepts = [
            _concept("concept1"),
            _concept("concept2", param_inputs=["concept1"]),
            _concept("concept3", param_inputs=["concept2"]),
            _concept("concept4", param_inputs=["concept1"]),
            _concept("concept5", param_inputs=["concept4"]),
        ]
        groups = build_groups(concepts)
        assert len(groups) == 1
        assert groups[0] == {"concept1", "concept2", "concept3", "concept4", "concept5"}

    def test_two_disconnected_clusters(self):
        """Two disconnected clusters produce 2 groups."""
        concepts = [
            _concept("concept1"),
            _concept("concept2", param_inputs=["concept1"]),
            # Disconnected cluster
            _concept("concept3"),
            _concept("concept4", param_inputs=["concept3"]),
        ]
        groups = build_groups(concepts)
        assert len(groups) == 2
        group_sets = [frozenset(g) for g in groups]
        assert frozenset({"concept1", "concept2"}) in group_sets
        assert frozenset({"concept3", "concept4"}) in group_sets

    def test_single_concept_no_parameterizations(self):
        """A single concept with no parameterizations is a group of 1."""
        concepts = [_concept("concept1")]
        groups = build_groups(concepts)
        assert len(groups) == 1
        assert groups[0] == {"concept1"}

    def test_linear_chain(self):
        """Linear chain A->B->C forms 1 group containing all three."""
        concepts = [
            _concept("concept1"),
            _concept("concept2", param_inputs=["concept1"]),
            _concept("concept3", param_inputs=["concept2"]),
        ]
        groups = build_groups(concepts)
        assert len(groups) == 1
        assert groups[0] == {"concept1", "concept2", "concept3"}

    def test_empty_input(self):
        """No concepts produces no groups."""
        groups = build_groups([])
        assert len(groups) == 0

    def test_multiple_inputs_per_parameterization(self):
        """A concept with multiple inputs connects all of them."""
        concepts = [
            _concept("concept1"),
            _concept("concept2"),
            _concept("concept3", param_inputs=["concept1", "concept2"]),
        ]
        groups = build_groups(concepts)
        assert len(groups) == 1
        assert groups[0] == {"concept1", "concept2", "concept3"}
