from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="WS-J2 closes when InterventionWorld and actual_cause gates pass")
def test_workstream_j2_done() -> None:
    assert False
