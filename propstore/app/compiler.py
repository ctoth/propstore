"""Application-layer compiler and alias workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from propstore.core.aliases import AliasExportEntry
from propstore.repository import Repository


@dataclass(frozen=True)
class AliasExportRequest:
    pass


def validate_repository(repo: Repository):
    from propstore.compiler.workflows import validate_repository as run_validate_repository

    return run_validate_repository(repo)


def build_repository(
    repo: Repository,
    *,
    force: bool,
    strict_authoring: bool = False,
):
    from propstore.compiler.workflows import build_repository as run_build_repository

    return run_build_repository(
        repo,
        force=force,
        strict_authoring=strict_authoring,
    )


def export_aliases(repo: Repository) -> Mapping[str, AliasExportEntry]:
    from propstore.core.aliases import export_concept_aliases

    return export_concept_aliases(repo)
