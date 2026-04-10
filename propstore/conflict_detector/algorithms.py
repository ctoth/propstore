"""Algorithm-claim conflict detection."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ast_equiv import compare as ast_compare
from propstore.claim_documents import LoadedClaimFile
from propstore.condition_classifier import classify_conditions as _classify_conditions

from .collectors import _collect_algorithm_claims
from .context import _append_context_classified_record, _claim_context
from .models import ConflictRecord

if TYPE_CHECKING:
    from propstore.cel_checker import ConceptInfo
    from propstore.validate_contexts import ContextHierarchy


def detect_algorithm_conflicts(
    claim_files: Sequence[LoadedClaimFile],
    cel_registry: dict[str, ConceptInfo],
    *,
    context_hierarchy: ContextHierarchy | None = None,
    solver=None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    by_concept = _collect_algorithm_claims(claim_files)

    for concept_id, claims in by_concept.items():
        if len(claims) < 2:
            continue
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim_a = claims[i]
                claim_b = claims[j]
                body_a = claim_a.get("body", "")
                body_b = claim_b.get("body", "")
                if not body_a or not body_b:
                    continue

                bindings_a = _bindings_for_algorithm_claim(claim_a)
                bindings_b = _bindings_for_algorithm_claim(claim_b)
                try:
                    result = ast_compare(body_a, bindings_a, body_b, bindings_b)
                except (ValueError, SyntaxError) as exc:
                    logging.warning("ast_compare failed for %s vs %s: %s", claim_a.get("id"), claim_b.get("id"), exc)
                    continue
                if result.equivalent and result.tier <= 2:
                    continue

                conditions_a = sorted(claim_a.get("conditions") or [])
                conditions_b = sorted(claim_b.get("conditions") or [])
                derivation_chain = f"similarity:{result.similarity:.3f} tier:{result.tier}"
                if _append_context_classified_record(
                    records,
                    concept_id=concept_id,
                    claim_a_id=claim_a["id"],
                    claim_b_id=claim_b["id"],
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=f"algorithm:{claim_a['id']}",
                    value_b=f"algorithm:{claim_b['id']}",
                    context_a=_claim_context(claim_a),
                    context_b=_claim_context(claim_b),
                    context_hierarchy=context_hierarchy,
                    derivation_chain=derivation_chain,
                ):
                    continue
                records.append(ConflictRecord(
                    concept_id=concept_id,
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
                    value_a=f"algorithm:{claim_a['id']}",
                    value_b=f"algorithm:{claim_b['id']}",
                    derivation_chain=derivation_chain,
                ))

    return records


def _bindings_for_algorithm_claim(claim: dict) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for var in claim.get("variables", []):
        if not isinstance(var, dict):
            continue
        name = var.get("name") or var.get("symbol")
        concept = var.get("concept")
        if name and concept:
            bindings[name] = concept
    return bindings
