"""Typed sidecar build stages and row bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClaimInsertRow:
    values: dict[str, object]


@dataclass(frozen=True)
class ClaimStanceInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ClaimSidecarRows:
    claim_rows: tuple[ClaimInsertRow, ...]
    stance_rows: tuple[ClaimStanceInsertRow, ...]
