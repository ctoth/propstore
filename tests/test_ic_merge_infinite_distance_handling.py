from __future__ import annotations

import pytest

from propstore.belief_set import Atom, TOP, conjunction, negate
from propstore.belief_set.ic_merge import (
    ICMergeOperator,
    ICMergeProfileMemberInconsistent,
    merge_belief_profile,
)


@pytest.mark.parametrize("operator", (ICMergeOperator.SIGMA, ICMergeOperator.GMAX))
def test_ic_merge_rejects_unsatisfiable_profile_member(operator: ICMergeOperator) -> None:
    """Class A - must fail today: ic_merge.py drops infinite distances."""

    p = Atom("p")
    unsatisfiable = conjunction(p, negate(p))

    with pytest.raises(ICMergeProfileMemberInconsistent):
        merge_belief_profile(
            frozenset({"p"}),
            (p, unsatisfiable),
            TOP,
            operator=operator,
        )
