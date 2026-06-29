"""WS-I Step 7: ATMS nogood updates interleave before propagation."""

from __future__ import annotations

import inspect

from propstore.world.atms import ATMSEngine


def test_ws_i_atms_build_does_not_propagate_before_nogood_update() -> None:
    """E.M3: nogoods are updated before propagation observes final labels."""

    source = inspect.getsource(ATMSEngine._build)

    assert "self._propagate_labels()\n            added_justifications" not in source
