"""Conflict detector package."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .collectors import (
    _collect_algorithm_claims,
    _collect_equation_claims,
    _collect_measurement_claims,
    _collect_parameter_claims,
)
from .context import (
    _append_context_classified_record,
    _claim_context,
    _classify_pair_context,
)
from .models import ConflictClass, ConflictRecord

if TYPE_CHECKING:
    from propstore.claim_documents import ClaimFileInput
    from propstore.validate_contexts import ContextHierarchy


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
) -> list[ConflictRecord]:
    from propstore.param_conflicts import (
        detect_transitive_conflicts as _detect_transitive_conflicts,
    )

    return _detect_transitive_conflicts(
        claim_files,
        concept_registry,
        context_hierarchy=context_hierarchy,
    )

__all__ = [
    "ConflictClass",
    "ConflictRecord",
    "detect_conflicts",
    "detect_transitive_conflicts",
    "_append_context_classified_record",
    "_claim_context",
    "_classify_pair_context",
    "_collect_algorithm_claims",
    "_collect_equation_claims",
    "_collect_measurement_claims",
    "_collect_parameter_claims",
]
