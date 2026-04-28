"""WS-I Step 7: ATMS justifications have one consequent field."""

from __future__ import annotations

import inspect

from propstore.world.atms import ATMSEngine


def test_ws_i_atms_justifications_have_one_consequent_field() -> None:
    """E.M2: dead multi-consequent production surface is deleted."""

    source = inspect.getsource(ATMSEngine)

    assert "consequent_ids" not in source
    assert "consequent_id" in source
