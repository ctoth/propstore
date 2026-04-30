from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="WS-N2 closure sentinel flips in the final WS-N2 commit")
def test_workstream_n2_done() -> None:
    assert False
