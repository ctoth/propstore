import pytest

from propstore.aspic_bridge.translate import _coerce_bridge_stance_row
from propstore import stances


def test_contradicts_stance_rejected_not_silently_rewritten() -> None:
    unknown_stance_type = getattr(stances, "UnknownStanceType", ValueError)

    with pytest.raises(unknown_stance_type, match="contradicts"):
        _coerce_bridge_stance_row(
            {
                "claim_id": "claim-a",
                "target_claim_id": "claim-b",
                "stance_type": "contradicts",
            }
        )
