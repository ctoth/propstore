"""Tests for the Dulwich-backed KnowledgeRepo and KnowledgePath implementations."""
from __future__ import annotations

from pathlib import Path

import yaml
import pytest

from propstore.knowledge_path import FilesystemKnowledgePath, GitKnowledgePath
from propstore.repo import KnowledgeRepo


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


# ── KnowledgePath: GitKnowledgePath ─────────────────────────────────


def test_git_knowledge_path_iterdir(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({
        "concepts/a.yaml": b"id: concept1\n",
        "concepts/b.yaml": b"id: concept2\n",
        "concepts/readme.txt": b"not yaml\n",
    }, "add")

    tree = GitKnowledgePath(kr) / "concepts"
    entries = [entry for entry in tree.iterdir() if entry.is_file() and entry.suffix == ".yaml"]
    names = [entry.stem for entry in entries]
    assert sorted(names) == ["a", "b"]
    for entry in entries:
        assert entry.read_bytes() == kr.read_file(f"concepts/{entry.name}")


def test_git_knowledge_path_read_bytes(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"concepts/foo.yaml": b"id: concept1\n"}, "add")

    tree = GitKnowledgePath(kr)
    assert (tree / "concepts" / "foo.yaml").read_bytes() == b"id: concept1\n"
    assert not (tree / "concepts" / "nonexistent.yaml").exists()


def test_git_knowledge_path_exists(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"concepts/a.yaml": b"x: 1\n"}, "add")

    tree = GitKnowledgePath(kr)
    assert (tree / "concepts").exists()
    assert not (tree / "claims").exists()


def test_git_knowledge_path_at_commit(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files({"concepts/a.yaml": b"v: 1\n"}, "v1")
    sha1 = kr.head_sha()
    kr.commit_files({"concepts/a.yaml": b"v: 2\n"}, "v2")

    current_tree = GitKnowledgePath(kr) / "concepts"
    old_tree = GitKnowledgePath(kr, commit=sha1) / "concepts"

    assert (current_tree / "a.yaml").read_bytes() == b"v: 2\n"
    assert (old_tree / "a.yaml").read_bytes() == b"v: 1\n"


# ── KnowledgePath: FilesystemKnowledgePath ──────────────────────────


def test_filesystem_knowledge_path_iterdir(tmp_path):
    root = tmp_path / "knowledge"
    concepts = root / "concepts"
    concepts.mkdir(parents=True)
    (concepts / "a.yaml").write_bytes(b"id: concept1\n")
    (concepts / "b.yaml").write_bytes(b"id: concept2\n")
    (concepts / "readme.txt").write_bytes(b"not yaml\n")

    tree = FilesystemKnowledgePath(root) / "concepts"
    entries = [entry for entry in tree.iterdir() if entry.is_file() and entry.suffix == ".yaml"]
    names = [entry.stem for entry in entries]
    assert sorted(names) == ["a", "b"]


def test_filesystem_knowledge_path_read_bytes(tmp_path):
    root = tmp_path / "knowledge"
    concepts = root / "concepts"
    concepts.mkdir(parents=True)
    (concepts / "foo.yaml").write_bytes(b"id: concept1\n")

    tree = FilesystemKnowledgePath(root)
    assert (tree / "concepts" / "foo.yaml").read_bytes() == b"id: concept1\n"
    assert not (tree / "concepts" / "nonexistent.yaml").exists()


def test_filesystem_knowledge_path_exists(tmp_path):
    root = tmp_path / "knowledge"
    (root / "concepts").mkdir(parents=True)

    tree = FilesystemKnowledgePath(root)
    assert (tree / "concepts").exists()
    assert not (tree / "claims").exists()


# ── KnowledgePath equivalence ───────────────────────────────────────


def test_knowledge_path_equivalence(tmp_path):
    """GitKnowledgePath and FilesystemKnowledgePath produce identical output after sync."""
    root = tmp_path / "knowledge"
    kr = KnowledgeRepo.init(root)
    kr.commit_files({
        "concepts/alpha.yaml": b"id: concept1\ncanonical_name: alpha\n",
        "concepts/beta.yaml": b"id: concept2\ncanonical_name: beta\n",
    }, "add concepts")
    kr.sync_worktree()

    git_tree = GitKnowledgePath(kr) / "concepts"
    fs_tree = FilesystemKnowledgePath(root) / "concepts"

    git_entries = sorted(
        (entry.stem, entry.read_bytes())
        for entry in git_tree.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    )
    fs_entries = sorted(
        (entry.stem, entry.read_bytes())
        for entry in fs_tree.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    )

    assert git_entries == fs_entries


# ── Loader reads via KnowledgePath ─────────────────────────────────


def test_load_concepts_from_git_tree(tmp_path):
    """load_concepts() works from a committed git-backed knowledge path."""
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

    from propstore.validate import load_concepts
    concepts = load_concepts(kr.tree() / "concepts")
    assert len(concepts) == 1
    assert concepts[0].data["id"] == "concept1"
    assert isinstance(concepts[0].source_path, GitKnowledgePath)
    assert concepts[0].filename == "test_concept"


def test_load_claim_files_from_git_tree(tmp_path):
    """load_claim_files() works from a committed git-backed knowledge path."""
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

    from propstore.validate_claims import load_claim_files
    claim_files = load_claim_files(kr.tree() / "claims")
    assert len(claim_files) == 1
    assert claim_files[0].data["claims"][0]["id"] == "claim1"
    assert isinstance(claim_files[0].source_path, GitKnowledgePath)
    assert claim_files[0].filename == "test_claims"


def test_load_contexts_from_git_tree(tmp_path):
    """load_contexts() works from a committed git-backed knowledge path."""
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    context_data = {
        "id": "ctx1",
        "name": "Test Context",
        "assumptions": ["test assumption"],
    }
    kr.commit_files({
        "contexts/test_context.yaml": yaml.dump(context_data).encode(),
    }, "add context")

    from propstore.validate_contexts import load_contexts
    contexts = load_contexts(kr.tree() / "contexts")
    assert len(contexts) == 1
    assert contexts[0].data["id"] == "ctx1"
    assert isinstance(contexts[0].source_path, GitKnowledgePath)
    assert contexts[0].filename == "test_context"


def test_context_add_creates_commit(tmp_path):
    """Adding a context in a git-backed repo creates a commit."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    commits_before = len(git.log(max_count=100))

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "context", "add",
        "--name", "ctx_test",
        "--description", "Committed context",
    ])
    assert result.exit_code == 0, result.output

    commits_after = len(git.log(max_count=100))
    assert commits_after == commits_before + 1

    data = yaml.safe_load(git.read_file("contexts/ctx_test.yaml"))
    assert data["id"] == "ctx_test"
    assert data["description"] == "Committed context"


def test_context_add_uses_committed_head_for_inheritance_checks(tmp_path):
    """Inherited parent lookup should come from committed HEAD, not ambient files."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "contexts/ctx_parent.yaml": yaml.dump({
            "id": "ctx_parent",
            "name": "ctx_parent",
            "description": "Parent context",
        }).encode("utf-8"),
    }, "Add parent context")
    git.sync_worktree()
    (root / "contexts" / "ctx_parent.yaml").unlink()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "context", "add",
        "--name", "ctx_child",
        "--description", "Child context",
        "--inherits", "ctx_parent",
    ])
    assert result.exit_code == 0, result.output

    child = yaml.safe_load(git.read_file("contexts/ctx_child.yaml"))
    assert child["inherits"] == "ctx_parent"


def test_context_list_reads_git_head_not_worktree(tmp_path):
    """Context listing should ignore uncommitted worktree edits in git-backed repos."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "contexts/ctx_test.yaml": yaml.dump({
            "id": "ctx_test",
            "name": "ctx_test",
            "description": "Committed description",
        }).encode("utf-8"),
    }, "Add context")
    git.sync_worktree()
    (root / "contexts" / "ctx_test.yaml").write_text(
        yaml.dump({
            "id": "ctx_test",
            "name": "ctx_test",
            "description": "Worktree-only description",
        }, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "context", "list",
    ])
    assert result.exit_code == 0, result.output
    assert "Committed description" in result.output
    assert "Worktree-only description" not in result.output


def test_form_add_creates_commit(tmp_path):
    """Adding a form in a git-backed repo creates a commit."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    commits_before = len(git.log(max_count=100))

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "form", "add",
        "--name", "frequency_like",
        "--unit", "Hz",
        "--dimensions", '{"T": -1}',
    ])
    assert result.exit_code == 0, result.output

    commits_after = len(git.log(max_count=100))
    assert commits_after == commits_before + 1

    data = yaml.safe_load(git.read_file("forms/frequency_like.yaml"))
    assert data["name"] == "frequency_like"
    assert data["unit_symbol"] == "Hz"


def test_form_show_reads_git_head_not_worktree(tmp_path):
    """Form show should ignore uncommitted worktree edits in git-backed repos."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "forms/frequency.yaml": yaml.dump({
            "name": "frequency",
            "dimensionless": False,
            "unit_symbol": "Hz",
        }).encode("utf-8"),
    }, "Add form")
    git.sync_worktree()
    (root / "forms" / "frequency.yaml").write_text(
        yaml.dump({
            "name": "frequency",
            "dimensionless": False,
            "unit_symbol": "kHz",
        }, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "form", "show", "frequency",
    ])
    assert result.exit_code == 0, result.output
    assert "unit_symbol: Hz" in result.output
    assert "unit_symbol: kHz" not in result.output


def test_form_list_reads_git_head_not_worktree(tmp_path):
    """Form list should ignore uncommitted worktree edits in git-backed repos."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "forms/frequency.yaml": yaml.dump({
            "name": "frequency",
            "dimensionless": False,
            "unit_symbol": "Hz",
        }).encode("utf-8"),
    }, "Add form")
    git.sync_worktree()
    (root / "forms" / "rogue.yaml").write_text(
        yaml.dump({
            "name": "rogue",
            "dimensionless": True,
        }, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "form", "list",
    ])
    assert result.exit_code == 0, result.output
    assert "frequency" in result.output
    assert "rogue" not in result.output


def test_form_remove_uses_committed_head_for_reference_checks(tmp_path):
    """Form removal should respect committed concept references, not ambient files."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "forms/frequency.yaml": yaml.dump({
            "name": "frequency",
            "dimensionless": False,
            "unit_symbol": "Hz",
        }).encode("utf-8"),
        "concepts/fundamental_frequency.yaml": yaml.dump({
            "id": "concept1",
            "canonical_name": "fundamental_frequency",
            "status": "accepted",
            "definition": "Frequency concept",
            "domain": "speech",
            "form": "frequency",
        }).encode("utf-8"),
    }, "Seed form and concept")
    git.sync_worktree()
    (root / "concepts" / "fundamental_frequency.yaml").unlink()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "form", "remove", "frequency",
    ])
    assert result.exit_code != 0
    assert "referenced by 1 concept" in result.output


def test_worldline_create_creates_commit(tmp_path):
    """Creating a worldline in a git-backed repo creates a commit."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    commits_before = len(git.log(max_count=100))

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "worldline", "create", "wl_test",
        "--target", "concept1",
    ])
    assert result.exit_code == 0, result.output

    commits_after = len(git.log(max_count=100))
    assert commits_after == commits_before + 1

    data = yaml.safe_load(git.read_file("worldlines/wl_test.yaml"))
    assert data["id"] == "wl_test"
    assert data["targets"] == ["concept1"]


def test_worldline_create_uses_committed_head_for_duplicate_checks(tmp_path):
    """Worldline create should reject duplicates based on committed HEAD."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "worldlines/wl_test.yaml": yaml.dump({
            "id": "wl_test",
            "name": "wl_test",
            "targets": ["concept1"],
        }).encode("utf-8"),
    }, "Seed worldline")
    git.sync_worktree()
    (root / "worldlines" / "wl_test.yaml").unlink()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "worldline", "create", "wl_test",
        "--target", "concept1",
    ])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_worldline_show_reads_git_head_not_worktree(tmp_path):
    """Worldline show should ignore uncommitted worktree edits in git-backed repos."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "worldlines/wl_test.yaml": yaml.dump({
            "id": "wl_test",
            "name": "Committed Worldline",
            "targets": ["concept1"],
        }, default_flow_style=False, sort_keys=False).encode("utf-8"),
    }, "Seed worldline")
    git.sync_worktree()
    (root / "worldlines" / "wl_test.yaml").write_text(
        yaml.dump({
            "id": "wl_test",
            "name": "Worktree Worldline",
            "targets": ["concept1"],
        }, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "worldline", "show", "wl_test",
    ])
    assert result.exit_code == 0, result.output
    assert "Committed Worldline" in result.output
    assert "Worktree Worldline" not in result.output


def test_worldline_list_reads_git_head_not_worktree(tmp_path):
    """Worldline list should ignore uncommitted worktree additions in git-backed repos."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "worldlines/wl_test.yaml": yaml.dump({
            "id": "wl_test",
            "name": "Committed Worldline",
            "targets": ["concept1"],
        }).encode("utf-8"),
    }, "Seed worldline")
    git.sync_worktree()
    (root / "worldlines" / "rogue.yaml").write_text(
        yaml.dump({
            "id": "rogue",
            "name": "Rogue Worldline",
            "targets": ["concept2"],
        }, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "worldline", "list",
    ])
    assert result.exit_code == 0, result.output
    assert "wl_test" in result.output
    assert "rogue" not in result.output


def test_worldline_delete_commits_delete_from_git_head(tmp_path):
    """Worldline delete should remove the committed definition even if the worktree is missing it."""
    from click.testing import CliRunner
    from propstore.cli import cli
    from propstore.cli.repository import Repository

    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    git.commit_files({
        "worldlines/wl_test.yaml": yaml.dump({
            "id": "wl_test",
            "name": "Committed Worldline",
            "targets": ["concept1"],
        }).encode("utf-8"),
    }, "Seed worldline")
    git.sync_worktree()
    (root / "worldlines" / "wl_test.yaml").unlink()
    commits_before = len(git.log(max_count=100))

    runner = CliRunner()
    result = runner.invoke(cli, [
        "-C", str(root),
        "worldline", "delete", "wl_test",
    ])
    assert result.exit_code == 0, result.output

    commits_after = len(git.log(max_count=100))
    assert commits_after == commits_before + 1
    with pytest.raises(FileNotFoundError):
        git.read_file("worldlines/wl_test.yaml")


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

    hash_key = kr.head_sha()
    tree = repo.tree(commit=hash_key)

    rebuilt = build_sidecar(
        tree, repo.sidecar_path, force=False,
        commit_hash=hash_key,
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

    hash_key = kr.head_sha()
    tree = repo.tree(commit=hash_key)

    # First build
    rebuilt1 = build_sidecar(
        tree, repo.sidecar_path, force=False,
        commit_hash=hash_key,
    )
    assert rebuilt1 is True

    # Second build with same HEAD ��� should skip
    rebuilt2 = build_sidecar(
        tree, repo.sidecar_path, force=False,
        commit_hash=hash_key,
    )
    assert rebuilt2 is False


def test_build_rebuilds_on_new_commit(tmp_path):
    """New commit triggers sidecar rebuild."""
    kr, repo = _setup_git_knowledge_repo(tmp_path)
    from propstore.build_sidecar import build_sidecar

    hash_key1 = kr.head_sha()
    tree1 = repo.tree(commit=hash_key1)

    # First build
    rebuilt1 = build_sidecar(
        tree1, repo.sidecar_path, force=False,
        commit_hash=hash_key1,
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

    hash_key2 = kr.head_sha()
    tree2 = repo.tree(commit=hash_key2)
    assert hash_key2 != hash_key1

    # Build with new commit hash — should rebuild
    rebuilt2 = build_sidecar(
        tree2, repo.sidecar_path, force=False,
        commit_hash=hash_key2,
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
    assert "Sidecar built from commit" in result.output

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
