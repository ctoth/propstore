from __future__ import annotations

from pathlib import Path
import yaml
import pytest

import propstore.app.claims as claims_app
from propstore.app.claim_views import ClaimViewRequest, build_claim_view
from propstore.app.claim_views import ClaimViewUnknownClaimError
from propstore.app.claims import (
    ClaimEmbedRequest,
    ClaimRelateRequest,
    ClaimSimilarRequest,
    UnknownClaimError,
    compare_algorithm_claims_from_repo,
    embed_claim_embeddings,
    find_similar_claims,
    relate_claims,
)
from propstore.proposals import stance_proposal_branch
from propstore.repository import Repository
from tests.family_helpers import materialized_world_store_path


def _repo_with_sidecar(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    materialized_world_store_path(repo, force=True)
    return repo


def test_claim_repo_world_model_wrappers_materialize_and_report_unknown_claim(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    with pytest.raises(ClaimViewUnknownClaimError):
        build_claim_view(repo, ClaimViewRequest(claim_id="claim-a"))

    with pytest.raises(UnknownClaimError):
        compare_algorithm_claims_from_repo(
            repo,
            claims_app.ClaimCompareRequest("claim-a", "claim-b"),
        )


def test_embed_claim_embeddings_uses_claim_declaration_embedding_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    calls: list[tuple[str, str | None, bool, int]] = []

    def fake_embed_for_request(
        sidecar,
        *,
        claim_id,
        embed_all,
        model,
        batch_size,
        on_progress,
    ):
        assert sidecar.exists()
        calls.append((model, claim_id, embed_all, batch_size))
        if on_progress is not None:
            on_progress(model, 3, 5)
        return [(model, {"embedded": 3, "skipped": 1, "errors": 0})]

    monkeypatch.setattr(claims_app, "embed_claims_for_request", fake_embed_for_request)
    progress: list[tuple[str, int, int]] = []

    report = embed_claim_embeddings(
        repo,
        ClaimEmbedRequest(
            claim_id="claim-a",
            embed_all=False,
            model="model-a",
            batch_size=11,
        ),
        on_progress=lambda model_name, done, total: progress.append(
            (model_name, done, total)
        ),
    )

    assert calls == [("model-a", "claim-a", False, 11)]
    assert progress == [("model-a", 3, 5)]
    assert report.results[0].embedded == 3
    assert report.results[0].skipped == 1


def test_find_similar_claims_uses_claim_declaration_similarity_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    captured: dict[str, object] = {}

    def fake_find_similar_rows(
        sidecar,
        *,
        claim_id,
        model,
        top_k,
        agree,
        disagree,
    ):
        captured.update(
            {
                "sidecar_exists": sidecar.exists(),
                "claim_id": claim_id,
                "model_name": model,
                "top_k": top_k,
                "agree": agree,
                "disagree": disagree,
            }
        )
        return [
            {
                "distance": 0.125,
                "id": "claim-b",
                "auto_summary": "close semantic neighbor",
                "source_paper": "paper-b",
            }
        ]

    monkeypatch.setattr(claims_app, "find_similar_claim_rows", fake_find_similar_rows)

    report = find_similar_claims(
        repo,
        ClaimSimilarRequest(
            claim_id="claim-a",
            model=None,
            top_k=7,
        ),
    )

    assert captured == {
        "sidecar_exists": True,
        "claim_id": "claim-a",
        "model_name": None,
        "top_k": 7,
        "agree": False,
        "disagree": False,
    }
    assert report.hits[0].claim_id == "claim-b"
    assert report.hits[0].summary == "close semantic neighbor"


def test_relate_claims_commits_single_claim_proposals_to_branch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)

    monkeypatch.setattr(
        claims_app,
        "relate_claim_from_sidecar",
        lambda sidecar, claim_id, model_name, embedding_model, top_k: [
            {
                "target": "claim-b",
                "type": "supports",
                "strength": "strong",
                "note": "synthetic stance",
                "conditions_differ": None,
                "resolution": {
                    "method": "nli_first_pass",
                    "model": model_name,
                    "confidence": 0.7,
                },
            }
        ],
    )

    report = relate_claims(
        repo,
        ClaimRelateRequest(
            claim_id="claim-a",
            relate_all=False,
            model="test-model",
            embedding_model=None,
            top_k=5,
        ),
    )

    assert report.branch == stance_proposal_branch()
    assert report.commit_sha is not None
    assert len(report.relpaths) == 1
    data = yaml.safe_load(
        repo.git.read_file(report.relpaths[0], commit=report.commit_sha)
    )
    assert data["source_claim"] == "claim-a"
    assert data["classification_model"] == "test-model"
    assert data["target"] == "claim-b"
    assert data["type"] == "supports"


def test_relate_claims_all_reports_summary_without_empty_commit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    progress: list[tuple[int, int]] = []

    monkeypatch.setattr(
        claims_app,
        "relate_all_from_sidecar",
        lambda sidecar, model_name, embedding_model, top_k, *, concurrency, on_progress: {
            "stances_by_claim": {},
            "claims_processed": 4,
            "stances_found": 0,
            "no_relation": 4,
        },
    )

    report = relate_claims(
        repo,
        ClaimRelateRequest(
            claim_id=None,
            relate_all=True,
            model="test-model",
            embedding_model=None,
            top_k=5,
            concurrency=3,
        ),
        on_progress=lambda done, total: progress.append((done, total)),
    )

    assert report.commit_sha is None
    assert report.relpaths == ()
    assert report.claims_processed == 4
    assert report.stances_found == 0
    assert report.no_relation == 4
    assert progress == []
