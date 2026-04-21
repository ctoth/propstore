"""Tests for the ASPIC+ bridge — claim graph to formal engine translation.

TDD Phase 0: All tests are RED (ImportError until aspic_bridge.py exists).

Property-based tests verify that the bridge translation (T1-T7) produces
well-formed ASPIC+ structures that satisfy the rationality postulates
from Modgil & Prakken 2018.

Concrete regression tests verify specific claim-graph scenarios.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from argumentation.aspic import (
    Literal,
    GroundAtom,
    ContrarinessFn,
    Rule,
    KnowledgeBase,
    ArgumentationSystem,
    PreferenceConfig,
    CSAF,
    PremiseArg,
    StrictArg,
    DefeasibleArg,
    build_arguments,
    compute_attacks,
    compute_defeats,
    conc,
    prem,
    sub,
    top_rule,
    def_rules,
    is_firm,
    is_strict,
    is_c_consistent,
    strict_closure,
    transposition_closure,
)
from propstore.core.justifications import CanonicalJustification
from argumentation.dung import (
    ArgumentationFramework,
    complete_extensions,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
    conflict_free,
)

# ── Bridge imports (RED until Phase 2) ─────────────────────────────

from propstore.aspic_bridge import (
    claims_to_literals,
    justifications_to_rules,
    stances_to_contrariness,
    claims_to_kb,
    build_preference_config,
    build_bridge_csaf,
    csaf_to_projection,
    build_aspic_projection,
)
from propstore.core.literal_keys import claim_key
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.structured_projection import (
    StructuredArgument,
    StructuredProjection,
    compute_structured_justified_arguments,
)


# ── Hypothesis strategies ──────────────────────────────────────────


def _make_claim(
    claim_id: str,
    *,
    concept_id: str | None = None,
    sample_size: int | None = None,
    uncertainty: float | None = None,
    confidence: float | None = None,
    premise_kind: str = "ordinary",
) -> dict:
    """Build a claim dict matching propstore's active claim format."""
    claim = {
        "id": claim_id,
        "concept_id": concept_id or f"concept_{claim_id}",
        "statement": f"Claim {claim_id}",
        "premise_kind": premise_kind,
    }
    if sample_size is not None:
        claim["sample_size"] = sample_size
    if uncertainty is not None:
        claim["uncertainty"] = uncertainty
    if confidence is not None:
        claim["confidence"] = confidence
    return claim


def _make_justification(
    justification_id: str,
    conclusion_claim_id: str,
    premise_claim_ids: tuple[str, ...] = (),
    rule_kind: str = "reported_claim",
    rule_strength: str = "defeasible",
) -> CanonicalJustification:
    """Build a CanonicalJustification with rule_strength."""
    return CanonicalJustification(
        justification_id=justification_id,
        conclusion_claim_id=conclusion_claim_id,
        premise_claim_ids=premise_claim_ids,
        rule_kind=rule_kind,
        rule_strength=rule_strength,
    )


@st.composite
def claim_ids(draw, min_claims=2, max_claims=5):
    """Generate a set of unique claim IDs."""
    n = draw(st.integers(min_value=min_claims, max_value=max_claims))
    return [f"claim_{i}" for i in range(n)]


@st.composite
def claim_graph(draw, min_claims=2, max_claims=5):
    """Generate a claim graph: claims, justifications, and stances.

    Produces a consistent set where:
    - Every claim has a reported_claim justification
    - Stances only reference existing claims
    - Justifications only reference existing claims
    """
    ids = draw(claim_ids(min_claims=min_claims, max_claims=max_claims))

    # Generate claims with varying metadata
    claims = []
    for cid in ids:
        premise_kind = draw(st.sampled_from(["ordinary", "necessary"]))
        sample_size = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=1000)))
        uncertainty = draw(st.one_of(st.none(), st.floats(min_value=0.01, max_value=1.0)))
        confidence = draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0)))
        claims.append(_make_claim(
            cid,
            sample_size=sample_size,
            uncertainty=uncertainty,
            confidence=confidence,
            premise_kind=premise_kind,
        ))

    # Every claim gets a reported_claim justification
    justifications = [
        _make_justification(
            f"reported:{cid}",
            cid,
            rule_kind="reported_claim",
        )
        for cid in ids
    ]

    # Generate some inference justifications (0 to len(ids)-1)
    n_inferences = draw(st.integers(min_value=0, max_value=max(0, len(ids) - 1)))
    for i in range(n_inferences):
        # Pick a conclusion and 1-2 premises (different from conclusion)
        conclusion = draw(st.sampled_from(ids))
        available_premises = [cid for cid in ids if cid != conclusion]
        if not available_premises:
            continue
        n_premises = draw(st.integers(min_value=1, max_value=min(2, len(available_premises))))
        premises = draw(
            st.lists(
                st.sampled_from(available_premises),
                min_size=n_premises,
                max_size=n_premises,
                unique=True,
            )
        )
        rule_strength = draw(st.sampled_from(["strict", "defeasible"]))
        rule_kind = draw(st.sampled_from([
            "support", "explanation", "empirical_support",
            "causal_explanation", "statistical_inference",
        ]))
        justifications.append(_make_justification(
            f"just_{i}:{','.join(premises)}->{conclusion}",
            conclusion,
            tuple(premises),
            rule_kind=rule_kind,
            rule_strength=rule_strength,
        ))

    # Generate attack stances (0 to len(ids)-1)
    n_attacks = draw(st.integers(min_value=0, max_value=max(0, len(ids) - 1)))
    stances = []
    for _ in range(n_attacks):
        source = draw(st.sampled_from(ids))
        target = draw(st.sampled_from([cid for cid in ids if cid != source]))
        stance_type = draw(st.sampled_from(["rebuts", "supersedes", "undermines"]))
        stances.append({
            "claim_id": source,
            "target_claim_id": target,
            "stance_type": stance_type,
        })

    return claims, justifications, stances


# ── T1: claims_to_literals ─────────────────────────────────────────


class TestClaimsToLiterals:
    """Property tests for T1: claims -> ASPIC+ literals."""

    @given(claim_graph())
    @settings(deadline=None)
    def test_every_claim_has_literal(self, graph):
        """Every claim_id maps to exactly one Literal."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        for claim in claims:
            assert claim_key(claim["id"]) in literals, (
                f"Claim {claim['id']} has no literal"
            )

    @given(claim_graph())
    @settings(deadline=None)
    def test_no_duplicate_atoms(self, graph):
        """No two claims share an atom."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        atoms = [lit.atom.predicate for lit in literals.values()]
        assert len(atoms) == len(set(atoms)), "Duplicate atoms in literals"

    @given(claim_graph())
    @settings(deadline=None)
    def test_literal_atom_is_claim_id(self, graph):
        """Each literal's atom equals its claim_id."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        for key, lit in literals.items():
            assert lit.atom.predicate == key.claim_id
            assert lit.negated is False

    @given(claim_graph())
    @settings(deadline=None)
    def test_language_closure(self, graph):
        """The language includes every literal's contrary.

        Modgil & Prakken 2018, Def 1 (p.8): L is closed under contrariness.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        # The full language L must include both the literal and its contrary
        all_lits = set(literals.values())
        all_lits.update(lit.contrary for lit in literals.values())
        for lit in list(all_lits):
            assert lit.contrary in all_lits, (
                f"{lit}.contrary = {lit.contrary} not in language"
            )


# ── T2: justifications_to_rules ────────────────────────────────────


class TestJustificationsToRules:
    """Property tests for T2: justifications -> ASPIC+ rules."""

    @given(claim_graph())
    @settings(deadline=None)
    def test_reported_claims_produce_no_rules(self, graph):
        """reported_claim justifications are premises, not rules."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        strict, defeasible = justifications_to_rules(justifications, literals)
        all_rule_names = {r.name for r in strict | defeasible if r.name}
        for j in justifications:
            if j.rule_kind == "reported_claim":
                assert j.justification_id not in all_rule_names, (
                    f"reported_claim {j.justification_id} produced a rule"
                )

    @given(claim_graph())
    @settings(deadline=None)
    def test_strict_rules_have_no_name(self, graph):
        """Strict rules have name=None (cannot be undercut).

        Modgil & Prakken 2018, Def 8c (p.11): undercutting targets
        n(r) which only exists for defeasible rules.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        strict, _defeasible = justifications_to_rules(justifications, literals)
        for rule in strict:
            assert rule.name is None, (
                f"Strict rule has name={rule.name}"
            )
            assert rule.kind == "strict"

    @given(claim_graph())
    @settings(deadline=None)
    def test_defeasible_rules_have_justification_id_as_name(self, graph):
        """Defeasible rules use justification_id as n(r).

        The naming function n maps defeasible rules to formulas
        enabling undercutting attacks. We use the justification ID.
        Modgil & Prakken 2018, Def 2 (p.8).
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        for rule in defeasible:
            assert rule.name is not None, "Defeasible rule has no name"
            assert rule.kind == "defeasible"

    @given(claim_graph())
    @settings(deadline=None)
    def test_rule_antecedents_match_premise_literals(self, graph):
        """Rule antecedents correspond to premise claim literals."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        strict, defeasible = justifications_to_rules(justifications, literals)
        all_rules = strict | defeasible
        inference_justs = [
            j for j in justifications
            if j.rule_kind != "reported_claim" and j.premise_claim_ids
        ]
        # Each inference justification should have a matching rule
        for j in inference_justs:
            expected_antes = tuple(literals[claim_key(pid)] for pid in j.premise_claim_ids)
            matching = [
                r for r in all_rules
                if set(r.antecedents) == set(expected_antes)
                and r.consequent == literals[claim_key(j.conclusion_claim_id)]
            ]
            assert len(matching) >= 1, (
                f"No rule found for justification {j.justification_id}"
            )


# ── T3: stances_to_contrariness ────────────────────────────────────


class TestStancesToContrariness:
    """Property tests for T3: attack stances -> contrariness function."""

    @given(claim_graph())
    @settings(deadline=None)
    def test_rebuts_produce_contradictories(self, graph):
        """rebuts stances produce symmetric contradictories.

        Modgil & Prakken 2018, Def 2 (p.8): contradictories are symmetric.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        cfn = stances_to_contrariness(stances, literals, defeasible)
        for stance in stances:
            if stance["stance_type"] == "rebuts":
                tgt = literals[claim_key(stance["target_claim_id"])]
                src = literals[claim_key(stance["claim_id"])]
                assert cfn.is_contradictory(src, tgt), (
                    f"{stance['stance_type']} {src}->{tgt} not contradictory"
                )
                assert cfn.is_contradictory(tgt, src), (
                    f"Contradictory not symmetric for {tgt}->{src}"
                )

    @given(claim_graph())
    @settings(deadline=None)
    def test_supersedes_produce_preference_sensitive_contradictions(self, graph):
        """supersedes stances produce preference-sensitive contradictions.

        Modgil & Prakken 2018, Def 9 (p.12): contradictory attacks are
        filtered by preferences, unlike directional contraries.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        cfn = stances_to_contrariness(stances, literals, defeasible)
        for stance in stances:
            if stance["stance_type"] == "supersedes":
                tgt = literals[claim_key(stance["target_claim_id"])]
                src = literals[claim_key(stance["claim_id"])]
                assert cfn.is_contradictory(src, tgt), (
                    f"supersedes {src}->{tgt} not in contrariness"
                )
                assert not cfn.is_contrary(src, tgt)

    @given(claim_graph())
    @settings(deadline=None)
    def test_no_self_contrariness(self, graph):
        """No literal is contrary or contradictory to itself.

        Modgil & Prakken 2018, Def 2 (p.8).
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        cfn = stances_to_contrariness(stances, literals, defeasible)
        for lit in literals.values():
            assert not cfn.is_contradictory(lit, lit)
            assert not cfn.is_contrary(lit, lit)

    @given(claim_graph())
    @settings(deadline=None)
    def test_contradictories_symmetric(self, graph):
        """All contradictory pairs are symmetric.

        Modgil & Prakken 2018, Def 2 (p.8).
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        cfn = stances_to_contrariness(stances, literals, defeasible)
        all_lits = list(literals.values())
        for a in all_lits:
            for b in all_lits:
                if cfn.is_contradictory(a, b):
                    assert cfn.is_contradictory(b, a), (
                        f"({a}, {b}) contradictory but ({b}, {a}) is not"
                    )

    def test_undercut_targets_only_named_defeasible_rule(self):
        claims = [
            _make_claim("support_a"),
            _make_claim("support_b"),
            _make_claim("target"),
            _make_claim("attacker"),
        ]
        justifications = [
            _make_justification("reported:support_a", "support_a"),
            _make_justification("reported:support_b", "support_b"),
            _make_justification("reported:target", "target"),
            _make_justification("reported:attacker", "attacker"),
            _make_justification(
                "supports:support_a->target",
                "target",
                ("support_a",),
                "supports",
                "defeasible",
            ),
            _make_justification(
                "supports:support_b->target",
                "target",
                ("support_b",),
                "supports",
                "defeasible",
            ),
        ]
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)

        cfn = stances_to_contrariness(
            [{
                "claim_id": "attacker",
                "target_claim_id": "target",
                "stance_type": "undercuts",
                "target_justification_id": "supports:support_a->target",
            }],
            literals,
            defeasible,
        )

        attacker = literals[claim_key("attacker")]
        rule_a = Literal(atom=GroundAtom("supports:support_a->target"), negated=False)
        rule_b = Literal(atom=GroundAtom("supports:support_b->target"), negated=False)

        assert cfn.is_contrary(attacker, rule_a)
        assert not cfn.is_contrary(attacker, rule_b)

    def test_undercut_without_rule_id_errors_when_multiple_target_rules_exist(self):
        claims = [
            _make_claim("support_a"),
            _make_claim("support_b"),
            _make_claim("target"),
            _make_claim("attacker"),
        ]
        justifications = [
            _make_justification("reported:support_a", "support_a"),
            _make_justification("reported:support_b", "support_b"),
            _make_justification("reported:target", "target"),
            _make_justification("reported:attacker", "attacker"),
            _make_justification(
                "supports:support_a->target",
                "target",
                ("support_a",),
                "supports",
                "defeasible",
            ),
            _make_justification(
                "supports:support_b->target",
                "target",
                ("support_b",),
                "supports",
                "defeasible",
            ),
        ]
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)

        with pytest.raises(ValueError, match="target_justification_id"):
            stances_to_contrariness(
                [{
                    "claim_id": "attacker",
                    "target_claim_id": "target",
                    "stance_type": "undercuts",
                }],
                literals,
                defeasible,
            )

    def test_undercut_without_rule_id_uses_only_rule_when_target_is_unambiguous(self):
        claims = [
            _make_claim("support_a"),
            _make_claim("target"),
            _make_claim("attacker"),
        ]
        justifications = [
            _make_justification("reported:support_a", "support_a"),
            _make_justification("reported:target", "target"),
            _make_justification("reported:attacker", "attacker"),
            _make_justification(
                "supports:support_a->target",
                "target",
                ("support_a",),
                "supports",
                "defeasible",
            ),
        ]
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)

        cfn = stances_to_contrariness(
            [{
                "claim_id": "attacker",
                "target_claim_id": "target",
                "stance_type": "undercuts",
            }],
            literals,
            defeasible,
        )

        attacker = literals[claim_key("attacker")]
        rule_a = Literal(atom=GroundAtom("supports:support_a->target"), negated=False)

        assert cfn.is_contrary(attacker, rule_a)


# ── T4: claims_to_kb ───────────────────────────────────────────────


class TestClaimsToKb:
    """Property tests for T4: claims -> ASPIC+ knowledge base."""

    @given(claim_graph())
    @settings(deadline=None)
    def test_kn_kp_disjoint(self, graph):
        """K_n and K_p are disjoint.

        Modgil & Prakken 2018, Def 4 (p.9): K = K_n ∪ K_p with K_n ∩ K_p = ∅.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        kb = claims_to_kb(claims, justifications, literals)
        assert not (kb.axioms & kb.premises), (
            f"K_n ∩ K_p = {kb.axioms & kb.premises}"
        )

    @given(claim_graph())
    @settings(deadline=None)
    def test_necessary_claims_in_kn(self, graph):
        """Claims with premise_kind='necessary' go to K_n."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        kb = claims_to_kb(claims, justifications, literals)
        for claim in claims:
            lit = literals[claim_key(claim["id"])]
            if claim.get("premise_kind") == "necessary":
                assert lit in kb.axioms, (
                    f"Necessary claim {claim['id']} not in K_n"
                )

    @given(claim_graph())
    @settings(deadline=None)
    def test_ordinary_claims_in_kp(self, graph):
        """Claims with premise_kind='ordinary' go to K_p."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        kb = claims_to_kb(claims, justifications, literals)
        for claim in claims:
            lit = literals[claim_key(claim["id"])]
            if claim.get("premise_kind", "ordinary") == "ordinary":
                assert lit in kb.premises, (
                    f"Ordinary claim {claim['id']} not in K_p"
                )

    @given(claim_graph())
    @settings(deadline=None)
    def test_kb_subset_of_language(self, graph):
        """K_n ∪ K_p ⊆ L.

        All premises are literals in the language.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        kb = claims_to_kb(claims, justifications, literals)
        all_lits = set(literals.values())
        assert kb.axioms <= all_lits, "K_n not subset of L"
        assert kb.premises <= all_lits, "K_p not subset of L"


# ── T5: build_preference_config ────────────────────────────────────


class TestPreferenceConfig:
    """Property tests for T5: claim metadata -> preference orderings."""

    @given(claim_graph())
    @settings(deadline=None)
    def test_premise_order_irreflexive(self, graph):
        """Premise ordering is irreflexive: no literal < itself.

        Modgil & Prakken 2018, Def 22 (p.22): strict partial order.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        pref = build_preference_config(claims, literals, defeasible)
        for weaker, stronger in pref.premise_order:
            assert weaker != stronger, (
                f"Premise order is reflexive: {weaker} < {weaker}"
            )

    @given(claim_graph())
    @settings(deadline=None)
    def test_premise_order_transitive(self, graph):
        """Premise ordering is transitive: if a < b and b < c then a < c.

        Modgil & Prakken 2018, Def 22 (p.22): strict partial order.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        pref = build_preference_config(claims, literals, defeasible)
        order = pref.premise_order
        for a, b in order:
            for c, d in order:
                if b == c:
                    assert (a, d) in order, (
                        f"Not transitive: {a} < {b} and {b} < {d} but {a} ≮ {d}"
                    )

    @given(claim_graph())
    @settings(deadline=None)
    def test_rule_order_irreflexive(self, graph):
        """Rule ordering is irreflexive.

        Modgil & Prakken 2018, Def 22 (p.22).
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        pref = build_preference_config(claims, literals, defeasible)
        for weaker, stronger in pref.rule_order:
            assert weaker != stronger, (
                f"Rule order is reflexive: {weaker} < {weaker}"
            )

    def test_grounded_rule_superiority_reaches_preference_config(self):
        """Rule-file superiority becomes ASPIC+ ``rule_order``.

        The rule-file surface uses ``(superior, inferior)`` pairs as in
        Garcia & Simari's DeLP superiority relation; ASPIC+ stores
        ``(weaker, stronger)`` pairs in ``PreferenceConfig.rule_order``.
        """
        from propstore.families.documents.rules import (
            AtomDocument,
            RuleDocument,
            RuleSourceDocument,
            RulesFileDocument,
            TermDocument,
        )
        from quire.documents import LoadedDocument
        from propstore.rule_files import LoadedRuleFile

        variable = TermDocument(kind="var", name="X")
        generic = RuleDocument(
            id="r1",
            kind="defeasible",
            head=AtomDocument(predicate="flies", terms=(variable,)),
            body=(AtomDocument(predicate="bird", terms=(variable,)),),
        )
        specific = RuleDocument(
            id="r2",
            kind="defeasible",
            head=AtomDocument(predicate="flies", terms=(variable,), negated=True),
            body=(AtomDocument(predicate="penguin", terms=(variable,)),),
        )
        rule_file = LoadedRuleFile.from_loaded_document(
            LoadedDocument(
                filename="superiority.yaml",
                source_path=None,
                knowledge_root=None,
                document=RulesFileDocument(
                    source=RuleSourceDocument(paper="Garcia_2004_DefeasibleLogicProgramming"),
                    rules=(generic, specific),
                    superiority=(("r2", "r1"),),
                ),
            )
        )
        bundle = GroundedRulesBundle(
            source_rules=(rule_file,),
            source_facts=(),
            sections={
                "definitely": {
                    "bird": frozenset({("tweety",)}),
                    "penguin": frozenset({("tweety",)}),
                },
                "defeasibly": {},
                "not_defeasibly": {},
                "undecided": {},
            },
        )

        csaf = build_bridge_csaf([], [], [], bundle=bundle)

        rule_order_names = {
            (weaker.name, stronger.name)
            for weaker, stronger in csaf.pref.rule_order
        }
        assert any(
            weaker is not None
            and stronger is not None
            and weaker.startswith("r1#")
            and stronger.startswith("r2#")
            for weaker, stronger in rule_order_names
        )
        assert not any(
            weaker is not None
            and stronger is not None
            and weaker.startswith("r2#")
            and stronger.startswith("r1#")
            for weaker, stronger in rule_order_names
        )


# ── T6: build_bridge_csaf (the big integration) ───────────────────


class TestBuildBridgeCsaf:
    """Property tests for T6: full bridge producing a CSAF."""

    @given(claim_graph())
    @settings(deadline=None)
    def test_every_claim_literal_in_language(self, graph):
        """Every active claim appears as a Literal in the CSAF language."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        literals = claims_to_literals(claims)
        for claim in claims:
            lit = literals[claim_key(claim["id"])]
            assert lit in csaf.system.language, (
                f"Claim {claim['id']} literal not in CSAF language"
            )

    @given(claim_graph())
    @settings(deadline=None)
    def test_no_attacks_means_no_defeats(self, graph):
        """If no attack stances, there should be no defeats."""
        claims, justifications, _stances = graph
        # Pass empty stances
        csaf = build_bridge_csaf(claims, justifications, [], bundle=GroundedRulesBundle.empty())
        assert len(csaf.defeats) == 0, (
            f"Got {len(csaf.defeats)} defeats with no attack stances"
        )

    @given(claim_graph())
    @settings(deadline=None)
    def test_no_attacks_all_claims_justified(self, graph):
        """With no attacks, all claims survive in grounded extension."""
        claims, justifications, _stances = graph
        csaf = build_bridge_csaf(claims, justifications, [], bundle=GroundedRulesBundle.empty())
        grounded = grounded_extension(csaf.framework)
        # Every reported claim should have an argument in the grounded extension
        reported_claim_ids = {
            j.conclusion_claim_id for j in justifications
            if j.rule_kind == "reported_claim"
        }
        justified_claim_ids = set()
        for arg_id in grounded:
            arg = csaf.id_to_arg[arg_id]
            c = conc(arg)
            if c.atom.predicate in reported_claim_ids:
                justified_claim_ids.add(c.atom.predicate)
        assert reported_claim_ids <= justified_claim_ids, (
            f"Claims without attack not all justified: "
            f"missing {reported_claim_ids - justified_claim_ids}"
        )

    @given(claim_graph())
    @settings(deadline=None)
    def test_framework_is_valid_dung_af(self, graph):
        """The CSAF's framework is a well-formed Dung AF."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        af = csaf.framework
        # All defeat endpoints are valid arguments
        for attacker, target in af.defeats:
            assert attacker in af.arguments, f"Defeat attacker {attacker} not in arguments"
            assert target in af.arguments, f"Defeat target {target} not in arguments"
        # All attack endpoints are valid arguments
        if af.attacks is not None:
            for attacker, target in af.attacks:
                assert attacker in af.arguments
                assert target in af.arguments
        # Defeats ⊆ attacks (every defeat came from an attack)
        if af.attacks is not None:
            assert af.defeats <= af.attacks, "Defeats not subset of attacks"


# ── Rationality postulates via bridge ──────────────────────────────


class TestBridgeRationalityPostulates:
    """The crown jewel: rationality postulates hold on bridge output.

    If the bridge produces a well-formed c-SAF, the existing ASPIC+
    engine guarantees all 8 rationality postulates (Modgil & Prakken
    2018, Thms 12-15, Def 18). So the bridge property test is:
    the bridge always produces output where these hold.

    These mirror TestRationalityPostulates in test_aspic.py but use
    bridge-constructed CSAFs from claim graphs.
    """

    @given(claim_graph())
    @settings(deadline=None, max_examples=25)
    def test_sub_argument_closure(self, graph):
        """Postulate 1 — Sub-argument closure (Thm 12, p.18).

        If A is in a complete extension E and A' in Sub(A),
        then A' is also in E.
        """
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        for ext_ids in complete_extensions(csaf.framework):
            for aid in ext_ids:
                arg = csaf.id_to_arg[aid]
                for sub_arg in sub(arg):
                    assert csaf.arg_to_id[sub_arg] in ext_ids, (
                        f"Sub-argument of {aid} not in extension"
                    )

    @given(claim_graph())
    @settings(deadline=None, max_examples=25)
    def test_direct_consistency(self, graph):
        """Postulate 3 — Direct consistency (Thm 14, p.18).

        No two conclusions in a complete extension are contraries
        or contradictories.

        Thm 14 requires axiom consistency (Def 12, p.13): the strict
        closure of K_n must not contain contraries/contradictories.
        """
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        # Postulate only holds for axiom-consistent c-SAFs (Def 12)
        assume(is_c_consistent(
            csaf.kb.axioms | csaf.kb.premises,
            csaf.system.strict_rules,
            csaf.system.contrariness,
        ))
        for ext_ids in complete_extensions(csaf.framework):
            conclusions = [conc(csaf.id_to_arg[aid]) for aid in ext_ids]
            for i, c1 in enumerate(conclusions):
                for c2 in conclusions[i + 1:]:
                    assert not csaf.system.contrariness.is_contradictory(c1, c2), (
                        f"Direct inconsistency: {c1} and {c2}"
                    )
                    assert not csaf.system.contrariness.is_contrary(c1, c2), (
                        f"Direct inconsistency: {c1} contrary of {c2}"
                    )

    @given(claim_graph())
    @settings(deadline=None, max_examples=25)
    def test_attack_based_conflict_free(self, graph):
        """Postulate 7 — Attack-based conflict-free (Def 14, p.14).

        Every complete extension is conflict-free w.r.t. attacks.
        """
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        if csaf.framework.attacks is None:
            return  # no attacks to check
        for ext_ids in complete_extensions(csaf.framework):
            assert conflict_free(ext_ids, csaf.framework.attacks), (
                f"Extension not attack-conflict-free"
            )

    @given(claim_graph())
    @settings(deadline=None)
    def test_undercutting_always_defeats(self, graph):
        """Postulate 6 — Undercutting always defeats (Def 9, p.12)."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        for atk in csaf.attacks:
            if atk.kind == "undercutting":
                pair = (csaf.arg_to_id[atk.attacker], csaf.arg_to_id[atk.target])
                assert pair in csaf.framework.defeats, (
                    f"Undercutting attack not a defeat"
                )

    @given(claim_graph())
    @settings(deadline=None)
    def test_firm_strict_in_every_complete(self, graph):
        """Postulate 5 — Firm+strict in every complete extension (Def 18)."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        firm_strict_ids = {
            csaf.arg_to_id[a] for a in csaf.arguments
            if is_firm(a) and is_strict(a)
        }
        for ext_ids in complete_extensions(csaf.framework):
            assert firm_strict_ids <= ext_ids, (
                f"Firm+strict args not in complete extension: "
                f"missing {firm_strict_ids - ext_ids}"
            )


# ── T7: csaf_to_projection ────────────────────────────────────────


class TestCsafToProjection:
    """Property tests for T7: CSAF -> StructuredProjection."""

    @given(claim_graph(max_claims=4))
    @settings(deadline=None, max_examples=50)
    def test_projection_arguments_preserve_claim_or_canonical_conclusion_identity(self, graph):
        """Projected arguments must have a stable identity surface.

        Claim-backed arguments map to authored claim ids. Grounded-only
        arguments may have ``claim_id=None`` but must expose a canonical
        ``conclusion_key`` and dependency claim ids that stay within the
        authored claim set.
        """
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        projection = csaf_to_projection(csaf, claims)
        claim_ids = {c["id"] for c in claims}
        for arg in projection.arguments:
            assert arg.conclusion_key
            if arg.claim_id is not None:
                assert arg.claim_id in claim_ids, (
                    f"Argument {arg.arg_id} maps to unknown claim {arg.claim_id}"
                )
            for dependency_claim_id in arg.dependency_claim_ids:
                assert dependency_claim_id in claim_ids, (
                    f"Argument {arg.arg_id} depends on unknown claim {dependency_claim_id}"
                )

    @given(claim_graph(max_claims=4))
    @settings(deadline=None, max_examples=50)
    def test_justified_claims_subset_of_active(self, graph):
        """Justified claims are a subset of active claims."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        projection = csaf_to_projection(csaf, claims)
        # Use compute_structured_justified_arguments which handles hybrid AFs
        grounded = compute_structured_justified_arguments(projection, semantics="grounded")
        claim_ids = {c["id"] for c in claims}
        for arg_id in grounded:
            if arg_id in projection.argument_to_claim_id:
                cid = projection.argument_to_claim_id[arg_id]
                assert cid in claim_ids, (
                    f"Justified claim {cid} not in active claims"
                )

    @given(claim_graph(max_claims=4))
    @settings(deadline=None, max_examples=50)
    def test_projection_framework_matches_csaf(self, graph):
        """The projection's Dung AF is derived from the CSAF."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        projection = csaf_to_projection(csaf, claims)
        # The projection framework should be a valid AF
        af = projection.framework
        for attacker, target in af.defeats:
            assert attacker in af.arguments
            assert target in af.arguments


# ── Concrete regression tests ──────────────────────────────────────


class TestBridgeConcrete:
    """Hand-constructed claim-graph scenarios."""

    def test_two_claims_rebut_stronger_wins(self):
        """Claim A rebuts claim B. A has higher confidence. A wins."""
        claims = [
            _make_claim("A", confidence=0.9, sample_size=100),
            _make_claim("B", confidence=0.3, sample_size=10),
        ]
        justifications = [
            _make_justification("reported:A", "A"),
            _make_justification("reported:B", "B"),
        ]
        stances = [
            {"claim_id": "A", "target_claim_id": "B", "stance_type": "rebuts"},
        ]
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom.predicate for aid in grounded}
        assert "A" in justified_atoms, "Stronger claim A should be justified"
        assert "B" not in justified_atoms, "Weaker claim B should be defeated"

    def test_strict_inference_not_undercut(self):
        """A strict justification cannot be undercut.

        Modgil & Prakken 2018, Def 8c (p.11): undercutting targets
        n(r) which only exists for defeasible rules.
        """
        claims = [
            _make_claim("premise", premise_kind="necessary"),
            _make_claim("derived"),
            _make_claim("attacker"),
        ]
        justifications = [
            _make_justification("reported:premise", "premise"),
            _make_justification("reported:derived", "derived"),
            _make_justification("reported:attacker", "attacker"),
            # Strict rule: premise -> derived
            _make_justification(
                "strict:premise->derived", "derived",
                ("premise",), "definition_application", "strict",
            ),
        ]
        stances = [
            # attacker tries to undercut the strict inference
            {"claim_id": "attacker", "target_claim_id": "derived", "stance_type": "undercuts"},
        ]
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom.predicate for aid in grounded}
        # derived should survive — strict rules can't be undercut
        assert "derived" in justified_atoms, (
            "Strict inference should not be undercut"
        )

    def test_necessary_premise_not_undermined(self):
        """A necessary premise (K_n) cannot be undermined.

        Modgil & Prakken 2018, Def 8a (p.11): undermining only
        targets ordinary premises (K_p), not axioms (K_n).
        """
        claims = [
            _make_claim("axiom", premise_kind="necessary"),
            _make_claim("attacker"),
        ]
        justifications = [
            _make_justification("reported:axiom", "axiom"),
            _make_justification("reported:attacker", "attacker"),
        ]
        stances = [
            {"claim_id": "attacker", "target_claim_id": "axiom", "stance_type": "undermines"},
        ]
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom.predicate for aid in grounded}
        assert "axiom" in justified_atoms, (
            "Axiom premise should not be undermined"
        )

    def test_support_chain_with_attack(self):
        """A supports B via defeasible rule. C rebuts B.

        Under last-link elitist preference (Modgil & Prakken 2018,
        Def 20), the defeasible argument for B (from A) has
        LastDefRules={rule} while C's premise argument has
        LastDefRules={}. With no rule ordering these are incomparable,
        so both attacks succeed as defeats — creating mutual defeat
        between the defeasible B-arg and C's premise arg.

        A survives because it is not attacked. The grounded extension
        is conservative: mutual defeat leaves both out.

        Page-image grounding:
        papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png
        papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png
        papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png
        """
        claims = [
            _make_claim("A", confidence=0.5),
            _make_claim("B", confidence=0.5),
            _make_claim("C", confidence=0.9, sample_size=200),
        ]
        justifications = [
            _make_justification("reported:A", "A"),
            _make_justification("reported:B", "B"),
            _make_justification("reported:C", "C"),
            _make_justification(
                "just:A->B", "B", ("A",),
                "empirical_support", "defeasible",
            ),
        ]
        stances = [
            {"claim_id": "C", "target_claim_id": "B", "stance_type": "rebuts"},
        ]
        csaf = build_bridge_csaf(claims, justifications, stances, bundle=GroundedRulesBundle.empty())
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom.predicate for aid in grounded}
        assert "A" in justified_atoms, "A should survive (not attacked)"
        # Under last-link with no rule ordering, the defeasible arg for B
        # and C's premise arg are in mutual defeat — grounded is conservative.
        # C's premise-only argument IS stronger (B < C in premise_order),
        # but the defeasible arg for B creates an incomparable attack.
        # Both B and C may be excluded from the grounded extension.
        # The key invariant: A is safe regardless.
        assert "B" not in justified_atoms or "C" not in justified_atoms, (
            "B and C are contradictory — at most one can be justified"
        )

    def test_no_stances_all_survive(self):
        """With no attack stances, all claims are justified."""
        claims = [
            _make_claim("X"),
            _make_claim("Y"),
            _make_claim("Z"),
        ]
        justifications = [
            _make_justification("reported:X", "X"),
            _make_justification("reported:Y", "Y"),
            _make_justification("reported:Z", "Z"),
        ]
        csaf = build_bridge_csaf(claims, justifications, [], bundle=GroundedRulesBundle.empty())
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom.predicate for aid in grounded}
        assert justified_atoms >= {"X", "Y", "Z"}, (
            f"All claims should survive, got {justified_atoms}"
        )


# ── Phase 3: build_aspic_projection entry point ──────────────────


class _MiniStore:
    """Minimal WorldStore-compatible mock for build_aspic_projection tests.

    Follows the _ProjectionStore pattern from test_structured_projection.py.
    """

    def __init__(
        self,
        *,
        claims: list[dict],
        stances: list[dict] | None = None,
    ) -> None:
        self._claims = list(claims)
        self._stances = list(stances or [])

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        return [
            stance
            for stance in self._stances
            if stance["claim_id"] in claim_ids and stance["target_claim_id"] in claim_ids
        ]

    def has_table(self, name: str) -> bool:
        return name == "relation_edge"


class TestBuildAspicProjection:
    """Tests for the build_aspic_projection entry point (Phase 3).

    build_aspic_projection is a drop-in replacement for
    build_structured_projection that routes through the ASPIC+ bridge
    (T1-T7) instead of the legacy structured_argument path.
    """

    def test_returns_structured_projection(self):
        """build_aspic_projection returns a StructuredProjection."""
        claims = [
            _make_claim("A"),
            _make_claim("B"),
        ]
        store = _MiniStore(claims=claims)
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty())
        assert isinstance(projection, StructuredProjection)

    def test_projection_has_required_fields(self):
        """Projection has .arguments, .framework, .claim_to_argument_ids, .argument_to_claim_id."""
        claims = [_make_claim("X")]
        store = _MiniStore(claims=claims)
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty())

        assert hasattr(projection, "arguments")
        assert hasattr(projection, "framework")
        assert hasattr(projection, "claim_to_argument_ids")
        assert hasattr(projection, "argument_to_claim_id")
        assert isinstance(projection.arguments, tuple)
        assert isinstance(projection.framework, ArgumentationFramework)
        assert isinstance(projection.claim_to_argument_ids, dict)
        assert isinstance(projection.argument_to_claim_id, dict)

    def test_arguments_are_structured_arguments(self):
        """Every element of .arguments is a StructuredArgument."""
        claims = [_make_claim("P"), _make_claim("Q")]
        store = _MiniStore(claims=claims)
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty())

        for arg in projection.arguments:
            assert isinstance(arg, StructuredArgument)

    def test_no_stances_all_claims_survive(self):
        """With no attack stances, grounded extension includes all claims."""
        claims = [
            _make_claim("X"),
            _make_claim("Y"),
            _make_claim("Z"),
        ]
        store = _MiniStore(claims=claims)
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty())
        grounded = compute_structured_justified_arguments(projection, semantics="grounded")

        justified_claim_ids = {
            projection.argument_to_claim_id[aid]
            for aid in grounded
            if aid in projection.argument_to_claim_id
        }
        assert justified_claim_ids >= {"X", "Y", "Z"}, (
            f"All claims should survive, got {justified_claim_ids}"
        )

    def test_rebut_stronger_wins(self):
        """With a rebut stance, the stronger claim wins."""
        claims = [
            _make_claim("strong", confidence=0.9, sample_size=100),
            _make_claim("weak", confidence=0.3, sample_size=10),
        ]
        store = _MiniStore(
            claims=claims,
            stances=[
                {"claim_id": "strong", "target_claim_id": "weak", "stance_type": "rebuts"},
            ],
        )
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty())
        grounded = compute_structured_justified_arguments(projection, semantics="grounded")

        justified_claim_ids = {
            projection.argument_to_claim_id[aid]
            for aid in grounded
            if aid in projection.argument_to_claim_id
        }
        assert "strong" in justified_claim_ids, "Stronger claim should be justified"
        assert "weak" not in justified_claim_ids, "Weaker claim should be defeated"

    def test_claim_to_argument_ids_covers_all_claims(self):
        """Every active claim has at least one argument mapped."""
        claims = [_make_claim("A"), _make_claim("B")]
        store = _MiniStore(claims=claims)
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty())

        for claim in claims:
            cid = claim["id"]
            assert cid in projection.claim_to_argument_ids, (
                f"Claim {cid} missing from claim_to_argument_ids"
            )
            assert len(projection.claim_to_argument_ids[cid]) >= 1

    def test_argument_to_claim_id_inverse(self):
        """argument_to_claim_id is consistent with claim_to_argument_ids."""
        claims = [_make_claim("A"), _make_claim("B")]
        store = _MiniStore(claims=claims)
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty())

        for cid, arg_ids in projection.claim_to_argument_ids.items():
            for aid in arg_ids:
                assert projection.argument_to_claim_id[aid] == cid

    def test_accepts_support_metadata(self):
        """build_aspic_projection accepts support_metadata kwarg."""
        from propstore.core.labels import Label, SupportQuality
        claims = [_make_claim("A")]
        store = _MiniStore(claims=claims)
        metadata = {"A": (Label.empty(), SupportQuality.EXACT)}
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty(), support_metadata=metadata)

        assert isinstance(projection, StructuredProjection)
        # The metadata should be applied to the argument
        a_args = [arg for arg in projection.arguments if arg.claim_id == "A"]
        assert len(a_args) >= 1
        assert a_args[0].label == Label.empty()
        assert a_args[0].support_quality == SupportQuality.EXACT

    def test_accepts_active_graph_none(self):
        """build_aspic_projection works with active_graph=None."""
        claims = [_make_claim("A")]
        store = _MiniStore(claims=claims)
        projection = build_aspic_projection(store, claims, bundle=GroundedRulesBundle.empty(), active_graph=None)
        assert isinstance(projection, StructuredProjection)


# ── Phase 4: Backend integration tests ───────────────────────────────


class TestAspicBackendIntegration:
    """Verify ASPIC backend is wired into resolution, worldline, and CLI."""

    def test_reasoning_backend_has_aspic(self):
        """ReasoningBackend.ASPIC exists and equals 'aspic'."""
        from propstore.world.types import ReasoningBackend

        assert hasattr(ReasoningBackend, "ASPIC")
        assert ReasoningBackend.ASPIC == "aspic"
        assert ReasoningBackend.ASPIC.value == "aspic"

    def test_worldline_policy_accepts_aspic_backend(self):
        """A worldline policy with reasoning_backend: 'aspic' is valid."""
        from propstore.world.types import ReasoningBackend
        from propstore.worldline import WorldlineDefinition

        worldline = WorldlineDefinition.from_dict({
            "id": "aspic_backend",
            "targets": ["force"],
            "policy": {"reasoning_backend": "aspic"},
        })

        assert worldline.policy.reasoning_backend == ReasoningBackend.ASPIC


class TestComparisonLinkThreading:
    """Regression: comparison/link params must reach PreferenceConfig."""

    def test_democratic_weakest_reaches_preference_config(self):
        """build_bridge_csaf with comparison='democratic', link='weakest'
        must produce a CSAF whose PreferenceConfig reflects those values.

        Bug: aspic_bridge.py hardcodes elitist/last in build_preference_config,
        ignoring the caller's requested comparison/link.

        Lifting/link choices are semantic inputs, not bridge-local defaults:
        papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png
        papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png
        """
        claims = [_make_claim("cmp_A"), _make_claim("cmp_B")]
        justifications = [
            CanonicalJustification(
                justification_id="reported:cmp_A",
                conclusion_claim_id="cmp_A",
                rule_kind="reported_claim",
            ),
            CanonicalJustification(
                justification_id="reported:cmp_B",
                conclusion_claim_id="cmp_B",
                rule_kind="reported_claim",
            ),
        ]
        stances: list[dict] = []

        csaf = build_bridge_csaf(
            claims, justifications, stances,
            bundle=GroundedRulesBundle.empty(),
            comparison="democratic", link="weakest",
        )

        assert csaf.pref.comparison == "democratic", (
            f"Expected comparison='democratic', got '{csaf.pref.comparison}'. "
            f"build_preference_config hardcodes 'elitist' instead of threading the param."
        )
        assert csaf.pref.link == "weakest", (
            f"Expected link='weakest', got '{csaf.pref.link}'. "
            f"build_preference_config hardcodes 'last' instead of threading the param."
        )
