"""Tests for committed-snapshot repository import."""
from __future__ import annotations

from uuid import uuid4
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from propstore.cli import cli
from propstore.cli.repository import Repository
from tests.conftest import make_claim_identity, make_concept_identity, normalize_claims_payload


SEMANTIC_DIRS = (
    "claims",
    "concepts",
    "contexts",
    "forms",
    "stances",
    "worldlines",
)


def _init_project(root: Path) -> Repository:
    return Repository.init(root / "knowledge")


def _write_source_file(project_root: Path, relative_path: str, content: bytes) -> None:
    path = project_root / "knowledge" / Path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _raw_claim_yaml(local_id: str) -> bytes:
    return yaml.safe_dump({"claims": [{"id": local_id}]}, sort_keys=False).encode()


def _expected_imported_claim_yaml(local_id: str, *, namespace: str) -> dict:
    return normalize_claims_payload(
        {"claims": [{"id": local_id}]},
        default_namespace=namespace,
    )


@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    source_claim_ids=st.lists(
        st.from_regex(r"claim_[a-z]{1,4}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    ),
    stale_claim_ids=st.lists(
        st.from_regex(r"stale_[a-z]{1,4}", fullmatch=True),
        min_size=0,
        max_size=3,
        unique=True,
    ),
)
def test_repo_import_is_snapshot_convergent_under_repeated_commits(
    tmp_path,
    source_claim_ids: list[str],
    stale_claim_ids: list[str],
):
    from propstore.repo.branch import create_branch
    from propstore.repo.repo_import import commit_repo_import, plan_repo_import

    assume(set(source_claim_ids).isdisjoint(stale_claim_ids))

    destination = _init_project(tmp_path / f"dest_{uuid4().hex}")
    destination_git = destination.git
    assert destination_git is not None
    create_branch(destination_git, "import/repo-b")
    if stale_claim_ids:
        destination_git.commit_files(
            {
                f"claims/{claim_id}.yaml": _raw_claim_yaml(claim_id)
                for claim_id in stale_claim_ids
            },
            "seed stale import branch",
            branch="import/repo-b",
        )

    source = _init_project(tmp_path / f"repo-b_{uuid4().hex}")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {
            f"claims/{claim_id}.yaml": _raw_claim_yaml(claim_id)
            for claim_id in source_claim_ids
        },
        "seed source snapshot",
    )

    first_result = commit_repo_import(destination, plan_repo_import(destination, source.root.parent))
    second_result = commit_repo_import(destination, plan_repo_import(destination, source.root.parent))

    first_tree = destination_git._repo[first_result.commit_sha.encode()].tree
    second_tree = destination_git._repo[second_result.commit_sha.encode()].tree
    assert first_tree == second_tree

    imported_claim_paths = set(destination_git.list_dir("claims", commit=second_result.commit_sha))
    assert imported_claim_paths == {f"{claim_id}.yaml" for claim_id in sorted(source_claim_ids)}
    for claim_id in stale_claim_ids:
        with pytest.raises(FileNotFoundError):
            destination_git.read_file(f"claims/{claim_id}.yaml", commit=second_result.commit_sha)


@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    concept_ids=st.lists(
        st.from_regex(r"concept_[a-z]{1,4}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    ),
)
def test_repo_import_normalizes_concepts_and_claim_refs_under_random_snapshots(
    tmp_path,
    concept_ids: list[str],
):
    from propstore.repo.repo_import import commit_repo_import, plan_repo_import

    destination = _init_project(tmp_path / f"dest_{uuid4().hex}")
    source = _init_project(tmp_path / f"repo-b_{uuid4().hex}")
    source_git = source.git
    assert source_git is not None

    concept_files = {
        f"concepts/{concept_id}.yaml": yaml.safe_dump(
            {
                "id": concept_id,
                "canonical_name": concept_id,
                "domain": "speech",
                "status": "accepted",
                "definition": f"Definition for {concept_id}",
            },
            sort_keys=False,
        ).encode()
        for concept_id in concept_ids
    }
    claim_files = {
        "claims/source.yaml": yaml.safe_dump(
            {
                "claims": [
                    {
                        "id": f"claim_{index}",
                        "type": "observation",
                        "statement": f"Claim for {concept_id}",
                        "concepts": [concept_id],
                    }
                    for index, concept_id in enumerate(concept_ids, start=1)
                ]
            },
            sort_keys=False,
        ).encode()
    }
    source_git.commit_files({**concept_files, **claim_files}, "seed randomized source snapshot")

    result = commit_repo_import(destination, plan_repo_import(destination, source.root.parent))
    imported_claims = yaml.safe_load(destination.git.read_file("claims/source.yaml", commit=result.commit_sha))

    expected_concept_ids = {
        concept_id: make_concept_identity(
            concept_id,
            domain="speech",
            canonical_name=concept_id,
        )["artifact_id"]
        for concept_id in concept_ids
    }

    for concept_id in concept_ids:
        imported_concept = yaml.safe_load(
            destination.git.read_file(f"concepts/{concept_id}.yaml", commit=result.commit_sha)
        )
        assert imported_concept["artifact_id"] == expected_concept_ids[concept_id]
        assert imported_concept["logical_ids"][0] == {"namespace": "speech", "value": concept_id}
        assert "id" not in imported_concept

    for index, concept_id in enumerate(concept_ids, start=1):
        imported_claim = imported_claims["claims"][index - 1]
        assert imported_claim["logical_ids"][0]["value"] == f"claim_{index}"
        assert imported_claim["concepts"] == [expected_concept_ids[concept_id]]


def test_plan_repo_import_requires_git_backed_source(tmp_path):
    from propstore.repo.repo_import import plan_repo_import

    destination = _init_project(tmp_path / "dest")
    source_project = tmp_path / "source"
    (source_project / "knowledge" / "concepts").mkdir(parents=True)

    with pytest.raises(ValueError, match="git-backed"):
        plan_repo_import(destination, source_project)


def test_plan_repo_import_uses_committed_head_snapshot(tmp_path):
    from propstore.repo.repo_import import plan_repo_import

    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None

    source_git.commit_files(
        {"claims/source.yaml": _raw_claim_yaml("committed")},
        "seed source claims",
    )
    source_git.sync_worktree()
    _write_source_file(
        source.root.parent,
        "claims/source.yaml",
        _raw_claim_yaml("uncommitted"),
    )

    plan = plan_repo_import(destination, source.root.parent)

    assert plan.source_commit == source_git.head_sha()
    assert yaml.safe_load(plan.writes["claims/source.yaml"]) == _expected_imported_claim_yaml(
        "committed",
        namespace="repo-b",
    )


def test_plan_repo_import_uses_default_branch_name_from_source_repo(tmp_path):
    from propstore.repo.repo_import import plan_repo_import

    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files({"concepts/example.yaml": b"id: concept1\n"}, "seed")

    plan = plan_repo_import(destination, source.root.parent)

    assert plan.repo_name == "repo-b"
    assert plan.target_branch == "import/repo-b"
    assert plan.sync_worktree_default is False


def test_plan_repo_import_limits_to_semantic_tree_and_excludes_sidecar(tmp_path):
    from propstore.repo.repo_import import plan_repo_import

    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None

    tracked_files = {
        "claims/source.yaml": b"claims: []\n",
        "concepts/example.yaml": b"id: concept1\n",
        "sidecar/propstore.sqlite": b"sqlite",
        ".git/config-copy": b"ignore-me",
        "notes.txt": b"not semantic",
    }
    source_git.commit_files(tracked_files, "seed")

    plan = plan_repo_import(destination, source.root.parent)

    assert set(plan.touched_paths) == {
        "claims/source.yaml",
        "concepts/example.yaml",
    }
    assert set(plan.writes) == set(plan.touched_paths)
    assert all(path.split("/", 1)[0] in SEMANTIC_DIRS for path in plan.touched_paths)


def test_commit_repo_import_writes_commit_to_target_branch_and_returns_result(tmp_path):
    from propstore.repo.branch import branch_head
    from propstore.repo.repo_import import commit_repo_import, plan_repo_import

    destination = _init_project(tmp_path / "dest")
    destination_git = destination.git
    assert destination_git is not None
    master_before = destination_git.head_sha()

    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {
            "claims/source.yaml": _raw_claim_yaml("imported"),
            "concepts/example.yaml": b"id: concept1\n",
        },
        "seed",
    )

    plan = plan_repo_import(destination, source.root.parent)
    result = commit_repo_import(destination, plan)
    imported_tip = branch_head(destination_git, plan.target_branch)

    assert imported_tip == result.commit_sha
    assert imported_tip != master_before
    assert yaml.safe_load(destination_git.read_file("claims/source.yaml", commit=imported_tip)) == (
        _expected_imported_claim_yaml("imported", namespace="repo-b")
    )
    assert result.surface == "repo_import_commit"
    assert result.source_repo == str(source.root)
    assert result.source_commit == source_git.head_sha()
    assert result.target_branch == "import/repo-b"
    assert result.touched_paths == [
        "claims/source.yaml",
        "concepts/example.yaml",
    ]
    assert result.deleted_paths == []
    assert result.worktree_synced is False


def test_commit_repo_import_does_not_mutate_master_unless_targeted(tmp_path):
    from propstore.repo.repo_import import commit_repo_import, plan_repo_import

    destination = _init_project(tmp_path / "dest")
    destination_git = destination.git
    assert destination_git is not None
    destination_git.commit_files({"concepts/local.yaml": b"id: local\n"}, "local seed")
    destination_git.sync_worktree()
    master_before = destination_git.head_sha()

    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files({"claims/source.yaml": yaml.safe_dump({"claims": []}, sort_keys=False).encode()}, "seed")

    plan = plan_repo_import(destination, source.root.parent)
    result = commit_repo_import(destination, plan)

    assert destination_git.head_sha() == master_before
    with pytest.raises(FileNotFoundError):
        destination_git.read_file("claims/source.yaml", commit=master_before)
    assert destination_git.read_file("claims/source.yaml", commit=result.commit_sha) == b"claims: []\n"


def test_commit_repo_import_auto_syncs_master_but_not_other_branches(tmp_path):
    from propstore.repo.repo_import import commit_repo_import, plan_repo_import

    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files({"claims/source.yaml": _raw_claim_yaml("imported")}, "seed")

    non_master_destination = _init_project(tmp_path / "dest-branch")
    non_master_plan = plan_repo_import(non_master_destination, source.root.parent)
    non_master_result = commit_repo_import(non_master_destination, non_master_plan)
    assert non_master_result.worktree_synced is False
    assert not (non_master_destination.root / "claims" / "source.yaml").exists()

    master_destination = _init_project(tmp_path / "dest-master")
    master_plan = plan_repo_import(
        master_destination,
        source.root.parent,
        target_branch="master",
    )
    master_result = commit_repo_import(master_destination, master_plan)
    assert master_result.worktree_synced is True
    assert yaml.safe_load((master_destination.root / "claims" / "source.yaml").read_bytes()) == (
        _expected_imported_claim_yaml("imported", namespace="repo-b")
    )


def test_plan_repo_import_deletes_paths_missing_from_latest_source_snapshot(tmp_path):
    from propstore.repo.branch import create_branch
    from propstore.repo.repo_import import plan_repo_import

    destination = _init_project(tmp_path / "dest")
    destination_git = destination.git
    assert destination_git is not None
    create_branch(destination_git, "import/repo-b")
    destination_git.commit_files(
        {
            "claims/stale.yaml": _raw_claim_yaml("stale"),
            "concepts/stale.yaml": b"id: stale\n",
        },
        "seed stale import branch",
        branch="import/repo-b",
    )

    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {"claims/fresh.yaml": _raw_claim_yaml("fresh")},
        "seed fresh source snapshot",
    )

    plan = plan_repo_import(destination, source.root.parent)

    assert plan.deletes == ["claims/stale.yaml", "concepts/stale.yaml"]
    assert plan.touched_paths == ["claims/fresh.yaml", "claims/stale.yaml", "concepts/stale.yaml"]


def test_import_repo_rewrites_stance_targets_to_claim_artifact_ids(tmp_path):
    from propstore.repo.repo_import import commit_repo_import, plan_repo_import

    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {
            "claims/source.yaml": yaml.safe_dump(
                {
                    "claims": [
                        {"id": "claim_a", "type": "observation", "statement": "A", "concepts": ["concept_a"]},
                        {"id": "claim_b", "type": "observation", "statement": "B", "concepts": ["concept_b"]},
                    ]
                },
                sort_keys=False,
            ).encode(),
            "stances/claim_a.yaml": yaml.safe_dump(
                {
                    "source_claim": "claim_a",
                    "stances": [{"target": "claim_b", "type": "contradicts"}],
                },
                sort_keys=False,
            ).encode(),
        },
        "seed source claims and stances",
    )

    plan = plan_repo_import(destination, source.root.parent)
    result = commit_repo_import(destination, plan)

    imported_stances = yaml.safe_load(
        destination.git.read_file("stances/claim_a.yaml", commit=result.commit_sha)
    )
    claim_a_id = make_claim_identity("claim_a", namespace="repo-b")["artifact_id"]
    claim_b_id = make_claim_identity("claim_b", namespace="repo-b")["artifact_id"]
    assert imported_stances["source_claim"] == claim_a_id
    assert imported_stances["stances"] == [{"target": claim_b_id, "type": "contradicts"}]


def test_import_repo_normalizes_concepts_and_rewrites_internal_concept_refs(tmp_path):
    from propstore.repo.repo_import import commit_repo_import, plan_repo_import

    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {
            "concepts/concept_a.yaml": yaml.safe_dump(
                {
                    "id": "concept_a",
                    "canonical_name": "concept_a",
                    "domain": "speech",
                    "status": "accepted",
                    "definition": "Concept A",
                    "relationships": [{"type": "related_to", "target": "concept_b"}],
                    "parameterization_relationships": [
                        {
                            "inputs": ["concept_b"],
                            "sympy": "Eq(concept_a, concept_b * 2)",
                            "exactness": "exact",
                        }
                    ],
                },
                sort_keys=False,
            ).encode(),
            "concepts/concept_b.yaml": yaml.safe_dump(
                {
                    "id": "concept_b",
                    "canonical_name": "concept_b",
                    "domain": "speech",
                    "status": "accepted",
                    "definition": "Concept B",
                },
                sort_keys=False,
            ).encode(),
        },
        "seed source concepts",
    )

    plan = plan_repo_import(destination, source.root.parent)
    result = commit_repo_import(destination, plan)

    concept_a = yaml.safe_load(destination.git.read_file("concepts/concept_a.yaml", commit=result.commit_sha))
    concept_b_id = make_concept_identity("concept_b", domain="speech", canonical_name="concept_b")["artifact_id"]

    assert concept_a["artifact_id"] == make_concept_identity(
        "concept_a",
        domain="speech",
        canonical_name="concept_a",
    )["artifact_id"]
    assert "id" not in concept_a
    assert concept_a["logical_ids"][0] == {"namespace": "speech", "value": "concept_a"}
    assert concept_a["version_id"].startswith("sha256:")
    assert concept_a["relationships"] == [{"type": "related_to", "target": concept_b_id}]
    assert concept_a["parameterization_relationships"][0]["inputs"] == [concept_b_id]


def test_import_repo_rewrites_claim_concept_refs_to_imported_concept_artifact_ids(tmp_path):
    from propstore.repo.repo_import import commit_repo_import, plan_repo_import

    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {
            "concepts/concept_a.yaml": yaml.safe_dump(
                {
                    "id": "concept_a",
                    "canonical_name": "concept_a",
                    "domain": "speech",
                    "status": "accepted",
                    "definition": "Concept A",
                },
                sort_keys=False,
            ).encode(),
            "claims/source.yaml": yaml.safe_dump(
                {
                    "claims": [
                        {
                            "id": "claim_a",
                            "type": "observation",
                            "statement": "A",
                            "concepts": ["concept_a"],
                        },
                        {
                            "id": "claim_b",
                            "type": "parameter",
                            "concept": "concept_a",
                            "value": 1.0,
                        },
                    ]
                },
                sort_keys=False,
            ).encode(),
        },
        "seed source concepts and claims",
    )

    plan = plan_repo_import(destination, source.root.parent)
    result = commit_repo_import(destination, plan)

    concept_a_id = make_concept_identity("concept_a", domain="speech", canonical_name="concept_a")["artifact_id"]
    imported_claims = yaml.safe_load(destination.git.read_file("claims/source.yaml", commit=result.commit_sha))

    assert imported_claims["claims"][0]["concepts"] == [concept_a_id]
    assert imported_claims["claims"][1]["concept"] == concept_a_id


def test_import_repo_cli_emits_structured_yaml_for_import_commit(tmp_path):
    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {"claims/source.yaml": _raw_claim_yaml("imported")},
        "seed",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-C", str(destination.root), "import-repo", str(source.root.parent)],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["surface"] == "repo_import_commit"
    assert payload["source_repo"] == str(source.root)
    assert payload["source_commit"] == source_git.head_sha()
    assert payload["target_branch"] == "import/repo-b"
    assert len(payload["commit_sha"]) == 40
    assert payload["touched_paths"] == ["claims/source.yaml"]
    assert payload["deleted_paths"] == []
    assert payload["worktree_synced"] is False


def test_import_repo_cli_can_target_master_and_sync_worktree(tmp_path):
    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "repo-b")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {"claims/source.yaml": _raw_claim_yaml("imported")},
        "seed",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "-C",
            str(destination.root),
            "import-repo",
            str(source.root.parent),
            "--target-branch",
            "master",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["target_branch"] == "master"
    assert payload["worktree_synced"] is True
    assert yaml.safe_load((destination.root / "claims" / "source.yaml").read_bytes()) == (
        _expected_imported_claim_yaml("imported", namespace="repo-b")
    )


def test_import_repo_does_not_break_top_level_propstore_repo_import():
    from propstore import repo as repo_module

    assert repo_module is not None
    assert hasattr(repo_module, "plan_repo_import")
    assert hasattr(repo_module, "commit_repo_import")
