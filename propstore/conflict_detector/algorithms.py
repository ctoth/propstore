"""Algorithm-claim conflict detection."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ast_equiv import compare as ast_compare
from propstore.condition_classifier import classify_conditions as _classify_conditions

from .collectors import _collect_algorithm_claims
from .context import _append_context_classified_record, _claim_context
from .models import ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.cel_checker import ConceptInfo
    from propstore.context_lifting import LiftingSystem


def detect_algorithm_conflicts(
    claims: Sequence[ConflictClaim],
    cel_registry: dict[str, ConceptInfo],
    *,
    lifting_system: LiftingSystem | None = None,
    solver=None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    by_concept = _collect_algorithm_claims(claims)

    for concept_id, claims in by_concept.items():
        if len(claims) < 2:
            continue
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim_a = claims[i]
                claim_b = claims[j]
                body_a = claim_a.body or ""
                body_b = claim_b.body or ""
                if not body_a or not body_b:
                    continue

                bindings_a = _bindings_for_algorithm_claim(claim_a)
                bindings_b = _bindings_for_algorithm_claim(claim_b)
                try:
                    result = ast_compare(body_a, bindings_a, body_b, bindings_b)
                except (ValueError, SyntaxError) as exc:
                    logging.warning(
                        "ast_compare failed for %s vs %s: %s",
                        claim_a.claim_id,
                        claim_b.claim_id,
                        exc,
                    )
                    continue
                if result.equivalent and result.tier <= 2:
                    continue

                conditions_a = sorted(claim_a.conditions)
                conditions_b = sorted(claim_b.conditions)
                derivation_chain = f"similarity:{result.similarity:.3f} tier:{result.tier}"
                if _append_context_classified_record(
                    records,
                    concept_id=concept_id,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=f"algorithm:{claim_a.claim_id}",
                    value_b=f"algorithm:{claim_b.claim_id}",
                    context_a=_claim_context(claim_a),
                    context_b=_claim_context(claim_b),
                    lifting_system=lifting_system,
                    derivation_chain=derivation_chain,
                ):
                    continue
                records.append(ConflictRecord(
                    concept_id=concept_id,
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
                    value_a=f"algorithm:{claim_a.claim_id}",
                    value_b=f"algorithm:{claim_b.claim_id}",
                    derivation_chain=derivation_chain,
                ))

    return records


def _bindings_for_algorithm_claim(claim: ConflictClaim) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for variable in claim.variables:
        name = variable.name or variable.symbol
        if name and variable.concept_id:
            bindings[name] = variable.concept_id
    return bindings
