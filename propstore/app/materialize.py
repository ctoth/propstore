"""Owner-layer loose-file materialize projection.

``materialize_repository`` projects a committed store's semantic tree onto disk as
human-readable loose YAML files (``concepts/…``, ``forms/…``, …). It is the owner
core the ``pks materialize`` adapter calls, and is deliberately distinct from the
content-addressed *sidecar* build (:func:`propstore.derived_build.materialize_world_sidecar`):
this writes round-trippable source files, that builds the SQLite query sidecar.

This is the one ``app`` module permitted to drive the worktree projection — the
ordinary view-builder modules never materialize loose files (a build/render
discipline guard the init tests enforce). Projection is scoped to the semantic
init roots and honours the git policy's ignored paths, so runtime sidecar files
on disk are never clobbered or deleted.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from propstore.repository import Repository
from propstore.storage.snapshot import (
    MaterializeConflictError,
    MaterializeReport,
)


class MaterializeError(Exception):
    """An expected, app-level materialize failure (e.g. an unknown branch)."""


@dataclass(frozen=True)
class MaterializeRequest:
    """A request to project a commit/branch's semantic tree onto disk.

    ``clean`` deletes stale loose files no longer in the source tree (skipping
    ignored runtime files); ``force`` overwrites local edits instead of raising a
    :class:`~propstore.storage.snapshot.MaterializeConflictError`.
    """

    directory: Path | None = None
    commit: str | None = None
    branch: str | None = None
    clean: bool = False
    force: bool = False


def materialize_repository(
    repo: Repository,
    request: MaterializeRequest,
) -> MaterializeReport:
    """Project the requested commit/branch into loose files; return the report.

    A :class:`MaterializeConflictError` (local edits would be overwritten without
    ``force``) propagates so the adapter can surface the conflicting paths; any
    other malformed request (unknown branch, commit/branch both set) is lowered to
    :class:`MaterializeError`.
    """

    target_repo = repo if request.directory is None else Repository.find(request.directory)
    try:
        return target_repo.snapshot.materialize(
            commit=request.commit,
            branch=request.branch,
            clean=request.clean,
            force=request.force,
        )
    except MaterializeConflictError:
        raise
    except ValueError as exc:
        raise MaterializeError(str(exc)) from exc
