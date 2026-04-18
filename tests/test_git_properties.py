"""Phase 8: Hypothesis property tests for GitStore.

Tests deep invariants of the git-backed knowledge repository using
property-based testing (Hypothesis) and a stateful RuleBasedStateMachine.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize

from quire.tree_path import FilesystemTreePath as FilesystemKnowledgePath, GitTreePath as GitKnowledgePath
from quire.git_store import GitStore
from propstore.storage import init_git_store, init_memory_git_store

# ── Strategies ──────────────────────────────────────────────────────

yaml_bytes = st.dictionaries(
    st.text(st.characters(whitelist_categories=("L", "N")), min_size=1, max_size=20),
    st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        st.text(min_size=0, max_size=50),
        st.booleans(),
    ),
    min_size=1,
    max_size=10,
).map(lambda d: yaml.dump(d, default_flow_style=False).encode("utf-8"))

valid_subdir = st.sampled_from(["concepts", "claims", "contexts", "stances", "worldlines"])

valid_filename = st.from_regex(r"[a-z][a-z0-9_]{0,20}", fullmatch=True).map(
    lambda s: f"{s}.yaml"
)

valid_path = st.tuples(valid_subdir, valid_filename).map(lambda t: f"{t[0]}/{t[1]}")


def _make_repo() -> GitStore:
    """Create a fresh in-memory GitStore."""
    return init_memory_git_store()


def _make_disk_repo() -> tuple[GitStore, Path]:
    """Create a fresh GitStore on disk (for worktree/filesystem tests)."""
    tmpdir = tempfile.mkdtemp()
    root = Path(tmpdir) / "knowledge"
    repo = init_git_store(root)
    return repo, root


# ── Property 1: Roundtrip preservation ──────────────────────────────


@settings(deadline=None)
@given(path=valid_path, content=yaml_bytes)
def test_roundtrip_preservation(path: str, content: bytes) -> None:
    """commit_files then read_file returns data byte-for-byte."""
    repo = _make_repo()
    repo.commit_files({path: content}, f"add {path}")
    assert repo.read_file(path) == content


# ── Property 2: Listing completeness ────────────────────────────────


@settings(deadline=None)
@given(subdir=valid_subdir, filenames=st.lists(valid_filename, min_size=1, max_size=5, unique=True))
def test_listing_completeness(subdir: str, filenames: list[str]) -> None:
    """Committed files appear in list_dir(subdir)."""
    repo = _make_repo()
    content = b"x: 1\n"
    changes: dict[str | Path, bytes] = {f"{subdir}/{fn}": content for fn in filenames}
    repo.commit_files(changes, f"add files to {subdir}")
    listed = repo.list_dir(subdir)
    for fn in filenames:
        assert fn in listed, f"{fn} not in {listed}"


# ── Property 3: Delete semantics ────────────────────────────────────


@settings(deadline=None)
@given(path=valid_path, content=yaml_bytes)
def test_delete_semantics(path: str, content: bytes) -> None:
    """After commit_deletes, read_file raises FileNotFoundError."""
    repo = _make_repo()
    repo.commit_files({path: content}, f"add {path}")
    repo.commit_deletes([path], f"delete {path}")
    try:
        repo.read_file(path)
        assert False, f"Expected FileNotFoundError for {path}"
    except FileNotFoundError:
        pass


# ── Property 4: Batch atomicity ─────────────────────────────────────


@settings(deadline=None)
@given(
    add_path=valid_path,
    add_content=yaml_bytes,
    del_path=valid_path,
    del_content=yaml_bytes,
)
def test_batch_atomicity(
    add_path: str, add_content: bytes, del_path: str, del_content: bytes
) -> None:
    """commit_batch produces one commit; adds present, deletes gone."""
    repo = _make_repo()
    # Pre-commit the file to be deleted
    repo.commit_files({del_path: del_content}, "setup")
    initial_count = len(repo.log(max_count=10000))

    # Batch: add one, delete the other
    repo.commit_batch(adds={add_path: add_content}, deletes=[del_path], message="batch op")
    new_count = len(repo.log(max_count=10000))

    # Exactly one new commit
    assert new_count == initial_count + 1

    if add_path == del_path:
        # Same path: implementation deletes after adding, so file is gone
        try:
            repo.read_file(add_path)
            assert False, f"Expected FileNotFoundError for {add_path} (add+delete same path)"
        except FileNotFoundError:
            pass
    else:
        # Add is present
        assert repo.read_file(add_path) == add_content
        # Delete is gone
        try:
            repo.read_file(del_path)
            assert False, f"Expected FileNotFoundError for {del_path}"
        except FileNotFoundError:
            pass


# ── Property 5: Worktree fidelity ───────────────────────────────────


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(path=valid_path, content=yaml_bytes)
def test_worktree_fidelity(path: str, content: bytes) -> None:
    """After sync_worktree, on-disk files match git tree byte-for-byte."""
    repo, root = _make_disk_repo()
    repo.commit_files({path: content}, f"add {path}")
    repo.sync_worktree()
    disk_path = root / path.replace("/", os.sep)
    assert disk_path.exists(), f"{disk_path} not on disk"
    assert disk_path.read_bytes() == content


# ── Property 6: KnowledgePath equivalence ───────────────────────────


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(subdir=valid_subdir, filename=valid_filename, content=yaml_bytes)
def test_knowledge_path_equivalence(subdir: str, filename: str, content: bytes) -> None:
    """GitKnowledgePath and FilesystemKnowledgePath produce same output after sync."""
    repo, root = _make_disk_repo()
    path = f"{subdir}/{filename}"
    repo.commit_files({path: content}, f"add {path}")
    repo.sync_worktree()

    git_tree = GitKnowledgePath(repo) / subdir
    fs_tree = FilesystemKnowledgePath(root) / subdir

    git_entries = {
        (entry.stem, entry.read_bytes())
        for entry in git_tree.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    }
    fs_entries = {
        (entry.stem, entry.read_bytes())
        for entry in fs_tree.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    }

    assert set(git_entries) == set(fs_entries), (
        f"git={git_entries}, fs={fs_entries}"
    )


# ── Property 7: History monotonicity ────────────────────────────────


@settings(deadline=None)
@given(
    paths=st.lists(valid_path, min_size=2, max_size=5, unique=True),
)
def test_history_monotonicity(paths: list[str]) -> None:
    """After N commits, log has N entries and head_sha changes each time."""
    repo = _make_repo()
    # init creates 1 commit
    shas = [repo.head_sha()]

    for i, path in enumerate(paths):
        repo.commit_files({path: f"v: {i}\n".encode()}, f"commit {i}")
        sha = repo.head_sha()
        assert sha not in shas, f"Duplicate sha after commit {i}"
        shas.append(sha)

    # 1 (init) + len(paths) commits
    expected = 1 + len(paths)
    history = repo.log(max_count=expected + 1)
    assert len(history) == expected, f"Expected {expected}, got {len(history)}"


# ── Property 8: Idempotent sync ─────────────────────────────────────


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(path=valid_path, content=yaml_bytes)
def test_idempotent_sync(path: str, content: bytes) -> None:
    """sync_worktree called twice produces same filesystem state."""
    repo, root = _make_disk_repo()
    repo.commit_files({path: content}, f"add {path}")

    repo.sync_worktree()
    first_snapshot = _snapshot_dir(root)

    repo.sync_worktree()
    second_snapshot = _snapshot_dir(root)

    assert first_snapshot == second_snapshot


def _snapshot_dir(root: Path) -> dict[str, bytes]:
    """Snapshot all non-.git files as {relative_posix_path: bytes}."""
    result: dict[str, bytes] = {}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        if rel.startswith(".git"):
            continue
        result[rel] = f.read_bytes()
    return result


# ── Property 9: Commit message preservation ─────────────────────────


@settings(deadline=None)
@given(
    path=valid_path,
    content=yaml_bytes,
    msg=st.text(
        st.characters(whitelist_categories=("L", "N", "Z"), whitelist_characters=" -_:."),
        min_size=1,
        max_size=80,
    ),
)
def test_commit_message_preservation(path: str, content: bytes, msg: str) -> None:
    """Message passed to commit_files appears in log output."""
    repo = _make_repo()
    repo.commit_files({path: content}, msg)
    history = repo.log(max_count=1)
    assert len(history) >= 1
    assert history[0]["message"] == msg.strip()


# ── Property 10: Path normalization ─────────────────────────────────


@settings(deadline=None)
@given(subdir=valid_subdir, name=valid_filename, content=yaml_bytes)
def test_path_normalization(subdir: str, name: str, content: bytes) -> None:
    """Paths with backslashes are normalized internally."""
    kr = _make_repo()

    posix_path = f"{subdir}/{name}"
    backslash_path = f"{subdir}\\{name}"

    kr.commit_files({backslash_path: content}, "add with backslash")
    # Should be readable via both path forms
    assert kr.read_file(posix_path) == content
    assert kr.read_file(backslash_path) == content


# ── Stateful test: RuleBasedStateMachine ────────────────────────────


class GitStoreMachine(RuleBasedStateMachine):
    """Model-based test: dict[str, bytes] is the oracle, GitStore is the SUT."""

    def __init__(self) -> None:
        super().__init__()
        self.model: dict[str, bytes] = {}
        self.commit_count = 0
        self.repo: GitStore | None = None
        self.tmpdir: str = ""

    @initialize()
    def init_repo(self) -> None:
        self.repo = init_memory_git_store()
        self.commit_count = 1  # init creates .gitignore commit
        self.model = {}

    @rule(path=valid_path, content=yaml_bytes)
    def commit_file(self, path: str, content: bytes) -> None:
        assert self.repo is not None
        self.repo.commit_files({path: content}, f"add {path}")
        self.model[path] = content
        self.commit_count += 1

    @rule(data=st.data())
    def delete_file(self, data: st.DataObject) -> None:
        if not self.model:
            return
        assert self.repo is not None
        path = data.draw(st.sampled_from(sorted(self.model.keys())))
        self.repo.commit_deletes([path], f"delete {path}")
        del self.model[path]
        self.commit_count += 1

    @invariant()
    def reads_match_model(self) -> None:
        if self.repo is None:
            return
        for path, expected in self.model.items():
            assert self.repo.read_file(path) == expected, f"Mismatch at {path}"

    @invariant()
    def deleted_files_gone(self) -> None:
        if self.repo is None:
            return
        for subdir in ["concepts", "claims", "contexts", "stances", "worldlines"]:
            try:
                names = self.repo.list_dir(subdir)
            except (FileNotFoundError, KeyError):
                continue
            for name in names:
                full = f"{subdir}/{name}"
                if full not in self.model and full != ".gitignore":
                    assert False, f"Ghost file: {full}"

    @invariant()
    def history_length(self) -> None:
        if self.repo is None:
            return
        history = self.repo.log(max_count=10000)
        assert len(history) == self.commit_count, (
            f"Expected {self.commit_count} commits, got {len(history)}"
        )


TestGitStore = GitStoreMachine.TestCase
TestGitStore.settings = settings(
    stateful_step_count=10,
    deadline=None,
)
