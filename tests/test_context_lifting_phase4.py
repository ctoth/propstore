from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.artifacts.documents.claims import ClaimDocument, IstPropositionDocument
from propstore.artifacts.documents.contexts import ContextDocument
from quire.documents import DocumentSchemaError, convert_document_value


def test_context_document_rejects_visibility_inheritance_fields() -> None:
    with pytest.raises(DocumentSchemaError, match="inherits"):
        convert_document_value(
            {
                "id": "ctx_child",
                "name": "Child",
                "inherits": "ctx_parent",
            },
            ContextDocument,
            source="contexts/ctx_child.yaml",
        )

    with pytest.raises(DocumentSchemaError, match="excludes"):
        convert_document_value(
            {
                "id": "ctx_a",
                "name": "A",
                "excludes": ["ctx_b"],
            },
            ContextDocument,
            source="contexts/ctx_a.yaml",
        )


def test_context_document_accepts_structured_context_and_lifting_rules() -> None:
    document = convert_document_value(
        {
            "id": "ctx_target",
            "name": "Target",
            "structure": {
                "assumptions": ["task == 'speech'"],
                "parameters": {"speaker": "speaker_a"},
                "perspective": "analyst",
            },
            "lifting_rules": [
                {
                    "id": "lift_source_target",
                    "source": "ctx_source",
                    "target": "ctx_target",
                    "conditions": ["license == 'bridge'"],
                    "mode": "bridge",
                    "justification": "Guha relative decontextualization",
                }
            ],
        },
        ContextDocument,
        source="contexts/ctx_target.yaml",
    )

    assert document.structure.assumptions == ("task == 'speech'",)
    assert document.structure.parameters["speaker"] == "speaker_a"
    assert document.lifting_rules[0].source == "ctx_source"
    assert document.lifting_rules[0].target == "ctx_target"


def test_claim_document_requires_explicit_context_reference() -> None:
    with pytest.raises(DocumentSchemaError, match="context"):
        convert_document_value(
            {
                "id": "claim_without_context",
                "type": "observation",
                "statement": "Contextless claim",
                "concepts": ["concept_a"],
            },
            ClaimDocument,
            source="claims/contextless.yaml",
        )

    claim = convert_document_value(
        {
            "id": "claim_with_context",
            "type": "observation",
            "context": {"id": "ctx_target"},
            "statement": "Context-qualified claim",
            "concepts": ["concept_a"],
        },
        ClaimDocument,
        source="claims/contextual.yaml",
    )

    assert claim.context.id == "ctx_target"


def test_claim_document_parses_nested_ist_proposition() -> None:
    claim = convert_document_value(
        {
            "artifact_id": "ps:claim:nested-ist",
            "context": {"id": "ctx_outer"},
            "proposition": {
                "kind": "ist",
                "context": {"id": "ctx_middle"},
                "proposition": {
                    "kind": "ist",
                    "context": {"id": "ctx_inner"},
                    "proposition": {
                        "kind": "atomic",
                        "type": "observation",
                        "statement": "nested proposition",
                        "concepts": ["concept_a"],
                    },
                },
            },
        },
        ClaimDocument,
        source="claims/nested-ist.yaml",
    )

    assert isinstance(claim.proposition, IstPropositionDocument)
    assert claim.proposition.context.id == "ctx_middle"
    inner = claim.proposition.proposition
    assert isinstance(inner, IstPropositionDocument)
    assert inner.context.id == "ctx_inner"
    assert claim.to_payload()["proposition"]["proposition"]["context"]["id"] == "ctx_inner"


@given(st.lists(st.sampled_from(["ctx_a", "ctx_b", "ctx_c", "ctx_d"]), min_size=1, max_size=4))
def test_nested_ist_proposition_round_trips_context_stack(context_ids: list[str]) -> None:
    proposition: dict[str, object] = {
        "kind": "atomic",
        "type": "observation",
        "statement": "round-trip proposition",
        "concepts": ["concept_a"],
    }
    for context_id in reversed(context_ids):
        proposition = {
            "kind": "ist",
            "context": {"id": context_id},
            "proposition": proposition,
        }

    claim_payload = {
        "artifact_id": "ps:claim:nested-ist-property",
        "context": {"id": "ctx_outer"},
        "proposition": proposition,
    }
    claim = convert_document_value(
        claim_payload,
        ClaimDocument,
        source="claims/nested-ist-property.yaml",
    )
    reparsed = convert_document_value(
        claim.to_payload(),
        ClaimDocument,
        source="claims/nested-ist-property-roundtrip.yaml",
    )

    cursor = reparsed.proposition
    observed_contexts: list[str] = []
    while isinstance(cursor, IstPropositionDocument):
        observed_contexts.append(cursor.context.id)
        cursor = cursor.proposition

    assert observed_contexts == context_ids


def test_lifting_system_is_explicit_rule_based() -> None:
    from propstore.context_lifting import (
        ContextReference,
        LiftingMode,
        LiftingRule,
        LiftingSystem,
    )

    system = LiftingSystem(
        contexts=(ContextReference(id="ctx_source"), ContextReference(id="ctx_target")),
        lifting_rules=(
            LiftingRule(
                id="lift_source_target",
                source=ContextReference(id="ctx_source"),
                target=ContextReference(id="ctx_target"),
                conditions=("license == 'bridge'",),
                mode=LiftingMode.BRIDGE,
                justification="Guha relative decontextualization",
            ),
        ),
    )

    assert system.can_lift("ctx_source", "ctx_target")
    assert not system.can_lift("ctx_target", "ctx_source")
    assert system.effective_assumptions("ctx_target") == ("license == 'bridge'",)
