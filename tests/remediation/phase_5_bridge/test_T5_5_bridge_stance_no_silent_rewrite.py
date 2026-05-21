import pytest

from propstore.families.relations.declaration import Stance
from propstore import stances


def test_contradicts_stance_rejected_not_silently_rewritten() -> None:
    unknown_stance_type = getattr(stances, "UnknownStanceType", ValueError)

    with pytest.raises(unknown_stance_type, match="contradicts"):
        Stance(
            claim_id="claim-a",
            target_claim_id="claim-b",
            stance_type="contradicts",
        ).stance_type
