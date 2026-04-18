"""Tests for multi-branch git primitives in propstore.storage.

TDD red phase: these tests define the contract for branch CRUD,
commit isolation, and merge-base computation. All should FAIL
(ImportError) until the storage package exists.

Literature grounding:
- Darwiche & Pearl 1997: iterated belief revision postulates C1-C4
- Bonanno 2007: Backward Uniqueness (BU) — linear history per branch
- Konieczny & Pino Pérez 2002: IC merging at merge points
"""
from __future__ import annotations

import pytest

from quire.git_store import GitStore
from propstore.storage import init_git_store
from propstore.storage.snapshot import RepositorySnapshot


def _create_two_parent_commit(
    kr: GitStore,
    *,
    left_parent: str,
    right_parent: str,
    target_branch: str = "master",
    message: str = "merge commit",
) -> str:
    """Create a synthetic two-parent commit for DAG-shaped merge-base tests."""
    return kr.commit_flat_tree(
        kr.flat_tree_entries(left_parent),
        message,
        parents=[left_parent, right_parent],
        branch=target_branch,
    )


# ── Group 1: Branch CRUD ──────────────────────────────────────────────


def test_create_branch_from_master(tmp_path):
    """Creating a branch from master tip copies the HEAD pointer.

    Propstore spec Phase 1: name.create_branch(source_commit=None)
    defaults to current branch tip. The new branch must appear in
    list_branches() and its tip must equal master's HEAD.
    """
    kr = init_git_store(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "seed")
    master_sha = kr.head_sha()

    kr.create_branch("paper/test")

    branches = kr.list_branches()
    branch_names = [b.name for b in branches]
    assert "paper/test" in branch_names
    assert kr.branch_sha("paper/test") == master_sha


def test_create_branch_from_commit(tmp_path):
    """Creating a branch from a specific commit anchors it there.

    Analogous to Darwiche & Pearl 1997 C1: a branch rooted at commit A
    represents the epistemic state at A — later master commits (B) are
    irrelevant to this branch's starting state. This is an analogy, not
    a formal C1 verification (which requires a revision operator).
    """
    kr = init_git_store(tmp_path / "knowledge")
    sha_a = kr.commit_files({"a.yaml": b"x: 1\n"}, "commit A")
    sha_b = kr.commit_files({"b.yaml": b"y: 2\n"}, "commit B")

    kr.create_branch("paper/anchored", source_commit=sha_a)

    assert kr.branch_sha("paper/anchored") == sha_a
    assert kr.branch_sha("paper/anchored") != sha_b


def test_create_branch_kinds(tmp_path):
    """Branch kind is inferred from the naming convention prefix.

    Propstore spec: three branch kinds — paper/{slug}, agent/{run_id},
    hypothesis/{name}. BranchInfo.kind must reflect the prefix.
    """
    kr = init_git_store(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "seed")

    kr.create_branch("paper/foo")
    kr.create_branch("agent/bar")
    kr.create_branch("hypothesis/baz")

    branches = {b.name: b for b in RepositorySnapshot.for_git(kr).list_branches()}
    assert branches["paper/foo"].kind == "paper"
    assert branches["agent/bar"].kind == "agent"
    assert branches["hypothesis/baz"].kind == "hypothesis"


def test_delete_branch(tmp_path):
    """Deleting a branch removes it from list and nullifies its head.

    Basic CRUD: after deletion, the branch must not appear in
    list_branches() and branch_head() must return None.
    """
    kr = init_git_store(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "seed")
    kr.create_branch("paper/ephemeral")

    kr.delete_branch("paper/ephemeral")

    branch_names = [b.name for b in kr.list_branches()]
    assert "paper/ephemeral" not in branch_names
    assert kr.branch_sha("paper/ephemeral") is None


def test_delete_current_head_branch_refused(tmp_path):
    """Deleting the current HEAD branch must raise ValueError."""
    kr = init_git_store(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "seed")
    kr.create_branch("paper/active")
    kr.set_current_branch("paper/active")

    with pytest.raises(ValueError):
        kr.delete_branch("paper/active")


def test_list_branches_includes_master(tmp_path):
    """A fresh repo with one commit must list master as a branch.

    Master is always present — it is the default epistemic state
    from which all branches fork.
    """
    kr = init_git_store(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "seed")

    branches = kr.list_branches()
    branch_names = [b.name for b in branches]
    assert "master" in branch_names


# ── Group 2: Commit to Branch (Darwiche-Pearl epistemic isolation) ────


def test_commit_to_branch_isolation(tmp_path):
    """Commits to branch X do not appear on master.

    Provides the isolation prerequisite for Darwiche & Pearl 1997 C1-C4:
    each branch maintains an independent commit sequence. C1-C4
    satisfaction requires a revision operator (Phase 2+); this test
    verifies the structural independence that makes C1-C4 applicable.
    """
    kr = init_git_store(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "commit A to master")

    kr.create_branch("paper/test")
    kr.commit_files({"b.yaml": b"y: 2\n"}, "commit B to branch", branch="paper/test")

    # Master sees A but not B
    assert kr.read_file("a.yaml") == b"x: 1\n"
    with pytest.raises(FileNotFoundError):
        kr.read_file("b.yaml")

    # Branch sees both A and B
    branch_tip = kr.branch_sha("paper/test")
    assert kr.read_file("a.yaml", commit=branch_tip) == b"x: 1\n"
    assert kr.read_file("b.yaml", commit=branch_tip) == b"y: 2\n"


def test_branch_linear_history(tmp_path):
    """Each branch has linear history (single parent per commit).

    Bonanno 2007, claim 9 (Backward Uniqueness): each instant has at
    most one predecessor in the successor relation, making the temporal
    structure tree-like forward but linear backward. Git branches must
    satisfy BU — each commit has exactly one parent (except the root
    which has zero). This rules out merge commits within a branch.
    """
    kr = init_git_store(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "root")
    kr.create_branch("paper/linear")

    kr.commit_files({"b.yaml": b"y: 2\n"}, "c1", branch="paper/linear")
    kr.commit_files({"c.yaml": b"z: 3\n"}, "c2", branch="paper/linear")
    kr.commit_files({"d.yaml": b"w: 4\n"}, "c3", branch="paper/linear")

    # Walk parents from branch tip — each has exactly 1 parent
    # except the very first commit (root) which has 0
    tip = kr.branch_sha("paper/linear")
    log = kr.log(max_count=50, branch="paper/linear")

    for entry in log[:-1]:  # all except root
        assert len(entry["parents"]) == 1, (
            f"Commit {entry['sha'][:8]} has {len(entry['parents'])} parents, "
            f"violating Backward Uniqueness (Bonanno 2007)"
        )
    # Root commit has 0 parents
    assert len(log[-1]["parents"]) == 0


def test_parallel_branch_divergence(tmp_path):
    """Parallel branches diverge independently after the fork point.

    Analogous to Darwiche & Pearl 1997 C2: contradicting evidence on
    one branch does not propagate to the other. This is an analogy, not
    a formal C2 verification (which requires a revision operator).
    Master and branch must each contain only their own commits after
    the fork.
    """
    kr = init_git_store(tmp_path / "knowledge")
    sha_a = kr.commit_files({"a.yaml": b"shared\n"}, "commit A (shared)")

    kr.create_branch("paper/diverge")

    # Diverge: B on master, C on branch
    kr.commit_files({"b.yaml": b"master-only\n"}, "commit B on master")
    kr.commit_files({"c.yaml": b"branch-only\n"}, "commit C on branch", branch="paper/diverge")

    # Master has A + B, not C
    assert kr.read_file("a.yaml") == b"shared\n"
    assert kr.read_file("b.yaml") == b"master-only\n"
    with pytest.raises(FileNotFoundError):
        kr.read_file("c.yaml")

    # Branch has A + C, not B
    branch_tip = kr.branch_sha("paper/diverge")
    assert kr.read_file("a.yaml", commit=branch_tip) == b"shared\n"
    assert kr.read_file("c.yaml", commit=branch_tip) == b"branch-only\n"
    with pytest.raises(FileNotFoundError):
        kr.read_file("b.yaml", commit=branch_tip)


# ── Group 3: Merge Base ──────────────────────────────────────────────


def test_merge_base_simple(tmp_path):
    """merge_base finds the common ancestor after divergence.

    Provides the common baseline for future IC merging (Konieczny &
    Pino Pérez 2002). merge_base() identifies the divergence point —
    the common knowledge base from which both branches evolved. IC0
    satisfaction requires the merge operator itself (Phase 2+).
    """
    kr = init_git_store(tmp_path / "knowledge")
    sha_a = kr.commit_files({"a.yaml": b"x: 1\n"}, "commit A")

    kr.create_branch("paper/test", source_commit=sha_a)
    kr.commit_files({"b.yaml": b"y: 2\n"}, "commit B on master")
    kr.commit_files({"c.yaml": b"z: 3\n"}, "commit C on branch", branch="paper/test")

    result = kr.merge_base("master", "paper/test")
    assert result == sha_a


def test_merge_base_no_divergence(tmp_path):
    """merge_base with no divergence returns the shared tip.

    When a branch is created and neither side commits, the merge base
    is the branch point itself (trivially the common ancestor).
    """
    kr = init_git_store(tmp_path / "knowledge")
    sha_a = kr.commit_files({"a.yaml": b"x: 1\n"}, "commit A")

    kr.create_branch("paper/test", source_commit=sha_a)

    result = kr.merge_base("master", "paper/test")
    assert result == sha_a


def test_merge_base_deep_history(tmp_path):
    """merge_base works correctly with deep divergence.

    Bonanno 2007, Backward Uniqueness: the temporal structure is
    tree-like forward. With 5 commits on master, a branch at commit 3,
    and further commits on both sides, merge_base must return commit 3
    — the unique branching point in the forward-tree structure.
    """
    kr = init_git_store(tmp_path / "knowledge")

    shas = []
    for i in range(5):
        sha = kr.commit_files({f"f{i}.yaml": f"v: {i}\n".encode()}, f"master commit {i}")
        shas.append(sha)

    # Branch at commit 3 (index 2, zero-based)
    kr.create_branch("paper/deep", source_commit=shas[2])

    # Two more on master (already have shas[3] and shas[4])
    # Two more on branch
    kr.commit_files({"branch_1.yaml": b"b: 1\n"}, "branch commit 1", branch="paper/deep")
    kr.commit_files({"branch_2.yaml": b"b: 2\n"}, "branch commit 2", branch="paper/deep")

    result = kr.merge_base("master", "paper/deep")
    assert result == shas[2]


def test_merge_base_same_branch(tmp_path):
    """merge_base of a branch with itself returns its HEAD.

    Trivial case: a branch's common ancestor with itself is its tip.
    """
    kr = init_git_store(tmp_path / "knowledge")
    sha = kr.commit_files({"a.yaml": b"x: 1\n"}, "commit A")

    result = kr.merge_base("master", "master")
    assert result == sha


def test_merge_base_prefers_nearer_common_ancestor_over_older_one(tmp_path):
    """A branch tip that is itself a common ancestor must beat an older ancestor.

    Regression for a merge-shaped DAG:
    - branch tip B descends from base A
    - master tip M is a merge commit with parents A and B

    The correct merge base of master and the branch is B, not A.
    """
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({"base.yaml": b"base\n"}, "base")
    kr.create_branch("paper/merge", source_commit=base_sha)
    branch_tip = kr.commit_files(
        {"branch.yaml": b"branch\n"},
        "branch commit",
        branch="paper/merge",
    )

    merge_sha = _create_two_parent_commit(
        kr,
        left_parent=base_sha,
        right_parent=branch_tip,
        target_branch="master",
    )
    assert kr.branch_sha("master") == merge_sha

    result = kr.merge_base("master", "paper/merge")
    assert result == branch_tip


# ── Group 4: Storage API ──────────────────────────────────


def test_existing_api_unchanged(tmp_path):
    """GitStore public API works identically when imported from propstore.storage.

    All existing operations (init, commit_files, read_file, list_dir,
    head_sha, log) must work without a branch parameter, defaulting to
    the current HEAD branch. This ensures the Phase 1 refactor does not break any
    existing callers.
    """
    kr = init_git_store(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "seed master")
    master_tip = kr.head_sha()
    kr.create_branch("paper/current")
    kr.set_current_branch("paper/current")

    # commit_files without branch param defaults to the current HEAD branch
    sha = kr.commit_files({"b.yaml": b"y: 2\n"}, "add b")
    assert isinstance(sha, str) and len(sha) == 40

    # read_file works
    assert kr.read_file("b.yaml") == b"y: 2\n"
    assert master_tip is not None
    with pytest.raises(FileNotFoundError):
        kr.read_file("b.yaml", commit=master_tip)

    # list_dir works
    entries = kr.list_dir(".")
    assert "b.yaml" in entries

    # head_sha works
    assert kr.head_sha() == sha

    # log works
    entries = kr.log(max_count=10)
    assert len(entries) >= 1
    assert entries[0]["message"].startswith("add b")


def test_propstore_storage_exports_policy_constructor_only():
    from propstore.storage import init_git_store as imported_init_git_store

    assert imported_init_git_store is init_git_store
