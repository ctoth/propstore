from __future__ import annotations

from dataclasses import dataclass

from argumentation.af_revision import (
    ExtensionRevisionResult,
    ExtensionRevisionState,
    diller_2015_revise_by_framework,
)
from argumentation.dung import ArgumentationFramework, stable_extensions


@dataclass(frozen=True, slots=True)
class NoStableExtensionRevisionTarget(ValueError):
    """Raised when an AF revision target has no stable extensions."""

    framework: ArgumentationFramework

    def __str__(self) -> str:
        return "AF revision target has no stable extensions"


def revise_by_stable_framework(
    state: ExtensionRevisionState,
    framework: ArgumentationFramework,
) -> ExtensionRevisionResult:
    """Revise by an AF while preserving no-stable vs empty-stable distinction."""

    if not tuple(stable_extensions(framework)):
        raise NoStableExtensionRevisionTarget(framework)
    return diller_2015_revise_by_framework(state, framework, semantics="stable")
