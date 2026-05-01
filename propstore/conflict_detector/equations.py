"""Equation-claim conflict detection."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.condition_classifier import classify_conditions as _classify_conditions
from propstore.equation_comparison import (
    EquationComparisonStatus,
    EquationFailure,
    compare_equation_claims,
)

from .collectors import _collect_equation_claims
from .context import _append_context_classified_record, _claim_context
from .models import ConflictClaim, ConflictClass, ConflictRecord

if TYPE_CHECKING:
    from propstore.cel_checker import ConceptInfo
    from propstore.context_lifting import LiftingSystem


_LOGGER = logging.getLogger(__name__)


def detect_equation_conflicts(
    claims: Sequence[ConflictClaim],
    cel_registry: dict[str, ConceptInfo],
    *,
    lifting_system: LiftingSystem | None = None,
    solver=None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    by_signature = _collect_equation_claims(claims)

    for (signature_concept, _other_concepts), claims in by_signature.items():
        if len(claims) < 2:
            continue

        dependent_concept = _reported_equation_concept(claims) or signature_concept
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim_a = claims[i]
                claim_b = claims[j]
                comparison = compare_equation_claims(claim_a, claim_b)
                if isinstance(comparison.left, EquationFailure):
                    _log_equation_failure(claim_a, comparison.left)
                    continue
                if isinstance(comparison.right, EquationFailure):
                    _log_equation_failure(claim_b, comparison.right)
                    continue
                if comparison.status == EquationComparisonStatus.EQUIVALENT:
                    continue
                if comparison.status == EquationComparisonStatus.INCOMPARABLE:
                    continue

                conditions_a = sorted(claim_a.conditions)
                conditions_b = sorted(claim_b.conditions)
                value_a = claim_a.expression or claim_a.sympy or comparison.left.canonical
                value_b = claim_b.expression or claim_b.sympy or comparison.right.canonical
                if comparison.status == EquationComparisonStatus.UNKNOWN:
                    records.append(ConflictRecord(
                        concept_id=dependent_concept,
                        claim_a_id=claim_a.claim_id,
                        claim_b_id=claim_b.claim_id,
                        warning_class=ConflictClass.UNKNOWN,
                        conditions_a=conditions_a,
                        conditions_b=conditions_b,
                        value_a=value_a,
                        value_b=value_b,
                    ))
                    continue

                if _append_context_classified_record(
                    records,
                    concept_id=dependent_concept,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=value_a,
                    value_b=value_b,
                    context_a=_claim_context(claim_a),
                    context_b=_claim_context(claim_b),
                    lifting_system=lifting_system,
                ):
                    continue
                records.append(ConflictRecord(
                    concept_id=dependent_concept,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    warning_class=_classify_conditions(
                        conditions_a,
                        conditions_b,
                        cel_registry,
                        solver=solver,
                    ),
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=value_a,
                    value_b=value_b,
                ))

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
