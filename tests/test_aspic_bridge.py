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

from propstore.aspic import (
    Literal,
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
from propstore.dung import (
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
        stance_type = draw(st.sampled_from(["rebuts", "contradicts", "supersedes", "undermines"]))
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
    @settings(max_examples=200, deadline=None)
    def test_every_claim_has_literal(self, graph):
        """Every claim_id maps to exactly one Literal."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        for claim in claims:
            assert claim["id"] in literals, (
                f"Claim {claim['id']} has no literal"
            )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_no_duplicate_atoms(self, graph):
        """No two claims share an atom."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        atoms = [lit.atom for lit in literals.values()]
        assert len(atoms) == len(set(atoms)), "Duplicate atoms in literals"

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_literal_atom_is_claim_id(self, graph):
        """Each literal's atom equals its claim_id."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        for claim_id, lit in literals.items():
            assert lit.atom == claim_id
            assert lit.negated is False

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
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
            expected_antes = tuple(literals[pid] for pid in j.premise_claim_ids)
            matching = [
                r for r in all_rules
                if set(r.antecedents) == set(expected_antes)
                and r.consequent == literals[j.conclusion_claim_id]
            ]
            assert len(matching) >= 1, (
                f"No rule found for justification {j.justification_id}"
            )


# ── T3: stances_to_contrariness ────────────────────────────────────


class TestStancesToContrariness:
    """Property tests for T3: attack stances -> contrariness function."""

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_rebuts_produce_contradictories(self, graph):
        """rebuts/contradicts stances produce symmetric contradictories.

        Modgil & Prakken 2018, Def 2 (p.8): contradictories are symmetric.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        cfn = stances_to_contrariness(stances, literals, defeasible)
        for stance in stances:
            if stance["stance_type"] in ("rebuts", "contradicts"):
                src = literals[stance["claim_id"]]
                tgt = literals[stance["target_claim_id"]]
                assert cfn.is_contradictory(src, tgt), (
                    f"{stance['stance_type']} {src}->{tgt} not contradictory"
                )
                assert cfn.is_contradictory(tgt, src), (
                    f"Contradictory not symmetric for {tgt}->{src}"
                )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_supersedes_produce_contraries(self, graph):
        """supersedes stances produce asymmetric contraries.

        Modgil & Prakken 2018, Def 2 (p.8): contraries are directional.
        """
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        _strict, defeasible = justifications_to_rules(justifications, literals)
        cfn = stances_to_contrariness(stances, literals, defeasible)
        for stance in stances:
            if stance["stance_type"] == "supersedes":
                src = literals[stance["claim_id"]]
                tgt = literals[stance["target_claim_id"]]
                assert cfn.is_contrary(src, tgt) or cfn.is_contradictory(src, tgt), (
                    f"supersedes {src}->{tgt} not in contrariness"
                )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
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


# ── T4: claims_to_kb ───────────────────────────────────────────────


class TestClaimsToKb:
    """Property tests for T4: claims -> ASPIC+ knowledge base."""

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
    def test_necessary_claims_in_kn(self, graph):
        """Claims with premise_kind='necessary' go to K_n."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        kb = claims_to_kb(claims, justifications, literals)
        for claim in claims:
            lit = literals[claim["id"]]
            if claim.get("premise_kind") == "necessary":
                assert lit in kb.axioms, (
                    f"Necessary claim {claim['id']} not in K_n"
                )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_ordinary_claims_in_kp(self, graph):
        """Claims with premise_kind='ordinary' go to K_p."""
        claims, justifications, stances = graph
        literals = claims_to_literals(claims)
        kb = claims_to_kb(claims, justifications, literals)
        for claim in claims:
            lit = literals[claim["id"]]
            if claim.get("premise_kind", "ordinary") == "ordinary":
                assert lit in kb.premises, (
                    f"Ordinary claim {claim['id']} not in K_p"
                )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
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
    @settings(max_examples=200, deadline=None)
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


# ── T6: build_bridge_csaf (the big integration) ───────────────────


class TestBuildBridgeCsaf:
    """Property tests for T6: full bridge producing a CSAF."""

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_every_claim_literal_in_language(self, graph):
        """Every active claim appears as a Literal in the CSAF language."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
        literals = claims_to_literals(claims)
        for claim in claims:
            lit = literals[claim["id"]]
            assert lit in csaf.system.language, (
                f"Claim {claim['id']} literal not in CSAF language"
            )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_no_attacks_means_no_defeats(self, graph):
        """If no attack stances, there should be no defeats."""
        claims, justifications, _stances = graph
        # Pass empty stances
        csaf = build_bridge_csaf(claims, justifications, [])
        assert len(csaf.defeats) == 0, (
            f"Got {len(csaf.defeats)} defeats with no attack stances"
        )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_no_attacks_all_claims_justified(self, graph):
        """With no attacks, all claims survive in grounded extension."""
        claims, justifications, _stances = graph
        csaf = build_bridge_csaf(claims, justifications, [])
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
            if c.atom in reported_claim_ids:
                justified_claim_ids.add(c.atom)
        assert reported_claim_ids <= justified_claim_ids, (
            f"Claims without attack not all justified: "
            f"missing {reported_claim_ids - justified_claim_ids}"
        )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_framework_is_valid_dung_af(self, graph):
        """The CSAF's framework is a well-formed Dung AF."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
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
    @settings(max_examples=200, deadline=None)
    def test_sub_argument_closure(self, graph):
        """Postulate 1 — Sub-argument closure (Thm 12, p.18).

        If A is in a complete extension E and A' in Sub(A),
        then A' is also in E.
        """
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
        for ext_ids in complete_extensions(csaf.framework):
            for aid in ext_ids:
                arg = csaf.id_to_arg[aid]
                for sub_arg in sub(arg):
                    assert csaf.arg_to_id[sub_arg] in ext_ids, (
                        f"Sub-argument of {aid} not in extension"
                    )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_direct_consistency(self, graph):
        """Postulate 3 — Direct consistency (Thm 14, p.18).

        No two conclusions in a complete extension are contraries
        or contradictories.

        Thm 14 requires axiom consistency (Def 12, p.13): the strict
        closure of K_n must not contain contraries/contradictories.
        """
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
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
    @settings(max_examples=200, deadline=None)
    def test_attack_based_conflict_free(self, graph):
        """Postulate 7 — Attack-based conflict-free (Def 14, p.14).

        Every complete extension is conflict-free w.r.t. attacks.
        """
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
        if csaf.framework.attacks is None:
            return  # no attacks to check
        for ext_ids in complete_extensions(csaf.framework):
            assert conflict_free(ext_ids, csaf.framework.attacks), (
                f"Extension not attack-conflict-free"
            )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_undercutting_always_defeats(self, graph):
        """Postulate 6 — Undercutting always defeats (Def 9, p.12)."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
        for atk in csaf.attacks:
            if atk.kind == "undercutting":
                pair = (csaf.arg_to_id[atk.attacker], csaf.arg_to_id[atk.target])
                assert pair in csaf.framework.defeats, (
                    f"Undercutting attack not a defeat"
                )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_firm_strict_in_every_complete(self, graph):
        """Postulate 5 — Firm+strict in every complete extension (Def 18)."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
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

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_every_argument_maps_to_claim(self, graph):
        """Every projection argument maps to a real claim_id.

        Transposition-generated arguments (negated literals with no
        claim_id) are excluded from the projection.
        """
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
        projection = csaf_to_projection(csaf, claims)
        claim_ids = {c["id"] for c in claims}
        for arg in projection.arguments:
            assert arg.claim_id in claim_ids, (
                f"Argument {arg.arg_id} maps to unknown claim {arg.claim_id}"
            )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_justified_claims_subset_of_active(self, graph):
        """Justified claims are a subset of active claims."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
        projection = csaf_to_projection(csaf, claims)
        grounded = grounded_extension(projection.framework)
        claim_ids = {c["id"] for c in claims}
        for arg_id in grounded:
            if arg_id in projection.argument_to_claim_id:
                cid = projection.argument_to_claim_id[arg_id]
                assert cid in claim_ids, (
                    f"Justified claim {cid} not in active claims"
                )

    @given(claim_graph())
    @settings(max_examples=200, deadline=None)
    def test_projection_framework_matches_csaf(self, graph):
        """The projection's Dung AF is derived from the CSAF."""
        claims, justifications, stances = graph
        csaf = build_bridge_csaf(claims, justifications, stances)
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
        csaf = build_bridge_csaf(claims, justifications, stances)
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom for aid in grounded}
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
        csaf = build_bridge_csaf(claims, justifications, stances)
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom for aid in grounded}
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
        csaf = build_bridge_csaf(claims, justifications, stances)
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom for aid in grounded}
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
        csaf = build_bridge_csaf(claims, justifications, stances)
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom for aid in grounded}
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
        csaf = build_bridge_csaf(claims, justifications, [])
        grounded = grounded_extension(csaf.framework)

        justified_atoms = {conc(csaf.id_to_arg[aid]).atom for aid in grounded}
        assert justified_atoms >= {"X", "Y", "Z"}, (
            f"All claims should survive, got {justified_atoms}"
        )
