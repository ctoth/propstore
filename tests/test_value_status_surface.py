def test_underdetermined_member_removed():
    from propstore.world.types import ValueStatus

    assert not hasattr(ValueStatus, "UNDERDETERMINED")
    assert "underdetermined" not in ValueStatus._value2member_map_
