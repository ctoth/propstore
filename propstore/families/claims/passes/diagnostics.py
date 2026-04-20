"""Claim-family diagnostic construction helpers."""

from __future__ import annotations

from typing import Literal

from propstore.families.claims.stages import ClaimStage
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.types import PassDiagnostic


def claim_diagnostic(
    *,
    level: Literal["info", "warning", "error"],
    message: str,
    filename: str | None = None,
    artifact_id: str | None = None,
    code: str | None = None,
    pass_name: str = "claim.compile",
) -> PassDiagnostic:
    diagnostic_level: Literal["warning", "error"] = (
        "warning" if level == "info" else level
    )
    return PassDiagnostic(
        level=diagnostic_level,
        code=code or f"claim.{level}",
        message=message,
        family=PropstoreFamily.CLAIMS,
        stage=ClaimStage.CHECKED,
        filename=filename,
        artifact_id=artifact_id,
        pass_name=pass_name,
    )
