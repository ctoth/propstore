from __future__ import annotations

import importlib

import pytest

from propstore.families.claims.lifecycle import (
    rewrite_imported_claim_concept_refs,
    rewrite_source_claim_concept_refs,
)


def test_source_claim_concept_rewrite_updates_nested_variables_and_parameters() -> None:
    unresolved: set[str] = set()

    rewritten = rewrite_imported_claim_concept_refs(
        {
            "type": "algorithm",
            "context": {"id": "ctx"},
            "output_concept": "output",
            "variables": [{"name": "x", "concept": "input"}],
            "parameters": [{"name": "p", "concept": "param"}],
        },
        {
            "output": "ps:concept:output",
            "input": "ps:concept:input",
            "param": "ps:concept:param",
        },
        unresolved=unresolved,
    )

    assert unresolved == set()
    assert rewritten["output_concept"] == "ps:concept:output"
    assert rewritten["variables"] == [{"name": "x", "concept": "ps:concept:input"}]
    assert rewritten["parameters"] == [{"name": "p", "concept": "ps:concept:param"}]


def test_source_claim_concept_rewrite_preserves_global_refs_and_reports_unresolved() -> (
    None
):
    unresolved: set[str] = set()

    rewritten = rewrite_imported_claim_concept_refs(
        {
            "type": "observation",
            "context": {"id": "ctx"},
            "concepts": ["missing", "ps:concept:already", "tag:topic"],
        },
        {},
        unresolved=unresolved,
    )

    assert rewritten["concepts"] == ["missing", "ps:concept:already", "tag:topic"]
    assert unresolved == {"missing"}


def test_old_source_claim_concept_placement_helpers_are_deleted() -> None:
    promote = importlib.import_module("propstore.source.promote")
    passes = importlib.import_module("propstore.importing.passes")

    assert not hasattr(promote, "_place_promoted_singular_concept")
    assert not hasattr(passes, "_place_rewritten_singular_concept")
