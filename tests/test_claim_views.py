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
from propstore.core.claim_values import ClaimProvenance, ClaimSource
from propstore.core.claim_concept_link_roles import ClaimConceptLinkRole
from propstore.core.row_types import ClaimConceptLinkRow, ClaimRow, ConceptRow
from propstore.repository import Repository
from propstore.world import RenderPolicy


class _World:
    def __init__(
        self,
        *,
        claim: ClaimRow | None = None,
        claims: tuple[ClaimRow, ...] = (),
        concept: ConceptRow | None = None,
        concepts: tuple[ConceptRow, ...] = (),
        visible: bool = True,
    ) -> None:
        claim_rows = list(claims)
        if claim is not None:
            claim_rows.append(claim)
        self.claims = {str(item.claim_id): item for item in claim_rows}
        concept_rows = list(concepts)
        if concept is not None:
            concept_rows.append(concept)
        self.concepts = {str(item.concept_id): item for item in concept_rows}
        self.visible = visible

    def get_claim(self, claim_id: str) -> ClaimRow | None:
        return self.claims.get(claim_id)

    def get_concept(self, concept_id: str) -> ConceptRow | None:
        return self.concepts.get(concept_id)

    def claims_with_policy(
        self,
        concept_id: str | None,
        policy: RenderPolicy,
    ) -> list[ClaimRow]:
        if not self.visible:
            return []
        claims = list(self.claims.values())
        if concept_id is None:
            return claims
        return [
            claim
            for claim in claims
            if any(str(link.concept_id) == concept_id for link in claim.concept_links)
        ]

    def resolve_concept(self, name: str) -> str | None:
        for concept in self.concepts.values():
            if name in {str(concept.concept_id), concept.canonical_name}:
                return str(concept.concept_id)
        return None


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
        "concept_links": (
            ClaimConceptLinkRow(
                claim_id="claim1",
                concept_id="concept1",
                role=ClaimConceptLinkRole.OUTPUT,
                ordinal=0,
            ),
        ),
        "value": 12.5,
        "unit": "Hz",
        "value_si": 12.5,
        "uncertainty": 0.2,
        "sample_size": 30,
        "source": ClaimSource(source_id="paper1", slug="paper1"),
        "provenance": ClaimProvenance(paper="paper1", page=4),
    }
    values.update(overrides)
    if "concept_links" not in overrides:
        claim_id = str(values["claim_id"])
        values["concept_links"] = (
            ClaimConceptLinkRow(
                claim_id=claim_id,
                concept_id="concept1",
                role=ClaimConceptLinkRole.OUTPUT,
                ordinal=0,
            ),
        )
    return ClaimRow(**values)


def _concept() -> ConceptRow:
    return ConceptRow(
        concept_id="concept1",
        canonical_name="fundamental_frequency",
        form="frequency",
    )


def _concept2() -> ConceptRow:
    return ConceptRow(
        concept_id="concept2",
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
        claim_type="mechanism",
        concept_links=(
            ClaimConceptLinkRow(
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


def test_list_claim_views_projects_visible_claim_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        claims=(
            _claim(claim_id="claim2", artifact_id="claim2"),
            _claim(claim_id="claim1", artifact_id="claim1"),
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
                artifact_id="claim_obs",
                claim_type="observation",
                concept_links=(
                    ClaimConceptLinkRow(
                        claim_id="claim_obs",
                        concept_id="concept1",
                        role=ClaimConceptLinkRole.ABOUT,
                        ordinal=0,
                    ),
                    ClaimConceptLinkRow(
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
                artifact_id="claim_interval",
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
                artifact_id="claim_eq",
                claim_type="equation",
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
            _claim(claim_id="claim1", artifact_id="claim1", statement="fundamental frequency rises"),
            _claim(claim_id="claim2", artifact_id="claim2", statement="another measurement"),
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
                artifact_id="claim_obs",
                claim_type="observation",
                concept_links=(
                    ClaimConceptLinkRow(
                        claim_id="claim_obs",
                        concept_id="concept1",
                        role=ClaimConceptLinkRole.ABOUT,
                        ordinal=0,
                    ),
                    ClaimConceptLinkRow(
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
