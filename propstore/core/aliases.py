"""Concept alias export helpers."""
from __future__ import annotations

from dataclasses import dataclass

from propstore.families.concepts.stages import parse_concept_record_document
from propstore.families.identity.logical_ids import primary_logical_id
from propstore.repository import Repository


@dataclass(frozen=True)
class AliasExportEntry:
    logical_id: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return {
            "logical_id": self.logical_id,
            "name": self.name,
        }


def export_concept_aliases(repo: Repository) -> dict[str, AliasExportEntry]:
    aliases: dict[str, AliasExportEntry] = {}
    for handle in repo.families.concepts.iter_handles():
        document = handle.document
        data = parse_concept_record_document(document).to_payload()
        logical_id = primary_logical_id(data) or data.get("canonical_name", "")
        name = data.get("canonical_name", "")
        for alias in data.get("aliases", []) or []:
            alias_name = alias.get("name", "")
            if alias_name:
                aliases[alias_name] = AliasExportEntry(
                    logical_id=str(logical_id),
                    name=str(name),
                )
    return aliases
