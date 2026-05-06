"""Application-layer compiler, sidecar, and alias workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from propstore.compiler.workflows import CompilerWorkflowError
from propstore.core.aliases import AliasExportEntry
from propstore.repository import Repository
from propstore.sidecar.query import SidecarQueryError


@dataclass(frozen=True)
class SidecarQueryRequest:
    sql: str


@dataclass(frozen=True)
class AliasExportRequest:
    pass


def validate_repository(repo: Repository):
    from propstore.compiler.workflows import validate_repository as run_validate_repository

    return run_validate_repository(repo)


def build_repository(
    repo: Repository,
    *,
    output: str | None,
    force: bool,
    strict_authoring: bool = False,
):
    from propstore.compiler.workflows import build_repository as run_build_repository

    return run_build_repository(
        repo,
        output=output,
        force=force,
        strict_authoring=strict_authoring,
    )


def query_sidecar(repo: Repository, request: SidecarQueryRequest):
    from propstore.sidecar.query import query_sidecar as run_query_sidecar

    return run_query_sidecar(repo, request.sql)


def export_aliases(repo: Repository) -> Mapping[str, AliasExportEntry]:
    from propstore.core.aliases import export_concept_aliases

    return export_concept_aliases(repo)
