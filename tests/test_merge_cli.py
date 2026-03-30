"""CLI tests for formal merge inspection and execution."""
from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.cli.repository import Repository
from propstore.repo.branch import create_branch


def _claim_yaml(claims: list[dict], paper: str = "test_paper") -> bytes:
    doc = {
        "source": {
            "paper": paper,
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": claims,
    }
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
        "claim1": sorted(payload["arguments"]),
    }
    assert len(payload["argument_details"]) == 2


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
