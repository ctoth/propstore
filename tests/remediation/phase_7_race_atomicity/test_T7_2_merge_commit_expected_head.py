from __future__ import annotations

import pytest

from propstore.merge.merge_commit import create_merge_commit
from propstore.repository import Repository
from tests.git_store_helpers import init_store
from propstore.storage.snapshot import RepositorySnapshot
from quire.git_store import GitStore, HeadMismatchError


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))
