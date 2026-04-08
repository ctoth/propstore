"""Structured diagnostics for claim compilation."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.validate import ValidationResult


@dataclass(frozen=True)
class SemanticDiagnostic:
    """Structured diagnostic emitted by the claim compiler."""

    level: str
    message: str
    filename: str | None = None
    artifact_id: str | None = None

    @property
    def is_error(self) -> bool:
        return self.level == "error"

    @property
    def is_warning(self) -> bool:
        return self.level == "warning"

    def render(self) -> str:
        prefix: list[str] = []
        if self.filename:
            prefix.append(self.filename)
        if self.artifact_id:
            prefix.append(f"claim '{self.artifact_id}'")
        if prefix:
            return f"{': '.join(prefix)}: {self.message}"
        return self.message


def diagnostics_to_validation_result(
    diagnostics: list[SemanticDiagnostic],
) -> ValidationResult:
    """Convert structured diagnostics to the legacy ValidationResult shape."""
    result = ValidationResult()
    for diagnostic in diagnostics:
        rendered = diagnostic.render()
        if diagnostic.is_warning:
            result.warnings.append(rendered)
        else:
            result.errors.append(rendered)
    return result
