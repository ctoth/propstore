from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason="WS-H records the propstore consumer hook; WS-O-arg-gradual owns the formula proof"
)
def test_dfquad_attack_support_per_upstream_paper_contract():
    """Codex #17: propstore pins to the upstream paper-faithful DF-QuAD contract."""
    pytest.fail("blocked on WS-O-arg-gradual paper-contract resolution")
