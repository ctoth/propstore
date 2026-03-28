"""Tests for the Dulwich-backed KnowledgeRepo and TreeReader implementations."""
from __future__ import annotations

import yaml
import pytest

from propstore.cli.git_backend import KnowledgeRepo
from propstore.tree_reader import FilesystemReader, GitTreeReader


# ── KnowledgeRepo lifecycle ─────────────────────────────────────────


def test_init_creates_repo(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    assert (tmp_path / "knowledge" / ".git").is_dir()
    assert (tmp_path / "knowledge" / ".gitignore").exists()
    gitignore = (tmp_path / "knowledge" / ".gitignore").read_text()
    assert "sidecar/" in gitignore
    assert "*.sqlite" in gitignore


def test_is_repo(tmp_path):
    root = tmp_path / "knowledge"
    assert not KnowledgeRepo.is_repo(root)
    KnowledgeRepo.init(root)
    assert KnowledgeRepo.is_repo(root)


def test_open_existing(tmp_path):
    root = tmp_path / "knowledge"
    KnowledgeRepo.init(root)
    kr = KnowledgeRepo.open(root)
    assert kr is not None


# ── commit_files + read_file ────────────────────────────────────────


def test_commit_and_read(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    content = b"x: 1\n"
    sha = kr.commit_files({"a.yaml": content}, "add a")
    assert isinstance(sha, str)
    assert len(sha) == 40
    assert kr.read_file("a.yaml") == content


def test_commit_nested_path(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    content = b"name: test\n"
    kr.commit_files({"concepts/test_concept.yaml": content}, "add concept")
    assert kr.read_file("concepts/test_concept.yaml") == content


def test_read_nonexistent_raises(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "seed")
    with pytest.raises(FileNotFoundError):
        kr.read_file("nonexistent.yaml")


def test_commit_overwrites_existing(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"v: 1\n"}, "v1")
    kr.commit_files({"a.yaml": b"v: 2\n"}, "v2")
    assert kr.read_file("a.yaml") == b"v: 2\n"


# ── list_dir ────────────────────────────────────────────────────────


def test_list_dir(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({
        "concepts/alpha.yaml": b"id: concept1\n",
        "concepts/beta.yaml": b"id: concept2\n",
        "claims/paper1.yaml": b"claims: []\n",
    }, "add files")
    concepts = kr.list_dir("concepts")
    assert sorted(concepts) == ["alpha.yaml", "beta.yaml"]
    claims = kr.list_dir("claims")
    assert claims == ["paper1.yaml"]


def test_list_dir_empty(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n"}, "seed")
    assert kr.list_dir("concepts") == []


def test_list_dir_no_commits(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    assert kr.list_dir("concepts") == []


# ── commit_deletes ──────────────────────────────────────────────────


def test_commit_deletes(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"x: 1\n", "b.yaml": b"y: 2\n"}, "add")
    kr.commit_deletes(["a.yaml"], "remove a")
    with pytest.raises(FileNotFoundError):
        kr.read_file("a.yaml")
    assert kr.read_file("b.yaml") == b"y: 2\n"


# ── commit_batch ────────────────────────────────────────────────────


def test_commit_batch(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({
        "old.yaml": b"old: true\n",
        "keep.yaml": b"keep: true\n",
    }, "setup")

    kr.commit_batch(
        adds={"new.yaml": b"new: true\n"},
        deletes=["old.yaml"],
        message="batch op",
    )

    assert kr.read_file("new.yaml") == b"new: true\n"
    assert kr.read_file("keep.yaml") == b"keep: true\n"
    with pytest.raises(FileNotFoundError):
        kr.read_file("old.yaml")

    # Exactly one commit for the batch (3 total: init .gitignore + setup + batch)
    history = kr.log(max_count=10)
    assert len(history) == 3


# ── sync_worktree ───────────────────────────────────────────────────


def test_sync_worktree(tmp_path):
    root = tmp_path / "knowledge"
    kr = KnowledgeRepo.init(root)
    kr.commit_files({
        "concepts/foo.yaml": b"id: concept1\ncanonical_name: foo\n",
    }, "add foo")
    kr.sync_worktree()

    on_disk = root / "concepts" / "foo.yaml"
    assert on_disk.exists()
    assert on_disk.read_bytes() == b"id: concept1\ncanonical_name: foo\n"


def test_sync_worktree_removes_deleted(tmp_path):
    root = tmp_path / "knowledge"
    kr = KnowledgeRepo.init(root)
    kr.commit_files({"a.yaml": b"x: 1\n"}, "add")
    kr.sync_worktree()
    assert (root / "a.yaml").exists()

    kr.commit_deletes(["a.yaml"], "remove")
    kr.sync_worktree()
    assert not (root / "a.yaml").exists()


# ── log ─────────────────────────────────────────────────────────────


def test_log(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"v: 1\n"}, "first")
    kr.commit_files({"a.yaml": b"v: 2\n"}, "second")

    history = kr.log(max_count=10)
    # .gitignore commit + first + second = 3
    assert len(history) == 3
    assert history[0]["message"].startswith("second")
    assert history[1]["message"].startswith("first")
    assert "sha" in history[0]
    assert "time" in history[0]
    assert "author" in history[0]


def test_log_empty_repo(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    # init creates a .gitignore commit
    history = kr.log()
    assert len(history) == 1


def test_head_sha(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    sha1 = kr.head_sha()
    assert sha1 is not None
    assert len(sha1) == 40

    kr.commit_files({"a.yaml": b"x: 1\n"}, "add")
    sha2 = kr.head_sha()
    assert sha2 != sha1


# ── read_file at historical commit ──────────────────────────────────


def test_read_file_at_commit(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"a.yaml": b"v: 1\n"}, "v1")
    sha1 = kr.head_sha()
    kr.commit_files({"a.yaml": b"v: 2\n"}, "v2")

    assert kr.read_file("a.yaml") == b"v: 2\n"
    assert kr.read_file("a.yaml", commit=sha1) == b"v: 1\n"


# ── next_concept_id ─────────────────────────────────────────────────


def test_next_concept_id_empty(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    assert kr.next_concept_id() == 1


def test_next_concept_id_scans_tree(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    c3 = yaml.dump({"id": "concept3", "canonical_name": "alpha"}).encode()
    c7 = yaml.dump({"id": "concept7", "canonical_name": "beta"}).encode()
    kr.commit_files({
        "concepts/alpha.yaml": c3,
        "concepts/beta.yaml": c7,
    }, "add concepts")
    assert kr.next_concept_id() == 8


def test_next_concept_id_ignores_non_concept_ids(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    data = yaml.dump({"id": "something_else", "canonical_name": "foo"}).encode()
    kr.commit_files({"concepts/foo.yaml": data}, "add")
    assert kr.next_concept_id() == 1


# ── TreeReader: GitTreeReader ───────────────────────────────────────


def test_git_tree_reader_list_yaml(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({
        "concepts/a.yaml": b"id: concept1\n",
        "concepts/b.yaml": b"id: concept2\n",
        "concepts/readme.txt": b"not yaml\n",
    }, "add")

    reader = GitTreeReader(kr)
    entries = reader.list_yaml("concepts")
    names = [name for name, _ in entries]
    assert sorted(names) == ["a", "b"]
    # Content matches
    for name, content in entries:
        assert content == kr.read_file(f"concepts/{name}.yaml")


def test_git_tree_reader_read_yaml(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"concepts/foo.yaml": b"id: concept1\n"}, "add")

    reader = GitTreeReader(kr)
    assert reader.read_yaml("concepts/foo.yaml") == b"id: concept1\n"
    assert reader.read_yaml("concepts/nonexistent.yaml") is None


def test_git_tree_reader_exists(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"concepts/a.yaml": b"x: 1\n"}, "add")

    reader = GitTreeReader(kr)
    assert reader.exists("concepts")
    assert not reader.exists("claims")


def test_git_tree_reader_at_commit(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"concepts/a.yaml": b"v: 1\n"}, "v1")
    sha1 = kr.head_sha()
    kr.commit_files({"concepts/a.yaml": b"v: 2\n"}, "v2")

    reader_current = GitTreeReader(kr)
    reader_old = GitTreeReader(kr, commit=sha1)

    current_entries = dict(reader_current.list_yaml("concepts"))
    old_entries = dict(reader_old.list_yaml("concepts"))

    assert current_entries["a"] == b"v: 2\n"
    assert old_entries["a"] == b"v: 1\n"


# ── TreeReader: FilesystemReader ────────────────────────────────────


def test_filesystem_reader_list_yaml(tmp_path):
    root = tmp_path / "knowledge"
    concepts = root / "concepts"
    concepts.mkdir(parents=True)
    (concepts / "a.yaml").write_bytes(b"id: concept1\n")
    (concepts / "b.yaml").write_bytes(b"id: concept2\n")
    (concepts / "readme.txt").write_bytes(b"not yaml\n")

    reader = FilesystemReader(root)
    entries = reader.list_yaml("concepts")
    names = [name for name, _ in entries]
    assert sorted(names) == ["a", "b"]


def test_filesystem_reader_read_yaml(tmp_path):
    root = tmp_path / "knowledge"
    concepts = root / "concepts"
    concepts.mkdir(parents=True)
    (concepts / "foo.yaml").write_bytes(b"id: concept1\n")

    reader = FilesystemReader(root)
    assert reader.read_yaml("concepts/foo.yaml") == b"id: concept1\n"
    assert reader.read_yaml("concepts/nonexistent.yaml") is None


def test_filesystem_reader_exists(tmp_path):
    root = tmp_path / "knowledge"
    (root / "concepts").mkdir(parents=True)

    reader = FilesystemReader(root)
    assert reader.exists("concepts")
    assert not reader.exists("claims")


# ── TreeReader equivalence ──────────────────────────────────────────


def test_tree_reader_equivalence(tmp_path):
    """GitTreeReader and FilesystemReader produce identical output after sync."""
    root = tmp_path / "knowledge"
    kr = KnowledgeRepo.init(root)
    kr.commit_files({
        "concepts/alpha.yaml": b"id: concept1\ncanonical_name: alpha\n",
        "concepts/beta.yaml": b"id: concept2\ncanonical_name: beta\n",
    }, "add concepts")
    kr.sync_worktree()

    git_reader = GitTreeReader(kr)
    fs_reader = FilesystemReader(root)

    git_entries = sorted(git_reader.list_yaml("concepts"))
    fs_entries = sorted(fs_reader.list_yaml("concepts"))

    assert git_entries == fs_entries


# ── Phase 2: Loader refactor — load via TreeReader ────────────────


def test_load_concepts_from_tree_reader(tmp_path):
    """load_concepts() works via GitTreeReader from a committed git tree."""
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    concept_data = {
        "id": "concept1",
        "canonical_name": "test_concept",
        "status": "proposed",
        "definition": "A test concept",
        "domain": "testing",
        "form": "scalar",
    }
    kr.commit_files({
        "concepts/test_concept.yaml": yaml.dump(concept_data).encode(),
    }, "add concept")

    from propstore.tree_reader import GitTreeReader
    from propstore.validate import load_concepts
    reader = GitTreeReader(kr)
    concepts = load_concepts(None, reader=reader)
    assert len(concepts) == 1
    assert concepts[0].data["id"] == "concept1"
    assert concepts[0].filepath is None
    assert concepts[0].filename == "test_concept"


def test_load_claim_files_from_tree_reader(tmp_path):
    """load_claim_files() works via GitTreeReader from a committed git tree."""
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    claim_data = {
        "claims": [
            {
                "id": "claim1",
                "type": "observation",
                "statement": "test observation",
                "concepts": ["concept1"],
                "provenance": {"paper": "test", "page": 1},
            }
        ]
    }
    kr.commit_files({
        "claims/test_claims.yaml": yaml.dump(claim_data).encode(),
    }, "add claims")

    from propstore.tree_reader import GitTreeReader
    from propstore.validate_claims import load_claim_files
    reader = GitTreeReader(kr)
    claim_files = load_claim_files(None, reader=reader)
    assert len(claim_files) == 1
    assert claim_files[0].data["claims"][0]["id"] == "claim1"
    assert claim_files[0].filepath is None
    assert claim_files[0].filename == "test_claims"


def test_load_contexts_from_tree_reader(tmp_path):
    """load_contexts() works via GitTreeReader from a committed git tree."""
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    context_data = {
        "id": "ctx1",
        "name": "Test Context",
        "assumptions": ["test assumption"],
    }
    kr.commit_files({
        "contexts/test_context.yaml": yaml.dump(context_data).encode(),
    }, "add context")

    from propstore.tree_reader import GitTreeReader
    from propstore.validate_contexts import load_contexts
    reader = GitTreeReader(kr)
    contexts = load_contexts(None, reader=reader)
    assert len(contexts) == 1
    assert contexts[0].data["id"] == "ctx1"
    assert contexts[0].filepath is None
    assert contexts[0].filename == "test_context"
