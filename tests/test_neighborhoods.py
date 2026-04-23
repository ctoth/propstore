from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

import pytest

from propstore.app import neighborhoods
from propstore.app.claim_views import ClaimViewUnknownClaimError
from propstore.app.neighborhoods import (
    SemanticNeighborhoodRequest,
    SemanticNeighborhoodUnsupportedFocusError,
    build_semantic_neighborhood,
)
from propstore.core.claim_values import ClaimProvenance
from propstore.core.row_types import ClaimRow, ConceptRow, StanceRow
from propstore.repository import Repository
from propstore.world import RenderPolicy


class _World:
    def __init__(
        self,
        *,
        claims: tuple[ClaimRow, ...],
        stances: tuple[StanceRow, ...] = (),
        visible_ids: tuple[str, ...] | None = None,
    ) -> None:
        self.claims = {str(claim.claim_id): claim for claim in claims}
        self.stances = stances
        self.visible_ids = set(self.claims) if visible_ids is None else set(visible_ids)

    def get_claim(self, claim_id: str) -> ClaimRow | None:
        return self.claims.get(claim_id)

    def get_concept(self, concept_id: str) -> ConceptRow | None:
        return ConceptRow(
            concept_id=concept_id,
            canonical_name="focus_concept",
        )

    def claims_with_policy(
        self,
        concept_id: str | None,
        policy: RenderPolicy,
    ) -> list[ClaimRow]:
        rows = [
            claim
            for claim_id, claim in self.claims.items()
            if claim_id in self.visible_ids
        ]
        if concept_id is None:
            return rows
        return [claim for claim in rows if str(claim.concept_id) == concept_id]

    def all_claim_stances(self) -> list[StanceRow]:
        return list(self.stances)


@contextmanager
def _open_world(world: _World) -> Iterator[_World]:
    yield world


def _repo() -> Repository:
    return cast(Repository, object())


def _claim(claim_id: str, *, concept_id: str = "concept1") -> ClaimRow:
    return ClaimRow(
        claim_id=claim_id,
        artifact_id=claim_id,
        claim_type="parameter",
        concept_id=concept_id,
        value=1.0,
        provenance=ClaimProvenance(paper="paper1"),
    )


def _stance(source: str, stance_type: str, target: str) -> StanceRow:
    return StanceRow(
        claim_id=source,
        target_claim_id=target,
        stance_type=stance_type,
    )


def test_claim_neighborhood_reports_moves_edges_and_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        claims=(
            _claim("focus"),
            _claim("supporter"),
            _claim("attacker"),
            _claim("same_concept"),
        ),
        stances=(
            _stance("supporter", "supports", "focus"),
            _stance("attacker", "rebuts", "focus"),
        ),
    )
    monkeypatch.setattr(neighborhoods, "open_app_world_model", lambda repo: _open_world(world))

    report = build_semantic_neighborhood(
        _repo(),
        SemanticNeighborhoodRequest(focus_kind="claim", focus_id="focus"),
    )

    moves = {move.kind: move for move in report.moves}
    assert moves["supporters"].target_ids == ("supporter",)
    assert moves["attackers"].target_ids == ("attacker",)
    assert moves["shared_concept"].target_count == 3
    assert moves["assumptions"].state == "unavailable"
    assert report.status.state == "known"
    assert {edge.edge_kind for edge in report.edges} == {"supports", "rebuts"}
    assert all(edge.sentence for edge in report.edges)
    assert any(row.section == "supporters" for row in report.table_rows)
    assert "1 supporters" in report.prose_summary


def test_claim_neighborhood_marks_blocked_focus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(claims=(_claim("focus"),), visible_ids=())
    monkeypatch.setattr(neighborhoods, "open_app_world_model", lambda repo: _open_world(world))

    report = build_semantic_neighborhood(
        _repo(),
        SemanticNeighborhoodRequest(focus_kind="claim", focus_id="focus"),
    )

    assert report.status.state == "blocked"
    assert report.status.visible_under_policy is False


def test_claim_neighborhood_rejects_unsupported_focus() -> None:
    with pytest.raises(SemanticNeighborhoodUnsupportedFocusError, match="concept"):
        build_semantic_neighborhood(
            _repo(),
            SemanticNeighborhoodRequest(focus_kind="concept", focus_id="concept1"),
        )


def test_claim_neighborhood_reports_unknown_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(claims=())
    monkeypatch.setattr(neighborhoods, "open_app_world_model", lambda repo: _open_world(world))

    with pytest.raises(ClaimViewUnknownClaimError, match="missing"):
        build_semantic_neighborhood(
            _repo(),
            SemanticNeighborhoodRequest(focus_kind="claim", focus_id="missing"),
        )
