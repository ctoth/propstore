"""WS-J Step 8/J-M4: override claim sentinels use one public constant."""

from __future__ import annotations

from propstore.worldline._constants import OVERRIDE_CLAIM_PREFIX
from propstore.worldline.trace import ResolutionTrace


def test_ws_j_override_claim_prefix_constant_controls_dependency_filter() -> None:
    trace = ResolutionTrace()

    trace.record_claim_dependency(f"{OVERRIDE_CLAIM_PREFIX}target")
    trace.record_claim_dependency("ps:assertion:real")

    assert {str(claim_id) for claim_id in trace.dependency_claims} == {
        "ps:assertion:real"
    }
