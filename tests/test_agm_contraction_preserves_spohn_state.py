from __future__ import annotations

from propstore.belief_set import Atom, SpohnEpistemicState, full_meet_contract, revise


def test_full_meet_contraction_preserves_spohn_ranking_information() -> None:
    """Class A - must fail today.

    Counterexample: agm.py rebuilds the Spohn state via
    ``from_belief_set(contracted)``, assigning rank 0 to models and rank 1 to
    non-models irrespective of the prior ranking.

    Spohn 1988 OCF Definition 4 (p.115) defines kappa as the disbelief grade
    with kappa(W)=0, kappa(empty)=Omega, and kappa(A)=min{kappa(w) | w in A}.
    Darwiche-Pearl 1997 p.15 gives bullet revision:

        (kappa * mu)(w) = kappa(w) - kappa(mu) if w satisfies mu
                       = kappa(w) + 1          otherwise

    Harper identity (Alchourron, Gardenfors, and Makinson 1985 Observation
    2.3) lifted to OCFs keeps a world when it survives either the original
    kappa or revision by not-phi:

        (kappa / phi)(w) = min(kappa(w), (kappa * not-phi)(w))

    Booth and Meyer 2006 section 5 uses this min-of-prior-and-revised ranking
    as an OCF contraction construction.

    Worked fixture over p,q:
    - A: {pq:0, p not-q:1, not-p q:2, not-p not-q:3}
    - B: {pq:0, not-p q:1, p not-q:2, not-p not-q:3}

    Contract both by p. Harper contraction yields:
    - A / p = {not-p not-q:1, not-p q:0, p not-q:1, pq:0}
    - B / p = {not-p not-q:2, not-p q:0, p not-q:2, pq:0}

    Both contracted belief sets are {not-p q, pq}, but their rankings differ.
    Revising each contracted state by q must preserve that difference:
    - (A / p) * q = {not-p not-q:2, not-p q:0, p not-q:2, pq:0}
    - (B / p) * q = {not-p not-q:3, not-p q:0, p not-q:3, pq:0}
    """

    p = Atom("p")
    q = Atom("q")
    alphabet = frozenset({"p", "q"})
    not_p_not_q = frozenset()
    not_p_q = frozenset({"q"})
    p_not_q = frozenset({"p"})
    p_q = frozenset({"p", "q"})

    state_a = SpohnEpistemicState.from_ranks(
        alphabet,
        {
            p_q: 0,
            p_not_q: 1,
            not_p_q: 2,
            not_p_not_q: 3,
        },
    )
    state_b = SpohnEpistemicState.from_ranks(
        alphabet,
        {
            p_q: 0,
            not_p_q: 1,
            p_not_q: 2,
            not_p_not_q: 3,
        },
    )

    contracted_a = full_meet_contract(state_a, p).state
    contracted_b = full_meet_contract(state_b, p).state

    assert contracted_a.belief_set == contracted_b.belief_set
    assert contracted_a.ranks == {
        not_p_not_q: 1,
        not_p_q: 0,
        p_not_q: 1,
        p_q: 0,
    }
    assert contracted_b.ranks == {
        not_p_not_q: 2,
        not_p_q: 0,
        p_not_q: 2,
        p_q: 0,
    }

    revised_a = revise(contracted_a, q).state
    revised_b = revise(contracted_b, q).state

    assert revised_a.ranks == {
        not_p_not_q: 2,
        not_p_q: 0,
        p_not_q: 2,
        p_q: 0,
    }
    assert revised_b.ranks == {
        not_p_not_q: 3,
        not_p_q: 0,
        p_not_q: 3,
        p_q: 0,
    }
    assert revised_a.ranks != revised_b.ranks
