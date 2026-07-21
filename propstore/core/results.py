"""Canonical analyzer result dataclasses for the semantic core."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from propstore.core.labels import Label


def _pairs_from_mapping(metadata: Mapping[str, object]) -> list[tuple[str, object]]:
    return [(str(key), value) for key, value in metadata.items()]


def _pairs_from_iterable(
    metadata: tuple[tuple[str, object], ...],
) -> list[tuple[str, object]]:
    return [(str(key), value) for key, value in metadata]


def _normalize_strings(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(str(value) for value in values)))


def _normalize_metadata(
    metadata: Mapping[str, object] | tuple[tuple[str, object], ...] | None,
) -> tuple[tuple[str, object], ...]:
    if metadata is None:
        return ()
    pairs = (
        _pairs_from_mapping(metadata)
        if isinstance(metadata, Mapping)
        else _pairs_from_iterable(metadata)
    )
    return tuple(sorted(pairs, key=lambda pair: pair[0]))


@dataclass(frozen=True, order=True)
class ExtensionResult:
    name: str
    accepted_claim_ids: tuple[str, ...] = ()
    rejected_claim_ids: tuple[str, ...] = ()
    undecided_claim_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "accepted_claim_ids", _normalize_strings(self.accepted_claim_ids)
        )
        object.__setattr__(
            self, "rejected_claim_ids", _normalize_strings(self.rejected_claim_ids)
        )
        object.__setattr__(
            self, "undecided_claim_ids", _normalize_strings(self.undecided_claim_ids)
        )


@dataclass(frozen=True, order=True)
class ClaimProjection:
    target_claim_ids: tuple[str, ...] = ()
    survivor_claim_ids: tuple[str, ...] = ()
    witness_claim_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "target_claim_ids", _normalize_strings(self.target_claim_ids)
        )
        object.__setattr__(
            self, "survivor_claim_ids", _normalize_strings(self.survivor_claim_ids)
        )
        object.__setattr__(
            self, "witness_claim_ids", _normalize_strings(self.witness_claim_ids)
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
