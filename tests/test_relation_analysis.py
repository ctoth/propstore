from __future__ import annotations

from propstore.relation_analysis import stance_summary
from propstore.families.relations.declaration import Stance
from propstore.stances import StanceType


class _TypedStanceStore:
    def stances_between(self, claim_ids: set[str]) -> list[Stance]:
        return [
            Stance(
                source_kind="claim",
                source_id="claim:a",
                relation_type=str(StanceType.SUPERSEDES),
                target_kind="claim",
                target_id="claim:b",
                resolution_model="demo-model",
                opinion_uncertainty=0.25,
            ),
            Stance(
                source_kind="claim",
                source_id="claim:c",
                relation_type=str(StanceType.SUPPORTS),
                target_kind="claim",
                target_id="claim:d",
                opinion_uncertainty=1.0,
            ),
        ]


def test_stance_summary_accepts_typed_stance_rows() -> None:
    summary = stance_summary(
        _TypedStanceStore(),
        {"claim:a", "claim:b", "claim:c", "claim:d"},
    )

    assert summary == {
        "total_stances": 2,
        "included_as_attacks": 1,
        "vacuous_count": 0,
        "excluded_non_attack": 1,
        "models": ["demo-model"],
        "mean_uncertainty": 0.25,
    }
