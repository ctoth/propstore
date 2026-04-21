from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import yaml
import pytest

import propstore.app.claims as claims_app
from propstore.app.claims import (
    ClaimEmbedRequest,
    ClaimRelateRequest,
    ClaimSidecarMissingError,
    ClaimSimilarRequest,
    compare_algorithm_claims_from_repo,
    embed_claim_embeddings,
    find_similar_claims,
    relate_claims,
    show_claim_from_repo,
)
import propstore.embed as embed_mod
import propstore.relate as relate_mod
from propstore.proposals import stance_proposal_branch
from propstore.repository import Repository


def _repo_with_sidecar(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    repo.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    repo.sidecar_path.touch()
    return repo


def test_claim_repo_world_model_wrappers_report_missing_sidecar(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    with pytest.raises(ClaimSidecarMissingError):
        show_claim_from_repo(repo, "claim-a")

    with pytest.raises(ClaimSidecarMissingError):
        compare_algorithm_claims_from_repo(
            repo,
            claims_app.ClaimCompareRequest("claim-a", "claim-b"),
        )


def test_embed_claim_embeddings_owns_connection_and_reports_progress(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    conn = MagicMock()
    calls: list[tuple[str, list[str] | None, int]] = []

    def fake_embed_claims(
        conn_arg,
        model_name,
        *,
        claim_ids,
        batch_size,
        on_progress,
    ):
        assert conn_arg is conn
        calls.append((model_name, claim_ids, batch_size))
        if on_progress is not None:
            on_progress(3, 5)
        return {"embedded": 3, "skipped": 1, "errors": 0}

    monkeypatch.setattr(claims_app, "connect_sidecar", lambda path: conn)
    monkeypatch.setattr(embed_mod, "_load_vec_extension", lambda conn_arg: None)
    monkeypatch.setattr(embed_mod, "embed_claims", fake_embed_claims)
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

    assert calls == [("model-a", ["claim-a"], 11)]
    assert progress == [("model-a", 3, 5)]
    assert report.results[0].embedded == 3
    assert report.results[0].skipped == 1
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


def test_find_similar_claims_uses_registered_default_model_and_closes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    conn = MagicMock()
    captured: dict[str, object] = {}

    def fake_find_similar(conn_arg, claim_id, model_name, *, top_k):
        captured.update(
            {
                "conn": conn_arg,
                "claim_id": claim_id,
                "model_name": model_name,
                "top_k": top_k,
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

    monkeypatch.setattr(claims_app, "connect_sidecar", lambda path: conn)
    monkeypatch.setattr(embed_mod, "_load_vec_extension", lambda conn_arg: None)
    monkeypatch.setattr(
        embed_mod,
        "get_registered_models",
        lambda conn_arg: [{"model_name": "model-a"}],
    )
    monkeypatch.setattr(embed_mod, "find_similar", fake_find_similar)

    report = find_similar_claims(
        repo,
        ClaimSimilarRequest(
            claim_id="claim-a",
            model=None,
            top_k=7,
        ),
    )

    assert captured == {
        "conn": conn,
        "claim_id": "claim-a",
        "model_name": "model-a",
        "top_k": 7,
    }
    assert report.hits[0].claim_id == "claim-b"
    assert report.hits[0].summary == "close semantic neighbor"
    conn.close.assert_called_once()


def test_relate_claims_commits_single_claim_proposals_to_branch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)

    monkeypatch.setattr(embed_mod, "_load_vec_extension", lambda conn: None)
    monkeypatch.setattr(
        relate_mod,
        "relate_claim",
        lambda conn, claim_id, model_name, embedding_model, top_k: [
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

    assert report.branch == stance_proposal_branch(repo)
    assert report.commit_sha is not None
    assert report.relpaths == ("stances/claim-a.yaml",)
    data = yaml.safe_load(
        repo.git.read_file("stances/claim-a.yaml", commit=report.commit_sha)
    )
    assert data["source_claim"] == "claim-a"
    assert data["classification_model"] == "test-model"
    assert data["stances"][0]["target"] == "claim-b"


def test_relate_claims_all_reports_summary_without_empty_commit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    progress: list[tuple[int, int]] = []

    monkeypatch.setattr(embed_mod, "_load_vec_extension", lambda conn: None)
    monkeypatch.setattr(
        relate_mod,
        "relate_all",
        lambda conn, model_name, embedding_model, top_k, *, concurrency, on_progress: {
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
