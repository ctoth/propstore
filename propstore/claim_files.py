"""Loaded-claim file helpers and claim-file coercion."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from propstore.artifacts.documents.claims import ClaimDocument, ClaimsFileDocument
from propstore.artifacts.schema import convert_document_value, load_document_dir
from propstore.knowledge_path import KnowledgePath
from propstore.loaded import LoadedDocument, LoadedEntry


def _source_label(filename: str, source_path: KnowledgePath | None) -> str:
    if source_path is None:
        return filename
    rendered = source_path.as_posix()
    return rendered if rendered else filename


class LoadedClaimFile(LoadedDocument[ClaimsFileDocument]):
    """Typed claim-file envelope."""

    @classmethod
    def from_payload(
        cls,
        *,
        filename: str,
        source_path: KnowledgePath | Path | None,
        data: dict[str, Any],
        knowledge_root: KnowledgePath | Path | None = None,
    ) -> LoadedClaimFile:
        label = filename if source_path is None else str(source_path)
        document = convert_document_value(
            data,
            ClaimsFileDocument,
            source=label,
        )
        return cls(
            filename=filename,
            source_path=source_path,
            knowledge_root=knowledge_root,
            document=document,
        )

    @classmethod
    def from_loaded_document(
        cls,
        document: LoadedDocument[ClaimsFileDocument],
    ) -> LoadedClaimFile:
        return cls(
            filename=document.filename,
            source_path=document.source_path,
            knowledge_root=document.knowledge_root,
            document=document.document,
        )

    @classmethod
    def from_loaded_entry(cls, entry: LoadedEntry) -> LoadedClaimFile:
        document = convert_document_value(
            entry.data,
            ClaimsFileDocument,
            source=_source_label(entry.filename, entry.source_path),
        )
        return cls(
            filename=entry.filename,
            source_path=entry.source_path,
            knowledge_root=entry.knowledge_root,
            document=document,
        )

    @property
    def claims(self) -> tuple[ClaimDocument, ...]:
        return self.document.claims

    @property
    def source_paper(self) -> str:
        return self.document.source.paper

    @property
    def stage(self) -> str | None:
        return self.document.stage

    @property
    def data(self) -> dict[str, Any]:
        return self.document.to_payload()

    @data.setter
    def data(self, value: dict[str, Any]) -> None:
        self.document = convert_document_value(
            value,
            ClaimsFileDocument,
            source=_source_label(self.filename, self.source_path),
        )

    def to_loaded_entry(self) -> LoadedEntry:
        return LoadedEntry(
            filename=self.filename,
            source_path=self.source_path,
            knowledge_root=self.knowledge_root,
            data=self.document.to_payload(),
        )


ClaimFileInput = LoadedClaimFile | LoadedEntry


def coerce_loaded_claim_file(claim_file: ClaimFileInput) -> LoadedClaimFile:
    if isinstance(claim_file, LoadedClaimFile):
        return claim_file
    return LoadedClaimFile.from_loaded_entry(claim_file)


def coerce_loaded_claim_files(
    claim_files: list[ClaimFileInput],
) -> list[LoadedClaimFile]:
    return [coerce_loaded_claim_file(claim_file) for claim_file in claim_files]


def claim_file_claim_payloads(claim_file: ClaimFileInput) -> tuple[dict[str, Any], ...]:
    if isinstance(claim_file, LoadedClaimFile):
        return tuple(claim.to_payload() for claim in claim_file.claims)
    raw_claims = claim_file.data.get("claims")
    if not isinstance(raw_claims, list):
        return ()
    return tuple(dict(claim) for claim in raw_claims if isinstance(claim, dict))


def claim_file_default_source_paper(claim_file: ClaimFileInput) -> str | None:
    if isinstance(claim_file, LoadedClaimFile):
        source_paper = claim_file.source_paper
    else:
        source = claim_file.data.get("source")
        source_paper = source.get("paper") if isinstance(source, dict) else None
    if isinstance(source_paper, str) and source_paper:
        return source_paper
    return None


def claim_payload_source_paper(
    claim: Mapping[str, Any],
    claim_file: ClaimFileInput,
) -> str | None:
    if not isinstance(claim_file, LoadedClaimFile):
        return claim_file_default_source_paper(claim_file)
    source_paper = claim.get("source_paper")
    if isinstance(source_paper, str) and source_paper:
        return source_paper
    return claim_file_default_source_paper(claim_file)


def load_claim_files(claims_dir: KnowledgePath | None) -> list[LoadedClaimFile]:
    """Load all claim YAML files from a claims subtree."""
    return load_document_dir(
        claims_dir,
        ClaimsFileDocument,
        wrapper=LoadedClaimFile.from_loaded_document,
    )
