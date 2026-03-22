"""Conflict detector for the propstore propositional knowledge store.

Classifies pairs of claims that bind to the same concept into:
- COMPATIBLE: values consistent (within tolerance or overlapping ranges)
- PHI_NODE: values differ, conditions fully disjoint
- CONFLICT: values differ, conditions identical (or both unconditional)
- OVERLAP: values differ, conditions partially overlapping
- PARAM_CONFLICT: conflict detected via parameterization chain

COMPATIBLE pairs are detected but not returned (they're fine).
All other classifications are returned as ConflictRecord instances.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ast_equiv import compare as ast_compare

from propstore.cel_checker import build_cel_registry
from propstore.equation_comparison import canonicalize_equation, equation_signature
from propstore.validate_claims import LoadedClaimFile


class ConflictClass(Enum):
    COMPATIBLE = "COMPATIBLE"
    PHI_NODE = "PHI_NODE"
    CONFLICT = "CONFLICT"
    OVERLAP = "OVERLAP"
    PARAM_CONFLICT = "PARAM_CONFLICT"
    CONTEXT_PHI_NODE = "CONTEXT_PHI_NODE"


@dataclass
class ConflictRecord:
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    warning_class: ConflictClass
    conditions_a: list[str]  # CEL expressions
    conditions_b: list[str]  # CEL expressions
    value_a: str  # string representation
    value_b: str  # string representation
    derivation_chain: str | None = None  # for PARAM_CONFLICT only


# ── Context-aware classification ─────────────────────────────────────


def _classify_pair_context(
    context_a: str | None,
    context_b: str | None,
    hierarchy: object | None,
) -> ConflictClass | None:
    """Check if two claims' contexts make them non-conflicting.

    Returns CONTEXT_PHI_NODE if the claims are in different, unrelated contexts.
    Returns None if normal classification should proceed (same context,
    ancestor/descendant, one or both universal, or no hierarchy available).
    """
    if hierarchy is None:
        return None
    if context_a is None or context_b is None:
        return None  # universal claims use normal classification
    if context_a == context_b:
        return None  # same context — normal classification

    # Check if one is an ancestor of the other
    if hierarchy.is_visible(context_a, context_b):  # type: ignore[union-attr]
        return None  # ancestor/descendant — both visible, normal classification
    if hierarchy.is_visible(context_b, context_a):  # type: ignore[union-attr]
        return None

    # Different, unrelated contexts — not a real conflict
    return ConflictClass.CONTEXT_PHI_NODE


# ── Value comparison ─────────────────────────────────────────────────

from propstore.value_comparison import (
    value_str as _value_str,
    values_compatible as _values_compatible,
)

from propstore.condition_classifier import classify_conditions as _classify_conditions

# ── Main detector ────────────────────────────────────────────────────


def _collect_measurement_claims(
    claim_files: Sequence[LoadedClaimFile],
) -> dict[tuple[str, str], list[dict]]:
    """Group measurement claims by (target_concept, measure) across all claim files."""
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if (claim.get("type") == "measurement"
                    and claim.get("target_concept")
                    and claim.get("measure")):
                key = (claim["target_concept"], claim["measure"])
                by_key[key].append(claim)
    return dict(by_key)


def _collect_parameter_claims(claim_files: Sequence[LoadedClaimFile]) -> dict[str, list[dict]]:
    """Group parameter claims by concept_id across all claim files."""
    by_concept: dict[str, list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if claim.get("type") == "parameter" and claim.get("concept"):
                by_concept[claim["concept"]].append(claim)
    return dict(by_concept)


def _collect_equation_claims(
    claim_files: Sequence[LoadedClaimFile],
) -> dict[tuple[str, tuple[str, ...]], list[dict]]:
    """Group equation claims by dependent concept and independent concept set."""
    by_signature: dict[tuple[str, tuple[str, ...]], list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if claim.get("type") != "equation":
                continue
            signature = equation_signature(claim)
            if signature is None:
                continue
            by_signature[signature].append(claim)
    return dict(by_signature)


def _collect_algorithm_claims(
    claim_files: Sequence[LoadedClaimFile],
) -> dict[str, list[dict]]:
    """Group algorithm claims by their primary concept (first concept in variables list).

    Returns dict mapping concept_id to list of algorithm claim dicts.
    """
    by_concept: dict[str, list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if claim.get("type") != "algorithm":
                continue
            variables = claim.get("variables")
            if not isinstance(variables, list) or not variables:
                continue
            # Primary concept is the first variable's concept
            first_concept = None
            for var in variables:
                if isinstance(var, dict):
                    c = var.get("concept")
                    if isinstance(c, str) and c:
                        first_concept = c
                        break
            if first_concept is not None:
                by_concept[first_concept].append(claim)
    return dict(by_concept)





def detect_conflicts(
    claim_files: Sequence[LoadedClaimFile],
    concept_registry: dict[str, dict],
) -> list[ConflictRecord]:
    """Detect conflicts between claims binding to the same concept.

    Returns list of ConflictRecord for non-COMPATIBLE pairs.
    COMPATIBLE pairs are detected but not returned (they're fine).
    """
    records: list[ConflictRecord] = []
    cel_registry = build_cel_registry(concept_registry)

    # Step 1: Collect parameter claims grouped by concept_id
    by_concept = _collect_parameter_claims(claim_files)

    # Step 2: For each concept with 2+ claims, compare every pair
    for concept_id, claims in by_concept.items():
        if len(claims) < 2:
            continue

        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim_a = claims[i]
                claim_b = claims[j]

                value_a = claim_a.get("value", [])
                value_b = claim_b.get("value", [])
                conditions_a = sorted(claim_a.get("conditions") or [])
                conditions_b = sorted(claim_b.get("conditions") or [])

                # Step 3a: Compare values (named fields take priority)
                if _values_compatible(value_a, value_b,
                                      claim_a=claim_a, claim_b=claim_b):
                    continue  # COMPATIBLE — skip

                # Step 3c: Values differ — classify based on conditions
                warning_class = _classify_conditions(conditions_a, conditions_b, cel_registry)

                records.append(ConflictRecord(
                    concept_id=concept_id,
                    claim_a_id=claim_a["id"],
                    claim_b_id=claim_b["id"],
                    warning_class=warning_class,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=_value_str(value_a, claim=claim_a),
                    value_b=_value_str(value_b, claim=claim_b),
                ))

    # Step 3: Measurement claims — grouped separately by (target_concept, measure)
    by_measurement = _collect_measurement_claims(claim_files)
    for key, m_claims in by_measurement.items():
        if len(m_claims) < 2:
            continue
        target_concept, measure = key

        for i in range(len(m_claims)):
            for j in range(i + 1, len(m_claims)):
                claim_a = m_claims[i]
                claim_b = m_claims[j]

                # Check value compatibility using _extract_interval
                if _values_compatible(None, None, claim_a=claim_a, claim_b=claim_b):
                    continue  # COMPATIBLE — skip

                # Check listener_population: if different, PHI_NODE
                pop_a = claim_a.get("listener_population", "")
                pop_b = claim_b.get("listener_population", "")
                if pop_a and pop_b and pop_a != pop_b:
                    warning_class = ConflictClass.PHI_NODE
                else:
                    conditions_a = sorted(claim_a.get("conditions") or [])
                    conditions_b = sorted(claim_b.get("conditions") or [])
                    warning_class = _classify_conditions(conditions_a, conditions_b, cel_registry)

                records.append(ConflictRecord(
                    concept_id=target_concept,
                    claim_a_id=claim_a["id"],
                    claim_b_id=claim_b["id"],
                    warning_class=warning_class,
                    conditions_a=sorted(claim_a.get("conditions") or []),
                    conditions_b=sorted(claim_b.get("conditions") or []),
                    value_a=_value_str(None, claim=claim_a),
                    value_b=_value_str(None, claim=claim_b),
                ))

    # Step 4: Equation claims — compare claims for the same dependent relation
    byequation_signature = _collect_equation_claims(claim_files)
    for (dependent_concept, _independent_concepts), equation_claims in byequation_signature.items():
        if len(equation_claims) < 2:
            continue

        # Pre-compute canonical forms to avoid redundant SymPy parsing
        canonicals = [canonicalize_equation(c) for c in equation_claims]

        for i in range(len(equation_claims)):
            for j in range(i + 1, len(equation_claims)):
                claim_a = equation_claims[i]
                claim_b = equation_claims[j]

                canonical_a = canonicals[i]
                canonical_b = canonicals[j]
                if canonical_a is None or canonical_b is None or canonical_a == canonical_b:
                    continue

                conditions_a = sorted(claim_a.get("conditions") or [])
                conditions_b = sorted(claim_b.get("conditions") or [])
                warning_class = _classify_conditions(conditions_a, conditions_b, cel_registry)

                records.append(ConflictRecord(
                    concept_id=dependent_concept,
                    claim_a_id=claim_a["id"],
                    claim_b_id=claim_b["id"],
                    warning_class=warning_class,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=claim_a.get("expression") or claim_a.get("sympy") or canonical_a,
                    value_b=claim_b.get("expression") or claim_b.get("sympy") or canonical_b,
                ))

    # Step 5: Algorithm claims — compare pairs using ast-equiv
    by_algorithm_concept = _collect_algorithm_claims(claim_files)
    for concept_id, algo_claims in by_algorithm_concept.items():
        if len(algo_claims) < 2:
            continue

        for i in range(len(algo_claims)):
            for j in range(i + 1, len(algo_claims)):
                claim_a = algo_claims[i]
                claim_b = algo_claims[j]

                body_a = claim_a.get("body", "")
                body_b = claim_b.get("body", "")
                if not body_a or not body_b:
                    continue

                # Build bindings: variable name -> concept
                bindings_a = {}
                for var in claim_a.get("variables", []):
                    if isinstance(var, dict):
                        name = var.get("name") or var.get("symbol")
                        concept = var.get("concept")
                        if name and concept:
                            bindings_a[name] = concept

                bindings_b = {}
                for var in claim_b.get("variables", []):
                    if isinstance(var, dict):
                        name = var.get("name") or var.get("symbol")
                        concept = var.get("concept")
                        if name and concept:
                            bindings_b[name] = concept

                # Compare using ast-equiv, Tiers 1-2 only (no known_values)
                try:
                    result = ast_compare(body_a, bindings_a, body_b, bindings_b)
                except Exception:
                    continue  # parse failure — skip pair

                if result.equivalent and result.tier <= 2:
                    continue  # equivalent — no conflict

                # Not equivalent — classify conditions
                conditions_a = sorted(claim_a.get("conditions") or [])
                conditions_b = sorted(claim_b.get("conditions") or [])
                warning_class = _classify_conditions(conditions_a, conditions_b, cel_registry)

                records.append(ConflictRecord(
                    concept_id=concept_id,
                    claim_a_id=claim_a["id"],
                    claim_b_id=claim_b["id"],
                    warning_class=warning_class,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=f"algorithm:{claim_a['id']}",
                    value_b=f"algorithm:{claim_b['id']}",
                    derivation_chain=f"similarity:{result.similarity:.3f} tier:{result.tier}",
                ))

    # Step 6: Parameterization conflict detection
    from propstore.param_conflicts import _detect_param_conflicts
    _detect_param_conflicts(records, by_concept, concept_registry, claim_files)

    return records


# Re-export for backward compatibility
from propstore.param_conflicts import detect_transitive_conflicts  # noqa: E402, F401
