"""Top-level conflict detection orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from propstore.cel_checker import (
    ConceptInfo,
    synthetic_category_concept,
    with_synthetic_concepts,
)

from .algorithms import detect_algorithm_conflicts
from .equations import detect_equation_conflicts
from .measurements import detect_measurement_conflicts
from .models import ConflictClaim, ConflictRecord
from .parameter_claims import detect_parameter_conflicts
from .parameterization_conflicts import _detect_parameterization_conflicts

if TYPE_CHECKING:
    from propstore.context_hierarchy import ContextHierarchy


def detect_conflicts(
    claims: Sequence[ConflictClaim],
    concept_registry: dict[str, dict],
    cel_registry: Mapping[str, ConceptInfo],
    context_hierarchy: ContextHierarchy | None = None,
) -> list[ConflictRecord]:
    """Detect conflicts between claims binding to the same concept."""
    records: list[ConflictRecord] = []
    _validate_conflict_concept_registry(concept_registry)
    # Inject a synthetic 'source' category so Z3 treats source conditions
    # as enum comparisons and recognizes different papers as disjoint.
    source_name_set: set[str] = set()
    for claim in claims:
        if claim.source_paper:
            source_name_set.add(claim.source_paper)
    source_names = sorted(source_name_set)
    synthetic_concepts = [
        synthetic_category_concept(
            concept_id="ps:concept:__source__",
            canonical_name="source",
            values=source_names,
            extensible=False,
        ),
    ]
    for synthetic_name in ("domain", "source_kind", "origin_type", "name"):
        if synthetic_name in cel_registry:
            continue
        synthetic_concepts.append(
            synthetic_category_concept(
                concept_id=f"ps:concept:__{synthetic_name}__",
                canonical_name=synthetic_name,
                values=(),
                extensible=True,
            )
        )
    cel_registry = with_synthetic_concepts(
        cel_registry,
        synthetic_concepts,
    )
    condition_solver = _build_condition_solver(cel_registry)

    parameter_records, by_concept = detect_parameter_conflicts(
        claims,
        cel_registry,
        context_hierarchy=context_hierarchy,
        solver=condition_solver,
    )
    records.extend(parameter_records)
    records.extend(
        detect_measurement_conflicts(
            claims,
            cel_registry,
            context_hierarchy=context_hierarchy,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_equation_conflicts(
            claims,
            cel_registry,
            context_hierarchy=context_hierarchy,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_algorithm_conflicts(
            claims,
            cel_registry,
            context_hierarchy=context_hierarchy,
            solver=condition_solver,
        )
    )

    _detect_parameterization_conflicts(
        records,
        by_concept,
        concept_registry,
        claims,
        context_hierarchy=context_hierarchy,
    )
    return records


def _build_condition_solver(cel_registry):
    try:
        from propstore.z3_conditions import Z3ConditionSolver
    except ImportError:
        return None
    return Z3ConditionSolver(cel_registry)


def _validate_conflict_concept_registry(concept_registry: dict[str, dict]) -> None:
    entries_by_id: dict[str, dict[str, object]] = {}
    for key, value in concept_registry.items():
        if not isinstance(value, dict):
            raise TypeError(
                "conflict detector CEL projection expects concept_registry values to be mappings"
            )
        concept_id = value.get("artifact_id", value.get("id"))
        if not isinstance(concept_id, str) or not concept_id:
            raise ValueError(
                f"invalid concept registry entry for key '{key}': missing artifact_id/id"
            )
        normalized = {
            str(field): field_value
            for field, field_value in value.items()
            if not str(field).startswith("_")
        }
        normalized.setdefault("artifact_id", concept_id)
        existing = entries_by_id.get(concept_id)
        if existing is not None:
            if existing != normalized:
                raise ValueError(
                    f"conflicting concept registry entries for concept id '{concept_id}'"
                )
            continue
        entries_by_id[concept_id] = normalized
