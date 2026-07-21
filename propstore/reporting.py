"""Shared JSON serialization for typed reports.

The fragility, revision, and observatory report types (later phases) mix in
:class:`JsonReportMixin` so a deterministic, JSON-ready view falls out of their
dataclass fields without a hand-written ``to_dict`` per type. :func:`json_ready`
is the recursive lowering: enums become their value, paths become strings,
dataclasses/msgspec structs/mappings/sequences recurse, and anything else is
stringified.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, TypeAlias, TypeGuard

import msgspec

JsonValue: TypeAlias = (
    "None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]"
)


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _is_sequence(value: object) -> TypeGuard[Sequence[Any]]:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


class JsonReportMixin:
    """Mixin giving a dataclass a deterministic JSON-ready ``to_json`` view."""

    def to_json(self) -> dict[str, JsonValue]:
        value = json_ready(self)
        if isinstance(value, dict):
            return value
        return {"value": value}


def json_ready(value: object) -> JsonValue:
    """Lower an arbitrary value into a JSON-ready :data:`JsonValue`."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, msgspec.Struct):
        return json_ready(msgspec.to_builtins(value))
    if is_dataclass(value) and not isinstance(value, type):
        return json_ready(asdict(value))
    if _is_mapping(value):
        return {str(key): json_ready(item) for key, item in value.items()}
    if _is_sequence(value):
        return [json_ready(item) for item in value]
    return str(value)
