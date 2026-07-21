"""Single-concept view + concept list/search summary (Phase 10-0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.app.concept_views import (
    ConceptViewUnknownConceptError,
    build_concept_view,
)
from propstore.app.concepts import (
    ConceptSearchSyntaxError,
    list_concepts,
    search_concepts,
)
from propstore.app.concepts.display import ConceptDisplayError
from propstore.app.rendering import AppRenderPolicyRequest, build_render_policy
from propstore.app.view_state import ViewState
from propstore.families.concepts import Concept
from propstore.world import RenderPolicy, WorldQuery
from tests.app_render_helpers import build_demo_repo


def _default_policy() -> RenderPolicy:
    return build_render_policy(AppRenderPolicyRequest())


def _include_all_policy() -> RenderPolicy:
    return build_render_policy(
        AppRenderPolicyRequest(include_drafts=True, include_blocked=True)
    )


def test_concept_view_known(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_concept_view(world, "speed", policy=_default_policy())
    assert report.canonical_name == "speed"
    assert report.form.state is ViewState.KNOWN
    assert report.form.form_name == "velocity"
    assert report.status.state is ViewState.KNOWN
    assert report.value_summary.state is ViewState.KNOWN
    assert report.provenance_summary.state is ViewState.MISSING


def test_concept_view_resolves_by_name(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    repo.families.concept.save(
        "ps:concept:velocity",
        Concept(concept_id="ps:concept:velocity", canonical_name="velocity"),
        message="m",
    )
    with WorldQuery(repo) as world:
        report = build_concept_view(world, "velocity", policy=_default_policy())
    assert report.concept_id == "ps:concept:velocity"


def test_concept_form_missing_without_lexical_entry(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_concept_view(world, "distance", policy=_default_policy())
    assert report.form.state is ViewState.MISSING
    assert report.form.form_name is None


def test_concept_claim_groups_and_related_links(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_concept_view(world, "speed", policy=_default_policy())
    group_types = {group.claim_type for group in report.claim_groups}
    assert {"parameter", "observation", "mechanism"} <= group_types
    relations = {link.claim_id: link.relation for link in report.related_claim_links}
    assert relations["p_speed"] == "instantiates"


def test_concept_status_missing_when_no_claims(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        # draftconcept has no claims at all -> the status section is honestly
        # MISSING rather than a fabricated zero-value "known".
        report = build_concept_view(world, "draftconcept", policy=_include_all_policy())
    assert report.status.state is ViewState.MISSING
    assert report.status.total_claim_count == 0


def test_concept_view_include_blocked_split(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_concept_view(world, "distance", policy=_include_all_policy())
    assert report.status.blocked_claim_count == 0  # all visible when included
    assert report.status.total_claim_count >= 2


def test_unknown_concept_raises(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        with pytest.raises(ConceptViewUnknownConceptError):
            build_concept_view(world, "nope", policy=_default_policy())


def test_list_concepts_hides_drafts_by_default(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = list_concepts(world, policy=_default_policy())
    ids = {entry.concept_id for entry in report.entries}
    assert report.concepts_found is True
    assert "speed" in ids
    assert "draftconcept" not in ids


def test_list_concepts_includes_drafts_when_opted_in(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = list_concepts(world, policy=_include_all_policy())
    ids = {entry.concept_id for entry in report.entries}
    assert "draftconcept" in ids


def test_search_concepts_substring(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = search_concepts(world, "Spe", policy=_default_policy())
    ids = {hit.concept_id for hit in report.hits}
    assert ids == {"speed"}


def test_concept_search_syntax_error_is_display_error() -> None:
    err = ConceptSearchSyntaxError("bad(")
    assert isinstance(err, ConceptDisplayError)
    assert err.query == "bad("
