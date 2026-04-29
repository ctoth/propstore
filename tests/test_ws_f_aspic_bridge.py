"""WS-F ASPIC+ bridge fidelity regressions."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest
from argumentation.aspic import Attack, GroundAtom, Literal, PremiseArg, Rule
from argumentation.dung import ArgumentationFramework

from propstore.aspic_bridge import (
    build_bridge_csaf,
    build_preference_config,
    claims_to_literals,
    csaf_to_projection,
    grounded_rules_to_rules,
    justifications_to_rules,
    stances_to_contrariness,
)
from propstore.aspic_bridge.build import compile_bridge_context
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import claim_key
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.structured_projection import (
    StructuredProjection,
    compute_structured_justified_arguments,
)
from propstore.world.types import ReasoningBackend


def _claim(
    claim_id: str,
    *,
    sample_size: int | None = None,
    uncertainty: float | None = None,
    confidence: float | None = None,
) -> dict[str, object]:
    claim: dict[str, object] = {
        "id": claim_id,
        "concept_id": f"concept_{claim_id}",
        "statement": f"Claim {claim_id}",
        "premise_kind": "ordinary",
    }
    if sample_size is not None:
        claim["sample_size"] = sample_size
    if uncertainty is not None:
        claim["uncertainty"] = uncertainty
    if confidence is not None:
        claim["confidence"] = confidence
    return claim


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        premise_claim_ids=(),
        rule_kind="reported_claim",
        rule_strength="defeasible",
    )


def _support(
    justification_id: str,
    conclusion: str,
    premises: tuple[str, ...],
    *,
    strength: str = "defeasible",
) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=justification_id,
        conclusion_claim_id=conclusion,
        premise_claim_ids=premises,
        rule_kind="supports",
        rule_strength=strength,
    )


def _stance(source: str, target: str, stance_type: str) -> dict[str, str]:
    return {
        "claim_id": source,
        "target_claim_id": target,
        "stance_type": stance_type,
    }


def test_stances_asymmetric_contrary_for_directional_relations() -> None:
    claims = [_claim("a"), _claim("b")]
    literals = claims_to_literals(claims)
    _strict, defeasible = justifications_to_rules([_reported("a"), _reported("b")], literals)

    supersedes = stances_to_contrariness(
        [_stance("a", "b", "supersedes")],
        literals,
        defeasible,
    )
    a = literals[claim_key("a")]
    b = literals[claim_key("b")]
    assert supersedes.is_contrary(a, b)
    assert not supersedes.is_contradictory(a, b)
    assert not supersedes.is_contrary(b, a)
    assert not supersedes.is_contradictory(b, a)

    rebuts = stances_to_contrariness([_stance("a", "b", "rebuts")], literals, defeasible)
    assert rebuts.is_contradictory(a, b)
    assert rebuts.is_contradictory(b, a)

    mixed = stances_to_contrariness(
        [_stance("a", "b", "rebuts"), _stance("b", "a", "undermines")],
        literals,
        defeasible,
    )
    assert mixed.is_contradictory(a, b)
    assert mixed.is_contrary(b, a)
    assert not mixed.is_contradictory(b, a)


def test_compile_bridge_uses_full_contrariness_transposition_language() -> None:
    claims = [_claim("a"), _claim("b"), _claim("c")]
    justifications = [
        _reported("a"),
        _reported("b"),
        _support("strict:a-to-c", "c", ("a",), strength="strict"),
    ]

    compiled = compile_bridge_context(
        claims,
        justifications,
        [_stance("c", "b", "rebuts")],
        bundle=GroundedRulesBundle.empty(),
    )

    b = compiled.literals[claim_key("b")]
    not_b = b.contrary
    c = compiled.literals[claim_key("c")]
    not_c = c.contrary
    a = compiled.literals[claim_key("a")]
    not_a = a.contrary
    assert Rule(antecedents=(not_c,), consequent=not_a, kind="strict") in compiled.system.strict_rules
    assert {b, not_b, c, not_c, a, not_a} <= compiled.system.language


def test_premise_order_respects_democratic_comparison_for_incomparable_vectors() -> None:
    claims = [
        _claim("sample", sample_size=1000, uncertainty=1.0, confidence=0.2),
        _claim("certain", sample_size=10, uncertainty=0.1, confidence=0.9),
    ]
    literals = claims_to_literals(claims)

    elitist = build_preference_config(
        claims,
        literals,
        frozenset(),
        comparison="elitist",
    )
    democratic = build_preference_config(
        claims,
        literals,
        frozenset(),
        comparison="democratic",
    )

    sample = literals[claim_key("sample")]
    certain = literals[claim_key("certain")]
    assert (sample, certain) not in elitist.premise_order
    assert (certain, sample) not in elitist.premise_order
    assert (sample, certain) in democratic.premise_order


def test_query_no_private_argumentation_imports() -> None:
    for path in Path("propstore").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("argumentation"):
                imported = {alias.name for alias in node.names}
                private = sorted(name for name in imported if name.startswith("_"))
                assert not private, f"{path} imports private argumentation names {private}"


def test_aspic_grounded_is_attack_conflict_free() -> None:
    projection = StructuredProjection(
        arguments=(),
        framework=ArgumentationFramework(
            arguments=frozenset({"a", "b"}),
            defeats=frozenset(),
            attacks=frozenset({("a", "b"), ("b", "a")}),
        ),
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )

    justified = compute_structured_justified_arguments(
        projection,
        semantics="grounded",
        backend=ReasoningBackend.ASPIC,
    )

    assert not ({"a", "b"} <= justified)


def test_advertised_aspic_semantics_are_executable() -> None:
    projection = StructuredProjection(
        arguments=(),
        framework=ArgumentationFramework(arguments=frozenset({"a"}), defeats=frozenset()),
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )

    assert compute_structured_justified_arguments(
        projection,
        semantics="complete",
        backend=ReasoningBackend.ASPIC,
    ) == [frozenset({"a"})]
    assert compute_structured_justified_arguments(
        projection,
        semantics="aspic-direct-grounded",
        backend=ReasoningBackend.ASPIC,
    ) == frozenset({"a"})
    assert compute_structured_justified_arguments(
        projection,
        semantics="aspic-incomplete-grounded",
        backend=ReasoningBackend.ASPIC,
    ) == frozenset({"a"})


def test_projection_preserves_attack_without_defeat_and_rejects_unprojected_attack() -> None:
    claims = [
        _claim("weak", sample_size=1, uncertainty=1.0, confidence=0.1),
        _claim("strong", sample_size=100, uncertainty=0.1, confidence=0.9),
    ]
    justifications = [_reported("weak"), _reported("strong")]
    csaf = build_bridge_csaf(
        claims,
        justifications,
        [_stance("weak", "strong", "rebuts")],
        bundle=GroundedRulesBundle.empty(),
    )
    projection = csaf_to_projection(csaf, claims)

    assert projection.framework.attacks - projection.framework.defeats

    external = PremiseArg(Literal(GroundAtom("external")), is_axiom=False)
    known = next(iter(csaf.arguments))
    malformed = replace(
        csaf,
        attacks=csaf.attacks
        | frozenset({Attack(attacker=external, target=known, target_sub=known, kind="undermining")}),
    )
    with pytest.raises(ValueError, match="outside projected argument domain"):
        csaf_to_projection(malformed, claims)


def test_defeater_rule_with_named_rule_head_emits_undercutter() -> None:
    from propstore.families.documents.rules import (
        AtomDocument,
        RuleDocument,
        RuleSourceDocument,
        RulesFileDocument,
        TermDocument,
    )
    from propstore.rule_files import LoadedRuleFile
    from quire.documents import LoadedDocument

    x = TermDocument(kind="var", name="X")
    target = RuleDocument(
        id="birds-fly",
        kind="defeasible",
        head=AtomDocument(predicate="flies", terms=(x,)),
        body=(AtomDocument(predicate="bird", terms=(x,)),),
    )
    defeater = RuleDocument(
        id="named-defeater",
        kind="defeater",
        head=AtomDocument(
            predicate="birds-fly",
            terms=(TermDocument(kind="const", value="tweety"),),
            negated=True,
        ),
        body=(AtomDocument(predicate="exception", terms=(x,)),),
    )
    loaded = LoadedDocument(
        filename="rules.yaml",
        source_path=None,
        knowledge_root=None,
        document=RulesFileDocument(
            source=RuleSourceDocument(paper="ws-f"),
            rules=(target, defeater),
        ),
    )
    bundle = GroundedRulesBundle(
        source_rules=(LoadedRuleFile.from_loaded_document(loaded),),
        source_facts=(),
        sections={
            "definitely": {
                "bird": frozenset({("tweety",)}),
                "exception": frozenset({("tweety",)}),
            },
            "defeasibly": {},
            "not_defeasibly": {},
            "undecided": {},
        },
    )

    _strict, defeasible, _literals = grounded_rules_to_rules(bundle, {})

    target_name = next(rule.name for rule in defeasible if rule.name and rule.name.startswith("birds-fly#"))
    assert any(
        rule.consequent == Literal(GroundAtom(target_name), negated=True)
        for rule in defeasible
        if rule.name and rule.name.startswith("named-defeater#")
    )
