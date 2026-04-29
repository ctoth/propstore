from __future__ import annotations

from propstore.core.results import AnalyzerResult, ClaimProjection
from propstore.world.resolution import _ResolutionClaimView, _resolve_praf


class _World:
    def has_table(self, name: str) -> bool:
        return name == "relation_edge"


def _claim(claim_id: str) -> _ResolutionClaimView:
    return _ResolutionClaimView(
        id=claim_id,
        value=None,
        provenance=None,
        sample_size=None,
        opinion_belief=None,
        opinion_disbelief=None,
        opinion_uncertainty=None,
        opinion_base_rate=None,
        confidence=None,
    )


def test_praf_paper_td_complete_routes_resolution_to_extension_probability(monkeypatch):
    """Codex #14: paper-TD complete is extension probability, not argument acceptance."""
    calls: list[dict[str, object]] = []

    def fake_shared(*_args, **_kwargs):
        return object()

    def fake_analyze_praf(_shared, **kwargs):
        calls.append(dict(kwargs))
        return AnalyzerResult(
            backend="praf",
            semantics="praf-paper-td-complete",
            projection=ClaimProjection(
                target_claim_ids=("claim_a",),
                survivor_claim_ids=("claim_a",),
                witness_claim_ids=("claim_a",),
            ),
            metadata={
                "query_kind": "extension_probability",
                "inference_mode": None,
                "queried_set": ("claim_a",),
                "acceptance_probs": None,
                "extension_probability": 0.75,
                "strategy_used": "paper_td",
            },
        )

    monkeypatch.setattr(
        "propstore.core.analyzers.shared_analyzer_input_from_store",
        fake_shared,
    )
    monkeypatch.setattr("propstore.core.analyzers.analyze_praf", fake_analyze_praf)

    winner, reason, acceptance = _resolve_praf(
        [_claim("claim_a")],
        [_claim("claim_a")],
        _World(),
        semantics="praf-paper-td-complete",
    )

    assert calls[0]["semantics"] == "praf-paper-td-complete"
    assert calls[0]["query_kind"] == "extension_probability"
    assert calls[0]["inference_mode"] is None
    assert calls[0]["target_claim_ids"] == {"claim_a"}
    assert winner == "claim_a"
    assert "paper_td" in (reason or "")
    assert acceptance is None
