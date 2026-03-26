from __future__ import annotations

from types import SimpleNamespace

from propstore.world.resolution import (
    _resolve_claim_graph_argumentation,
    _resolve_structured_argumentation,
)


class _World:
    def has_table(self, name: str) -> bool:
        return name == "claim_stance"


class _View:
    pass


def test_claim_graph_resolution_distinguishes_skeptical_failure(monkeypatch) -> None:
    def _compute(*args, **kwargs):
        return [frozenset({"claim_a"}), frozenset({"claim_b"})]

    monkeypatch.setattr(
        "propstore.argumentation.compute_claim_graph_justified_claims",
        _compute,
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
        "propstore.argumentation.compute_claim_graph_justified_claims",
        lambda *args, **kwargs: [],
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
