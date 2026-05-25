"""Core diagnostic data shapes shared by family compilers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuarantineDiagnostic:
    artifact_id: str
    kind: str
    diagnostic_kind: str
    message: str
    file: str | None = None
