from __future__ import annotations

from types import SimpleNamespace

from propstore.repository import Repository
from propstore.support_revision.projection import project_belief_base


class _EmptyBoundWorld:
    def __init__(self, repo: Repository) -> None:
        self._store = SimpleNamespace(_repo=repo)
        self._environment = SimpleNamespace(
            bindings={},
            context_id=None,
            assumptions=(),
        )

    def active_claims(self, _target):
        return ()


def test_project_belief_base_threads_real_git_merge_parents(tmp_path) -> None:
    """Class A - must fail today: RevisionScope drops real merge DAG parents."""

    repo = Repository.init(tmp_path / "knowledge")
    assert repo.git is not None
    base = repo.git.head_sha()
    assert base is not None
    repo.git.create_branch("topic", source_commit=base)
    left = repo.git.commit_files({"left.txt": b"left\n"}, "left", branch="master", expected_head=base)
    right = repo.git.commit_files({"right.txt": b"right\n"}, "right", branch="topic", expected_head=base)
    merge = repo.git.commit_flat_tree(
        {**repo.git.flat_tree_entries(left), **repo.git.flat_tree_entries(right)},
        "merge",
        parents=[left, right],
        branch="master",
        expected_head=left,
    )

    assert repo.git.commit_parent_shas(merge) == [left, right]

    base_projection = project_belief_base(_EmptyBoundWorld(repo))

    assert base_projection.scope.branch == "master"
    assert base_projection.scope.commit == merge
    assert base_projection.scope.merge_parent_commits == (left, right)
