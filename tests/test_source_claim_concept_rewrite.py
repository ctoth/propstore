from __future__ import annotations

import importlib
from typing import Any

import pytest
from quire.documents import convert_document_value

from propstore.families.documents.sources import SourceClaimDocument
from propstore.source.claim_concepts import rewrite_claim_concept_refs


def _source_claim(payload: dict[str, Any]) -> SourceClaimDocument:
    return convert_document_value(
        payload,
        SourceClaimDocument,
        source="test:source-claim",
    )


@pytest.mark.parametrize(
    ("claim_type", "expected_field"),
    (
        ("parameter", "output_concept"),
        ("algorithm", "output_concept"),
        ("measurement", "target_concept"),
        ("observation", "concepts"),
    ),
)
def test_source_local_concept_placement_is_shared_for_import_and_promotion(
    claim_type: str,
    expected_field: str,
) -> None:
    raw_payload = {
        "type": claim_type,
        "context": {"id": "ctx"},
        "concept": "local_concept",
        "statement": "Observed." if claim_type == "observation" else None,
        "value": 1.0 if claim_type in {"parameter", "measurement"} else None,
        "expression": "x + 1" if claim_type == "algorithm" else None,
    }
    raw_payload = {key: value for key, value in raw_payload.items() if value is not None}
    source_claim = _source_claim(
        {
            **raw_payload,
            "context": "ctx",
        }
    )
    concept_map = {"local_concept": "ps:concept:mapped"}

    import_payload = rewrite_claim_concept_refs(
        raw_payload,
        concept_map,
        unresolved=set(),
    )
    promotion_payload = rewrite_claim_concept_refs(
        source_claim,
        concept_map,
        unresolved=set(),
    )

    assert "concept" not in import_payload
    assert "concept" not in promotion_payload
    if expected_field == "concepts":
        assert import_payload["concepts"] == ["ps:concept:mapped"]
        assert promotion_payload["concepts"] == ["ps:concept:mapped"]
    else:
        assert import_payload[expected_field] == "ps:concept:mapped"
        assert promotion_payload[expected_field] == "ps:concept:mapped"


def test_source_claim_concept_rewrite_updates_nested_variables_and_parameters() -> None:
    unresolved: set[str] = set()

    rewritten = rewrite_claim_concept_refs(
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


def test_source_claim_concept_rewrite_preserves_global_refs_and_reports_unresolved() -> None:
    unresolved: set[str] = set()

    rewritten = rewrite_claim_concept_refs(
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
    passes = importlib.import_module("propstore.source.passes")

    assert not hasattr(promote, "_place_promoted_singular_concept")
    assert not hasattr(passes, "_place_rewritten_singular_concept")
