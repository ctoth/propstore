"""Diagnostic helpers for semantic pass results."""

from __future__ import annotations

from propstore.semantic_passes.types import PassDiagnostic


def render_diagnostics(
    diagnostics: tuple[PassDiagnostic, ...],
) -> tuple[str, ...]:
    return tuple(diagnostic.render() for diagnostic in diagnostics)
