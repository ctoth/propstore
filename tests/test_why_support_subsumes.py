from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.provenance.projections import WhySupport, normalize_why_supports


WHY_SET = st.sets(st.text(min_size=1, max_size=8), min_size=0, max_size=5)


@given(WHY_SET, WHY_SET)
@pytest.mark.property
def test_why_support_api_name_matches_set_inclusion(left: set[str], right: set[str]) -> None:
    support = WhySupport(tuple(sorted(left)))
    other = WhySupport(tuple(sorted(right)))

    assert not hasattr(WhySupport, "subsumes")
    assert support.is_subsumed_by(other) is left.issubset(right)


def test_normalize_why_supports_keeps_minimal_basis() -> None:
    narrow = WhySupport(("paper:a",))
    broad = WhySupport(("paper:a", "paper:b"))
    separate = WhySupport(("paper:c",))

    assert normalize_why_supports((broad, narrow, separate)) == (narrow, separate)
