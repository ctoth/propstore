"""Typed claim-side value objects for nested row payloads."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from propstore.opinion import Opinion
from propstore.core.source_types import (
    SourceKind,
    SourceOriginType,
    coerce_source_kind,
    coerce_source_origin_type,
)


def _maybe_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _parse_mapping_json(raw: object) -> Mapping[str, Any] | None:
    if isinstance(raw, Mapping):
        return dict(raw)
    if not isinstance(raw, str) or not raw:
        return None
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return dict(loaded) if isinstance(loaded, Mapping) else None


def _parse_provenance_payload(raw: object) -> Mapping[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, Mapping):
        return dict(raw)
    if not isinstance(raw, str):
        raise ValueError("claim provenance must be a mapping or JSON object")
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("claim provenance must be valid JSON") from exc
    if not isinstance(loaded, Mapping):
        raise ValueError("claim provenance JSON must decode to a mapping")
    return dict(loaded)


def _parse_list_json(raw: object) -> tuple[str, ...]:
    if isinstance(raw, Sequence) and not isinstance(raw, str):
        return tuple(str(item) for item in raw)
    if not isinstance(raw, str) or not raw:
        return ()
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(loaded, Sequence) or isinstance(loaded, str):
        return ()
    return tuple(str(item) for item in loaded)


def _opinion_from_mapping(raw: object) -> Opinion | None:
    payload = _parse_mapping_json(raw)
    if payload is None:
        return None
    required = {"b", "d", "u", "a"}
    if not required.issubset(payload):
        return None
    return Opinion(
        float(payload["b"]),
        float(payload["d"]),
        float(payload["u"]),
        float(payload["a"]),
    )


def _opinion_to_mapping(opinion: Opinion) -> dict[str, float]:
    return {
        "b": opinion.b,
        "d": opinion.d,
        "u": opinion.u,
        "a": opinion.a,
    }


@dataclass(frozen=True)
class SourceOrigin:
    origin_type: SourceOriginType | None = None
    value: str | None = None
    retrieved: str | None = None
    content_ref: str | None = None

    def __post_init__(self) -> None:
        if self.origin_type is not None:
            object.__setattr__(
                self,
                "origin_type",
                coerce_source_origin_type(self.origin_type),
            )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> SourceOrigin | None:
        if data is None:
            return None
        origin_type = data.get("type")
        origin = cls(
            origin_type=(
                None
                if origin_type is None
                else coerce_source_origin_type(origin_type)
            ),
            value=_maybe_str(data.get("value")),
            retrieved=_maybe_str(data.get("retrieved")),
            content_ref=_maybe_str(data.get("content_ref")),
        )
        return None if origin.is_empty else origin

    @property
    def is_empty(self) -> bool:
        return all(
            value is None
            for value in (
                self.origin_type,
                self.value,
                self.retrieved,
                self.content_ref,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.origin_type is not None:
            data["type"] = self.origin_type.value
        if self.value is not None:
            data["value"] = self.value
        if self.retrieved is not None:
            data["retrieved"] = self.retrieved
        if self.content_ref is not None:
            data["content_ref"] = self.content_ref
        return data


@dataclass(frozen=True)
class SourceTrust:
    prior_base_rate: Opinion | None = None
    quality: Opinion | None = None
    derived_from: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> SourceTrust | None:
        if data is None:
            return None
        trust = cls(
            prior_base_rate=_opinion_from_mapping(data.get("prior_base_rate")),
            quality=_opinion_from_mapping(data.get("quality")),
            derived_from=_parse_list_json(data.get("derived_from")),
        )
        return None if trust.is_empty else trust

    @property
    def is_empty(self) -> bool:
        return (
            self.prior_base_rate is None
            and self.quality is None
            and not self.derived_from
        )

    def quality_dict(self) -> dict[str, float] | None:
        if self.quality is None:
            return None
        return _opinion_to_mapping(self.quality)

    def prior_base_rate_dict(self) -> dict[str, float] | None:
        if self.prior_base_rate is None:
            return None
        return _opinion_to_mapping(self.prior_base_rate)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.prior_base_rate is not None:
            data["prior_base_rate"] = self.prior_base_rate_dict()
        if self.quality is not None:
            data["quality"] = self.quality_dict()
        if self.derived_from:
            data["derived_from"] = list(self.derived_from)
        return data


@dataclass(frozen=True)
class ClaimSource:
    source_id: str | None = None
    kind: SourceKind | None = None
    slug: str | None = None
    origin: SourceOrigin | None = None
    trust: SourceTrust | None = None

    def __post_init__(self) -> None:
        if self.kind is not None:
            object.__setattr__(self, "kind", coerce_source_kind(self.kind))

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any] | None,
        *,
        slug: str | None = None,
    ) -> ClaimSource | None:
        if data is None and slug is None:
            return None
        origin = SourceOrigin.from_mapping(
            data.get("origin") if isinstance(data, Mapping) and isinstance(data.get("origin"), Mapping) else None
        )
        trust = SourceTrust.from_mapping(
            data.get("trust") if isinstance(data, Mapping) and isinstance(data.get("trust"), Mapping) else None
        )
        kind = (
            None
            if not isinstance(data, Mapping) or data.get("kind") is None
            else coerce_source_kind(data.get("kind"))
        )
        source = cls(
            source_id=(
                None if not isinstance(data, Mapping) else _maybe_str(data.get("id"))
            ),
            kind=kind,
            slug=slug,
            origin=origin,
            trust=trust,
        )
        return None if source.is_empty else source

    @property
    def is_empty(self) -> bool:
        return (
            self.source_id is None
            and self.kind is None
            and self.slug is None
            and self.origin is None
            and self.trust is None
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.source_id is not None:
            data["id"] = self.source_id
        if self.kind is not None:
            data["kind"] = self.kind.value
        if self.origin is not None and not self.origin.is_empty:
            data["origin"] = self.origin.to_dict()
        if self.trust is not None and not self.trust.is_empty:
            data["trust"] = self.trust.to_dict()
        return data


@dataclass(frozen=True)
class ClaimProvenance:
    paper: str | None = None
    page: int | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))

    @classmethod
    def from_components(
        cls,
        *,
        paper: str | None = None,
        page: int | None = None,
        provenance_json: object = None,
    ) -> ClaimProvenance | None:
        payload = _parse_provenance_payload(provenance_json)
        resolved_paper = paper
        if resolved_paper is None and isinstance(payload.get("paper"), str):
            resolved_paper = str(payload["paper"])
        resolved_page = page
        if resolved_page is None and payload.get("page") is not None:
            resolved_page = int(payload["page"])
        provenance = cls(
            paper=resolved_paper,
            page=resolved_page,
            payload=payload,
        )
        return None if provenance.is_empty else provenance

    @property
    def is_empty(self) -> bool:
        return self.paper is None and self.page is None and not self.payload

    def to_dict(self) -> dict[str, Any]:
        data = dict(self.payload)
        if self.paper is not None:
            data["paper"] = self.paper
        if self.page is not None:
            data["page"] = self.page
        return data

    def to_json(self) -> str | None:
        data = self.to_dict()
        if not data:
            return None
        return json.dumps(data, sort_keys=True)
