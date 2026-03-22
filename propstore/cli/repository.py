"""Repository — locates and provides paths within a propstore knowledge/ directory."""
from __future__ import annotations

from pathlib import Path


class RepositoryNotFound(Exception):
    """Raised when no knowledge/ directory can be found."""


class Repository:
    """A propstore knowledge repository rooted at a ``knowledge/`` directory.

    All path resolution for concepts, claims, forms, sidecar, and counters
    goes through this object.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    @property
    def root(self) -> Path:
        return self._root

    @property
    def concepts_dir(self) -> Path:
        return self._root / "concepts"

    @property
    def claims_dir(self) -> Path:
        return self._root / "claims"

    @property
    def forms_dir(self) -> Path:
        return self._root / "forms"

    @property
    def sidecar_dir(self) -> Path:
        return self._root / "sidecar"

    @property
    def sidecar_path(self) -> Path:
        return self._root / "sidecar" / "propstore.sqlite"

    @property
    def stances_dir(self) -> Path:
        return self._root / "stances"

    @property
    def counters_dir(self) -> Path:
        return self._root / "concepts" / ".counters"

    @classmethod
    def find(cls, start: Path | None = None) -> Repository:
        """Walk up from *start* (default: cwd) looking for a ``knowledge/`` directory.

        Also recognises *start* itself as a repository root if it contains
        a ``concepts/`` subdirectory (e.g. ``pks -C path/to/knowledge``
        or when cwd is already inside the knowledge tree).
        """
        current = (start or Path.cwd()).resolve()
        # If start itself has the knowledge structure (e.g. -C pointed at it,
        # or cwd is already the knowledge dir)
        if (current / "concepts").is_dir():
            return cls(current)
        # Walk up looking for knowledge/
        for ancestor in [current, *current.parents]:
            candidate = ancestor / "knowledge"
            if candidate.is_dir() and (candidate / "concepts").is_dir():
                return cls(candidate)
        raise RepositoryNotFound(
            f"No knowledge/ directory found (searched from {current}). "
            f"Run 'pks init' to create one."
        )

    @classmethod
    def init(cls, root: Path) -> Repository:
        """Create the directory structure and return a Repository."""
        dirs = [
            root / "concepts" / ".counters",
            root / "claims",
            root / "forms",
            root / "sidecar",
            root / "stances",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        return cls(root)
