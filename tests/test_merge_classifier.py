"""Regression tests for the new repository merge surface."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import yaml
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from propstore.families.identity.claims import compute_claim_version_id
from quire.git_store import GitStore
from propstore.storage import init_git_store
from propstore.repository import Repository
from propstore.merge.merge_classifier import build_merge_framework
from propstore.storage.merge_commit import create_merge_commit
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import make_claim_identity, normalize_claims_payload


def _claim_yaml(claims: list[dict], paper: str = "test_paper") -> bytes:
    doc = normalize_claims_payload({
        "source": {
            "paper": paper,
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": claims,
    })
    return yaml.dump(doc, sort_keys=False).encode()


def _claims_commit_payload(claim_ids: list[str], *, prefix: str) -> dict[str, bytes]:
    if not claim_ids:
        return {}
    midpoint = max(1, len(claim_ids) // 2)
    payload: dict[str, bytes] = {}
    first_half = claim_ids[:midpoint]
    second_half = claim_ids[midpoint:]
    if first_half:
        payload[f"claims/{prefix}_a.yaml"] = _claim_yaml(
            [_obs_claim(claim_id, f"{claim_id} statement", [f"concept_{claim_id}"]) for claim_id in first_half]
        )
    if second_half:
        payload[f"claims/{prefix}_b.yaml"] = _claim_yaml(
            [_obs_claim(claim_id, f"{claim_id} statement", [f"concept_{claim_id}"]) for claim_id in reversed(second_half)]
        )
    return payload


def _obs_claim(
    cid: str,
    statement: str,
    concepts: list[str],
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "observation",
        "statement": statement,
        "concepts": concepts,
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def _param_claim(
    cid: str,
    concept: str,
    value: float,
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "parameter",
        "concept": concept,
        "value": value,
        "unit": "K",
        "concepts": [concept],
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def _claim_yaml_with_explicit_identities(claims: list[dict], paper: str = "test_paper") -> bytes:
    normalized = normalize_claims_payload(
        {
            "source": {
                "paper": paper,
                "extraction_model": "test",
                "extraction_date": "2026-01-01",
            },
            "claims": claims,
        }
    )
    rewritten_claims: list[dict] = []
    for original, normalized_claim in zip(claims, normalized["claims"], strict=True):
        merged = dict(normalized_claim)
        if "artifact_id" in original:
            merged["artifact_id"] = original["artifact_id"]
        if "logical_ids" in original:
            merged["logical_ids"] = original["logical_ids"]
        merged["version_id"] = compute_claim_version_id(merged)
        rewritten_claims.append(merged)
    normalized["claims"] = rewritten_claims
    return yaml.dump(normalized, sort_keys=False).encode()


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))


def test_identical_claims_collapse_to_one_emitted_argument(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )
    branch_name = "paper/test"
    kr.create_branch(branch_name, source_commit=base_sha)

    merge = build_merge_framework(_snapshot(kr), "master", branch_name)

    assert len(merge.arguments) == 1
    assert merge.arguments[0].claim_id == make_claim_identity("claim1", namespace="test_paper")["artifact_id"]
    assert merge.arguments[0].branch_origins == ("master", branch_name)


def test_syntax_independence_claim_order(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    claim_a = _obs_claim("claimA", "A", ["concept_a"])
    claim_b = _obs_claim("claimB", "B", ["concept_b"])
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([claim_a, claim_b])},
        "seed",
    )
    branch_name = "paper/reorder"
    kr.create_branch(branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([claim_b, claim_a])},
        "reorder",
    )

    merge = build_merge_framework(_snapshot(kr), "master", branch_name)
    emitted = {argument.claim_id for argument in merge.arguments}
    assert emitted == {
        make_claim_identity("claimA", namespace="test_paper")["artifact_id"],
        make_claim_identity("claimB", namespace="test_paper")["artifact_id"],
    }


def test_syntax_independence_filename(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    claims = [_obs_claim("claimA", "Observation A", ["concept_a"])]
    base_sha = kr.commit_files(
        {"claims/original.yaml": _claim_yaml(claims)},
        "seed",
    )
    branch_name = "paper/rename"
    kr.create_branch(branch_name, source_commit=base_sha)

    kr.commit_batch(
        adds={"claims/renamed.yaml": _claim_yaml(claims)},
        deletes=["claims/original.yaml"],
        message="rename file",
    )

    merge = build_merge_framework(_snapshot(kr), "master", branch_name)
    assert len(merge.arguments) == 1
    assert merge.arguments[0].claim_id == make_claim_identity("claimA", namespace="test_paper")["artifact_id"]


def test_merge_commit_has_two_parents(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )
    branch_name = "paper/merge_test"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left", ["concept_a"])])},
        "left",
    )
    left_sha = kr.branch_sha("master")
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right", ["concept_b"])])},
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(_snapshot(kr), "master", branch_name)
    assert kr.commit_parent_shas(merge_sha) == [left_sha, kr.branch_sha(branch_name)]


def test_merge_commit_preserves_both_disjoint_additions(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )
    branch_name = "paper/preserve"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left only", ["concept_a"])])},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right only", ["concept_b"])])},
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(_snapshot(kr), "master", branch_name)

    from propstore.claims import claim_file_payload
    from tests.family_helpers import load_claim_files

    claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")
    all_claim_ids = {
        claim["artifact_id"]
        for claim_file in claim_files
        for claim in claim_file_payload(claim_file).get("claims", [])
    }
    assert make_claim_identity("claimL", namespace="test_paper")["artifact_id"] in all_claim_ids
    assert make_claim_identity("claimR", namespace="test_paper")["artifact_id"] in all_claim_ids


def test_merge_commit_valid_claims(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )
    branch_name = "paper/valid"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left", ["concept_a"])])},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right", ["concept_b"])])},
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(_snapshot(kr), "master", branch_name)

    from tests.family_helpers import load_claim_files
    from propstore.compiler.context import build_compilation_context_from_repo
    from propstore.families.claims.passes import validate_claims

    claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")
    result = validate_claims(
        claim_files,
        build_compilation_context_from_repo(None),
    )
    assert not result.errors


def test_conflict_merge_is_deterministic(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/conflict"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right",
        branch=branch_name,
    )

    merge_sha_a = create_merge_commit(_snapshot(kr), "master", branch_name, target_branch="merge_a")
    merge_sha_b = create_merge_commit(_snapshot(kr), "master", branch_name, target_branch="merge_b")

    assert kr.flat_tree_entries(merge_sha_a) == kr.flat_tree_entries(merge_sha_b)


def test_same_logical_id_different_artifacts_merge_as_conflicting_alternatives(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/logical_conflict"
    kr.create_branch(branch_name, source_commit=base_sha)

    shared_logical_ids = [{"namespace": "shared_paper", "value": "claim1"}]
    left_claim = _param_claim("claim1", "concept_x", 300.0)
    left_claim["artifact_id"] = "ps:claim:leftlogical0001"
    left_claim["logical_ids"] = shared_logical_ids
    right_claim = _param_claim("claim1", "concept_x", 150.0)
    right_claim["artifact_id"] = "ps:claim:rightlogical0001"
    right_claim["logical_ids"] = shared_logical_ids

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml_with_explicit_identities([left_claim])},
        "left",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml_with_explicit_identities([right_claim])},
        "right",
        branch=branch_name,
    )

    merge = build_merge_framework(_snapshot(kr), "master", branch_name)

    assert len(merge.arguments) == 2
    assert {argument.canonical_claim_id for argument in merge.arguments} == {"shared_paper:claim1"}
    assert len(merge.framework.attacks) == 2
    assert not merge.framework.ignorance


def test_merge_commit_preserves_branch_origin_provenance(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/conflict"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right",
        branch=branch_name,
    )

    merge = build_merge_framework(_snapshot(kr), "master", branch_name)
    expected_origins = {
        argument.claim_id: list(argument.branch_origins)
        for argument in merge.arguments
    }

    merge_sha = create_merge_commit(_snapshot(kr), "master", branch_name)

    manifest_path = kr.tree(commit=merge_sha) / "merge" / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    observed_origins = {
        row["claim_id"]: row["branch_origins"]
        for row in manifest["merge"]["arguments"]
    }
    assert observed_origins == expected_origins


@settings(
    deadline=None,
)
@given(
    left_ids=st.lists(
        st.from_regex(r"left_[a-z]{1,4}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    ),
    right_ids=st.lists(
        st.from_regex(r"right_[a-z]{1,4}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    ),
)
def test_merge_commit_materializes_exact_union_of_disjoint_branch_additions(
    left_ids: list[str],
    right_ids: list[str],
):
    from propstore.claims import claim_file_payload
    from tests.family_helpers import load_claim_files

    assume(set(left_ids).isdisjoint(right_ids))

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "knowledge"
        kr = init_git_store(root)
        base_sha = kr.commit_files({}, "seed")
        branch_name = "paper/property_preserve"
        kr.create_branch(branch_name, source_commit=base_sha)

        left_payload = _claims_commit_payload(left_ids, prefix="left")
        right_payload = _claims_commit_payload(right_ids, prefix="right")
        if left_payload:
            kr.commit_files(left_payload, "left additions")
        if right_payload:
            kr.commit_files(right_payload, "right additions", branch=branch_name)

        merge_sha = create_merge_commit(_snapshot(kr), "master", branch_name)
        claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")
        merged_artifact_ids = {
            claim["artifact_id"]
            for claim_file in claim_files
            for claim in claim_file_payload(claim_file).get("claims", [])
        }
        expected_artifact_ids = {
            make_claim_identity(claim_id, namespace="test_paper")["artifact_id"]
            for claim_id in [*left_ids, *right_ids]
        }
        assert merged_artifact_ids == expected_artifact_ids
