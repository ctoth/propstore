import pytest

from propstore.families.relations.declaration import Stance
from propstore import stances


def test_contradicts_stance_rejected_not_silently_rewritten() -> None:
    unknown_stance_type = getattr(stances, "UnknownStanceType", ValueError)

    with pytest.raises(unknown_stance_type, match="contradicts"):
        Stance(
            source_kind="claim",
            source_id="claim-a",
            relation_type="contradicts",
            target_kind="claim",
            target_id="claim-b",
        ).stance_type
