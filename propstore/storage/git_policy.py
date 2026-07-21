"""The git store policy for a propstore knowledge repository.

``PROPSTORE_GIT_POLICY`` is the one :class:`~quire.git_store.GitStorePolicy` for
every propstore repository: the authoring identity, the primary branch, and the
ignored derived-artifact paths (the content-addressed sidecar / sqlite files
live outside version control). It is supplied to ``GitStore.open`` / ``init`` so
the policy travels with the store rather than being re-stated per call.
"""

from __future__ import annotations

from quire.git_store import GitStorePolicy

_GITIGNORE_CONTENT = (
    "sidecar/\n*.sqlite\n*.sqlite-wal\n*.sqlite-shm\n*.hash\n*.provenance\n"
)

PROPSTORE_GIT_POLICY = GitStorePolicy(
    author=b"pks <pks@propstore>",
    primary_branch="master",
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
