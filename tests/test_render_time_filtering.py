"""Render-time filtering / non-commitment discipline for the view tier.

Hidden rows are present in storage and filtered at render time, never dropped at
build time. The same corpus yields different views under different policies.
"""

from __future__ import annotations

from pathlib import Path

from propstore.app.claims import list_claim_views
from propstore.app.rendering import AppRenderPolicyRequest, build_render_policy
from propstore.world import WorldQuery
from tests.app_render_helpers import build_demo_repo


def _policy(**kwargs: bool):
    return build_render_policy(AppRenderPolicyRequest(**kwargs))


def test_hidden_rows_remain_in_storage(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        # Storage holds every claim regardless of lifecycle status.
        stored = {str(claim.claim_id) for claim in world.claims_for(None)}
        assert {"p_blocked", "p_draft"} <= stored
        # The default render view hides them — filtered, not deleted.
        default_ids = {
            entry.claim_id
            for entry in list_claim_views(world, policy=_policy()).entries
        }
        assert "p_blocked" not in default_ids
        assert "p_draft" not in default_ids


def test_same_corpus_different_views(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        default_ids = {
            entry.claim_id
            for entry in list_claim_views(world, policy=_policy()).entries
        }
        drafts_ids = {
            entry.claim_id
            for entry in list_claim_views(
                world, policy=_policy(include_drafts=True)
            ).entries
        }
        all_ids = {
            entry.claim_id
            for entry in list_claim_views(
                world, policy=_policy(include_drafts=True, include_blocked=True)
            ).entries
        }
    assert "p_draft" in drafts_ids and "p_draft" not in default_ids
    assert "p_blocked" not in drafts_ids
    assert {"p_draft", "p_blocked"} <= all_ids


def test_draft_only_lifts_drafts_not_blocked(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        ids = {
            entry.claim_id
            for entry in list_claim_views(
                world, policy=_policy(include_drafts=True)
            ).entries
        }
    assert "p_draft" in ids
    assert "p_blocked" not in ids
