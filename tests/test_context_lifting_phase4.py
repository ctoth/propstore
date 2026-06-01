from __future__ import annotations

import pytest

from propstore.families.claims.declaration import ClaimDocument
from propstore.families.contexts.declaration import ContextDocument
from quire.documents import (
    DocumentSchemaError,
    convert_document_value,
)


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
            "assumptions": ["task == 'speech'"],
            "parameters": {"speaker": "speaker_a"},
            "perspective": "analyst",
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

    assert document.assumptions == ("task == 'speech'",)
    assert document.parameters["speaker"] == "speaker_a"
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


def test_lifting_system_is_explicit_rule_based() -> None:
    from propstore.core.assertions.refs import ContextReference
    from propstore.families.contexts.lifting import (
        IstProposition,
        LiftingDecisionStatus,
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

    forward_decisions = system.lift_decisions_between(
        "ctx_source",
        "ctx_target",
        "claim_source",
    )
    reverse_decisions = system.lift_decisions_between(
        "ctx_target",
        "ctx_source",
        "claim_source",
    )

    assert tuple(decision.status for decision in forward_decisions) == (
        LiftingDecisionStatus.UNKNOWN,
    )
    assert reverse_decisions == ()
    assert (
        system.materialize_lifted_assertions(
            (
                IstProposition(
                    context=ContextReference("ctx_source"),
                    proposition_id="claim_source",
                ),
            )
        )
        == ()
    )
    assert system.effective_assumptions("ctx_target") == ()
