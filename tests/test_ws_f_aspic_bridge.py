"""WS-F ASPIC+ bridge fidelity regressions."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from argumentation.aspic import Attack, GroundAtom, Literal, PremiseArg, Rule, conc
from argumentation.bipolar import BipolarArgumentationFramework
from argumentation.dung import ArgumentationFramework
from argumentation.probabilistic import PrAFResult

from propstore.aspic_bridge import (
    build_bridge_csaf,
    build_preference_config,
    claims_to_literals,
    csaf_to_projection,
    grounded_rules_to_rules,
    justifications_to_rules,
    query_claim,
    stances_to_contrariness,
)
from propstore.app.world_reasoning import (
    AppWorldExtensionsRequest,
    WorldExtensionsStanceSummary,
    _praf_extensions,
)
from propstore.aspic_bridge.build import compile_bridge_context
from propstore.context_lifting import (
    IstProposition,
    LiftingException,
    LiftingDecisionStatus,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.analyzers import SharedAnalyzerInput, analyze_praf
from propstore.core.assertions import ContextReference
from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, CompiledWorldGraph
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import claim_key
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.probabilistic_relations import ClaimGraphRelations
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
    assert mixed.is_contrary(b, a)
    assert not mixed.is_contradictory(a, b)
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
        _claim("sample", sample_size=1000, uncertainty=0.9, confidence=0.2),
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
        if path.name.startswith("_ws_n2_violation_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("argumentation"):
                imported = {alias.name for alias in node.names}
                private = sorted(name for name in imported if name.startswith("_"))
                assert not private, f"{path} imports private argumentation names {private}"


def test_aspic_grounded_is_attack_conflict_free() -> None:
    """ASPIC grounded extensions must be conflict-free against raw attacks.

    This pins Modgil and Prakken 2018 sections 3-4: attacks and defeats are
    distinct, and attack-conflict-freeness cannot be weakened to defeat-only
    conflict-freeness.
    """

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


def test_lifted_bridge_decision_projects_target_ist_argument() -> None:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(LiftingRule("lift-source-target", source, target),),
    )
    decisions = system.lift_decisions_for(
        IstProposition(context=source, proposition_id="claim_alpha")
    )

    compiled = compile_bridge_context(
        [{**_claim("claim_alpha"), "context_id": "ctx_source"}],
        [_reported("claim_alpha")],
        [],
        bundle=GroundedRulesBundle.empty(),
        lifting_decisions=decisions,
    )
    csaf = build_bridge_csaf(
        [{**_claim("claim_alpha"), "context_id": "ctx_source"}],
        [_reported("claim_alpha")],
        [],
        bundle=GroundedRulesBundle.empty(),
        lifting_decisions=decisions,
    )
    target_literal = compiled.literals[claim_key("claim_alpha", context_id="ctx_target")]

    assert any(rule.consequent == target_literal for rule in compiled.system.strict_rules)
    assert any(conc(argument) == target_literal for argument in csaf.arguments)
    assert compiled.lifting_projection.records[0].rule_id == "lift-source-target"
    assert compiled.lifting_projection.records[0].status is LiftingDecisionStatus.LIFTED


def test_blocked_lifting_decision_does_not_project_target_argument() -> None:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(LiftingRule("lift-source-target", source, target),),
        lifting_exceptions=(
            LiftingException(
                id="except-alpha",
                rule_id="lift-source-target",
                target=target,
                proposition_id="claim_alpha",
                clashing_set=("claim_beta",),
            ),
        ),
    )
    decisions = system.lift_decisions_for(
        IstProposition(context=source, proposition_id="claim_alpha")
    )
    csaf = build_bridge_csaf(
        [{**_claim("claim_alpha"), "context_id": "ctx_source"}],
        [_reported("claim_alpha")],
        [],
        bundle=GroundedRulesBundle.empty(),
        lifting_decisions=decisions,
    )

    target_literal = Literal(GroundAtom("ist", ("ctx_target", "claim_alpha")))
    assert decisions[0].status is LiftingDecisionStatus.BLOCKED
    assert not any(conc(argument) == target_literal for argument in csaf.arguments)


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
        _claim("weak", sample_size=1, uncertainty=0.9, confidence=0.1),
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
        BodyLiteralDocument,
        RuleDocument,
        RuleSourceDocument,
        RulesFileDocument,
        TermDocument,
    )
    from propstore.rule_files import LoadedRuleFile
    from quire.documents import LoadedDocument

    x = TermDocument(kind="var", name="X")
    target = RuleDocument(
        id="birds_fly",
        kind="defeasible",
        head=AtomDocument(predicate="flies", terms=(x,)),
        body=(
            BodyLiteralDocument(
                kind="positive",
                atom=AtomDocument(predicate="bird", terms=(x,)),
            ),
        ),
    )
    defeater = RuleDocument(
        id="named-defeater",
        kind="proper_defeater",
        head=AtomDocument(
            predicate="birds_fly",
            terms=(TermDocument(kind="const", value="tweety"),),
            negated=True,
        ),
        body=(
            BodyLiteralDocument(
                kind="positive",
                atom=AtomDocument(predicate="exception", terms=(x,)),
            ),
        ),
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
    from propstore.grounding.grounder import ground
    from propstore.grounding.predicates import PredicateRegistry

    bundle = ground(
        (LoadedRuleFile.from_loaded_document(loaded),),
        (
            GroundAtom("bird", ("tweety",)),
            GroundAtom("exception", ("tweety",)),
        ),
        PredicateRegistry(()),
        return_arguments=True,
    )

    _strict, defeasible, _literals = grounded_rules_to_rules(bundle, {})

    target_name = next(rule.name for rule in defeasible if rule.name and rule.name.startswith("birds_fly#"))
    assert any(
        rule.consequent == Literal(GroundAtom(target_name), negated=True)
        for rule in defeasible
        if rule.name and rule.name.startswith("named-defeater#")
    )


def test_arguments_against_includes_undermine_and_undercut_attackers() -> None:
    claims = [_claim("premise"), _claim("goal"), _claim("anti_premise"), _claim("rule_attack")]
    justifications = [
        _reported("premise"),
        _reported("anti_premise"),
        _reported("rule_attack"),
        _support("support:premise-to-goal", "goal", ("premise",)),
    ]
    result = query_claim(
        "goal",
        claims,
        justifications,
        [
            _stance("anti_premise", "premise", "undermines"),
            {
                "claim_id": "rule_attack",
                "target_claim_id": "goal",
                "stance_type": "undercuts",
                "target_justification_id": "support:premise-to-goal",
            },
        ],
        bundle=GroundedRulesBundle.empty(),
    )

    literals = claims_to_literals(claims)
    attacker_conclusions = {conc(argument) for argument in result.arguments_against}
    assert literals[claim_key("anti_premise")] in attacker_conclusions
    assert literals[claim_key("rule_attack")] in attacker_conclusions


def test_claim_canonical_name_collision_does_not_collapse_aspic_literals() -> None:
    claims = [
        {
            **_claim("first"),
            "concept_id": "shared_concept",
            "canonical_name": "same canonical concept",
        },
        {
            **_claim("second"),
            "concept_id": "shared_concept",
            "canonical_name": "same canonical concept",
        },
    ]
    literals = claims_to_literals(claims)

    first = literals[claim_key("first")]
    second = literals[claim_key("second")]
    assert first != second
    assert first.atom.predicate == "ist"
    assert second.atom.predicate == "ist"
    assert first.atom.arguments[-1] == "first"
    assert second.atom.arguments[-1] == "second"

    csaf = build_bridge_csaf(
        claims,
        [_reported("first"), _reported("second")],
        [],
        bundle=GroundedRulesBundle.empty(),
    )
    projection = csaf_to_projection(csaf, claims)

    assert set(projection.claim_to_argument_ids) == {"first", "second"}
    assert set(projection.claim_to_argument_ids["first"]).isdisjoint(
        projection.claim_to_argument_ids["second"]
    )


def _minimal_praf_shared_input() -> SharedAnalyzerInput:
    prior = {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5}
    active_graph = ActiveWorldGraph(
        compiled=CompiledWorldGraph(
            claims=(
                ClaimNode(
                    claim_id="claim_a",
                    claim_type="observation",
                    attributes={"source_prior_base_rate": prior},
                ),
            )
        ),
        active_claim_ids=("claim_a",),
    )
    return SharedAnalyzerInput(
        active_graph=active_graph,
        comparison="elitist",
        claims_by_id={
            "claim_a": {
                "id": "claim_a",
                "source_prior_base_rate": prior,
            },
        },
        stance_rows=(),
        relations=ClaimGraphRelations(
            arguments=frozenset({"claim_a"}),
            attacks=frozenset(),
            direct_defeats=frozenset(),
            supports=frozenset(),
        ),
        argumentation_framework=ArgumentationFramework(
            arguments=frozenset({"claim_a"}),
            defeats=frozenset(),
            attacks=frozenset(),
        ),
        bipolar_framework=BipolarArgumentationFramework(
            arguments=frozenset({"claim_a"}),
            defeats=frozenset(),
            supports=frozenset(),
        ),
    )


def test_praf_paper_td_complete_routes_core_analyzer_to_extension_probability() -> None:
    result = analyze_praf(
        _minimal_praf_shared_input(),
        semantics="praf-paper-td-complete",
        strategy="exact_enum",
        query_kind="argument_acceptance",
        inference_mode="credulous",
        target_claim_ids=("claim_a",),
    )

    metadata = dict(result.metadata)
    assert result.semantics == "praf-paper-td-complete"
    assert metadata["strategy_used"] == "paper_td"
    assert metadata["query_kind"] == "extension_probability"
    assert metadata["inference_mode"] is None
    assert metadata["queried_set"] == ("claim_a",)
    assert metadata["extension_probability"] == pytest.approx(0.5)
    assert metadata["acceptance_probs"] is None
    assert result.projection is not None
    assert result.projection.survivor_claim_ids == ("claim_a",)


def test_praf_paper_td_complete_routes_app_report_to_extension_probability(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_build_praf(world: object, claim_ids: set[str], *, comparison: str) -> SimpleNamespace:
        del world, comparison
        return SimpleNamespace(kernel=SimpleNamespace(framework=SimpleNamespace(arguments=frozenset(claim_ids))))

    def fake_compute(kernel: object, **kwargs: object) -> PrAFResult:
        del kernel
        calls.append(dict(kwargs))
        return PrAFResult(
            extension_probability=0.75,
            strategy_used="paper_td",
            strategy_requested="paper_td",
            semantics="complete",
            query_kind="extension_probability",
            inference_mode=None,
            queried_set=("claim_a",),
        )

    monkeypatch.setattr("propstore.praf.build_praf", fake_build_praf)
    monkeypatch.setattr("argumentation.probabilistic.compute_probabilistic_acceptance", fake_compute)

    report = _praf_extensions(
        world=object(),
        active=(),
        claim_ids={"claim_a"},
        request=AppWorldExtensionsRequest(
            bindings={},
            backend="praf",
            semantics="praf-paper-td-complete",
            praf_strategy="exact_enum",
        ),
        active_lines=(),
        summary=WorldExtensionsStanceSummary(
            total_stances=0,
            included_as_attacks=0,
            vacuous_count=0,
            excluded_non_attack=0,
            models=(),
        ),
    )

    assert calls == [
        {
            "semantics": "complete",
            "strategy": "paper_td",
            "query_kind": "extension_probability",
            "inference_mode": None,
            "queried_set": ("claim_a",),
            "mc_epsilon": 0.01,
            "mc_confidence": 0.95,
            "rng_seed": None,
        }
    ]
    assert report.strategy_used == "paper_td"
    assert report.extension_probability == pytest.approx(0.75)
    assert report.acceptance_probabilities == ()


@pytest.mark.property
@given(st.integers(min_value=1, max_value=4))
@settings(deadline=None, max_examples=20)
def test_strict_rule_closure_is_monotone_when_strict_rules_are_added(rule_count: int) -> None:
    claims = [_claim(f"c{i}") for i in range(rule_count + 2)]
    base_justifications = [_reported("c0")] + [
        _support(f"strict:c{i}-to-c{i + 1}", f"c{i + 1}", (f"c{i}",), strength="strict")
        for i in range(rule_count)
    ]
    extended_justifications = base_justifications + [
        _support(
            f"strict:c{rule_count}-to-c{rule_count + 1}",
            f"c{rule_count + 1}",
            (f"c{rule_count}",),
            strength="strict",
        )
    ]

    base = compile_bridge_context(
        claims,
        base_justifications,
        [],
        bundle=GroundedRulesBundle.empty(),
    )
    extended = compile_bridge_context(
        claims,
        extended_justifications,
        [],
        bundle=GroundedRulesBundle.empty(),
    )

    assert base.system.strict_rules <= extended.system.strict_rules


@pytest.mark.property
@given(
    weak_sample_size=st.integers(min_value=1, max_value=10),
    strong_sample_size=st.integers(min_value=100, max_value=1000),
    weak_uncertainty=st.floats(min_value=0.7, max_value=0.95, allow_nan=False, allow_infinity=False),
    strong_uncertainty=st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False),
    weak_confidence=st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False),
    strong_confidence=st.floats(min_value=0.7, max_value=0.95, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None, max_examples=30)
def test_generated_preference_cases_can_have_attack_without_defeat(
    weak_sample_size: int,
    strong_sample_size: int,
    weak_uncertainty: float,
    strong_uncertainty: float,
    weak_confidence: float,
    strong_confidence: float,
) -> None:
    claims = [
        _claim(
            "weak",
            confidence=weak_confidence,
            sample_size=weak_sample_size,
            uncertainty=weak_uncertainty,
        ),
        _claim(
            "strong",
            confidence=strong_confidence,
            sample_size=strong_sample_size,
            uncertainty=strong_uncertainty,
        ),
    ]
    csaf = build_bridge_csaf(
        claims,
        [_reported("weak"), _reported("strong")],
        [_stance("weak", "strong", "rebuts")],
        bundle=GroundedRulesBundle.empty(),
    )

    assert csaf.framework.attacks is not None
    assert csaf.framework.defeats <= csaf.framework.attacks
    assert csaf.framework.attacks - csaf.framework.defeats


@pytest.mark.property
@given(
    first_rule_id=st.from_regex(r"alpha_[a-z]{1,6}", fullmatch=True),
    second_rule_id=st.from_regex(r"beta_[a-z]{1,6}", fullmatch=True),
)
@settings(deadline=None, max_examples=30)
def test_alpha_renaming_rule_ids_preserves_claim_acceptance(
    first_rule_id: str,
    second_rule_id: str,
) -> None:
    assume(first_rule_id != second_rule_id)
    claims = [_claim("premise"), _claim("goal")]
    first_csaf = build_bridge_csaf(
        claims,
        [_reported("premise"), _support(first_rule_id, "goal", ("premise",))],
        [],
        bundle=GroundedRulesBundle.empty(),
    )
    second_csaf = build_bridge_csaf(
        claims,
        [_reported("premise"), _support(second_rule_id, "goal", ("premise",))],
        [],
        bundle=GroundedRulesBundle.empty(),
    )
    first_projection = csaf_to_projection(first_csaf, claims)
    second_projection = csaf_to_projection(second_csaf, claims)

    def accepted_claim_ids(projection: StructuredProjection) -> set[str]:
        accepted_args = compute_structured_justified_arguments(
            projection,
            semantics="grounded",
            backend=ReasoningBackend.ASPIC,
        )
        return {
            projection.argument_to_claim_id[arg_id]
            for arg_id in accepted_args
            if arg_id in projection.argument_to_claim_id
        }

    assert accepted_claim_ids(first_projection) == accepted_claim_ids(second_projection)
