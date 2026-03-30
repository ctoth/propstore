"""Top-level conflict detection orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.cel_checker import build_cel_registry
from propstore.loaded import LoadedEntry

from .algorithms import detect_algorithm_conflicts
from .equations import detect_equation_conflicts
from .measurements import detect_measurement_conflicts
from .models import ConflictRecord
from .parameters import detect_parameter_conflicts

if TYPE_CHECKING:
    from propstore.validate_contexts import ContextHierarchy


def detect_conflicts(
    claim_files: Sequence[LoadedEntry],
    concept_registry: dict[str, dict],
    context_hierarchy: ContextHierarchy | None = None,
) -> list[ConflictRecord]:
    """Detect conflicts between claims binding to the same concept."""
    records: list[ConflictRecord] = []
    cel_registry = build_cel_registry(concept_registry)
    condition_solver = _build_condition_solver(cel_registry)

    parameter_records, by_concept = detect_parameter_conflicts(
        claim_files,
        cel_registry,
        context_hierarchy=context_hierarchy,
        solver=condition_solver,
    )
    records.extend(parameter_records)
    records.extend(
        detect_measurement_conflicts(
            claim_files,
            cel_registry,
            context_hierarchy=context_hierarchy,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_equation_conflicts(
            claim_files,
            cel_registry,
            context_hierarchy=context_hierarchy,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_algorithm_conflicts(
            claim_files,
            cel_registry,
            context_hierarchy=context_hierarchy,
            solver=condition_solver,
        )
    )

    from propstore.param_conflicts import _detect_param_conflicts

    _detect_param_conflicts(records, by_concept, concept_registry, claim_files)
    return records


def _build_condition_solver(cel_registry):
    try:
        from propstore.z3_conditions import Z3ConditionSolver
    except ImportError:
        return None
    return Z3ConditionSolver(cel_registry)
