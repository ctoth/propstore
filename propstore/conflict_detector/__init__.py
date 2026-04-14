"""Conflict detector package."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .models import ConflictClass, ConflictRecord

if TYPE_CHECKING:
    from propstore.claim_files import ClaimFileInput
    from propstore.context_hierarchy import ContextHierarchy
    from propstore.form_utils import FormDefinition


def detect_conflicts(
    claim_files: Sequence[ClaimFileInput],
    concept_registry: dict[str, dict],
    context_hierarchy: ContextHierarchy | None = None,
) -> list[ConflictRecord]:
    from .orchestrator import detect_conflicts as _detect_conflicts

    return _detect_conflicts(
        claim_files,
        concept_registry,
        context_hierarchy=context_hierarchy,
    )


def detect_transitive_conflicts(
    claim_files: Sequence[ClaimFileInput],
    concept_registry: dict[str, dict],
    *,
    context_hierarchy: ContextHierarchy | None = None,
    forms: dict[str, FormDefinition] | None = None,
) -> list[ConflictRecord]:
    from .parameterization_conflicts import (
        detect_transitive_conflicts as _detect_transitive_conflicts,
    )

    return _detect_transitive_conflicts(
        claim_files,
        concept_registry,
        context_hierarchy=context_hierarchy,
        forms=forms,
    )

__all__ = [
    "ConflictClass",
    "ConflictRecord",
    "detect_conflicts",
    "detect_transitive_conflicts",
]
