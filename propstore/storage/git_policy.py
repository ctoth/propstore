"""Propstore git-store policy."""
from __future__ import annotations

from quire.git_store import GitStorePolicy

_DEFAULT_AUTHOR = b"pks <pks@propstore>"
_PRIMARY_BRANCH = "master"
_GITIGNORE_CONTENT = """\
sidecar/
*.sqlite
*.sqlite-wal
*.sqlite-shm
*.hash
*.provenance
"""

PROPSTORE_GIT_POLICY = GitStorePolicy(
    author=_DEFAULT_AUTHOR,
    primary_branch=_PRIMARY_BRANCH,
    initial_files={".gitignore": _GITIGNORE_CONTENT.encode("utf-8")},
    initial_commit_message="Initialize knowledge repository",
    ignored_path_prefixes=("sidecar/",),
    ignored_path_suffixes=(
        ".sqlite",
        ".sqlite-wal",
        ".sqlite-shm",
        ".hash",
        ".provenance",
    ),
)
