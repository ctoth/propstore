from __future__ import annotations

from pathlib import Path

from propstore.repository import Repository
from quire.tree_path import FilesystemTreePath as FilesystemKnowledgePath, GitTreePath as GitKnowledgePath
from propstore.storage import GitStore


def test_filesystem_knowledge_path_basic_traversal(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    claims = root / "claims"
    claims.mkdir(parents=True)
    (claims / "paper.yaml").write_bytes(b"claims: []\n")

    tree = FilesystemKnowledgePath(root)
    claims_dir = tree / "claims"
    claim_file = claims_dir / "paper.yaml"

    assert tree.is_dir()
    assert claims_dir.is_dir()
    assert claim_file.is_file()
    assert claim_file.exists()
    assert not (tree / "missing.yaml").exists()
    assert claim_file.name == "paper.yaml"
    assert claim_file.stem == "paper"
    assert claim_file.suffix == ".yaml"
    assert claim_file.parent.as_posix() == "claims"
    assert claim_file.as_posix() == "claims/paper.yaml"
    assert claim_file.read_text() == "claims: []\n"
    assert [child.name for child in claims_dir.iterdir()] == ["paper.yaml"]


def test_git_knowledge_path_basic_traversal(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = GitStore.init(root)
    repo.commit_files({"claims/paper.yaml": b"claims: []\n"}, "add claims")

    tree = GitKnowledgePath(repo)
    claims_dir = tree / "claims"
    claim_file = claims_dir / "paper.yaml"

    assert tree.is_dir()
    assert claims_dir.is_dir()
    assert claim_file.is_file()
    assert claim_file.exists()
    assert not (tree / "missing.yaml").exists()
    assert claim_file.name == "paper.yaml"
    assert claim_file.stem == "paper"
    assert claim_file.suffix == ".yaml"
    assert claim_file.parent.as_posix() == "claims"
    assert claim_file.as_posix() == "claims/paper.yaml"
    assert claim_file.read_text() == "claims: []\n"
    assert [child.name for child in claims_dir.iterdir()] == ["paper.yaml"]


def test_knowledge_path_parity_between_git_and_filesystem(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = GitStore.init(root)
    repo.commit_files(
        {
            "concepts/alpha.yaml": b"id: concept1\n",
            "concepts/beta.yaml": b"id: concept2\n",
        },
        "add concepts",
    )
    repo.sync_worktree()

    git_tree = GitKnowledgePath(repo)
    fs_tree = FilesystemKnowledgePath(root)

    git_entries = sorted(
        (child.name, child.read_bytes())
        for child in (git_tree / "concepts").iterdir()
    )
    fs_entries = sorted(
        (child.name, child.read_bytes())
        for child in (fs_tree / "concepts").iterdir()
    )

    assert git_entries == fs_entries


def test_repository_tree_uses_git_head_for_git_backed_repos(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = GitStore.init(root)
    repository = Repository(root)

    repo.commit_files({"concepts/alpha.yaml": b"id: concept1\n"}, "v1")
    sha1 = repo.head_sha()
    assert sha1 is not None
    repo.commit_files({"concepts/alpha.yaml": b"id: concept2\n"}, "v2")
    repo.sync_worktree()

    live_tree = repository.tree()
    old_tree = repository.tree(commit=sha1)

    assert isinstance(live_tree, GitKnowledgePath)
    assert isinstance(old_tree, GitKnowledgePath)
    assert (live_tree / "concepts" / "alpha.yaml").read_text() == "id: concept2\n"
    assert (old_tree / "concepts" / "alpha.yaml").read_text() == "id: concept1\n"


def test_repository_tree_ignores_uncommitted_worktree_edits_for_git_backed_repos(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = GitStore.init(root)
    repository = Repository(root)

    repo.commit_files({"concepts/alpha.yaml": b"id: concept1\n"}, "v1")
    repo.sync_worktree()
    (root / "concepts" / "alpha.yaml").write_text("id: concept999\n", encoding="utf-8")

    live_tree = repository.tree()

    assert isinstance(live_tree, GitKnowledgePath)
    assert (live_tree / "concepts" / "alpha.yaml").read_text() == "id: concept1\n"


def test_coerced_filesystem_path_preserves_parent_ancestry(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    concepts = root / "concepts"
    concepts.mkdir(parents=True)
    concept_file = concepts / "alpha.yaml"
    concept_file.write_text("id: concept1\n")

    coerced = FilesystemKnowledgePath.from_filesystem_path(concept_file)

    assert coerced.name == "alpha.yaml"
    assert coerced.parent.concrete_path() == concepts
    assert coerced.parent.parent.concrete_path() == root
    assert (coerced.parent.parent / "forms").concrete_path() == root / "forms"
