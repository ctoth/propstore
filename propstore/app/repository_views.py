"""Shared application-layer repository view contracts for read surfaces."""

from __future__ import annotations

from dataclasses import dataclass


class AppRepositoryViewError(Exception):
    """Base class for expected repository-view app failures."""


class RepositoryViewUnsupportedStateError(AppRepositoryViewError):
    """Raised when a requested repository view is not implemented."""


@dataclass(frozen=True)
class AppRepositoryViewRequest:
    branch: str | None = None
    revision: str | None = None


def validate_repository_view(request: AppRepositoryViewRequest) -> None:
    """Reject repository-view modes that the read surfaces do not support yet."""

    if request.branch is not None:
        raise RepositoryViewUnsupportedStateError(
            "branch-qualified views are not implemented"
        )
    if request.revision is not None:
        raise RepositoryViewUnsupportedStateError(
            "revision-qualified views are not implemented"
        )


def repository_view_label(request: AppRepositoryViewRequest) -> str:
    """Return a stable label for the current repository view."""

    validate_repository_view(request)
    return "current worktree"
