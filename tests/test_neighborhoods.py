from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

import pytest

from propstore.app import neighborhoods
from propstore.app.claim_views import ClaimViewBlockedError, ClaimViewUnknownClaimError
from propstore.app.neighborhoods import (
    SemanticNeighborhoodRequest,
    SemanticNeighborhoodUnsupportedFocusError,
    build_semantic_neighborhood,
)
from propstore.app.repository_views import (
    AppRepositoryViewRequest,
    RepositoryViewUnsupportedStateError,
)
from propstore.families.claims.types import ClaimType
from propstore.families.claims.declaration import Claim
from propstore.families.concepts.declaration import Concept
from propstore.families.relations.declaration import Stance
from propstore.repository import Repository
from propstore.world import RenderPolicy
from tests.claim_model_helpers import make_claim


class _World:
    def __init__(
        self,
        *,
        claims: tuple[Claim, ...],
        stances: tuple[Stance, ...] = (),
        visible_ids: tuple[str, ...] | None = None,
    ) -> None:
        self.claims = {str(claim.id): claim for claim in claims}
        self.stances = stances
        self.visible_ids = set(self.claims) if visible_ids is None else set(visible_ids)

    def get_claim(self, claim_id: str) -> Claim | None:
        return self.claims.get(claim_id)

    def get_concept(self, concept_id: str) -> Concept | None:
        return Concept(
            concept_id=concept_id,
            canonical_name="focus_concept",
        )

    def claims_with_policy(
        self,
        concept_id: str | None,
        policy: RenderPolicy,
    ) -> list[Claim]:
        rows = [
            claim
            for claim_id, claim in self.claims.items()
            if claim_id in self.visible_ids
        ]
        if concept_id is None:
            return rows
        return [
            claim for claim in rows if str(claim.value_concept_id or "") == concept_id
        ]

    def all_claim_stances(self) -> list[Stance]:
        return list(self.stances)

    def claim_stances_with_policy(
        self,
        focus_claim_id: str,
        policy: RenderPolicy,
    ) -> list[Stance]:
        return [
            stance
            for stance in self.stances
            if (
                str(stance.claim_id) in self.visible_ids
                and str(stance.target_claim_id) in self.visible_ids
                and (
                    str(stance.claim_id) == focus_claim_id
                    or str(stance.target_claim_id) == focus_claim_id
                )
            )
        ]


@contextmanager
def _open_world(world: _World) -> Iterator[_World]:
    yield world


def _repo() -> Repository:
    return cast(Repository, object())


def _stance(source: str, stance_type: str, target: str) -> Stance:
    return Stance(
        source_kind="claim",
        source_id=source,
        relation_type=stance_type,
        target_kind="claim",
        target_id=target,
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
    monkeypatch.setattr(
        neighborhoods, "open_app_world_model", lambda repo: _open_world(world)
    )

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
    monkeypatch.setattr(
        neighborhoods, "open_app_world_model", lambda repo: _open_world(world)
    )

    with pytest.raises(ClaimViewBlockedError, match="Not Found"):
        build_semantic_neighborhood(
            _repo(),
            SemanticNeighborhoodRequest(focus_kind="claim", focus_id="focus"),
        )


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
    monkeypatch.setattr(
        neighborhoods, "open_app_world_model", lambda repo: _open_world(world)
    )

    with pytest.raises(ClaimViewUnknownClaimError, match="missing"):
        build_semantic_neighborhood(
            _repo(),
            SemanticNeighborhoodRequest(focus_kind="claim", focus_id="missing"),
        )


def test_claim_neighborhood_rejects_unimplemented_repository_state() -> None:
    with pytest.raises(RepositoryViewUnsupportedStateError, match="revision-qualified"):
        build_semantic_neighborhood(
            _repo(),
            SemanticNeighborhoodRequest(
                focus_kind="claim",
                focus_id="focus",
                repository_view=AppRepositoryViewRequest(revision="deadbeef"),
            ),
        )
