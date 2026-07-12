"""Algorithm-claim conflict detection.

Whether two ALGORITHM claims implement the same computation is AST/algorithm
equivalence — owned by ``ast-equiv``. Equivalent bodies (canonical, SymPy, or
partial-eval tier) never conflict; a proven non-equivalence is condition-classified.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

import ast_equiv
from ast_equiv import AlgorithmParseError, ComparisonResult
from condition_ir import ConceptInfo, ConditionSolver

from .collectors import collect_algorithm_claims
from .condition_classifier import classify_conditions
from .context import append_context_classified_record, claim_context
from .models import ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem

_LOGGER = logging.getLogger(__name__)

# ast-equiv is pinned at a rev whose ``compare`` types its symbol-binding
# parameters as bare ``dict`` (a loose upstream surface). Narrow it once here
# behind a fully-typed call-through; tests patch ``ast_compare`` on this module.
_ast_equiv_compare: Any = getattr(ast_equiv, "compare")


def ast_compare(
    body_a: str,
    bindings_a: dict[str, str],
    body_b: str,
    bindings_b: dict[str, str],
    known_values: dict[str, float] | None = None,
) -> ComparisonResult:
    result: ComparisonResult = _ast_equiv_compare(
        body_a, bindings_a, body_b, bindings_b, known_values
    )
    return result


def detect_algorithm_conflicts(
    claims: Sequence[ConflictClaim],
    cel_registry: Mapping[str, ConceptInfo],
    *,
    lifting_system: LiftingSystem | None = None,
    solver: ConditionSolver | None = None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    by_concept = collect_algorithm_claims(claims)

    for concept_id, group in by_concept.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                claim_a = group[i]
                claim_b = group[j]
                body_a = claim_a.body or ""
                body_b = claim_b.body or ""
                if not body_a or not body_b:
                    continue

                bindings_a = _bindings_for_algorithm_claim(claim_a)
                bindings_b = _bindings_for_algorithm_claim(claim_b)
                try:
                    result = ast_compare(body_a, bindings_a, body_b, bindings_b)
                except (
                    ValueError,
                    SyntaxError,
                    AlgorithmParseError,
                    RecursionError,
                ) as exc:
                    _LOGGER.warning(
                        "ast_compare failed for %s vs %s: %s",
                        claim_a.claim_id,
                        claim_b.claim_id,
                        exc,
                    )
                    continue
                if result.equivalent:
                    continue

                conditions_a = sorted(claim_a.conditions)
                conditions_b = sorted(claim_b.conditions)
                derivation_chain = (
                    f"similarity:{result.similarity:.3f} tier:{result.tier}"
                )
                value_a = f"algorithm:{claim_a.claim_id}"
                value_b = f"algorithm:{claim_b.claim_id}"
                if append_context_classified_record(
                    records,
                    concept_id=concept_id,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=value_a,
                    value_b=value_b,
                    context_a=claim_context(claim_a),
                    context_b=claim_context(claim_b),
                    lifting_system=lifting_system,
                    derivation_chain=derivation_chain,
                ):
                    continue
                records.append(
                    ConflictRecord(
                        concept_id=concept_id,
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
                        derivation_chain=derivation_chain,
                    )
                )

    return records


def _bindings_for_algorithm_claim(claim: ConflictClaim) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for variable in claim.variables:
        name = variable.name or variable.symbol
        if name and variable.concept:
            bindings[name] = variable.concept
    return bindings
