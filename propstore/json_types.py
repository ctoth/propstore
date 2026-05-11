"""Shared JSON-native type aliases."""

from __future__ import annotations

from typing import TypeAlias, TypeVar

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
JsonValueT = TypeVar("JsonValueT", bound=JsonValue)
