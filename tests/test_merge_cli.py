"""CLI tests for formal merge inspection and execution."""
from __future__ import annotations

from copy import deepcopy

import yaml
import pytest
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from propstore.storage.branch import create_branch
from propstore.storage.merge_classifier import build_merge_framework
from propstore.storage.merge_report import summarize_merge_framework
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import normalize_claims_payload


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


def _claim_yaml_with_explicit_identities(claims: list[dict], paper: str = "test_paper") -> bytes:
    doc = normalize_claims_payload({
        "source": {
            "paper": paper,
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": claims,
    })
    rewritten_claims: list[dict] = []
    for original, normalized_claim in zip(claims, doc["claims"], strict=True):
        merged = deepcopy(normalized_claim)
        artifact_id = original.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id:
            merged["artifact_id"] = artifact_id
        logical_ids = original.get("logical_ids")
        if isinstance(logical_ids, list):
            merged["logical_ids"] = logical_ids
        rewritten_claims.append(merged)
    doc["claims"] = rewritten_claims
    return yaml.dump(doc, sort_keys=False).encode()


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


def _snapshot(repo: Repository) -> RepositorySnapshot:
    return repo.snapshot


def test_merge_inspect_cli_surfaces_query_summary(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    base_sha = git.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/phi"
    create_branch(git, branch_name, source_commit=base_sha)
    git.commit_files(
        {
            "claims/shared.yaml": _claim_yaml(
                [_param_claim("claim1", "concept_x", 300.0, conditions=["temp > 300"])]
            )
        },
        "left",
    )
    git.commit_files(
        {
            "claims/shared.yaml": _claim_yaml(
                [_param_claim("claim1", "concept_x", 150.0, conditions=["temp < 200"])]
            )
        },
        "right",
        branch=branch_name,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-C", str(repo.root), "merge", "inspect", "master", branch_name],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["surface"] == "formal_merge_report"
    assert payload["framework_type"] == "partial_argumentation_framework"
    assert payload["completion_count"] == 4
    assert len(payload["credulous"]) == 2
    assert payload["relation_counts"] == {
        "attack": 0,
        "ignorance": 2,
        "non_attack": 2,
    }
    assert payload["canonical_groups"] == {
        "test_paper:claim1": sorted(payload["arguments"]),
    }
    assert len(payload["argument_details"]) == 2


@pytest.mark.parametrize("semantics", ["grounded", "preferred"])
def test_merge_inspect_cli_matches_report_helper_output(tmp_path, semantics):
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    base_sha = git.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/differential"
    create_branch(git, branch_name, source_commit=base_sha)
    git.commit_files(
        {
            "claims/shared.yaml": _claim_yaml(
                [_param_claim("claim1", "concept_x", 300.0, conditions=["temp > 300"])]
            )
        },
        "left",
    )
    git.commit_files(
        {
            "claims/shared.yaml": _claim_yaml(
                [_param_claim("claim1", "concept_x", 150.0, conditions=["temp < 200"])]
            )
        },
        "right",
        branch=branch_name,
    )

    expected = summarize_merge_framework(
        build_merge_framework(_snapshot(repo), "master", branch_name),
        semantics=semantics,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "merge",
            "inspect",
            "master",
            branch_name,
            "--semantics",
            semantics,
        ],
    )

    assert result.exit_code == 0, result.output
    assert yaml.safe_load(result.output) == expected


def test_merge_commit_cli_surfaces_storage_commit_metadata(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    base_sha = git.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/conflict"
    create_branch(git, branch_name, source_commit=base_sha)
    git.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left",
    )
    git.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right",
        branch=branch_name,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-C", str(repo.root), "merge", "commit", "master", branch_name],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["surface"] == "storage_merge_commit"
    assert payload["branch_a"] == "master"
    assert payload["branch_b"] == branch_name
    assert payload["target_branch"] == "master"
    assert payload["claims_path"] == "claims/merged.yaml"
    assert payload["manifest_path"] == "merge/manifest.yaml"
    assert len(payload["commit_sha"]) == 40
    assert "completion_count" not in payload


def test_merge_inspect_cli_surfaces_semantic_candidate_details(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    base_sha = git.commit_files({}, "seed")
    branch_name = "paper/candidates"
    create_branch(git, branch_name, source_commit=base_sha)

    left_claim = {
        "id": "claim_a",
        "type": "observation",
        "statement": "Equivalent observation",
        "concepts": ["concept_x"],
        "provenance": {"paper": "left_paper", "page": 1},
        "artifact_id": "ps:claim:leftcandidate0001",
        "logical_ids": [{"namespace": "left_paper", "value": "claim_a"}],
    }
    right_claim = {
        "id": "claim_b",
        "type": "observation",
        "statement": "Equivalent observation",
        "concepts": ["concept_x"],
        "provenance": {"paper": "right_paper", "page": 1},
        "artifact_id": "ps:claim:rightcandidate0001",
        "logical_ids": [{"namespace": "right_paper", "value": "claim_b"}],
    }

    git.commit_files(
        {"claims/left.yaml": _claim_yaml_with_explicit_identities([left_claim], paper="left_paper")},
        "left",
    )
    git.commit_files(
        {"claims/right.yaml": _claim_yaml_with_explicit_identities([right_claim], paper="right_paper")},
        "right",
        branch=branch_name,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-C", str(repo.root), "merge", "inspect", "master", branch_name],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["semantic_candidates"] == [
        ["ps:claim:leftcandidate0001", "ps:claim:rightcandidate0001"]
    ]
    assert payload["semantic_candidate_details"] == [
        {
            "claim_ids": ["ps:claim:leftcandidate0001", "ps:claim:rightcandidate0001"],
            "logical_ids": ["left_paper:claim_a", "right_paper:claim_b"],
            "artifact_ids": ["ps:claim:leftcandidate0001", "ps:claim:rightcandidate0001"],
            "arguments": [
                {
                    "claim_id": "ps:claim:leftcandidate0001",
                    "logical_id": "left_paper:claim_a",
                    "artifact_id": "ps:claim:leftcandidate0001",
                    "branch_origins": ["master"],
                    "source_paper": "left_paper",
                },
                {
                    "claim_id": "ps:claim:rightcandidate0001",
                    "logical_id": "right_paper:claim_b",
                    "artifact_id": "ps:claim:rightcandidate0001",
                    "branch_origins": [branch_name],
                    "source_paper": "right_paper",
                },
            ],
        }
    ]


def test_merge_commit_cli_reports_semantic_candidate_count(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    base_sha = git.commit_files({}, "seed")
    branch_name = "paper/candidates"
    create_branch(git, branch_name, source_commit=base_sha)

    left_claim = {
        "id": "claim_a",
        "type": "observation",
        "statement": "Equivalent observation",
        "concepts": ["concept_x"],
        "provenance": {"paper": "left_paper", "page": 1},
        "artifact_id": "ps:claim:leftcandidate0001",
        "logical_ids": [{"namespace": "left_paper", "value": "claim_a"}],
    }
    right_claim = {
        "id": "claim_b",
        "type": "observation",
        "statement": "Equivalent observation",
        "concepts": ["concept_x"],
        "provenance": {"paper": "right_paper", "page": 1},
        "artifact_id": "ps:claim:rightcandidate0001",
        "logical_ids": [{"namespace": "right_paper", "value": "claim_b"}],
    }

    git.commit_files(
        {"claims/left.yaml": _claim_yaml_with_explicit_identities([left_claim], paper="left_paper")},
        "left",
    )
    git.commit_files(
        {"claims/right.yaml": _claim_yaml_with_explicit_identities([right_claim], paper="right_paper")},
        "right",
        branch=branch_name,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-C", str(repo.root), "merge", "commit", "master", branch_name],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["semantic_candidate_count"] == 1


def test_merge_commit_cli_matches_materialized_merge_state(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    base_sha = git.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/storage"
    create_branch(git, branch_name, source_commit=base_sha)
    git.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left",
    )
    git.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right",
        branch=branch_name,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-C", str(repo.root), "merge", "commit", "master", branch_name],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    commit_sha = payload["commit_sha"]
    assert git.head_sha() == commit_sha

    merged_claims = yaml.safe_load(
        (git.tree(commit=commit_sha) / "claims" / "merged.yaml").read_text()
    )
    manifest = yaml.safe_load(
        (git.tree(commit=commit_sha) / "merge" / "manifest.yaml").read_text()
    )

    assert payload["claims_path"] == "claims/merged.yaml"
    assert payload["manifest_path"] == "merge/manifest.yaml"
    assert manifest["merge"]["branch_a"] == "master"
    assert manifest["merge"]["branch_b"] == branch_name
    materialized_count = sum(
        1
        for argument in manifest["merge"]["arguments"]
        if argument["materialized"]
    )
    assert len(merged_claims["claims"]) == materialized_count
    assert payload["semantic_candidate_count"] == len(
        manifest["merge"].get("semantic_candidate_details", [])
    )
