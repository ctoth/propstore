"""Strict report serialization for web JSON responses."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import TypeAlias

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


class WebSerializationError(TypeError):
    """Raised when a report contains an unsupported JSON value."""


def to_json_compatible(value) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Enum):
        enum_value = value.value
        if isinstance(enum_value, bool | int | float | str):
            return enum_value
        raise WebSerializationError(
            f"enum {type(value).__name__} has non-JSON value {type(enum_value).__name__}"
        )
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple | list):
        return [to_json_compatible(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_json_compatible(getattr(value, field.name))
            for field in fields(value)
        }
    raise WebSerializationError(f"unsupported web JSON value: {type(value).__name__}")
