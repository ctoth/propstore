"""The scalar value domain shared by authored claims and direct runtime views."""

from __future__ import annotations

import math
from typing import TypeAlias


ScalarValue: TypeAlias = str | bool | int | float

_MIN_SIGNED_INT64 = -(2**63)
_MAX_SIGNED_INT64 = 2**63 - 1


def validate_scalar_value(value: ScalarValue | None) -> None:
    """Reject values outside the canonical scalar storage contract."""

    if value is None or isinstance(value, str | bool):
        return
    if isinstance(value, int):
        if not _MIN_SIGNED_INT64 <= value <= _MAX_SIGNED_INT64:
            raise ValueError("scalar integer must fit signed 64-bit storage")
        return
    if not math.isfinite(value):
        raise ValueError("scalar float must be finite")


__all__ = ["ScalarValue", "validate_scalar_value"]
