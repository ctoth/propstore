"""WS-J Step 3: worldline argumentation preserves multi-extension state."""

from __future__ import annotations

from propstore.core.id_types import to_claim_id
from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
from propstore.world.types import RenderPolicy
from propstore.worldline.argumentation import _capture_claim_graph


def test_ws_j_claim_graph_multi_extension_state_is_captured(monkeypatch) -> None:
    """J-H3: multiple extensions must not collapse to no argumentation state."""

    def fake_analyze_claim_graph(_analyzer_input, *, semantics, **_kwargs):
        return AnalyzerResult(
            backend="claim_graph",
            semantics=str(semantics),
            extensions=(
                ExtensionResult(name=str(semantics), accepted_claim_ids=("claim_a",)),
                ExtensionResult(name=str(semantics), accepted_claim_ids=("claim_b",)),
            ),
            projection=ClaimProjection(
                target_claim_ids=("claim_a", "claim_b"),
                survivor_claim_ids=("claim_a", "claim_b"),
                witness_claim_ids=("claim_a", "claim_b"),
            ),
        )

    monkeypatch.setattr(
        "propstore.core.analyzers.shared_analyzer_input_from_active_graph",
        lambda active_graph, **_kwargs: active_graph,
    )
    monkeypatch.setattr(
        "propstore.core.analyzers.analyze_claim_graph",
        fake_analyze_claim_graph,
    )

    state = _capture_claim_graph(
        world=object(),
        active_ids={to_claim_id("claim_a"), to_claim_id("claim_b")},
        active_graph=object(),
        policy=RenderPolicy(),
        normalized_semantics="preferred",
    )

    assert state is not None
    assert state.inference_mode == "credulous"
    assert state.extensions == (("claim_a",), ("claim_b",))
    assert state.justified == ("claim_a", "claim_b")
    assert state.defeated == ()
