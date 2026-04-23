from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

import pytest

from propstore.app import claim_views
from propstore.app.claim_views import (
    ClaimViewRequest,
    ClaimViewUnknownClaimError,
    ClaimViewUnsupportedStateError,
    build_claim_view,
)
from propstore.app.rendering import AppRenderPolicyRequest
from propstore.core.claim_values import ClaimProvenance, ClaimSource
from propstore.core.row_types import ClaimRow, ConceptRow
from propstore.repository import Repository
from propstore.world import RenderPolicy


class _World:
    def __init__(
        self,
        *,
        claim: ClaimRow | None,
        concept: ConceptRow | None = None,
        visible: bool = True,
    ) -> None:
        self.claim = claim
        self.concept = concept
        self.visible = visible

    def get_claim(self, claim_id: str) -> ClaimRow | None:
        if self.claim is None or str(self.claim.claim_id) != claim_id:
            return None
        return self.claim

    def get_concept(self, concept_id: str) -> ConceptRow | None:
        if self.concept is None or str(self.concept.concept_id) != concept_id:
            return None
        return self.concept

    def claims_with_policy(
        self,
        concept_id: str | None,
        policy: RenderPolicy,
    ) -> list[ClaimRow]:
        if self.claim is None or not self.visible:
            return []
        if concept_id is not None and str(self.claim.concept_id) != concept_id:
            return []
        return [self.claim]


@contextmanager
def _open_world(world: _World) -> Iterator[_World]:
    yield world


def _repo() -> Repository:
    return cast(Repository, object())


def _claim(**overrides) -> ClaimRow:
    values = {
        "claim_id": "claim1",
        "artifact_id": "claim1",
        "claim_type": "parameter",
        "concept_id": "concept1",
        "value": 12.5,
        "unit": "Hz",
        "value_si": 12.5,
        "uncertainty": 0.2,
        "sample_size": 30,
        "source": ClaimSource(source_id="paper1", slug="paper1"),
        "provenance": ClaimProvenance(paper="paper1", page=4),
    }
    values.update(overrides)
    return ClaimRow(**values)


def _concept() -> ConceptRow:
    return ConceptRow(
        concept_id="concept1",
        canonical_name="fundamental_frequency",
        form="frequency",
    )


def test_build_claim_view_returns_typed_literal_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(claim=_claim(conditions_cel=None), concept=_concept())
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = build_claim_view(_repo(), ClaimViewRequest(claim_id="claim1"))

    assert report.claim_id == "claim1"
    assert report.heading == "Claim claim1"
    assert report.concept.state == "known"
    assert report.value.state == "known"
    assert report.value.value == 12.5
    assert report.uncertainty.state == "known"
    assert report.condition.state == "vacuous"
    assert "vacuous" in report.condition.sentence
    assert report.provenance.state == "known"
    assert report.status.state == "known"
    assert report.render_policy.reasoning_backend == "claim_graph"


def test_build_claim_view_speaks_absence_literals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claim = _claim(
        claim_type="mechanism",
        value=None,
        unit=None,
        value_si=None,
        uncertainty=None,
        sample_size=None,
        source=None,
        provenance=None,
    )
    world = _World(claim=claim, concept=None)
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = build_claim_view(_repo(), ClaimViewRequest(claim_id="claim1"))

    assert report.concept.state == "unknown"
    assert report.value.state == "not_applicable"
    assert "not applicable" in report.value.sentence
    assert report.uncertainty.state == "missing"
    assert report.provenance.state == "missing"


def test_build_claim_view_reports_policy_blocked_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claim = _claim(attributes={"stage": "draft"})
    world = _World(claim=claim, concept=_concept(), visible=False)
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = build_claim_view(
        _repo(),
        ClaimViewRequest(
            claim_id="claim1",
            render_policy=AppRenderPolicyRequest(include_drafts=False),
        ),
    )

    assert report.status.state == "blocked"
    assert report.status.visible_under_policy is False
    assert "drafts are hidden" in report.status.reason


def test_build_claim_view_rejects_unimplemented_repository_state() -> None:
    with pytest.raises(ClaimViewUnsupportedStateError, match="branch-qualified"):
        build_claim_view(_repo(), ClaimViewRequest(claim_id="claim1", branch="feature"))


def test_build_claim_view_reports_unknown_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(claim=None)
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    with pytest.raises(ClaimViewUnknownClaimError, match="missing"):
        build_claim_view(_repo(), ClaimViewRequest(claim_id="missing"))
