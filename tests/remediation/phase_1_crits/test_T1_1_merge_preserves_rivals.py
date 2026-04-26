from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.claims import claim_file_payload
from propstore.repository import Repository
from propstore.storage import init_git_store
from propstore.merge.merge_commit import create_merge_commit
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import normalize_claims_payload
from tests.family_helpers import load_claim_files


def _claim_yaml(claims: list[dict], paper: str = "test_paper") -> bytes:
    doc = normalize_claims_payload(
        {
            "source": {
                "paper": paper,
                "extraction_model": "test",
                "extraction_date": "2026-01-01",
            },
            "claims": claims,
        }
    )
    return yaml.dump(doc, sort_keys=False).encode()


def _obs_claim(claim_id: str, statement: str) -> dict:
    return {
        "id": claim_id,
        "type": "observation",
        "statement": statement,
        "concepts": ["concept_x"],
        "provenance": {"paper": "test_paper", "page": 1},
    }


def _snapshot(root: Path) -> RepositorySnapshot:
    return RepositorySnapshot(Repository(root))


_PRINTABLE = st.characters(min_codepoint=32, max_codepoint=126)


@settings(max_examples=8, deadline=None)
@given(
    left_body=st.text(alphabet=_PRINTABLE, min_size=1, max_size=50),
    right_body=st.text(alphabet=_PRINTABLE, min_size=1, max_size=50),
)
def test_merge_preserves_rival_bodies(left_body: str, right_body: str) -> None:
    """Two-parent merge keeps rival claim bodies per Clark et al. micropublications."""
    assume(left_body != right_body)

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "knowledge"
        kr = init_git_store(root)
        base_sha = kr.commit_files({}, "seed")
        branch_name = "paper/rival_body"
        kr.create_branch(branch_name, source_commit=base_sha)

        kr.commit_files(
            {"claims/shared.yaml": _claim_yaml([_obs_claim("claim1", left_body)])},
            "left rival body",
        )
        kr.commit_files(
            {"claims/shared.yaml": _claim_yaml([_obs_claim("claim1", right_body)])},
            "right rival body",
            branch=branch_name,
        )

        merge_sha = create_merge_commit(_snapshot(root), "master", branch_name)
        manifest = yaml.safe_load(
            (kr.tree(commit=merge_sha) / "merge" / "manifest.yaml").read_text()
        )
        claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")
        canonical_claim_id = "test_paper:claim1"
        materialized_claim_ids = {
            argument["artifact_id"]
            for argument in manifest["merge"]["arguments"]
            if argument["canonical_claim_id"] == canonical_claim_id
        }
        bodies = [
            claim["statement"]
            for claim_file in claim_files
            for claim in claim_file_payload(claim_file).get("claims", [])
            if claim["artifact_id"] in materialized_claim_ids
        ]

        assert len(materialized_claim_ids) == 2
        assert len(bodies) == 2
        assert left_body in bodies
        assert right_body in bodies
