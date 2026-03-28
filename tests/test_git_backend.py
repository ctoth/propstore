"""Tests for the Dulwich-backed KnowledgeRepo and TreeReader implementations."""
from __future__ import annotations

from pathlib import Path

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


# ── Phase 3: Build sidecar from git ─────────────────────────────────


def _setup_git_knowledge_repo(tmp_path):
    """Helper: create a git-backed knowledge repo with one concept and form."""
    import shutil
    from pathlib import Path
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    kr = KnowledgeRepo.init(root)

    # Seed forms directory on disk (forms are package resources, loaded from filesystem)
    forms_dir = root / "forms"
    forms_dir.mkdir(exist_ok=True)
    package_forms = Path(__file__).resolve().parent.parent / "propstore" / "_resources" / "forms"
    for f in package_forms.glob("*.yaml"):
        shutil.copy2(f, forms_dir / f.name)

    # Create required dirs for Repository
    for d in ["concepts", "claims", "contexts", "sidecar", "stances", "worldlines"]:
        (root / d).mkdir(exist_ok=True)
    (root / "concepts" / ".counters").mkdir(exist_ok=True)

    concept_data = {
        "id": "concept1",
        "canonical_name": "test_frequency",
        "status": "proposed",
        "definition": "A test frequency concept",
        "domain": "testing",
        "form": "frequency",
    }
    kr.commit_files({
        "concepts/test_frequency.yaml": yaml.dump(concept_data).encode(),
    }, "add concept")
    kr.sync_worktree()

    repo = Repository(root)
    return kr, repo


def test_build_from_git(tmp_path):
    """pks build produces sidecar from git tree, keyed to commit hash."""
    kr, repo = _setup_git_knowledge_repo(tmp_path)
    from propstore.build_sidecar import build_sidecar
    from propstore.validate import load_concepts
    from propstore.tree_reader import GitTreeReader

    reader = GitTreeReader(kr)
    hash_key = kr.head_sha()

    concepts = load_concepts(None, reader=reader)
    assert len(concepts) == 1

    rebuilt = build_sidecar(
        concepts, repo.sidecar_path, force=False,
        repo=repo,
        commit_hash=hash_key,
        reader=reader,
    )
    assert rebuilt is True

    # .hash file contains commit sha, not content hash
    hash_path = repo.sidecar_path.with_suffix(".hash")
    assert hash_path.exists()
    stored_hash = hash_path.read_text().strip()
    assert stored_hash == hash_key
    assert len(stored_hash) == 40

    # Sidecar sqlite exists and contains concept data
    import sqlite3
    conn = sqlite3.connect(repo.sidecar_path)
    rows = conn.execute("SELECT id, canonical_name FROM concept").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "concept1"
    assert rows[0][1] == "test_frequency"


def test_build_skips_when_unchanged(tmp_path):
    """Second build with same HEAD skips rebuild."""
    kr, repo = _setup_git_knowledge_repo(tmp_path)
    from propstore.build_sidecar import build_sidecar
    from propstore.validate import load_concepts
    from propstore.tree_reader import GitTreeReader

    reader = GitTreeReader(kr)
    hash_key = kr.head_sha()
    concepts = load_concepts(None, reader=reader)

    # First build
    rebuilt1 = build_sidecar(
        concepts, repo.sidecar_path, force=False,
        repo=repo,
        commit_hash=hash_key,
        reader=reader,
    )
    assert rebuilt1 is True

    # Second build with same HEAD — should skip
    rebuilt2 = build_sidecar(
        concepts, repo.sidecar_path, force=False,
        repo=repo,
        commit_hash=hash_key,
        reader=reader,
    )
    assert rebuilt2 is False


def test_build_rebuilds_on_new_commit(tmp_path):
    """New commit triggers sidecar rebuild."""
    kr, repo = _setup_git_knowledge_repo(tmp_path)
    from propstore.build_sidecar import build_sidecar
    from propstore.validate import load_concepts
    from propstore.tree_reader import GitTreeReader

    reader = GitTreeReader(kr)
    hash_key1 = kr.head_sha()
    concepts = load_concepts(None, reader=reader)

    # First build
    rebuilt1 = build_sidecar(
        concepts, repo.sidecar_path, force=False,
        repo=repo,
        commit_hash=hash_key1,
        reader=reader,
    )
    assert rebuilt1 is True

    # New commit changes HEAD
    concept2_data = {
        "id": "concept2",
        "canonical_name": "test_boolean",
        "status": "proposed",
        "definition": "A test boolean concept",
        "domain": "testing",
        "form": "boolean",
    }
    kr.commit_files({
        "concepts/test_boolean.yaml": yaml.dump(concept2_data).encode(),
    }, "add second concept")

    # Re-read with new reader and new hash
    reader2 = GitTreeReader(kr)
    hash_key2 = kr.head_sha()
    assert hash_key2 != hash_key1

    concepts2 = load_concepts(None, reader=reader2)
    assert len(concepts2) == 2

    # Build with new commit hash — should rebuild
    rebuilt2 = build_sidecar(
        concepts2, repo.sidecar_path, force=False,
        repo=repo,
        commit_hash=hash_key2,
        reader=reader2,
    )
    assert rebuilt2 is True

    # Hash file now contains new commit sha
    hash_path = repo.sidecar_path.with_suffix(".hash")
    assert hash_path.read_text().strip() == hash_key2

    # Sidecar has both concepts
    import sqlite3
    conn = sqlite3.connect(repo.sidecar_path)
    rows = conn.execute("SELECT id FROM concept ORDER BY id").fetchall()
    conn.close()
    assert [r[0] for r in rows] == ["concept1", "concept2"]


# ── Phase 4-6: Mutations through git, pks log, Repository integration ─


def test_concept_add_creates_commit(tmp_path):
    """pks concept add against a git-backed workspace creates a commit."""
    import shutil
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)

    # Seed forms so validation passes
    package_forms = Path(__file__).resolve().parent.parent / "propstore" / "_resources" / "forms"
    for f in package_forms.glob("*.yaml"):
        shutil.copy2(f, repo.forms_dir / f.name)

    # Commit forms into git so they're available
    git = repo.git
    form_files = {}
    for f in sorted(repo.forms_dir.glob("*.yaml")):
        rel = f.relative_to(repo.root).as_posix()
        form_files[rel] = f.read_bytes()
    git.commit_files(form_files, "Seed forms")
    git.sync_worktree()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "concept", "add",
        "--domain", "testing",
        "--name", "test_freq",
        "--definition", "A test frequency",
        "--form", "frequency",
    ])
    assert result.exit_code == 0, result.output

    # Verify commit exists with the concept
    history = git.log(max_count=10)
    assert any("test_freq" in e["message"] for e in history)

    # Verify file is in git tree
    content = git.read_file("concepts/test_freq.yaml")
    data = yaml.safe_load(content)
    assert data["canonical_name"] == "test_freq"
    assert data["id"].startswith("concept")


def test_concept_rename_atomic(tmp_path):
    """Renaming a concept produces one commit with old file gone, new present."""
    import shutil
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)

    # Seed forms
    package_forms = Path(__file__).resolve().parent.parent / "propstore" / "_resources" / "forms"
    for f in package_forms.glob("*.yaml"):
        shutil.copy2(f, repo.forms_dir / f.name)

    git = repo.git
    form_files = {}
    for f in sorted(repo.forms_dir.glob("*.yaml")):
        rel = f.relative_to(repo.root).as_posix()
        form_files[rel] = f.read_bytes()
    git.commit_files(form_files, "Seed forms")
    git.sync_worktree()

    # Add a concept first
    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "concept", "add",
        "--domain", "testing",
        "--name", "old_name",
        "--definition", "A test concept",
        "--form", "boolean",
    ])
    assert result.exit_code == 0, result.output

    commits_before = len(git.log(max_count=100))

    # Rename it
    # Find the concept ID first
    data = yaml.safe_load(git.read_file("concepts/old_name.yaml"))
    cid = data["id"]

    result = runner.invoke(cli, [
        "-C", str(root),
        "concept", "rename", cid,
        "--name", "new_name",
    ])
    assert result.exit_code == 0, result.output

    # One new commit for the rename
    commits_after = len(git.log(max_count=100))
    assert commits_after == commits_before + 1

    # Old file gone, new file present
    assert "new_name.yaml" in git.list_dir("concepts")
    assert "old_name.yaml" not in git.list_dir("concepts")


def test_promote_commits(tmp_path):
    """Promoting stance files creates a git commit."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)

    # Create a proposal stance file (proposals/ is outside git-tracked dirs)
    proposals_dir = root / "proposals" / "stances"
    proposals_dir.mkdir(parents=True)
    stance_data = {"id": "stance1", "type": "support"}
    (proposals_dir / "test_stance.yaml").write_text(
        yaml.dump(stance_data, default_flow_style=False)
    )
    # Ensure stances dir exists
    repo.stances_dir.mkdir(parents=True, exist_ok=True)

    git = repo.git
    commits_before = len(git.log(max_count=100))

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "promote", "-y"])
    assert result.exit_code == 0, result.output
    assert "1 file(s) promoted" in result.output

    commits_after = len(git.log(max_count=100))
    assert commits_after == commits_before + 1

    # Stance file is in git
    assert "test_stance.yaml" in git.list_dir("stances")


def test_init_creates_git_repo(tmp_path):
    """pks init creates a git-backed repo with initial commits."""
    from click.testing import CliRunner
    from propstore.cli import cli

    runner = CliRunner()
    root = tmp_path / "knowledge"
    result = runner.invoke(cli, ["init", str(root)])
    assert result.exit_code == 0, result.output

    assert (root / ".git").is_dir()

    # Should have commits (gitignore + forms)
    kr = KnowledgeRepo.open(root)
    history = kr.log(max_count=10)
    assert len(history) >= 2  # .gitignore init + forms seed


def test_log_output(tmp_path):
    """pks log shows history after operations."""
    import shutil
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)

    # Seed forms
    package_forms = Path(__file__).resolve().parent.parent / "propstore" / "_resources" / "forms"
    for f in package_forms.glob("*.yaml"):
        shutil.copy2(f, repo.forms_dir / f.name)

    git = repo.git
    form_files = {}
    for f in sorted(repo.forms_dir.glob("*.yaml")):
        rel = f.relative_to(repo.root).as_posix()
        form_files[rel] = f.read_bytes()
    git.commit_files(form_files, "Seed forms")
    git.sync_worktree()

    # Add a concept
    runner = CliRunner()
    runner.invoke(cli, [
        "-C", str(root),
        "concept", "add",
        "--domain", "testing",
        "--name", "log_test",
        "--definition", "Testing log",
        "--form", "boolean",
    ])

    result = runner.invoke(cli, ["-C", str(root), "log"])
    assert result.exit_code == 0, result.output
    assert "log_test" in result.output
    assert "Seed forms" in result.output


def test_ensure_git_migrates(tmp_path):
    """ensure_git() on a plain dir commits existing YAML files."""
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    # Create dirs manually without git
    for d in ["concepts", "claims", "forms"]:
        (root / d).mkdir(parents=True)
    (root / "concepts" / "foo.yaml").write_bytes(
        yaml.dump({"id": "concept1", "canonical_name": "foo"}).encode()
    )

    repo = Repository(root)
    assert repo.git is None  # No git yet

    git = repo.ensure_git()
    assert git is not None

    # Existing file was committed
    content = git.read_file("concepts/foo.yaml")
    data = yaml.safe_load(content)
    assert data["canonical_name"] == "foo"


def test_repo_no_git(tmp_path):
    """Repository over a plain dir has git == None."""
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    root.mkdir(parents=True)
    (root / "concepts").mkdir()

    repo = Repository(root)
    assert repo.git is None


# ── Phase 7: History commands ──────────────────────────────────────


def test_diff_shows_changes(tmp_path):
    """diff_commits() returns correct added/modified/deleted between two commits."""
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({
        "concepts/alpha.yaml": b"id: concept1\n",
        "concepts/beta.yaml": b"id: concept2\n",
    }, "first commit")
    sha1 = kr.head_sha()

    kr.commit_files({
        "concepts/alpha.yaml": b"id: concept1\nstatus: active\n",  # modified
        "concepts/gamma.yaml": b"id: concept3\n",  # added
    }, "second commit")
    kr.commit_deletes(["concepts/beta.yaml"], "delete beta")
    sha3 = kr.head_sha()

    # Diff HEAD (sha3) vs sha1
    diff = kr.diff_commits(commit1=sha3, commit2=sha1)
    assert "concepts/gamma.yaml" in diff["added"]
    assert "concepts/alpha.yaml" in diff["modified"]
    assert "concepts/beta.yaml" in diff["deleted"]


def test_show_commit(tmp_path):
    """show_commit() returns correct sha, message, and file changes."""
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"concepts/a.yaml": b"v: 1\n"}, "add concept a")
    sha = kr.head_sha()

    info = kr.show_commit(sha)
    assert info["sha"] == sha
    assert "add concept a" in info["message"]
    assert info["author"] == "pks <pks@propstore>"
    assert "concepts/a.yaml" in info["added"]
    assert len(info["modified"]) == 0
    assert len(info["deleted"]) == 0


def test_diff_cli(tmp_path):
    """pks diff via CliRunner shows output."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git

    git.commit_files({"concepts/a.yaml": b"v: 1\n"}, "add a")
    git.commit_files({"concepts/a.yaml": b"v: 2\n"}, "modify a")
    git.sync_worktree()

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "diff"])
    assert result.exit_code == 0, result.output
    assert "Modified" in result.output
    assert "concepts/a.yaml" in result.output


def test_show_cli(tmp_path):
    """pks show <sha> via CliRunner shows output."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git

    git.commit_files({"concepts/a.yaml": b"v: 1\n"}, "add concept a")
    sha = git.head_sha()
    git.sync_worktree()

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "show", sha])
    assert result.exit_code == 0, result.output
    assert "add concept a" in result.output
    assert "Commit:" in result.output
    assert "Author:" in result.output


def test_checkout_builds_from_historical(tmp_path):
    """pks checkout <v1_sha> builds sidecar from v1 data."""
    import shutil
    import sqlite3
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)

    # Seed forms so build works
    package_forms = Path(__file__).resolve().parent.parent / "propstore" / "_resources" / "forms"
    for f in package_forms.glob("*.yaml"):
        shutil.copy2(f, repo.forms_dir / f.name)

    git = repo.git
    form_files = {}
    for f in sorted(repo.forms_dir.glob("*.yaml")):
        rel = f.relative_to(repo.root).as_posix()
        form_files[rel] = f.read_bytes()
    git.commit_files(form_files, "Seed forms")

    # v1: one concept
    v1_concept = yaml.dump({
        "id": "concept1",
        "canonical_name": "test_freq_v1",
        "status": "proposed",
        "definition": "A v1 concept",
        "domain": "testing",
        "form": "frequency",
    }).encode()
    git.commit_files({"concepts/test_freq_v1.yaml": v1_concept}, "v1 concept")
    v1_sha = git.head_sha()

    # v2: add another concept
    v2_concept = yaml.dump({
        "id": "concept2",
        "canonical_name": "test_bool_v2",
        "status": "proposed",
        "definition": "A v2 concept",
        "domain": "testing",
        "form": "boolean",
    }).encode()
    git.commit_files({"concepts/test_bool_v2.yaml": v2_concept}, "v2 concept")
    git.sync_worktree()

    # Checkout v1
    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "checkout", v1_sha])
    assert result.exit_code == 0, result.output
    assert "1 concepts" in result.output

    # Verify sidecar contains only v1 data
    hash_path = repo.sidecar_path.with_suffix(".hash")
    assert hash_path.exists()
    assert hash_path.read_text().strip() == v1_sha

    conn = sqlite3.connect(repo.sidecar_path)
    rows = conn.execute("SELECT id, canonical_name FROM concept").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "concept1"
    assert rows[0][1] == "test_freq_v1"
