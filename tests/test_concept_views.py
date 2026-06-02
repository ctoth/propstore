from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

import pytest
from quire.documents import LoadedDocument

from propstore.app import concept_views
from propstore.app.concept_views import (
    ConceptViewRequest,
    ConceptViewUnknownConceptError,
    build_concept_view,
)
from propstore.app.rendering import AppRenderPolicyRequest
from propstore.app.repository_views import (
    AppRepositoryViewRequest,
    RepositoryViewUnsupportedStateError,
)
from propstore.families.claims.types import ClaimType
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import Claim, ClaimConceptLink
from propstore.families.concepts.declaration import (
    Concept,
    ConceptDocument,
    ConceptLogicalIdDocument,
    LexicalEntryDocument,
    LexicalFormDocument,
    LexicalSenseDocument,
    OntologyReferenceDocument,
)
from propstore.repository import Repository
from propstore.world import RenderPolicy
from tests.claim_model_helpers import claim_concept_link


class _World:
    def __init__(
        self,
        *,
        concept: Concept | None = None,
        claims: tuple[Claim, ...] = (),
        visible_ids: tuple[str, ...] | None = None,
    ) -> None:
        self.concept = concept
        self.claims = {str(claim.id): claim for claim in claims}
        self.visible_ids = set(self.claims) if visible_ids is None else set(visible_ids)

    def get_concept(self, concept_id: str) -> Concept | None:
        if self.concept is None:
            return None
        if concept_id in {
            str(self.concept.concept_id),
            self.concept.canonical_name,
            self.concept.primary_logical_id,
        }:
            return self.concept
        return None

    def claims_for(self, concept_id: str) -> list[Claim]:
        if self.concept is None:
            return []
        concept = self.get_concept(concept_id)
        resolved = str(concept.concept_id) if concept is not None else concept_id
        return [
            claim
            for claim in self.claims.values()
            if str(claim.value_concept_id or "") == resolved
        ]

    def claims_related_to_concept(self, concept_id: str) -> list[Claim]:
        if self.concept is None:
            return []
        concept = self.get_concept(concept_id)
        resolved = str(concept.concept_id) if concept is not None else concept_id
        return [
            claim
            for claim in self.claims.values()
            if (
                str(claim.output_concept_id or "") == resolved
                or str(claim.target_concept or "") == resolved
                or resolved in {str(linked_id) for linked_id in claim.about_concept_ids}
                or resolved in {str(linked_id) for linked_id in claim.input_concept_ids}
            )
        ]

    def claims_with_policy(
        self,
        concept_id: str | None,
        policy: RenderPolicy,
    ) -> list[Claim]:
        if concept_id is None:
            return []
        concept = self.get_concept(concept_id)
        resolved = str(concept.concept_id) if concept is not None else concept_id
        return [
            claim
            for claim_id, claim in self.claims.items()
            if claim_id in self.visible_ids
            and (
                str(claim.output_concept_id or "") == resolved
                or str(claim.target_concept or "") == resolved
                or resolved
                in {str(concept_id) for concept_id in claim.about_concept_ids}
                or resolved
                in {str(concept_id) for concept_id in claim.input_concept_ids}
            )
        ]


@contextmanager
def _open_world(world: _World) -> Iterator[_World]:
    yield world


def _repo() -> Repository:
    return cast(Repository, object())


def _concept() -> Concept:
    return Concept(
        id="concept1",
        canonical_name="fundamental_frequency",
        status="accepted",
        definition="Primary oscillation rate.",
        kind_type="quantity",
        form="frequency",
        domain="speech",
        primary_logical_id="speech:fundamental_frequency",
    )


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


def _concept_entry() -> LoadedDocument[ConceptDocument]:
    ontology_reference = OntologyReferenceDocument(
        uri="ps:concept:fundamental_frequency",
        label="fundamental_frequency",
    )
    document = ConceptDocument(
        artifact_id="ps:concept:fundamental_frequency",
        status="accepted",
        ontology_reference=ontology_reference,
        lexical_entry=LexicalEntryDocument(
            identifier="fundamental_frequency",
            canonical_form=LexicalFormDocument(
                written_rep="fundamental_frequency",
                language="en",
            ),
            senses=(LexicalSenseDocument(reference=ontology_reference),),
            physical_dimension_form="frequency",
        ),
        logical_ids=(
            ConceptLogicalIdDocument(
                namespace="speech",
                value="fundamental_frequency",
            ),
        ),
        version_id="concept-version-1",
        domain="speech",
    )
    return LoadedDocument(
        filename="fundamental_frequency.yaml",
        artifact_path=None,
        store_root=None,
        document=document,
    )


def test_build_concept_view_returns_typed_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        concept=_concept(),
        claims=(
            _claim("claim-visible-a"),
            _claim("claim-visible-b", claim_type=ClaimType.MEASUREMENT, value=101.5),
            _claim("claim-blocked", value=98.0),
        ),
        visible_ids=("claim-visible-a", "claim-visible-b"),
    )
    monkeypatch.setattr(
        concept_views, "open_app_world_model", lambda repo: _open_world(world)
    )
    monkeypatch.setattr(
        concept_views, "_find_concept_entry", lambda repo, handle: _concept_entry()
    )

    report = build_concept_view(
        _repo(),
        ConceptViewRequest(
            concept_id_or_name="fundamental_frequency",
            render_policy=AppRenderPolicyRequest(include_blocked=False),
        ),
    )

    assert report.concept_id == "concept1"
    assert report.logical_id == "speech:fundamental_frequency"
    assert report.artifact_id == "ps:concept:fundamental_frequency"
    assert report.version_id == "concept-version-1"
    assert report.kind_type == "quantity"
    assert report.form.state == "known"
    assert report.form.form_name == "frequency"
    assert report.form.unit == "Hz"
    assert report.status.state == "known"
    assert report.status.visible_claim_count == 2
    assert report.status.blocked_claim_count == 0
    assert report.status.total_claim_count == 2
    assert {group.claim_type for group in report.claim_groups} == {
        "measurement",
        "parameter",
    }
    assert report.value_summary.state == "known"
    assert report.value_summary.claim_count == 2
    assert report.uncertainty_summary.state == "known"
    assert report.provenance_summary.state == "known"
    assert report.provenance_summary.papers == ("paper1",)
    assert len(report.related_claim_links) == 2


def test_build_concept_view_reports_blocked_when_all_claims_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        concept=_concept(),
        claims=(_claim("claim-hidden"),),
        visible_ids=(),
    )
    monkeypatch.setattr(
        concept_views, "open_app_world_model", lambda repo: _open_world(world)
    )
    monkeypatch.setattr(
        concept_views, "_find_concept_entry", lambda repo, handle: _concept_entry()
    )

    report = build_concept_view(
        _repo(), ConceptViewRequest(concept_id_or_name="concept1")
    )

    assert report.status.state == "missing"
    assert report.status.visible_claim_count == 0
    assert report.status.blocked_claim_count == 0
    assert report.status.total_claim_count == 0
    assert "No claims refer to this concept" in report.status.reason


def test_build_concept_view_counts_about_links_as_related_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(
        concept=_concept(),
        claims=(
            _claim(
                "claim-about-only",
                claim_type=ClaimType.OBSERVATION,
                concept_links=(
                    _claim_link(
                        claim_id="claim-about-only",
                        concept_id="concept1",
                        role=ClaimConceptLinkRole.ABOUT,
                    ),
                ),
                value=None,
                unit=None,
                uncertainty=None,
                sample_size=None,
                statement="Observed at concept1",
            ),
        ),
        visible_ids=("claim-about-only",),
    )
    monkeypatch.setattr(
        concept_views, "open_app_world_model", lambda repo: _open_world(world)
    )
    monkeypatch.setattr(
        concept_views, "_find_concept_entry", lambda repo, handle: _concept_entry()
    )

    report = build_concept_view(
        _repo(), ConceptViewRequest(concept_id_or_name="concept1")
    )

    assert report.status.state == "known"
    assert report.status.total_claim_count == 1
    assert report.status.visible_claim_count == 1
    assert report.claim_groups[0].claim_type == "observation"
    assert report.related_claim_links[0].relation == "related"


def test_build_concept_view_rejects_unimplemented_repository_state() -> None:
    with pytest.raises(RepositoryViewUnsupportedStateError, match="branch-qualified"):
        build_concept_view(
            _repo(),
            ConceptViewRequest(
                concept_id_or_name="concept1",
                repository_view=AppRepositoryViewRequest(branch="feature"),
            ),
        )


def test_build_concept_view_reports_unknown_concept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _World(concept=None)
    monkeypatch.setattr(
        concept_views, "open_app_world_model", lambda repo: _open_world(world)
    )
    monkeypatch.setattr(concept_views, "_find_concept_entry", lambda repo, handle: None)

    with pytest.raises(ConceptViewUnknownConceptError, match="missing"):
        build_concept_view(
            _repo(),
            ConceptViewRequest(concept_id_or_name="missing"),
        )
