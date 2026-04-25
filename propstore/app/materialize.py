"""Explicit repository materialization workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from propstore.repository import Repository
from propstore.storage.snapshot import MaterializeConflictError, MaterializeReport


class MaterializeError(Exception):
    pass


@dataclass(frozen=True)
class MaterializeRequest:
    directory: Path | None = None
    commit: str | None = None
    branch: str | None = None
    clean: bool = False
    force: bool = False


def materialize_repository(repo: Repository, request: MaterializeRequest) -> MaterializeReport:
    target_repo = Repository.find(request.directory) if request.directory is not None else repo
    try:
        return target_repo.snapshot.materialize(
            commit=request.commit,
            branch=request.branch,
            clean=request.clean,
            force=request.force,
        )
    except (MaterializeConflictError, ValueError) as exc:
        raise MaterializeError(str(exc)) from exc
