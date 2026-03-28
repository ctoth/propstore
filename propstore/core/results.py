"""Canonical analyzer result dataclasses for the semantic core."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from propstore.core.graph_types import label_from_dict, label_to_dict
from propstore.core.labels import Label


def _normalize_strings(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(str(value) for value in values)))


def _normalize_metadata(
    metadata: Mapping[str, Any] | Iterable[tuple[str, Any]] | None,
) -> tuple[tuple[str, Any], ...]:
    if metadata is None:
        return ()
    if isinstance(metadata, Mapping):
        items = metadata.items()
    else:
        items = metadata
    return tuple(sorted((str(key), value) for key, value in items))


@dataclass(frozen=True, order=True)
class ExtensionResult:
    name: str
    accepted_claim_ids: tuple[str, ...] = ()
    rejected_claim_ids: tuple[str, ...] = ()
    undecided_claim_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_claim_ids", _normalize_strings(self.accepted_claim_ids))
        object.__setattr__(self, "rejected_claim_ids", _normalize_strings(self.rejected_claim_ids))
        object.__setattr__(self, "undecided_claim_ids", _normalize_strings(self.undecided_claim_ids))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "accepted_claim_ids": list(self.accepted_claim_ids),
            "rejected_claim_ids": list(self.rejected_claim_ids),
            "undecided_claim_ids": list(self.undecided_claim_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExtensionResult:
        return cls(
            name=str(data["name"]),
            accepted_claim_ids=tuple(data.get("accepted_claim_ids") or ()),
            rejected_claim_ids=tuple(data.get("rejected_claim_ids") or ()),
            undecided_claim_ids=tuple(data.get("undecided_claim_ids") or ()),
        )


@dataclass(frozen=True, order=True)
class ClaimProjection:
    target_claim_ids: tuple[str, ...] = ()
    survivor_claim_ids: tuple[str, ...] = ()
    witness_claim_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_claim_ids", _normalize_strings(self.target_claim_ids))
        object.__setattr__(self, "survivor_claim_ids", _normalize_strings(self.survivor_claim_ids))
        object.__setattr__(self, "witness_claim_ids", _normalize_strings(self.witness_claim_ids))

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_claim_ids": list(self.target_claim_ids),
            "survivor_claim_ids": list(self.survivor_claim_ids),
            "witness_claim_ids": list(self.witness_claim_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> ClaimProjection | None:
        if data is None:
            return None
        return cls(
            target_claim_ids=tuple(data.get("target_claim_ids") or ()),
            survivor_claim_ids=tuple(data.get("survivor_claim_ids") or ()),
            witness_claim_ids=tuple(data.get("witness_claim_ids") or ()),
        )


@dataclass(frozen=True)
class AnalyzerResult:
    backend: str
    semantics: str
    extensions: tuple[ExtensionResult, ...] = ()
    projection: ClaimProjection | None = None
    support_label: Label | None = None
    metadata: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "extensions", tuple(sorted(self.extensions)))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "backend": self.backend,
            "semantics": self.semantics,
            "extensions": [extension.to_dict() for extension in self.extensions],
        }
        if self.projection is not None:
            data["projection"] = self.projection.to_dict()
        if self.support_label is not None:
            data["support_label"] = label_to_dict(self.support_label)
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AnalyzerResult:
        return cls(
            backend=str(data["backend"]),
            semantics=str(data["semantics"]),
            extensions=tuple(
                ExtensionResult.from_dict(extension)
                for extension in data.get("extensions") or ()
            ),
            projection=ClaimProjection.from_dict(data.get("projection")),
            support_label=label_from_dict(data.get("support_label")),
            metadata=data.get("metadata") or (),
        )
