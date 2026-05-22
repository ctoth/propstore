"""Application-layer compiler and alias workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from propstore.families.concepts.stages import parse_concept_record_document
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
        record = parse_concept_record_document(handle.document)
        logical_id = record.primary_logical_id or record.canonical_name
        for alias in record.aliases:
            aliases[alias.name] = AliasExportEntry(
                logical_id=str(logical_id),
                name=record.canonical_name,
            )
    return aliases
