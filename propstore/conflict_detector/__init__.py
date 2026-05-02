"""Conflict detector package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from propstore.core.conditions.registry import ConceptInfo

from .models import ConflictClass, ConflictRecord

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem
    from propstore.families.forms.stages import FormDefinition
    from propstore.conflict_detector.models import ConflictClaim


def detect_conflicts(
    claims: Sequence[ConflictClaim],
    concept_registry: dict[str, dict],
    cel_registry: Mapping[str, ConceptInfo],
    lifting_system: LiftingSystem | None = None,
) -> list[ConflictRecord]:
    from .orchestrator import detect_conflicts as _detect_conflicts

    return _detect_conflicts(
        claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )


def detect_transitive_conflicts(
    claims: Sequence[ConflictClaim],
    concept_registry: dict[str, dict],
    *,
    lifting_system: LiftingSystem | None = None,
    forms: dict[str, FormDefinition] | None = None,
) -> list[ConflictRecord]:
    from .parameterization_conflicts import (
        detect_transitive_conflicts as _detect_transitive_conflicts,
    )

    return _detect_transitive_conflicts(
        claims,
        concept_registry,
        lifting_system=lifting_system,
        forms=forms,
    )

__all__ = [
    "ConflictClass",
    "ConflictRecord",
    "detect_conflicts",
    "detect_transitive_conflicts",
]
