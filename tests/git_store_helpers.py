from __future__ import annotations

from pathlib import Path

from quire.git_store import GitStore

from propstore.storage import PROPSTORE_GIT_POLICY


def init_store(root: Path) -> GitStore:
    return GitStore.init(root, policy=PROPSTORE_GIT_POLICY)


def open_store(root: Path) -> GitStore:
    return GitStore.open(root, policy=PROPSTORE_GIT_POLICY)


def is_store(root: Path) -> bool:
    return GitStore.is_repo(root)
