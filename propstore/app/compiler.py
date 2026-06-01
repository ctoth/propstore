"""Application-layer compiler and alias workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from propstore.repository import Repository


@dataclass(frozen=True)
class AliasExportRequest:
    pass


@dataclass(frozen=True)
class AliasExportEntry:
    logical_id: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return {
            "logical_id": self.logical_id,
            "name": self.name,
        }


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
    aliases: dict[str, AliasExportEntry] = {}
    for handle in repo.families.concepts.iter_handles():
        document = handle.document
        canonical_name = document.lexical_entry.canonical_form.written_rep
        primary_logical_id = None
        if document.logical_ids:
            primary = document.logical_ids[0]
            primary_logical_id = f"{primary.namespace}:{primary.value}"
        logical_id = primary_logical_id or canonical_name
        for alias in document.aliases:
            aliases[alias.name] = AliasExportEntry(
                logical_id=str(logical_id),
                name=canonical_name,
            )
    return aliases
