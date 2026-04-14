"""Equation-claim conflict detection."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.claim_files import ClaimFileInput
from propstore.condition_classifier import classify_conditions as _classify_conditions
from propstore.equation_comparison import EquationFailure, canonicalize_equation

from .collectors import _collect_equation_claims
from .context import _append_context_classified_record, _claim_context
from .models import ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.cel_checker import ConceptInfo
    from propstore.context_hierarchy import ContextHierarchy


_LOGGER = logging.getLogger(__name__)


def detect_equation_conflicts(
    claim_files: Sequence[ClaimFileInput],
    cel_registry: dict[str, ConceptInfo],
    *,
    context_hierarchy: ContextHierarchy | None = None,
    solver=None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    by_signature = _collect_equation_claims(claim_files)

    for (dependent_concept, _independent_concepts), claims in by_signature.items():
        if len(claims) < 2:
            continue

        canonicals = [canonicalize_equation(claim) for claim in claims]
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim_a = claims[i]
                claim_b = claims[j]
                canonical_a = canonicals[i]
                canonical_b = canonicals[j]
                if isinstance(canonical_a, EquationFailure):
                    _log_equation_failure(claim_a, canonical_a)
                    continue
                if isinstance(canonical_b, EquationFailure):
                    _log_equation_failure(claim_b, canonical_b)
                    continue
                if canonical_a.canonical == canonical_b.canonical:
                    continue

                conditions_a = sorted(claim_a.conditions)
                conditions_b = sorted(claim_b.conditions)
                value_a = claim_a.expression or claim_a.sympy or canonical_a.canonical
                value_b = claim_b.expression or claim_b.sympy or canonical_b.canonical
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
                    context_hierarchy=context_hierarchy,
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


def _log_equation_failure(claim: ConflictClaim, failure: EquationFailure) -> None:
    _LOGGER.warning(
        "Skipping equation comparison for claim %s: %s (%s)",
        claim.claim_id,
        failure.code,
        failure.detail,
    )
