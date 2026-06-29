"""Equation-claim conflict detection.

Whether two EQUATION claims agree is equation equivalence — owned by ``eq-equiv``
and reached here through :func:`propstore.conflict_detector.collectors`. A proven
difference becomes a condition-classified conflict; an undecidable pair stays
:attr:`ConflictClass.UNKNOWN` (honest ignorance), never forced to a verdict.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from condition_ir import ConceptInfo, ConditionSolver
from eq_equiv import (
    EquationComparisonStatus,
    EquationFailure,
    compare_equations,
)

from .collectors import collect_equation_claims, equation_bound_for_claim
from .condition_classifier import classify_conditions
from .context import append_context_classified_record, claim_context
from .models import ConflictClaim, ConflictClass, ConflictRecord

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem

_LOGGER = logging.getLogger(__name__)


def detect_equation_conflicts(
    claims: Sequence[ConflictClaim],
    cel_registry: Mapping[str, ConceptInfo],
    *,
    lifting_system: LiftingSystem | None = None,
    solver: ConditionSolver | None = None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    by_signature = collect_equation_claims(claims)

    for (signature_concept, _other_concepts), group in by_signature.items():
        if len(group) < 2:
            continue

        dependent_concept = _reported_equation_concept(group) or signature_concept
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                claim_a = group[i]
                claim_b = group[j]
                comparison = compare_equations(
                    equation_bound_for_claim(claim_a),
                    equation_bound_for_claim(claim_b),
                )
                left = comparison.left
                right = comparison.right
                if isinstance(left, EquationFailure):
                    _log_equation_failure(claim_a, left)
                    continue
                if isinstance(right, EquationFailure):
                    _log_equation_failure(claim_b, right)
                    continue
                if comparison.status == EquationComparisonStatus.EQUIVALENT:
                    continue
                if comparison.status == EquationComparisonStatus.INCOMPARABLE:
                    continue

                conditions_a = sorted(claim_a.conditions)
                conditions_b = sorted(claim_b.conditions)
                value_a = claim_a.expression or claim_a.sympy or left.canonical
                value_b = claim_b.expression or claim_b.sympy or right.canonical
                if comparison.status == EquationComparisonStatus.UNKNOWN:
                    records.append(
                        ConflictRecord(
                            concept_id=dependent_concept,
                            claim_a_id=claim_a.claim_id,
                            claim_b_id=claim_b.claim_id,
                            warning_class=ConflictClass.UNKNOWN,
                            conditions_a=conditions_a,
                            conditions_b=conditions_b,
                            value_a=value_a,
                            value_b=value_b,
                        )
                    )
                    continue

                if append_context_classified_record(
                    records,
                    concept_id=dependent_concept,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=value_a,
                    value_b=value_b,
                    context_a=claim_context(claim_a),
                    context_b=claim_context(claim_b),
                    lifting_system=lifting_system,
                ):
                    continue
                records.append(
                    ConflictRecord(
                        concept_id=dependent_concept,
                        claim_a_id=claim_a.claim_id,
                        claim_b_id=claim_b.claim_id,
                        warning_class=classify_conditions(
                            conditions_a,
                            conditions_b,
                            cel_registry,
                            solver=solver,
                        ),
                        conditions_a=conditions_a,
                        conditions_b=conditions_b,
                        value_a=value_a,
                        value_b=value_b,
                    )
                )

    return records


def _reported_equation_concept(claims: Sequence[ConflictClaim]) -> str | None:
    dependent_ids = {
        variable.concept_id
        for claim in claims
        for variable in claim.variables
        if variable.role == "dependent" and variable.concept_id
    }
    if len(dependent_ids) == 1:
        return next(iter(dependent_ids))
    return None


def _log_equation_failure(claim: ConflictClaim, failure: EquationFailure) -> None:
    _LOGGER.warning(
        "Skipping equation comparison for claim %s: %s (%s)",
        claim.claim_id,
        failure.code,
        failure.detail,
    )
