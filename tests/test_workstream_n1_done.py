from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="WS-N1 closure sentinel flips in the final WS-N1 commit")
def test_workstream_n1_done() -> None:
    assert False
