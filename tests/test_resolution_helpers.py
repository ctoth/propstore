from __future__ import annotations

from types import SimpleNamespace

from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
from propstore.world.resolution import (
    _resolve_claim_graph_argumentation,
    _resolve_structured_argumentation,
)


class _World:
    def has_table(self, name: str) -> bool:
        return name == "relation_edge"


class _View:
    pass


def test_claim_graph_resolution_distinguishes_skeptical_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "propstore.core.analyzers.shared_analyzer_input_from_store",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "propstore.core.analyzers.analyze_claim_graph",
        lambda *args, **kwargs: AnalyzerResult(
            backend="claim_graph",
            semantics="preferred",
            extensions=(
                ExtensionResult(name="preferred:1", accepted_claim_ids=("claim_a",)),
                ExtensionResult(name="preferred:2", accepted_claim_ids=("claim_b",)),
            ),
            projection=ClaimProjection(
                target_claim_ids=("claim_a", "claim_b"),
                survivor_claim_ids=(),
                witness_claim_ids=("claim_a", "claim_b"),
            ),
        ),
    )

    winner, reason = _resolve_claim_graph_argumentation(
        [{"id": "claim_a"}, {"id": "claim_b"}],
        [{"id": "claim_a"}, {"id": "claim_b"}],
        _World(),
        semantics="preferred",
    )

    assert winner is None
    assert reason == "no skeptically accepted claim in preferred extensions"


def test_claim_graph_resolution_distinguishes_no_stable_extension(monkeypatch) -> None:
    monkeypatch.setattr(
        "propstore.core.analyzers.shared_analyzer_input_from_store",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "propstore.core.analyzers.analyze_claim_graph",
        lambda *args, **kwargs: AnalyzerResult(
            backend="claim_graph",
            semantics="stable",
            extensions=(),
        ),
    )

    winner, reason = _resolve_claim_graph_argumentation(
        [{"id": "claim_a"}, {"id": "claim_b"}],
        [{"id": "claim_a"}, {"id": "claim_b"}],
        _World(),
        semantics="stable",
    )

    assert winner is None
    assert reason == "no stable extensions"


def test_structured_resolution_distinguishes_skeptical_failure(monkeypatch) -> None:
    projection = SimpleNamespace(
        claim_to_argument_ids={
            "claim_a": ("arg:a",),
            "claim_b": ("arg:b",),
        },
        argument_to_claim_id={
            "arg:a": "claim_a",
            "arg:b": "claim_b",
        },
    )
    monkeypatch.setattr(
        "propstore.structured_argument.build_structured_projection",
        lambda *args, **kwargs: projection,
    )
    monkeypatch.setattr(
        "propstore.structured_argument.compute_structured_justified_arguments",
        lambda *args, **kwargs: [frozenset({"arg:a"}), frozenset({"arg:b"})],
    )

    winner, reason = _resolve_structured_argumentation(
        [{"id": "claim_a"}, {"id": "claim_b"}],
        [{"id": "claim_a"}, {"id": "claim_b"}],
        _View(),
        _World(),
        semantics="preferred",
    )

    assert winner is None
    assert reason == "no skeptically accepted claim in preferred structured projection"
