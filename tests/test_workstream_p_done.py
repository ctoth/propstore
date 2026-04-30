from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="WS-P is open until all CEL/unit/equation gates close")
def test_workstream_p_closed() -> None:
    assert False
