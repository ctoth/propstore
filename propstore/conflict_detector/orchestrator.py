"""Top-level conflict detection orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.claim_documents import (
    ClaimFileInput,
    LoadedClaimFile,
    claim_file_claim_payloads,
    claim_file_default_source_paper,
)
from propstore.cel_checker import (
    build_cel_registry,
    synthetic_category_concept,
    with_synthetic_concepts,
)

from .algorithms import detect_algorithm_conflicts
from .collectors import _iter_conflict_claims
from .equations import detect_equation_conflicts
from .measurements import detect_measurement_conflicts
from .models import ConflictRecord
from .parameters import detect_parameter_conflicts

if TYPE_CHECKING:
    from propstore.context_hierarchy import ContextHierarchy


def detect_conflicts(
    claim_files: Sequence[ClaimFileInput],
    concept_registry: dict[str, dict],
    context_hierarchy: ContextHierarchy | None = None,
) -> list[ConflictRecord]:
    """Detect conflicts between claims binding to the same concept."""
    records: list[ConflictRecord] = []
    cel_registry = build_cel_registry(concept_registry)
    # Inject a synthetic 'source' category so Z3 treats source conditions
    # as enum comparisons and recognizes different papers as disjoint.
    source_name_set: set[str] = set()
    for claim_file in claim_files:
        default_source = claim_file_default_source_paper(claim_file)
        if isinstance(default_source, str) and default_source:
            source_name_set.add(default_source)
    for claim in _iter_conflict_claims(claim_files):
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
