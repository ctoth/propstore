from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import json
from typing import cast

import pytest

from propstore.app import claim_views
from propstore.app.claim_views import (
    ClaimViewBlockedError,
    ClaimViewRequest,
    ClaimViewUnknownClaimError,
    build_claim_view,
)
from propstore.app.rendering import AppRenderPolicyRequest
from propstore.app.repository_views import (
    AppRepositoryViewRequest,
    RepositoryViewUnsupportedStateError,
)
from propstore.families.claims.types import ClaimType
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import Claim, ClaimConceptLink
from propstore.families.concepts.declaration import Concept
from propstore.repository import Repository
from propstore.world import RenderPolicy
from tests.claim_model_helpers import claim_concept_link, claim_model


class _World:
    def __init__(
        self,
        *,
        claim: Claim | None = None,
        claims: tuple[Claim, ...] = (),
        concept: Concept | None = None,
        concepts: tuple[Concept, ...] = (),
        visible: bool = True,
    ) -> None:
        claim_items = list(claims)
        if claim is not None:
            claim_items.append(claim)
        self.claims = {str(item.id): item for item in claim_items}
        concept_items = list(concepts)
        if concept is not None:
            concept_items.append(concept)
        self.concepts: dict[str, Concept] = {}
        for item in concept_items:
            self.concepts[str(item.concept_id)] = item
            self.concepts[str(item.canonical_name)] = item
        self.visible = visible

    def get_claim(self, claim_id: str) -> Claim | None:
        return self.claims.get(claim_id)

    def get_concept(self, concept_id: str) -> Concept | None:
        return self.concepts.get(concept_id)

    def claims_with_policy(
        self,
        concept_id: str | None,
        policy: RenderPolicy,
    ) -> list[Claim]:
        if not self.visible:
            return []
        claims = list(self.claims.values())
        if concept_id is None:
            return claims
        concept = self.get_concept(concept_id)
        if concept is not None:
            concept_id = str(concept.concept_id)
        return [
            claim
            for claim in claims
            if any(str(link.concept_id) == concept_id for link in claim.concept_links)
        ]


@contextmanager
def _open_world(world: _World) -> Iterator[_World]:
    yield world


def _repo() -> Repository:
    return cast(Repository, object())


def _claim_link(
    *,
    claim_id: str,
    concept_id: str,
    role: ClaimConceptLinkRole,
    ordinal: int = 0,
    ) -> ClaimConceptLink:
    return claim_concept_link(
        claim_id=claim_id,
        concept_id=concept_id,
        role=role,
        ordinal=ordinal,
    )


def _claim(
    claim_id: str = "claim1",
    *,
    claim_type: ClaimType = ClaimType.PARAMETER,
    concept_links: tuple[ClaimConceptLink, ...] | None = None,
    value: float | None = 12.5,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    unit: str | None = "Hz",
    value_si: float | None = 12.5,
    uncertainty: float | None = 0.2,
    sample_size: int | None = 30,
    conditions_cel: str | None = None,
    source_slug: str | None = "paper1",
    source_paper: str = "paper1",
    provenance_page: int = 4,
    provenance_json: dict[str, object] | None = None,
    statement: str | None = None,
    expression: str | None = None,
    variables_json: str | None = None,
    build_status: str = "ingested",
    stage: str | None = None,
) -> Claim:
    if concept_links is None:
        concept_links = (
            _claim_link(
                claim_id=claim_id,
                concept_id="concept1",
                role=ClaimConceptLinkRole.OUTPUT,
                ordinal=0,
            ),
        )
    return claim_model(
        claim_id,
        claim_type=claim_type,
        concept_links=concept_links,
        value=value,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        unit=unit,
        value_si=value_si,
        uncertainty=uncertainty,
        sample_size=sample_size,
        conditions_cel=conditions_cel,
        source_slug=source_slug,
        source_paper=source_paper,
        provenance_page=provenance_page,
        provenance_json=provenance_json,
        statement=statement,
        expression=expression,
        variables_json=variables_json,
        stage=stage,
        build_status=build_status,
    )


def _concept() -> Concept:
    return Concept(
        id="concept1",
        canonical_name="fundamental_frequency",
        form="frequency",
    )


def _concept2() -> Concept:
    return Concept(
        id="concept2",
        canonical_name="subglottal_pressure",
        form="pressure",
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
        claim_type=ClaimType.MECHANISM,
        concept_links=(
            _claim_link(
                claim_id="claim1",
                concept_id="concept1",
                role=ClaimConceptLinkRole.ABOUT,
                ordinal=0,
            ),
        ),
        value=None,
        unit=None,
        value_si=None,
        uncertainty=None,
        sample_size=None,
        source_slug=None,
        source_paper="",
        provenance_page=0,
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
    claim = _claim(stage="draft")
    world = _World(claim=claim, concept=_concept(), visible=False)
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    with pytest.raises(ClaimViewBlockedError, match="Not Found"):
        build_claim_view(
            _repo(),
            ClaimViewRequest(
                claim_id="claim1",
                render_policy=AppRenderPolicyRequest(include_drafts=False),
            ),
        )


def test_build_claim_view_rejects_unimplemented_repository_state() -> None:
    with pytest.raises(RepositoryViewUnsupportedStateError, match="branch-qualified"):
        build_claim_view(
            _repo(),
            ClaimViewRequest(
                claim_id="claim1",
                repository_view=AppRepositoryViewRequest(branch="feature"),
            ),
        )


def test_build_claim_view_reports_unknown_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(claim=None)
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    with pytest.raises(ClaimViewUnknownClaimError, match="missing"):
        build_claim_view(_repo(), ClaimViewRequest(claim_id="missing"))


def test_list_claim_views_projects_visible_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        claims=(
            _claim(claim_id="claim2"),
            _claim(claim_id="claim1"),
        ),
        concept=_concept(),
    )
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = claim_views.list_claim_views(_repo(), claim_views.ClaimListRequest(limit=10))

    assert [entry.claim_id for entry in report.entries] == ["claim1", "claim2"]
    assert report.entries[0].concept_name == "fundamental_frequency"
    assert report.entries[0].concept_display == "fundamental_frequency"
    assert report.entries[0].value_display == "12.5 Hz"
    assert report.entries[0].condition_display == "(vacuous)"


def test_list_claim_views_renders_statement_claim_summaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        claims=(
            _claim(
                claim_id="claim_obs",
                claim_type=ClaimType.OBSERVATION,
                concept_links=(
                    _claim_link(
                        claim_id="claim_obs",
                        concept_id="concept1",
                        role=ClaimConceptLinkRole.ABOUT,
                        ordinal=0,
                    ),
                    _claim_link(
                        claim_id="claim_obs",
                        concept_id="concept2",
                        role=ClaimConceptLinkRole.ABOUT,
                        ordinal=1,
                    ),
                ),
                value=None,
                unit=None,
                statement="No interaction was found between aspirin and antioxidant treatments on any outcome.",
            ),
        ),
        concepts=(_concept(), _concept2()),
    )
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = claim_views.list_claim_views(_repo(), claim_views.ClaimListRequest(limit=10))

    assert len(report.entries) == 1
    assert report.entries[0].concept_display == "fundamental_frequency, subglottal_pressure"
    assert report.entries[0].value_display == (
        "No interaction was found between aspirin and antioxidant treatments on any outcome."
    )


def test_list_claim_views_renders_interval_only_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        claims=(
            _claim(
                claim_id="claim_interval",
                value=None,
                lower_bound=0.76,
                upper_bound=1.26,
                unit="dimensionless",
            ),
        ),
        concept=_concept(),
    )
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = claim_views.list_claim_views(_repo(), claim_views.ClaimListRequest(limit=10))

    assert len(report.entries) == 1
    assert report.entries[0].value_display == "0.76 to 1.26 dimensionless"


def test_list_claim_views_renders_equation_variable_concepts_and_expression(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        claims=(
            _claim(
                claim_id="claim_eq",
                claim_type=ClaimType.EQUATION,
                concept_links=(),
                value=None,
                unit=None,
                expression="y = f(x)",
                variables_json=json.dumps(
                    [
                        {"name": "x", "concept": "concept1"},
                        {"name": "y", "concept": "concept2"},
                    ]
                ),
            ),
        ),
        concepts=(_concept(), _concept2()),
    )
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = claim_views.list_claim_views(_repo(), claim_views.ClaimListRequest(limit=10))

    assert len(report.entries) == 1
    assert report.entries[0].concept_display == "fundamental_frequency, subglottal_pressure"
    assert report.entries[0].value_display == "y = f(x)"


def test_search_claim_views_filters_by_query_and_concept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        claims=(
            _claim(claim_id="claim1", statement="fundamental frequency rises"),
            _claim(claim_id="claim2", statement="another measurement"),
        ),
        concept=_concept(),
    )
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = claim_views.search_claim_views(
        _repo(),
        claim_views.ClaimSearchRequest(
            query="rises",
            concept="fundamental_frequency",
            limit=10,
        ),
    )

    assert [entry.claim_id for entry in report.entries] == ["claim1"]


def test_search_claim_views_matches_linked_concept_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        claims=(
            _claim(
                claim_id="claim_obs",
                claim_type=ClaimType.OBSERVATION,
                concept_links=(
                    _claim_link(
                        claim_id="claim_obs",
                        concept_id="concept1",
                        role=ClaimConceptLinkRole.ABOUT,
                        ordinal=0,
                    ),
                    _claim_link(
                        claim_id="claim_obs",
                        concept_id="concept2",
                        role=ClaimConceptLinkRole.ABOUT,
                        ordinal=1,
                    ),
                ),
                value=None,
                unit=None,
                statement="Interaction summary.",
            ),
        ),
        concepts=(_concept(), _concept2()),
    )
    monkeypatch.setattr(claim_views, "open_app_world_model", lambda repo: _open_world(world))

    report = claim_views.search_claim_views(
        _repo(),
        claim_views.ClaimSearchRequest(query="subglottal_pressure", limit=10),
    )

    assert [entry.claim_id for entry in report.entries] == ["claim_obs"]
