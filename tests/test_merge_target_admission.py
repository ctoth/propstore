"""A two-parent publication must contain the existing target's history."""

from pathlib import Path
from dataclasses import FrozenInstanceError

import pytest
import yaml
from click.testing import CliRunner
from quire.git_store import HeadMismatchError

from propstore.app.merge import (
    MergeCommitRequest, MergeInspectRequest, commit_merge, inspect_merge,
)
from propstore.cli import cli
from propstore.merge.merge_commit import (
    DivergentMergeTargetError, create_merge_commit, plan_merge_commit,
)
from propstore.repository import Repository
from tests.merge_commit_helpers import author_concept, author_obs_claim, init_repo


def _branches(tmp_path: Path) -> tuple[Repository, str, str, str]:
    repo = init_repo(tmp_path / "knowledge")
    base = author_concept(repo, "base")
    git = repo.require_git()
    git.create_branch("right", source_commit=base)
    left = author_obs_claim(repo, "left", "left observation")
    right = author_obs_claim(repo, "right", "right observation", branch="right")
    return repo, base, left, right


@pytest.mark.parametrize("operation", ["core", "inspect", "app"])
def test_divergent_target_preserves_its_head_and_data(tmp_path: Path, monkeypatch, operation) -> None:
    repo, base, left, right = _branches(tmp_path)
    git = repo.require_git()
    git.create_branch("target", source_commit=base)
    target = author_concept(repo, "target-only", branch="target")

    def unexpected_write(*args, **kwargs):
        pytest.fail("Divergent target admission must precede blob storage/publication")

    monkeypatch.setattr(type(git), "store_blob", unexpected_write)
    monkeypatch.setattr(type(git), "commit_flat_tree", unexpected_write)
    with pytest.raises(DivergentMergeTargetError) as caught:
        if operation == "core":
            create_merge_commit(repo, "master", "right", target_branch="target")
        elif operation == "inspect":
            inspect_merge(repo, MergeInspectRequest("master", "right", target_branch="target"))
        else:
            commit_merge(repo, MergeCommitRequest("master", "right", target_branch="target"))

    assert caught.value.target_branch == "target"
    assert caught.value.target_sha == target
    assert (caught.value.left_sha, caught.value.right_sha) == (left, right)
    assert git.branch_sha("target") == target
    assert repo.families.concept.load("target-only", commit=target) is not None
    assert (git.branch_sha("master"), git.branch_sha("right")) == (left, right)


@pytest.mark.parametrize("target", ["absent", "master", "right", "ancestor", "left-alias", "right-alias"])
def test_inspect_and_commit_share_admission_and_exact_parents(tmp_path: Path, target: str) -> None:
    repo, base, left, right = _branches(tmp_path)
    git = repo.require_git()
    if target in ("ancestor", "left-alias", "right-alias"):
        git.create_branch(target, source_commit={"ancestor": base, "left-alias": left, "right-alias": right}[target])
    expected_target = git.branch_sha(target)

    preview = inspect_merge(repo, MergeInspectRequest("master", "right", target_branch=target))
    plan = preview.plan
    assert (plan.left_sha, plan.right_sha, plan.target_sha) == (left, right, expected_target)
    assert plan.base_sha == base
    assert plan.target_admission == ("absent" if expected_target is None else "contained")
    assert preview.to_json()["target_admission"] == plan.target_admission
    assert git.branch_sha(target) == expected_target  # Inspect is read-only.
    with pytest.raises(FrozenInstanceError):
        plan.target_sha = "invalid"

    report = commit_merge(repo, MergeCommitRequest("master", "right", target_branch=target))
    assert report.plan == plan
    assert report.target_admission == plan.target_admission
    assert tuple(git.iter_commit_parent_shas(report.commit_sha)) == (left, right)
    assert git.branch_sha(target) == report.commit_sha
    assert repo.families.claim.load("left", commit=report.commit_sha) is not None
    assert repo.families.claim.load("right", commit=report.commit_sha) is not None
    if expected_target is not None:
        assert expected_target in git.ancestor_distances(left) or expected_target in git.ancestor_distances(right)


@pytest.mark.parametrize("target", ["absent", "ancestor", "master", "right"])
def test_planned_publication_rejects_target_move_without_retry(tmp_path: Path, target: str) -> None:
    repo, base, left, right = _branches(tmp_path)
    git = repo.require_git()
    if target == "ancestor":
        git.create_branch(target, source_commit=base)
    plan = plan_merge_commit(repo, "master", "right", target_branch=target)
    if target == "absent":
        git.create_branch(target, source_commit=base)
    concurrent = author_concept(repo, "concurrent", branch=target)

    with pytest.raises(HeadMismatchError) as caught:
        plan.commit(repo)
    assert caught.value.branch == target
    assert caught.value.expected_head == plan.target_sha
    assert caught.value.actual_head == concurrent
    assert git.branch_sha(target) == concurrent
    assert repo.families.concept.load("concurrent", commit=concurrent) is not None
    for name, sha in (("master", left), ("right", right)):
        if name != target:
            assert git.branch_sha(name) == sha


@pytest.mark.parametrize("side", ["master", "right"])
def test_target_strictly_ancestral_to_only_one_parent_is_admitted(tmp_path: Path, side: str) -> None:
    repo, _base, _left, _right = _branches(tmp_path)
    git = repo.require_git()
    target = git.branch_sha(side)
    git.create_branch("target", source_commit=target)
    other = "right" if side == "master" else "master"
    assert target not in git.ancestor_distances(git.branch_sha(other))
    descendant = author_obs_claim(repo, "descendant", "later on one side", branch=side)
    assert descendant != target
    left, right = git.branch_sha("master"), git.branch_sha("right")
    preview = inspect_merge(repo, MergeInspectRequest("master", "right", target_branch="target"))
    assert preview.plan.target_sha == target
    assert preview.plan.target_admission == "contained"
    report = commit_merge(repo, MergeCommitRequest("master", "right", target_branch="target"))
    assert report.plan == preview.plan
    assert tuple(git.iter_commit_parent_shas(report.commit_sha)) == (left, right)
    assert repo.families.claim.load("descendant", commit=report.commit_sha) is not None


@pytest.mark.parametrize("command", ["inspect", "commit"])
def test_cli_refuses_divergent_target_without_mutating_it(tmp_path: Path, command: str) -> None:
    repo, base, left, right = _branches(tmp_path)
    git = repo.require_git()
    git.create_branch("target", source_commit=base)
    target = author_concept(repo, "target-only", branch="target")
    result = CliRunner().invoke(cli, ["-C", str(repo.root), "merge", command, "master", "right", "--target-branch", "target"])
    assert result.exit_code != 0
    assert "not an ancestor of either parent" in result.output
    assert target in result.output
    assert git.branch_sha("target") == target
    assert repo.families.concept.load("target-only", commit=target) is not None
    assert (git.branch_sha("master"), git.branch_sha("right")) == (left, right)


def test_cli_preview_and_commit_expose_target_admission(tmp_path: Path) -> None:
    repo, _base, left, right = _branches(tmp_path)
    runner = CliRunner()
    args = ["-C", str(repo.root), "merge"]
    tail = ["master", "right", "--target-branch", "result"]
    preview = runner.invoke(cli, [*args, "inspect", *tail])
    assert preview.exit_code == 0, preview.output
    expected = yaml.safe_load(preview.output)
    assert expected["target_admission"] == "absent"
    assert expected["plan"]["target_sha"] is None
    assert repo.require_git().branch_sha("result") is None
    committed = runner.invoke(cli, [*args, "commit", *tail])
    assert committed.exit_code == 0, committed.output
    actual = yaml.safe_load(committed.output)
    assert actual["plan"] == expected["plan"]
    assert actual["target_admission"] == expected["target_admission"]
    assert tuple(repo.require_git().iter_commit_parent_shas(actual["commit_sha"])) == (left, right)


@pytest.mark.parametrize("existing", [False, True])
def test_cli_stale_target_reports_expected_actual_and_preserves_data(tmp_path: Path, monkeypatch, existing) -> None:
    from propstore.merge import merge_commit

    repo, base, _left, _right = _branches(tmp_path)
    git = repo.require_git()
    if existing:
        git.create_branch("result", source_commit=base)
    expected = git.branch_sha("result")
    original = merge_commit._transport_family_occurrences
    concurrent = None

    def advance_target(*args, **kwargs):
        nonlocal concurrent
        result = original(*args, **kwargs)
        if not existing:
            git.create_branch("result", source_commit=base)
        concurrent = author_concept(repo, "concurrent", branch="result")
        return result

    monkeypatch.setattr(merge_commit, "_transport_family_occurrences", advance_target)
    result = CliRunner().invoke(cli, ["-C", str(repo.root), "merge", "commit", "master", "right", "--target-branch", "result"])
    assert result.exit_code != 0
    assert "result" in result.output
    assert str(expected) in result.output
    assert concurrent in result.output
    assert git.branch_sha("result") == concurrent
    assert repo.families.concept.load("concurrent", commit=concurrent) is not None
