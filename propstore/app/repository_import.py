"""Application-layer repository import workflows."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Mapping

from propstore.repository import Repository


class RepositoryImportError(Exception):
    pass


def import_repository(
    repo: Repository,
    source_repository: Path,
    *,
    target_branch: str | None = None,
    message: str | None = None,
) -> Mapping[str, object]:
    from propstore.importing.repository_import import (
        commit_repository_import,
        plan_repository_import,
    )

    try:
        repo.snapshot.head_sha()
    except ValueError as exc:
        raise RepositoryImportError(
            "import-repository requires a git-backed repository"
        ) from exc

    plan = plan_repository_import(
        repo,
        source_repository,
        target_branch=target_branch,
    )
    result = commit_repository_import(repo, plan, message=message)
    return asdict(result)
