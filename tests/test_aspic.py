"""Tests for ASPIC+ logical language, contrariness, rules, and transposition.

Property-based tests verify formal definitions from:
    Modgil, S. & Prakken, H. (2018). A general account of argumentation
    with preferences. Artificial Intelligence, 248, 51-104.
    - Def 1 (p.8): Logical language L
    - Def 2 (p.8): Contrariness function, contradictories vs contraries
    - Def 2 (p.8): Strict rules R_s, defeasible rules R_d, naming function n
    - Def 12 (p.13): Transposition closure for strict rules

    Prakken, H. (2010). An abstract framework for argumentation with
    structured arguments. Argument & Computation, 1(2), 93-124.
    - Def 3.1: Argumentation system tuple
    - Def 3.2: Contrariness — symmetric (contradictory) vs asymmetric (contrary)
    - Def 3.4 (p.47-48): Strict vs defeasible rules
    - Def 5.1 (p.141-142): Transposition of strict rules
    - Def 5.2: Closure under transposition

Concrete regression tests verify hand-constructed examples.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from propstore.aspic import (
    Literal, ContrarinessFn, Rule, transposition_closure,
    PremiseArg, StrictArg, DefeasibleArg, Argument,
    KnowledgeBase, ArgumentationSystem,
    build_arguments, conc, prem, sub, top_rule,
    def_rules, last_def_rules, prem_p, is_firm, is_strict,
)


# ── Hypothesis strategies ───────────────────────────────────────────


@st.composite
def logical_language(draw, max_atoms=4):
    """Generate a logical language L with contrariness function.

    Modgil & Prakken 2018, Defs 1-2 (p.8).
    L consists of atoms and their negations.
    Contradictory pairs: (p, ~p) are symmetric — if φ ∈ ¯ψ then ψ ∈ ¯φ.
    """
    pool = ["p", "q", "r", "s", "t"]
    # Draw 2-4 distinct atoms
    atoms = draw(
        st.lists(
            st.sampled_from(pool),
            min_size=2,
            max_size=max_atoms,
            unique=True,
        )
    )
    # Build literals: each atom and its negation
    literals = frozenset(
        Literal(atom=a, negated=n) for a in atoms for n in (False, True)
    )
    # Build contrariness function: each atom and its negation are contradictories
    contradictory_pairs = frozenset(
        (Literal(atom=a, negated=False), Literal(atom=a, negated=True))
        for a in atoms
    )
    cfn = ContrarinessFn(contradictories=contradictory_pairs)
    return literals, cfn


# ── Property tests ─────────────────────────────────────────────────


class TestLanguageProperties:
    """Property tests for logical language L.

    Every property cites the formal definition it verifies.
    """

    @given(logical_language())
    @settings(max_examples=200, deadline=None)
    def test_every_literal_has_negation_in_L(self, lang_cfn):
        """For every literal in L, its .contrary is also in L.

        Modgil & Prakken 2018, Def 1 (p.8): L is closed —
        every formula's contraries/contradictories are in L.
        """
        L, _cfn = lang_cfn
        for lit in L:
            assert lit.contrary in L, (
                f"{lit}.contrary = {lit.contrary} not in L"
            )

    @given(logical_language())
    @settings(max_examples=200, deadline=None)
    def test_contrary_is_involutory(self, lang_cfn):
        """For every literal a in L, a.contrary.contrary == a.

        Negation is an involution: applying it twice returns
        the original formula. Follows from the symmetric structure
        of contradictories (Modgil & Prakken 2018, Def 2, p.8).
        """
        L, _cfn = lang_cfn
        for lit in L:
            assert lit.contrary.contrary == lit, (
                f"{lit}.contrary.contrary = {lit.contrary.contrary} != {lit}"
            )

    @given(logical_language())
    @settings(max_examples=200, deadline=None)
    def test_contradictories_are_symmetric(self, lang_cfn):
        """If (a, b) is a contradictory pair, then (b, a) is also.

        Modgil & Prakken 2018, Def 2 (p.8): φ and ψ are contradictories
        iff φ ∈ ¯ψ AND ψ ∈ ¯φ (symmetric relation).
        Prakken 2010, Def 3.2: same symmetry condition.
        """
        L, cfn = lang_cfn
        for a in L:
            for b in L:
                if cfn.is_contradictory(a, b):
                    assert cfn.is_contradictory(b, a), (
                        f"({a}, {b}) contradictory but ({b}, {a}) is not"
                    )

    @given(logical_language())
    @settings(max_examples=200, deadline=None)
    def test_no_self_contrary(self, lang_cfn):
        """No literal is contrary or contradictory to itself.

        A formula cannot be its own contrary or contradictory —
        self-conflict is not permitted in a well-formed language.
        Modgil & Prakken 2018, Def 2 (p.8): contrariness maps
        formulas to *other* formulas.
        """
        L, cfn = lang_cfn
        for lit in L:
            assert not cfn.is_contrary(lit, lit), (
                f"{lit} is contrary to itself"
            )
            assert not cfn.is_contradictory(lit, lit), (
                f"{lit} is contradictory to itself"
            )

    @given(logical_language())
    @settings(max_examples=200, deadline=None)
    def test_language_nonempty(self, lang_cfn):
        """L has at least 2 literals (an atom and its negation).

        A language must contain at least one atom and its negation
        to support any argumentation. Follows from the strategy
        drawing min_size=2 atoms, each producing 2 literals.
        """
        L, _cfn = lang_cfn
        assert len(L) >= 2

    @given(logical_language())
    @settings(max_examples=200, deadline=None)
    def test_language_even_size(self, lang_cfn):
        """|L| is even: every atom has exactly one negation.

        Since L is built from atoms and their negations, each atom
        contributes exactly 2 literals. |L| = 2 * |atoms|.
        """
        L, _cfn = lang_cfn
        assert len(L) % 2 == 0, f"|L| = {len(L)} is odd"


# ── Concrete regression tests ──────────────────────────────────────


class TestLanguageConcrete:
    """Hand-constructed examples for verifying language properties."""

    def test_simple_two_atom_language(self):
        """Manually construct L = {p, ~p, q, ~q}.

        Contradictories: {(p, ~p), (~p, p), (q, ~q), (~q, q)}.
        Verifies all properties from TestLanguageProperties hold
        on a concrete, known-good instance.
        """
        p = Literal(atom="p", negated=False)
        not_p = Literal(atom="p", negated=True)
        q = Literal(atom="q", negated=False)
        not_q = Literal(atom="q", negated=True)

        L = frozenset({p, not_p, q, not_q})

        contradictory_pairs = frozenset({(p, not_p), (q, not_q)})
        cfn = ContrarinessFn(contradictories=contradictory_pairs)

        # Every literal's negation is in L
        for lit in L:
            assert lit.contrary in L

        # Involution
        for lit in L:
            assert lit.contrary.contrary == lit

        # Contradictories are symmetric
        assert cfn.is_contradictory(p, not_p)
        assert cfn.is_contradictory(not_p, p)
        assert cfn.is_contradictory(q, not_q)
        assert cfn.is_contradictory(not_q, q)

        # No self-contrary
        for lit in L:
            assert not cfn.is_contrary(lit, lit)
            assert not cfn.is_contradictory(lit, lit)

        # Non-empty and even
        assert len(L) == 4
        assert len(L) % 2 == 0

        # Cross-atom pairs are not contradictory
        assert not cfn.is_contradictory(p, q)
        assert not cfn.is_contradictory(p, not_q)
        assert not cfn.is_contradictory(not_p, q)
        assert not cfn.is_contradictory(not_p, not_q)


# ── Phase 2: Rule strategies ─────────────────────────────────────


@st.composite
def strict_rules(draw, language, contrariness, max_rules=4):
    """Generate strict rules over L with transposition closure.

    Modgil & Prakken 2018, Defs 2, 12 (pp.8, 13).
    Prakken 2010, Defs 3.4, 5.1-5.2 (pp.47-48, 141-142).

    1. Draw 0-max_rules seed rules with 1-2 antecedents from L, consequent from L.
    2. Filter: consequent not in antecedents.
    3. Compute transposition closure (calls transposition_closure which does not
       exist yet -- tests will fail with ImportError in red phase).
    4. Return the closed rule set.
    """
    L_list = sorted(language, key=repr)
    n_rules = draw(st.integers(min_value=0, max_value=max_rules))
    seed_rules: list[Rule] = []
    for _ in range(n_rules):
        n_ante = draw(st.integers(min_value=1, max_value=min(2, len(L_list))))
        antecedents = tuple(
            draw(st.sampled_from(L_list)) for _ in range(n_ante)
        )
        consequent = draw(st.sampled_from(L_list))
        # Filter: consequent must not appear in antecedents
        if consequent in antecedents:
            continue
        seed_rules.append(
            Rule(
                antecedents=antecedents,
                consequent=consequent,
                kind="strict",
                name=None,
            )
        )
    # Compute transposition closure — calls function that doesn't exist yet
    closed = transposition_closure(frozenset(seed_rules), language, contrariness)
    return closed


@st.composite
def defeasible_rules(draw, language, max_rules=4):
    """Generate defeasible rules with naming function.

    Modgil & Prakken 2018, Def 2 (p.8): each defeasible rule r has a
    name n(r) in L, enabling undercutting attacks on the inference step.

    Prakken 2010, Def 3.4 (p.47-48): defeasible rules use => (presumptive).

    Names are strings "d0", "d1", etc. — these are rule identifiers, not
    Literals. The name-Literals are created during argument construction
    in Phase 3.
    """
    L_list = sorted(language, key=repr)
    n_rules = draw(st.integers(min_value=0, max_value=max_rules))
    rules: list[Rule] = []
    for i in range(n_rules):
        n_ante = draw(st.integers(min_value=1, max_value=min(2, len(L_list))))
        antecedents = tuple(
            draw(st.sampled_from(L_list)) for _ in range(n_ante)
        )
        consequent = draw(st.sampled_from(L_list))
        # Filter: consequent must not appear in antecedents
        if consequent in antecedents:
            continue
        rules.append(
            Rule(
                antecedents=antecedents,
                consequent=consequent,
                kind="defeasible",
                name=f"d{i}",
            )
        )
    return frozenset(rules)


# ── Phase 2: Rule property tests ─────────────────────────────────


class TestRuleProperties:
    """Property tests for strict and defeasible rules.

    Verifies structural invariants of rules generated by the strategies.
    Modgil & Prakken 2018, Def 2 (p.8); Prakken 2010, Def 3.4 (p.47-48).
    """

    @given(logical_language().flatmap(
        lambda lc: st.tuples(
            st.just(lc),
            strict_rules(language=lc[0], contrariness=lc[1]),
        )
    ))
    @settings(max_examples=200, deadline=None)
    def test_strict_rules_all_strict(self, lc_rules):
        """Every rule from strict_rules() has kind == 'strict'.

        Modgil & Prakken 2018, Def 2 (p.8): R_s contains only strict rules.
        """
        (_L, _cfn), rules = lc_rules
        for r in rules:
            assert r.kind == "strict", f"Rule {r} has kind={r.kind}, expected 'strict'"

    @given(logical_language().flatmap(
        lambda lc: st.tuples(
            st.just(lc),
            defeasible_rules(language=lc[0]),
        )
    ))
    @settings(max_examples=200, deadline=None)
    def test_defeasible_rules_all_defeasible(self, lc_rules):
        """Every rule from defeasible_rules() has kind == 'defeasible'.

        Modgil & Prakken 2018, Def 2 (p.8): R_d contains only defeasible rules.
        """
        (_L, _cfn), rules = lc_rules
        for r in rules:
            assert r.kind == "defeasible", (
                f"Rule {r} has kind={r.kind}, expected 'defeasible'"
            )

    @given(logical_language().flatmap(
        lambda lc: st.tuples(
            st.just(lc),
            defeasible_rules(language=lc[0]),
        )
    ))
    @settings(max_examples=200, deadline=None)
    def test_defeasible_rules_all_named(self, lc_rules):
        """Every defeasible rule has name is not None.

        Modgil & Prakken 2018, Def 2 (p.8): the naming function n maps
        each defeasible rule to a name n(r), enabling undercutting attacks.
        """
        (_L, _cfn), rules = lc_rules
        for r in rules:
            assert r.name is not None, f"Defeasible rule {r} has no name"

    @given(logical_language().flatmap(
        lambda lc: st.tuples(
            st.just(lc),
            strict_rules(language=lc[0], contrariness=lc[1]),
            defeasible_rules(language=lc[0]),
        )
    ))
    @settings(max_examples=200, deadline=None)
    def test_rule_antecedents_in_language(self, lc_sr_dr):
        """All antecedents and consequents are in L.

        Modgil & Prakken 2018, Def 2 (p.8): rules are over the language L.
        Prakken 2010, Def 3.4 (p.47-48): antecedents and consequent in L.
        """
        (L, _cfn), s_rules, d_rules = lc_sr_dr
        for r in s_rules | d_rules:
            for ante in r.antecedents:
                assert ante in L, f"Antecedent {ante} of rule {r} not in L"
            assert r.consequent in L, f"Consequent {r.consequent} of rule {r} not in L"

    @given(logical_language().flatmap(
        lambda lc: st.tuples(
            st.just(lc),
            strict_rules(language=lc[0], contrariness=lc[1]),
            defeasible_rules(language=lc[0]),
        )
    ))
    @settings(max_examples=200, deadline=None)
    def test_consequent_not_in_antecedents(self, lc_sr_dr):
        """No rule has its consequent appearing in its antecedents.

        A rule phi_1, ..., phi_n -> psi must have psi not in {phi_1, ..., phi_n}.
        This is a well-formedness constraint: a rule cannot trivially conclude
        one of its own premises.
        """
        (L, _cfn), s_rules, d_rules = lc_sr_dr
        for r in s_rules | d_rules:
            assert r.consequent not in r.antecedents, (
                f"Rule {r} has consequent {r.consequent} in antecedents"
            )


class TestTranspositionClosure:
    """Property tests for transposition closure of strict rules.

    Modgil & Prakken 2018, Def 12 (p.13): if A1,...,An -> C is a strict
    rule, then for each i, A1,...,~C,...,An -> ~Ai must also be in R_s.

    Prakken 2010, Defs 5.1-5.2 (pp.141-142): transposition and closure.

    Theorem 6.10 (Prakken 2010): closure under transposition is REQUIRED
    for the rationality postulates to hold.
    """

    @given(logical_language().flatmap(
        lambda lc: st.tuples(
            st.just(lc),
            strict_rules(language=lc[0], contrariness=lc[1]),
        )
    ))
    @settings(max_examples=200, deadline=None)
    def test_transposition_closure_complete(self, lc_rules):
        """For every strict rule A1,...,An -> C, for every i, the transposed
        rule A1,...,~C,...,An -> ~Ai exists in R_s.

        Modgil & Prakken 2018, Def 12 (p.13).
        Prakken 2010, Def 5.1 (p.141-142): a transposition of
        phi_1,...,phi_n -> psi is phi_1,...,-psi,...,phi_n -> -phi_i.
        """
        (L, _cfn), rules = lc_rules
        for r in rules:
            for i, ante_i in enumerate(r.antecedents):
                # Build the transposed rule: replace antecedent i with ~C,
                # consequent becomes ~ante_i
                transposed_antes = list(r.antecedents)
                transposed_antes[i] = r.consequent.contrary
                transposed = Rule(
                    antecedents=tuple(transposed_antes),
                    consequent=ante_i.contrary,
                    kind="strict",
                    name=None,
                )
                assert transposed in rules, (
                    f"Transposition of {r} at position {i} missing: {transposed}"
                )

    @given(logical_language().flatmap(
        lambda lc: st.tuples(
            st.just(lc),
            strict_rules(language=lc[0], contrariness=lc[1]),
        )
    ))
    @settings(max_examples=200, deadline=None)
    def test_transposition_closure_idempotent(self, lc_rules):
        """Applying transposition_closure again produces no new rules.

        Prakken 2010, Def 5.2: Cl_{R_s}(R_s) is the smallest set closed
        under transposition. Applying closure to an already-closed set
        must be a fixed point.
        """
        (L, cfn), rules = lc_rules
        closed_again = transposition_closure(rules, L, cfn)
        assert closed_again == rules, (
            f"Closure not idempotent: {len(closed_again)} rules vs {len(rules)}"
        )

    @given(logical_language().flatmap(
        lambda lc: st.tuples(
            st.just(lc),
            strict_rules(language=lc[0], contrariness=lc[1]),
        )
    ))
    @settings(max_examples=200, deadline=None)
    def test_transposition_closure_preserves_kind(self, lc_rules):
        """All transposed rules have kind == 'strict'.

        Transposition applies only to strict rules and produces strict rules.
        Modgil & Prakken 2018, Def 12 (p.13): transposition is defined
        only for strict rules in R_s.
        """
        (_L, _cfn), rules = lc_rules
        for r in rules:
            assert r.kind == "strict", (
                f"Transposed rule {r} has kind={r.kind}, expected 'strict'"
            )

    def test_empty_rules_closure_is_empty(self):
        """Transposition closure of the empty set is the empty set.

        Trivial base case: no rules means no transpositions to generate.
        """
        L = frozenset({Literal("p"), Literal("p", negated=True)})
        cfn = ContrarinessFn(
            contradictories=frozenset({(Literal("p"), Literal("p", negated=True))})
        )
        result = transposition_closure(frozenset(), L, cfn)
        assert result == frozenset(), f"Expected empty set, got {result}"


class TestRuleConcrete:
    """Hand-constructed examples for verifying rule and transposition properties."""

    def test_married_bachelor_transposition(self):
        """Classic example: married -> ~bachelor transposes to bachelor -> ~married.

        Modgil & Prakken 2014, Example 4.4.
        Prakken 2010, Def 5.1 (p.141-142).

        Given strict rule: married -> ~bachelor
        Transposition must produce: bachelor -> ~married
        (Replace the single antecedent 'married' with ~(~bachelor) = bachelor,
         and the consequent becomes ~married.)
        """
        married = Literal("married")
        not_married = Literal("married", negated=True)
        bachelor = Literal("bachelor")
        not_bachelor = Literal("bachelor", negated=True)

        L = frozenset({married, not_married, bachelor, not_bachelor})
        cfn = ContrarinessFn(
            contradictories=frozenset({
                (married, not_married),
                (bachelor, not_bachelor),
            })
        )

        # Original rule: married -> ~bachelor
        original = Rule(
            antecedents=(married,),
            consequent=not_bachelor,
            kind="strict",
            name=None,
        )

        # Expected transposition: bachelor -> ~married
        # (ante[0]=married replaced by ~(~bachelor)=bachelor, consequent=~married)
        expected_transposition = Rule(
            antecedents=(bachelor,),
            consequent=not_married,
            kind="strict",
            name=None,
        )

        # Compute closure
        closed = transposition_closure(frozenset({original}), L, cfn)

        # Original must be preserved
        assert original in closed, "Original rule missing from closure"

        # Transposition must be present
        assert expected_transposition in closed, (
            f"Expected transposition {expected_transposition} not in closure: {closed}"
        )


# ── Phase 3: Knowledge base strategy ─────────────────────────────


@st.composite
def knowledge_base(draw, language, strict_rules, defeasible_rules):
    """Generate a knowledge base with non-triviality guarantee.

    Modgil & Prakken 2018, Def 4 (p.9): K = K_n ∪ K_p where
    K_n (axioms) are not attackable, K_p (ordinary premises) are attackable.

    Non-triviality: forces at least one rule's antecedents into K_p,
    ensuring at least one non-premise argument can be constructed.
    See reports/hypothesis-aspic-feasibility.md Section 3, Level 4.
    """
    L_list = sorted(language, key=repr)
    all_rules = list(strict_rules) + list(defeasible_rules)

    # Force at least one rule's antecedents into K_p for non-triviality
    forced_premises: frozenset[Literal] = frozenset()
    if all_rules:
        target = draw(st.sampled_from(all_rules))
        forced_premises = frozenset(target.antecedents)

    # Draw additional K_p members from L (up to 4 total)
    extra_kp = draw(
        st.frozensets(st.sampled_from(L_list), max_size=4)
    )
    K_p = forced_premises | extra_kp

    # Draw K_n members from L (up to 2), ensuring consistency
    # (no literal and its contrary both in K_n)
    K_n_candidates = draw(
        st.frozensets(st.sampled_from(L_list), max_size=2)
    )
    # Filter: no contradictory pair in K_n
    K_n = frozenset()
    for lit in K_n_candidates:
        if lit.contrary not in K_n:
            K_n = K_n | {lit}

    # Ensure K_n and K_p are disjoint
    K_n = K_n - K_p

    return KnowledgeBase(axioms=K_n, premises=K_p)


# ── Phase 3: Argument construction property tests ─────────────────


class TestArgumentConstructionProperties:
    """Property tests for recursive argument construction.

    Modgil & Prakken 2018, Def 5 (pp.9-10): arguments are constructed
    recursively from premises and rules, with computed properties
    Prem(A), Conc(A), Sub(A), DefRules(A), TopRule(A), LastDefRules(A).

    Prakken 2010, Def 3.6 (p.36): argument construction.
    """

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_premise_arg_conclusion_equals_premise(self, data):
        """For every PremiseArg A, conc(A) == A.premise.

        Modgil & Prakken 2018, Def 5 clause 1 (p.9): if phi in K
        then Conc(A) = phi.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            if isinstance(arg, PremiseArg):
                assert conc(arg) == arg.premise, (
                    f"PremiseArg conclusion {conc(arg)} != premise {arg.premise}"
                )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_sub_contains_self(self, data):
        """For every argument A, A in sub(A).

        Modgil & Prakken 2018, Def 5 (p.9-10): Sub(A) always
        includes A itself.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            assert arg in sub(arg), (
                f"Argument {arg} not in its own sub-arguments"
            )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_sub_transitively_closed(self, data):
        """For every A, for every B in sub(A), sub(B) ⊆ sub(A).

        Modgil & Prakken 2018, Def 5 (p.9-10): Sub is defined
        recursively as Sub(A1) ∪ ... ∪ Sub(An) ∪ {A}, which
        makes it transitively closed by construction.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            for b in sub(arg):
                assert sub(b) <= sub(arg), (
                    f"sub({b}) not subset of sub({arg})"
                )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_prem_subset_of_kb(self, data):
        """For every argument A, prem(A) ⊆ K_n ∪ K_p.

        Modgil & Prakken 2018, Def 5 (p.9): premises come from K.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        all_kb = kb.axioms | kb.premises
        for arg in arguments:
            assert prem(arg) <= all_kb, (
                f"prem({arg}) = {prem(arg)} not subset of K = {all_kb}"
            )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_conc_in_language(self, data):
        """For every argument A, conc(A) in L.

        Modgil & Prakken 2018, Def 5 (p.9-10): conclusions are
        formulas in the logical language L.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            assert conc(arg) in L, (
                f"conc({arg}) = {conc(arg)} not in L"
            )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_rule_args_antecedents_match(self, data):
        """For every StrictArg/DefeasibleArg A, the conclusions of
        A.sub_args match the antecedents of A.rule.

        Modgil & Prakken 2018, Def 5 clauses 2-3 (p.9-10): if
        A1,...,An are arguments and their conclusions match a rule's
        antecedents, then the compound is an argument.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            if isinstance(arg, (StrictArg, DefeasibleArg)):
                sub_concs = tuple(conc(sa) for sa in arg.sub_args)
                assert sub_concs == arg.rule.antecedents, (
                    f"Sub-arg conclusions {sub_concs} != "
                    f"rule antecedents {arg.rule.antecedents}"
                )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_def_rules_empty_for_premise(self, data):
        """For every PremiseArg A, def_rules(A) == frozenset().

        Modgil & Prakken 2018, Def 5 clause 1 (p.9):
        DefRules(A) = ∅ for premise arguments.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            if isinstance(arg, PremiseArg):
                assert def_rules(arg) == frozenset(), (
                    f"PremiseArg has non-empty def_rules: {def_rules(arg)}"
                )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_def_rules_includes_top_for_defeasible(self, data):
        """For every DefeasibleArg A, A.rule in def_rules(A).

        Modgil & Prakken 2018, Def 5 clause 3 (p.9-10):
        DefRules(A) = DefRules(A1) ∪ ... ∪ DefRules(An) ∪ {TopRule(A)}.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            if isinstance(arg, DefeasibleArg):
                assert arg.rule in def_rules(arg), (
                    f"DefeasibleArg top rule {arg.rule} not in "
                    f"def_rules: {def_rules(arg)}"
                )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_is_firm_iff_prem_subset_kn(self, data):
        """is_firm(A) iff prem(A) ⊆ kb.axioms.

        Modgil & Prakken 2018, Def 5 / Prakken 2010 Def 3.8:
        an argument is firm iff all its premises are axioms (K_n).
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            expected = prem(arg) <= kb.axioms
            assert is_firm(arg) == expected, (
                f"is_firm({arg}) = {is_firm(arg)}, "
                f"but prem(A) <= K_n is {expected}"
            )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_is_strict_iff_no_def_rules(self, data):
        """is_strict(A) iff def_rules(A) == frozenset().

        Modgil & Prakken 2018, Def 5 / Prakken 2010 Def 3.8:
        an argument is strict iff it uses no defeasible rules.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        for arg in arguments:
            expected = def_rules(arg) == frozenset()
            assert is_strict(arg) == expected, (
                f"is_strict({arg}) = {is_strict(arg)}, "
                f"but def_rules empty is {expected}"
            )

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_firm_strict_exist_when_kn_nonempty(self, data):
        """When K_n is nonempty, at least one argument is both firm and strict.

        Modgil & Prakken 2018, Def 5 clause 1 (p.9): every phi in K
        is a PremiseArg. If phi in K_n, the argument is firm (prem ⊆ K_n)
        and strict (no defeasible rules). So K_n nonempty guarantees at
        least one firm+strict argument.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        assume(len(kb.axioms) > 0)
        arguments = build_arguments(system, kb)
        assert any(
            is_firm(a) and is_strict(a) for a in arguments
        ), "K_n nonempty but no firm+strict argument found"

    @given(data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_nontriviality(self, data):
        """When rules exist whose antecedents are in K, at least one
        non-PremiseArg is constructed.

        This is the non-triviality guarantee from the knowledge_base
        strategy: it forces at least one rule's antecedents into K_p,
        ensuring build_arguments produces compound arguments.
        See reports/hypothesis-aspic-feasibility.md Section 3, Level 4.
        """
        L, cfn = data.draw(logical_language())
        R_s = data.draw(strict_rules(L, cfn))
        R_d = data.draw(defeasible_rules(L))
        all_rules = R_s | R_d
        assume(len(all_rules) > 0)
        system = ArgumentationSystem(L, cfn, R_s, R_d)
        kb = data.draw(knowledge_base(L, R_s, R_d))
        arguments = build_arguments(system, kb)
        non_premise = [
            a for a in arguments if not isinstance(a, PremiseArg)
        ]
        assert len(non_premise) > 0, (
            "Rules exist and antecedents are in K, "
            "but no non-PremiseArg was constructed"
        )


class TestArgumentConstructionConcrete:
    """Hand-constructed examples for argument construction."""

    def test_simple_modus_ponens(self):
        """K_p = {p, q}. Defeasible rule: p, q => r.

        Modgil & Prakken 2018, Def 5 (p.9-10): construct arguments
        bottom-up from premises through rule application.

        Expected arguments:
        - PremiseArg(p), PremiseArg(q)
        - DefeasibleArg(sub_args=(PremiseArg(p), PremiseArg(q)),
                        rule=(p, q => r))
        The compound argument's conclusion is r.
        """
        p = Literal("p")
        q = Literal("q")
        r = Literal("r")
        not_p = p.contrary
        not_q = q.contrary
        not_r = r.contrary

        L = frozenset({p, q, r, not_p, not_q, not_r})
        cfn = ContrarinessFn(contradictories=frozenset({
            (p, not_p), (q, not_q), (r, not_r),
        }))

        rule_pq_r = Rule(
            antecedents=(p, q),
            consequent=r,
            kind="defeasible",
            name="d0",
        )

        system = ArgumentationSystem(
            language=L,
            contrariness=cfn,
            strict_rules=frozenset(),
            defeasible_rules=frozenset({rule_pq_r}),
        )
        kb = KnowledgeBase(
            axioms=frozenset(),
            premises=frozenset({p, q}),
        )

        arguments = build_arguments(system, kb)

        # Find premise arguments
        prem_p = PremiseArg(premise=p, is_axiom=False)
        prem_q = PremiseArg(premise=q, is_axiom=False)
        assert prem_p in arguments, f"PremiseArg(p) not in arguments: {arguments}"
        assert prem_q in arguments, f"PremiseArg(q) not in arguments: {arguments}"

        # Find the compound defeasible argument
        compound = DefeasibleArg(
            sub_args=(prem_p, prem_q),
            rule=rule_pq_r,
        )
        assert compound in arguments, (
            f"DefeasibleArg(p,q => r) not in arguments: {arguments}"
        )

        # Conclusion of the compound is r
        assert conc(compound) == r, (
            f"Expected conc = r, got {conc(compound)}"
        )
