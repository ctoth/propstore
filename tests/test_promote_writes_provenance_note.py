from __future__ import annotations

from pathlib import Path

from propstore.provenance import read_provenance_note
from propstore.repository import Repository
from propstore.source import promote_source_branch
from tests.test_source_promotion_alignment import _save_source


def test_promote_source_branch_writes_provenance_note(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _save_source(
        repo,
        "paper_source",
        {
            "concepts": [
                {
                    "local_name": "gravity",
                    "proposed_name": "gravity",
                    "definition": "Acceleration due to gravity.",
                    "form": "quantity",
                }
            ]
        },
        claims_payload={
            "source": {"paper": "paper_source"},
            "claims": [
                {
                    "id": "gravity_claim_local",
                    "type": "parameter",
                    "context": "ctx_test",
                    "concept": "gravity",
                    "value": 9.81,
                    "unit": "m/s^2",
                    "provenance": {"paper": "paper_source", "page": 1},
                }
            ],
        },
    )

    result = promote_source_branch(repo, "paper_source")

    assert repo.git is not None
    provenance = read_provenance_note(repo.git.raw_repo, result.commit_sha)
    assert provenance is not None
    assert provenance.operations == ("promote",)
    assert provenance.witnesses[0].method == "promote"
