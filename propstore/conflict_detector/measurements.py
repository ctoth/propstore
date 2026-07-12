"""Measurement-claim conflict detection.

Two MEASUREMENT claims on the same concept/measure conflict when their values
are incompatible (interval comparison, owned by ``value_comparison``); the
conditions decide the class. Population/regime splits are authored as CEL
conditions (the condition solver classifies disjoint regimes as PHI), not as a
dedicated claim field.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from condition_ir import ConceptInfo, ConditionSolver

from propstore.value_comparison import value_str, values_compatible

from .collectors import collect_measurement_claims
from .condition_classifier import classify_conditions
from .context import append_context_classified_record, claim_context
from .models import ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem


def detect_measurement_conflicts(
    claims: Sequence[ConflictClaim],
    cel_registry: Mapping[str, ConceptInfo],
    *,
    lifting_system: LiftingSystem | None = None,
    solver: ConditionSolver | None = None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    by_measurement = collect_measurement_claims(claims)

    for (target_concept, _measure), group in by_measurement.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                claim_a = group[i]
                claim_b = group[j]

                if values_compatible(None, None, claim_a=claim_a, claim_b=claim_b):
                    continue

                conditions_a = sorted(claim_a.conditions)
                conditions_b = sorted(claim_b.conditions)
                value_a = value_str(None, claim=claim_a)
                value_b = value_str(None, claim=claim_b)
                if append_context_classified_record(
                    records,
                    concept_id=target_concept,
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

                warning_class = classify_conditions(
                    conditions_a,
                    conditions_b,
                    cel_registry,
                    solver=solver,
                )
                records.append(
                    ConflictRecord(
                        concept_id=target_concept,
                        claim_a_id=claim_a.claim_id,
                        claim_b_id=claim_b.claim_id,
                        warning_class=warning_class,
                        conditions_a=conditions_a,
                        conditions_b=conditions_b,
                        value_a=value_a,
                        value_b=value_b,
                    )
                )

    return records
