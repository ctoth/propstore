"""WS-J Step 3: worldline argumentation preserves multi-extension state."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from propstore.core.id_types import to_claim_id
from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.world.types import RenderPolicy
from propstore.worldline.argumentation import _capture_aspic, _capture_claim_graph


class _GroundingWorld:
    def grounding_bundle(self) -> GroundedRulesBundle:
        return GroundedRulesBundle.empty()


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
        "propstore.core.analyzers.shared_analyzer_input_from_graph",
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


@pytest.mark.parametrize(
    (
        "semantics",
        "justified_arguments",
        "expected_extensions",
        "expected_justified",
        "expected_defeated",
        "expected_inference_mode",
    ),
    (
        (
            "grounded",
            frozenset({"arg:a"}),
            (("claim_a",),),
            ("claim_a",),
            ("claim_b",),
            "grounded",
        ),
        (
            "preferred",
            [frozenset({"arg:a"}), frozenset({"arg:b"})],
            (("claim_a",), ("claim_b",)),
            ("claim_a", "claim_b"),
            (),
            "credulous",
        ),
        (
            "stable",
            [],
            (),
            (),
            ("claim_a", "claim_b"),
            "credulous",
        ),
    ),
)
def test_aspic_successful_extension_shapes_are_captured(
    monkeypatch: pytest.MonkeyPatch,
    semantics: str,
    justified_arguments: frozenset[str] | list[frozenset[str]],
    expected_extensions: tuple[tuple[str, ...], ...],
    expected_justified: tuple[str, ...],
    expected_defeated: tuple[str, ...],
    expected_inference_mode: str,
) -> None:
    projection = SimpleNamespace(
        argument_to_claim_id={"arg:a": "claim_a", "arg:b": "claim_b"}
    )
    monkeypatch.setattr(
        "propstore.aspic_bridge.build_aspic_projection",
        lambda *args, **kwargs: projection,
    )
    monkeypatch.setattr(
        "propstore.structured_projection.compute_structured_justified_arguments",
        lambda *args, **kwargs: justified_arguments,
    )

    state = _capture_aspic(
        bound=object(),
        world=_GroundingWorld(),
        active=[],
        active_ids={to_claim_id("claim_a"), to_claim_id("claim_b")},
        active_graph=None,
        policy=RenderPolicy(),
        normalized_semantics=semantics,
    )

    assert state is not None
    assert state.backend == "aspic"
    assert state.semantics == semantics
    assert state.inference_mode == expected_inference_mode
    assert state.extensions == expected_extensions
    assert state.justified == expected_justified
    assert state.defeated == expected_defeated
