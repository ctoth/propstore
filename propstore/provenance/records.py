"""Typed provenance records for import-ready graph carriers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

_URI_PREFIXES = ("urn:", "ni://", "http://", "https://")


class ExternalStatementAttitude(StrEnum):
    """Carroll SWP-style stance toward an external statement graph."""

    ASSERTED = "asserted"
    QUOTED = "quoted"


def _require_non_empty(value: str, label: str) -> str:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{label} must be non-empty")
    return text


def _require_uri(value: str, label: str) -> str:
    text = _require_non_empty(value, label)
    if not text.startswith(_URI_PREFIXES):
        raise ValueError(f"{label} must be a URI")
    return text


def _require_content_hash(value: str) -> str:
    text = _require_non_empty(value, "content hash")
    if ":" not in text:
        raise ValueError("content hash must name the hash algorithm")
    return text


def _canonical_non_empty_set(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    canonical = tuple(sorted({_require_non_empty(value, label) for value in values}))
    if not canonical:
        raise ValueError(f"{label} set must be non-empty")
    return canonical


def _canonical_uri_set(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    canonical = tuple(sorted({_require_uri(value, label) for value in values}))
    if not canonical:
        raise ValueError(f"{label} set must be non-empty")
    return canonical


@dataclass(frozen=True)
class SourceVersionProvenanceRecord:
    """Source version and content hash used as a where-provenance anchor."""

    source_id: str
    version_id: str
    content_hash: str
    retrieved_at: str | None = None
    retrieval_uri: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _require_uri(self.source_id, "source_id"))
        object.__setattr__(self, "version_id", _require_non_empty(self.version_id, "version_id"))
        object.__setattr__(self, "content_hash", _require_content_hash(self.content_hash))
        if self.retrieved_at is not None:
            object.__setattr__(
                self,
                "retrieved_at",
                _require_non_empty(self.retrieved_at, "retrieved_at"),
            )
        if self.retrieval_uri is not None:
            object.__setattr__(
                self,
                "retrieval_uri",
                _require_uri(self.retrieval_uri, "retrieval_uri"),
            )

    def identity_payload(self) -> tuple[str, str, str, str]:
        return ("source_version", self.source_id, self.version_id, self.content_hash)

    def to_payload(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "kind": "source_version",
            "source_id": self.source_id,
            "version_id": self.version_id,
            "content_hash": self.content_hash,
        }
        if self.retrieved_at is not None:
            result["retrieved_at"] = self.retrieved_at
        if self.retrieval_uri is not None:
            result["retrieval_uri"] = self.retrieval_uri
        return result


@dataclass(frozen=True)
class LicenseProvenanceRecord:
    """License named by a source or import run."""

    license_id: str
    label: str
    uri: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "license_id", _require_uri(self.license_id, "license_id"))
        object.__setattr__(self, "label", _require_non_empty(self.label, "label"))
        if self.uri is not None:
            object.__setattr__(self, "uri", _require_uri(self.uri, "license uri"))

    def identity_payload(self) -> tuple[str, str]:
        return ("license", self.license_id)

    def to_payload(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "kind": "license",
            "license_id": self.license_id,
            "label": self.label,
        }
        if self.uri is not None:
            result["uri"] = self.uri
        return result


@dataclass(frozen=True)
class ImportRunProvenanceRecord:
    """Import activity linking a concrete source version to an importer."""

    run_id: str
    importer_id: str
    imported_at: str
    source: SourceVersionProvenanceRecord
    license: LicenseProvenanceRecord

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _require_uri(self.run_id, "run_id"))
        object.__setattr__(self, "importer_id", _require_uri(self.importer_id, "importer_id"))
        object.__setattr__(self, "imported_at", _require_non_empty(self.imported_at, "imported_at"))
        if not isinstance(self.source, SourceVersionProvenanceRecord):
            raise TypeError("source must be SourceVersionProvenanceRecord")
        if not isinstance(self.license, LicenseProvenanceRecord):
            raise TypeError("license must be LicenseProvenanceRecord")

    def identity_payload(self) -> tuple[str, str, tuple[str, str, str, str]]:
        return ("import_run", self.run_id, self.source.identity_payload())

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": "import_run",
            "run_id": self.run_id,
            "importer_id": self.importer_id,
            "imported_at": self.imported_at,
            "source": self.source.to_payload(),
            "license": self.license.to_payload(),
        }


@dataclass(frozen=True)
class ProjectionFrameProvenanceRecord:
    """Projection activity over one or more situated assertion identities."""

    frame_id: str
    backend: str
    projected_at: str
    source_assertion_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame_id", _require_uri(self.frame_id, "frame_id"))
        object.__setattr__(self, "backend", _require_non_empty(self.backend, "backend"))
        object.__setattr__(self, "projected_at", _require_non_empty(self.projected_at, "projected_at"))
        object.__setattr__(
            self,
            "source_assertion_ids",
            _canonical_non_empty_set(self.source_assertion_ids, "source assertion"),
        )

    def identity_payload(self) -> tuple[str, str, str, tuple[str, ...]]:
        return ("projection_frame", self.frame_id, self.backend, self.source_assertion_ids)

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": "projection_frame",
            "frame_id": self.frame_id,
            "backend": self.backend,
            "projected_at": self.projected_at,
            "source_assertion_ids": list(self.source_assertion_ids),
        }


@dataclass(frozen=True)
class ExternalStatementProvenanceRecord:
    """External statement located in a source version."""

    statement_id: str
    source: SourceVersionProvenanceRecord
    locator: str
    attitude: ExternalStatementAttitude
    authority_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "statement_id", _require_uri(self.statement_id, "statement_id"))
        if not isinstance(self.source, SourceVersionProvenanceRecord):
            raise TypeError("source must be SourceVersionProvenanceRecord")
        object.__setattr__(self, "locator", _require_non_empty(self.locator, "locator"))
        object.__setattr__(self, "attitude", ExternalStatementAttitude(self.attitude))
        if self.authority_id is not None:
            object.__setattr__(
                self,
                "authority_id",
                _require_uri(self.authority_id, "authority_id"),
            )

    def identity_payload(
        self,
    ) -> tuple[str, str, tuple[str, str, str, str], str, str]:
        return (
            "external_statement",
            self.statement_id,
            self.source.identity_payload(),
            self.locator,
            self.attitude.value,
        )

    def to_payload(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "kind": "external_statement",
            "statement_id": self.statement_id,
            "source": self.source.to_payload(),
            "locator": self.locator,
            "attitude": self.attitude.value,
        }
        if self.authority_id is not None:
            result["authority_id"] = self.authority_id
        return result


@dataclass(frozen=True)
class ExternalInferenceProvenanceRecord:
    """External inference over statement ids with explicit premises."""

    inference_id: str
    engine: str
    inferred_at: str
    premise_statement_ids: tuple[str, ...]
    conclusion_statement_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "inference_id", _require_uri(self.inference_id, "inference_id"))
        object.__setattr__(self, "engine", _require_non_empty(self.engine, "engine"))
        object.__setattr__(self, "inferred_at", _require_non_empty(self.inferred_at, "inferred_at"))
        object.__setattr__(
            self,
            "premise_statement_ids",
            _canonical_uri_set(self.premise_statement_ids, "premise statement"),
        )
        object.__setattr__(
            self,
            "conclusion_statement_id",
            _require_uri(self.conclusion_statement_id, "conclusion_statement_id"),
        )

    def identity_payload(self) -> tuple[str, str, tuple[str, ...], str]:
        return (
            "external_inference",
            self.inference_id,
            self.premise_statement_ids,
            self.conclusion_statement_id,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": "external_inference",
            "inference_id": self.inference_id,
            "engine": self.engine,
            "inferred_at": self.inferred_at,
            "premise_statement_ids": list(self.premise_statement_ids),
            "conclusion_statement_id": self.conclusion_statement_id,
        }
