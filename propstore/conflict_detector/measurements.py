"""Measurement-claim conflict detection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.claim_documents import ClaimFileInput
from propstore.condition_classifier import classify_conditions as _classify_conditions
from propstore.value_comparison import (
    value_str as _value_str,
    values_compatible as _values_compatible,
)

from .collectors import _collect_measurement_claims
from .context import _append_context_classified_record, _claim_context
from .models import ConflictClass, ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.cel_checker import ConceptInfo
    from propstore.context_hierarchy import ContextHierarchy


def detect_measurement_conflicts(
    claim_files: Sequence[ClaimFileInput],
    cel_registry: dict[str, ConceptInfo],
    *,
    context_hierarchy: ContextHierarchy | None = None,
    solver=None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    by_measurement = _collect_measurement_claims(claim_files)

    for (target_concept, _measure), claims in by_measurement.items():
        if len(claims) < 2:
            continue
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim_a = claims[i]
                claim_b = claims[j]

                if _values_compatible(None, None, claim_a=claim_a, claim_b=claim_b):
                    continue

                conditions_a = sorted(claim_a.conditions)
                conditions_b = sorted(claim_b.conditions)
                if _append_context_classified_record(
                    records,
                    concept_id=target_concept,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=_value_str(None, claim=claim_a),
                    value_b=_value_str(None, claim=claim_b),
                    context_a=_claim_context(claim_a),
                    context_b=_claim_context(claim_b),
                    context_hierarchy=context_hierarchy,
                ):
                    continue

                pop_a = claim_a.listener_population or ""
                pop_b = claim_b.listener_population or ""
                warning_class = (
                    ConflictClass.PHI_NODE
                    if pop_a and pop_b and pop_a != pop_b
                    else _classify_conditions(
                        conditions_a,
                        conditions_b,
                        cel_registry,
                        solver=solver,
                    )
                )
                records.append(ConflictRecord(
                    concept_id=target_concept,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    warning_class=warning_class,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=_value_str(None, claim=claim_a),
                    value_b=_value_str(None, claim=claim_b),
                ))

    return records
