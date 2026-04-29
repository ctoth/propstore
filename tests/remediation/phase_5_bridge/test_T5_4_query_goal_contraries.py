from argumentation.aspic import contraries_of
from propstore.aspic_bridge import query


def test_query_goal_contraries_helper_is_deleted() -> None:
    assert contraries_of is not None
    assert not hasattr(query, "_goal_contraries")
