"""Branded algorithm-stage strings used on the canonical/runtime path."""

from __future__ import annotations

from typing import NewType

AlgorithmStage = NewType("AlgorithmStage", str)


def to_algorithm_stage(value: str) -> AlgorithmStage:
    return AlgorithmStage(value)


def coerce_algorithm_stage(value: object | None) -> AlgorithmStage | None:
    if value is None:
        return None
    if isinstance(value, str):
        return to_algorithm_stage(value)
    raise TypeError(f"Unsupported algorithm stage type: {type(value).__name__}")
