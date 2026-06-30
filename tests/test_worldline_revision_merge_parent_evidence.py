"""RevisionScope carries the real git merge-DAG parents of a two-parent merge.

Deferred at Phase 7b-4 because it needed a real merge DAG produced by the storage
merge commit; Phase 9-2's ``create_merge_commit`` provides it. After a two-parent
merge, the belief-base projection's :class:`RevisionScope` reflects the merge
commit and both of its parents (the iterated-revision layer refuses to revise across
an unmerged fork, so it must see the parents).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from propstore.merge.merge_commit import create_merge_commit
from propstore.repository import Repository
from propstore.support_revision.projection import project_belief_base
from tests.merge_commit_helpers import author_obs_claim, init_repo


class _EmptyBoundWorld:
    def __init__(self, repo: Repository) -> None:
        self._store = SimpleNamespace(_repo=repo)
        self._environment = SimpleNamespace(
            bindings={},
            context_id=None,
            assumptions=(),
        )

    @property
    def environment(self) -> SimpleNamespace:
        return self._environment

    def active_claims(self, _target: object) -> tuple[object, ...]:
        return ()


def test_project_belief_base_threads_real_git_merge_parents(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_obs_claim(repo, "anchor", "Anchor")
    git = repo.require_git()
    base = git.branch_sha("master")
    assert base is not None

    branch = "paper/topic"
    git.create_branch(branch, source_commit=base)
    author_obs_claim(repo, "left", "Left")
    author_obs_claim(repo, "right", "Right", branch=branch)

    left = git.branch_sha("master")
    right = git.branch_sha(branch)
    merge = create_merge_commit(repo, "master", branch)

    assert git.commit_parent_shas(merge) == [left, right]

    base_projection = project_belief_base(_EmptyBoundWorld(repo))

    assert base_projection.scope.branch == "master"
    assert base_projection.scope.commit == merge
    assert base_projection.scope.merge_parent_commits == (left, right)
