"""Tests for committed-snapshot repository import."""
from __future__ import annotations

from pathlib import Path

import pytest

from propstore.cli.repository import Repository


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
        {"claims/source.yaml": b"claims:\n- id: committed\n"},
        "seed source claims",
    )
    source_git.sync_worktree()
    _write_source_file(
        source.root.parent,
        "claims/source.yaml",
        b"claims:\n- id: uncommitted\n",
    )

    plan = plan_repo_import(destination, source.root.parent)

    assert plan.source_commit == source_git.head_sha()
    assert plan.writes["claims/source.yaml"] == b"claims:\n- id: committed\n"


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
            "claims/source.yaml": b"claims:\n- id: imported\n",
            "concepts/example.yaml": b"id: concept1\n",
        },
        "seed",
    )

    plan = plan_repo_import(destination, source.root.parent)
    result = commit_repo_import(destination, plan)
    imported_tip = branch_head(destination_git, plan.target_branch)

    assert imported_tip == result.commit_sha
    assert imported_tip != master_before
    assert destination_git.read_file("claims/source.yaml", commit=imported_tip) == b"claims:\n- id: imported\n"
    assert result.surface == "repo_import_commit"
    assert result.source_repo == str(source.root)
    assert result.source_commit == source_git.head_sha()
    assert result.target_branch == "import/repo-b"
    assert result.touched_paths == [
        "claims/source.yaml",
        "concepts/example.yaml",
    ]
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
    source_git.commit_files({"claims/source.yaml": b"claims: []\n"}, "seed")

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
    source_git.commit_files({"claims/source.yaml": b"claims:\n- id: imported\n"}, "seed")

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
    assert (master_destination.root / "claims" / "source.yaml").read_bytes() == (
        b"claims:\n- id: imported\n"
    )
