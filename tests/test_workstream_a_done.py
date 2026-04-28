from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="WS-A remains open until all schema and identity gates pass")
def test_workstream_a_is_closed() -> None:
    assert False
