from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from propstore.repository import Repository
from propstore.storage.snapshot import MaterializeConflictError


def test_materialize_conflict_does_not_create_missing_snapshot_files(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {
            "concepts/a.yaml": b"name: a\n",
            "concepts/b.yaml": b"name: b\n",
            "concepts/c.yaml": b"name: c\n",
        },
        "seed snapshot",
    )
    repo.snapshot.materialize()

    missing_before = repo.root / "concepts" / "a.yaml"
    clean_before = repo.root / "concepts" / "b.yaml"
    conflict_before = repo.root / "concepts" / "c.yaml"
    missing_before.unlink()
    clean_bytes = clean_before.read_bytes()
    conflict_before.write_bytes(b"local edit\n")

    with pytest.raises(MaterializeConflictError):
        repo.snapshot.materialize()

    assert not missing_before.exists()
    assert clean_before.read_bytes() == clean_bytes
    assert conflict_before.read_bytes() == b"local edit\n"


@pytest.mark.property
@given(
    deleted_index=st.integers(min_value=0, max_value=2),
    conflicted_index=st.integers(min_value=0, max_value=2),
)
def test_materialize_is_all_or_nothing_for_generated_local_edits(
    deleted_index: int,
    conflicted_index: int,
) -> None:
    if deleted_index == conflicted_index:
        conflicted_index = (conflicted_index + 1) % 3
    with tempfile.TemporaryDirectory() as tmp_dir:
        _assert_generated_materialize_case(Path(tmp_dir), deleted_index, conflicted_index)


def _assert_generated_materialize_case(
    tmp_path: Path,
    deleted_index: int,
    conflicted_index: int,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    entries = {
        f"concepts/item_{index}.yaml": f"name: item_{index}\n".encode("utf-8")
        for index in range(3)
    }
    repo.git.commit_files(entries, "seed generated snapshot")
    repo.snapshot.materialize()

    paths = [repo.root / f"concepts/item_{index}.yaml" for index in range(3)]
    before = {
        path.relative_to(repo.root).as_posix(): path.read_bytes()
        for path in paths
        if path.exists()
    }
    paths[deleted_index].unlink()
    paths[conflicted_index].write_bytes(b"generated local edit\n")

    with pytest.raises(MaterializeConflictError):
        repo.snapshot.materialize()

    assert not paths[deleted_index].exists()
    for relpath, content in before.items():
        path = repo.root / relpath
        if path.exists():
            assert path.read_bytes() == (
                b"generated local edit\n"
                if path == paths[conflicted_index]
                else content
            )
