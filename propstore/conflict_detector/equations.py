"""Equation-claim conflict detection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.claim_documents import LoadedClaimFile
from propstore.condition_classifier import classify_conditions as _classify_conditions
from propstore.equation_comparison import canonicalize_equation

from .collectors import _collect_equation_claims
from .context import _append_context_classified_record, _claim_context
from .models import ConflictRecord

if TYPE_CHECKING:
    from propstore.cel_checker import ConceptInfo
    from propstore.validate_contexts import ContextHierarchy


def detect_equation_conflicts(
    claim_files: Sequence[LoadedClaimFile],
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
                if canonical_a is None or canonical_b is None or canonical_a == canonical_b:
                    continue

                conditions_a = sorted(claim_a.get("conditions") or [])
                conditions_b = sorted(claim_b.get("conditions") or [])
                value_a = claim_a.get("expression") or claim_a.get("sympy") or canonical_a
                value_b = claim_b.get("expression") or claim_b.get("sympy") or canonical_b
                if _append_context_classified_record(
                    records,
                    concept_id=dependent_concept,
                    claim_a_id=claim_a["id"],
                    claim_b_id=claim_b["id"],
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
                    claim_a_id=claim_a["id"],
                    claim_b_id=claim_b["id"],
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
