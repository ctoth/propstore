"""JSON-ready report contracts for the owner-layer view tier (Phase 10-0).

Every view report mixes in ``JsonReportMixin`` so the CLI and web adapters get a
deterministic, JSON-ready payload with no hand-written ``to_dict`` per type.
``ViewState`` enums lower to their string value.
"""

from __future__ import annotations

import json
from pathlib import Path

from propstore.app.claim_views import build_claim_view
from propstore.app.claims import list_claim_views
from propstore.app.concept_views import build_concept_view
from propstore.app.concepts import list_concepts, search_concepts
from propstore.app.neighborhoods import build_semantic_neighborhood
from propstore.app.rendering import AppRenderPolicyRequest, build_render_policy
from propstore.reporting import json_ready
from propstore.world import RenderPolicy, WorldQuery
from tests.app_render_helpers import build_demo_repo


def _policy() -> RenderPolicy:
    return build_render_policy(AppRenderPolicyRequest())


def _is_json_serializable(payload: object) -> bool:
    json.dumps(payload)
    return True


def test_claim_view_report_json_ready(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_claim_view(world, "p_speed", policy=_policy())
    payload = report.to_json()
    assert _is_json_serializable(payload)
    assert payload["concept"]["state"] == "known"
    assert payload["value"]["state"] == "known"
    assert payload["render_policy"]["semantics"] == "grounded"


def test_concept_view_report_json_ready(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_concept_view(world, "speed", policy=_policy())
    payload = report.to_json()
    assert _is_json_serializable(payload)
    assert payload["form"]["state"] == "known"


def test_summary_reports_json_ready(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        claims = list_claim_views(world, policy=_policy()).to_json()
        concepts = list_concepts(world, policy=_policy()).to_json()
        hits = search_concepts(world, "Speed", policy=_policy()).to_json()
    assert _is_json_serializable(claims)
    assert _is_json_serializable(concepts)
    assert _is_json_serializable(hits)


def test_neighborhood_report_json_ready(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_semantic_neighborhood(world, "claim", "p_speed", policy=_policy())
    payload = report.to_json()
    assert _is_json_serializable(payload)
    # ViewState lowers to its string value, not an enum repr.
    assert payload["status"]["state"] == "known"


def test_view_state_enum_lowers_to_string() -> None:
    from propstore.app.view_state import ViewState

    assert json_ready(ViewState.UNKNOWN) == "unknown"
