from __future__ import annotations

from pathlib import Path

from propstore.app.claims import ClaimRelateRequest, relate_claims
from propstore.proposals import commit_stance_proposals, stance_proposal_branch
from propstore.repository import Repository
import propstore.heuristic.embed as embed_mod
import propstore.heuristic.relate as relate_mod


def test_commit_stance_proposals_empty_input_is_noop(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    commit_sha, relpaths = commit_stance_proposals(repo, {}, "test-model")

    assert commit_sha is None
    assert relpaths == []
    assert repo.snapshot.branch_head(stance_proposal_branch()) is None


def test_relate_claims_all_delegates_empty_proposals_to_owner_layer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    repo.sidecar_path.touch()
    calls: list[dict[str, list[dict]]] = []

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

    def fake_commit_stance_proposals(
        repo_arg: Repository,
        stances_by_claim: dict[str, list[dict]],
        model_name: str,
    ) -> tuple[None, list[str]]:
        assert repo_arg is repo
        assert model_name == "test-model"
        calls.append(stances_by_claim)
        return None, []

    monkeypatch.setattr(
        "propstore.proposals.commit_stance_proposals",
        fake_commit_stance_proposals,
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
    )

    assert calls == [{}]
    assert report.commit_sha is None
    assert report.relpaths == ()
