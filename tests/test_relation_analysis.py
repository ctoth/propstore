from __future__ import annotations

from propstore.relation_analysis import stance_summary
from propstore.core.row_types import StanceRow


class _TypedStanceStore:
    def stances_between(self, claim_ids: set[str]) -> list[StanceRow]:
        return [
            StanceRow.from_mapping(
                {
                    "claim_id": "claim:a",
                    "target_claim_id": "claim:b",
                    "stance_type": "supersedes",
                    "resolution_model": "demo-model",
                    "opinion_uncertainty": 0.25,
                }
            ),
            StanceRow.from_mapping(
                {
                    "claim_id": "claim:c",
                    "target_claim_id": "claim:d",
                    "stance_type": "supports",
                    "opinion_uncertainty": 1.0,
                }
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
