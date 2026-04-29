from __future__ import annotations

import math

import pytest

from propstore.belief_set import Atom, TOP, conjunction, negate
from propstore.belief_set.ic_merge import (
    ICMergeProfileMemberInconsistent,
    ICMergeOperator,
    _distance_to_formula,
    merge_belief_profile,
)


def test_unsat_profile_member_is_rejected_at_merge_boundary() -> None:
    alphabet = frozenset({"p", "q"})
    phi1 = Atom("p")
    phi2 = Atom("q")
    unsat = conjunction(phi1, negate(phi1))

    for operator in (ICMergeOperator.SIGMA, ICMergeOperator.GMAX):
        profile_with_unsat = (phi1, phi2, unsat)

        with pytest.raises(ICMergeProfileMemberInconsistent) as exc_info:
            merge_belief_profile(
                alphabet,
                profile_with_unsat,
                TOP,
                operator=operator,
            )

        assert exc_info.value.formula == unsat


def test_unsat_formula_distance_is_infinite() -> None:
    alphabet = frozenset({"p"})
    unsat = conjunction(Atom("p"), negate(Atom("p")))

    assert math.isinf(_distance_to_formula(frozenset({"p"}), unsat, alphabet))
