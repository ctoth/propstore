"""Shared stance-type vocabulary and helpers."""

from __future__ import annotations

VALID_STANCE_TYPES = frozenset(
    {"rebuts", "undercuts", "undermines", "supports", "explains", "supersedes", "none"}
)
