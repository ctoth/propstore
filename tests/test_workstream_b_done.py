from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="WS-B remains open until render-policy gates all pass")
def test_workstream_b_is_closed() -> None:
    assert False
