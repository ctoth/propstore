"""Tests for ASPIC+ logical language and contrariness function.

Property-based tests verify formal definitions from:
    Modgil, S. & Prakken, H. (2018). A general account of argumentation
    with preferences. Artificial Intelligence, 248, 51-104.
    - Def 1 (p.8): Logical language L
    - Def 2 (p.8): Contrariness function, contradictories vs contraries

    Prakken, H. (2010). An abstract framework for argumentation with
    structured arguments. Argument & Computation, 1(2), 93-124.
    - Def 3.1: Argumentation system tuple
    - Def 3.2: Contrariness — symmetric (contradictory) vs asymmetric (contrary)

Concrete regression tests verify hand-constructed examples.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.aspic import Literal, ContrarinessFn


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
