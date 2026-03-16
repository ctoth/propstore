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

import warnings
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from compiler.validate_claims import LoadedClaimFile


class ConflictClass(Enum):
    COMPATIBLE = "COMPATIBLE"
    PHI_NODE = "PHI_NODE"
    CONFLICT = "CONFLICT"
    OVERLAP = "OVERLAP"
    PARAM_CONFLICT = "PARAM_CONFLICT"


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


# ── Value comparison ─────────────────────────────────────────────────

DEFAULT_TOLERANCE = 1e-9


def _parse_numeric_values(value_list: list) -> tuple[float, ...]:
    """Extract numeric values from a claim value list.

    Returns a tuple of floats. A single-element list is a scalar;
    a two-element list is a range [min, max].
    """
    result = []
    for v in value_list:
        try:
            result.append(float(v))
        except (TypeError, ValueError):
            pass
    return tuple(result)


def _values_compatible(value_a: list, value_b: list, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    """Check if two claim values are compatible.

    - Scalar vs scalar: abs difference within tolerance
    - Range vs range: ranges overlap
    - Scalar vs range: scalar falls within range (treated as compatible)
    """
    nums_a = _parse_numeric_values(value_a)
    nums_b = _parse_numeric_values(value_b)

    if not nums_a or not nums_b:
        # Non-numeric values: string equality
        return value_a == value_b

    # Both scalars
    if len(nums_a) == 1 and len(nums_b) == 1:
        return abs(nums_a[0] - nums_b[0]) < tolerance

    # Both ranges
    if len(nums_a) >= 2 and len(nums_b) >= 2:
        min_a, max_a = min(nums_a), max(nums_a)
        min_b, max_b = min(nums_b), max(nums_b)
        # Ranges overlap if one starts before the other ends
        return min_a <= max_b and min_b <= max_a

    # Scalar vs range: scalar within range bounds
    if len(nums_a) == 1 and len(nums_b) >= 2:
        min_b, max_b = min(nums_b), max(nums_b)
        return min_b - tolerance <= nums_a[0] <= max_b + tolerance

    if len(nums_b) == 1 and len(nums_a) >= 2:
        min_a, max_a = min(nums_a), max(nums_a)
        return min_a - tolerance <= nums_b[0] <= max_a + tolerance

    return value_a == value_b


# ── Condition classification ─────────────────────────────────────────


def _classify_conditions(
    conditions_a: list[str],
    conditions_b: list[str],
) -> ConflictClass:
    """Classify a pair of differing-value claims based on their conditions.

    Returns CONFLICT, PHI_NODE, or OVERLAP.
    """
    set_a = set(sorted(conditions_a))
    set_b = set(sorted(conditions_b))

    if set_a == set_b:
        # Identical conditions (or both empty) -> CONFLICT
        return ConflictClass.CONFLICT

    intersection = set_a & set_b
    if not intersection:
        # Fully disjoint -> PHI_NODE
        return ConflictClass.PHI_NODE

    # Partial overlap
    return ConflictClass.OVERLAP


# ── Main detector ────────────────────────────────────────────────────


def _collect_parameter_claims(claim_files: list[LoadedClaimFile]) -> dict[str, list[dict]]:
    """Group parameter claims by concept_id across all claim files."""
    by_concept: dict[str, list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if claim.get("type") == "parameter" and claim.get("concept"):
                by_concept[claim["concept"]].append(claim)
    return dict(by_concept)


def _value_str(value: list) -> str:
    """Convert a value list to a string representation."""
    if len(value) == 1:
        return str(value[0])
    return str(value)


def detect_conflicts(
    claim_files: list[LoadedClaimFile],
    concept_registry: dict[str, dict],
) -> list[ConflictRecord]:
    """Detect conflicts between claims binding to the same concept.

    Returns list of ConflictRecord for non-COMPATIBLE pairs.
    COMPATIBLE pairs are detected but not returned (they're fine).
    """
    records: list[ConflictRecord] = []

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

                # Step 3a: Compare values
                if _values_compatible(value_a, value_b):
                    continue  # COMPATIBLE — skip

                # Step 3c: Values differ — classify based on conditions
                warning_class = _classify_conditions(conditions_a, conditions_b)

                records.append(ConflictRecord(
                    concept_id=concept_id,
                    claim_a_id=claim_a["id"],
                    claim_b_id=claim_b["id"],
                    warning_class=warning_class,
                    conditions_a=conditions_a,
                    conditions_b=conditions_b,
                    value_a=_value_str(value_a),
                    value_b=_value_str(value_b),
                ))

    # Step 4: Parameterization conflict detection
    _detect_param_conflicts(records, by_concept, concept_registry, claim_files)

    return records


def _detect_param_conflicts(
    records: list[ConflictRecord],
    by_concept: dict[str, list[dict]],
    concept_registry: dict[str, dict],
    claim_files: list[LoadedClaimFile],
) -> None:
    """Detect PARAM_CONFLICT via parameterization relationships.

    For each concept with parameterization_relationships in the registry:
    - If exactness is 'exact'
    - Collect scalar claims for input concepts
    - Use SymPy to compute derived value
    - Compare with direct claims for the output concept
    """
    try:
        import sympy
    except ImportError:
        return  # SymPy not available, skip param conflict detection

    # Rebuild by_concept from all claim files if needed (may already have it)
    all_param_claims = by_concept
    if not all_param_claims:
        all_param_claims = _collect_parameter_claims(claim_files)

    for concept_id, concept_data in concept_registry.items():
        param_rels = concept_data.get("parameterization_relationships", [])
        if not param_rels:
            continue

        for rel in param_rels:
            if rel.get("exactness") != "exact":
                continue

            inputs = rel.get("inputs", [])
            sympy_expr_str = rel.get("sympy")
            if not inputs or not sympy_expr_str:
                continue

            # Check all inputs are quantity kind
            all_quantity = True
            for inp_id in inputs:
                inp_data = concept_registry.get(inp_id, {})
                kind = inp_data.get("kind", {})
                if "quantity" not in kind:
                    all_quantity = False
                    break
            if not all_quantity:
                continue

            # Get scalar values for each input concept
            input_values: dict[str, float] = {}
            input_claim_ids: dict[str, str] = {}
            for inp_id in inputs:
                inp_claims = all_param_claims.get(inp_id, [])
                for claim in inp_claims:
                    vals = _parse_numeric_values(claim.get("value", []))
                    if len(vals) == 1:
                        input_values[inp_id] = vals[0]
                        input_claim_ids[inp_id] = claim["id"]
                        break  # Use first scalar claim found

            if len(input_values) != len(inputs):
                continue  # Not all inputs have claims

            # Evaluate the SymPy expression
            try:
                # Create symbols for each input concept ID
                symbols = {inp_id: sympy.Symbol(inp_id) for inp_id in inputs}
                expr = sympy.sympify(sympy_expr_str, locals=symbols)
                derived_value = float(expr.subs(input_values))
            except Exception:
                # SymPy can't simplify -> warn, don't error
                warnings.warn(
                    f"Could not evaluate parameterization for {concept_id}: {sympy_expr_str}",
                    stacklevel=2,
                )
                continue

            # Compare derived value with direct claims for this concept
            direct_claims = all_param_claims.get(concept_id, [])
            for direct_claim in direct_claims:
                direct_vals = _parse_numeric_values(direct_claim.get("value", []))
                if len(direct_vals) == 1:
                    if not _values_compatible([derived_value], [direct_vals[0]]):
                        # Build derivation chain description
                        chain_parts = [f"{inp_id}={input_values[inp_id]}" for inp_id in inputs]
                        chain = f"{sympy_expr_str} with {', '.join(chain_parts)} => {derived_value}"

                        records.append(ConflictRecord(
                            concept_id=concept_id,
                            claim_a_id=direct_claim["id"],
                            claim_b_id="+".join(input_claim_ids[inp] for inp in inputs),
                            warning_class=ConflictClass.PARAM_CONFLICT,
                            conditions_a=sorted(direct_claim.get("conditions") or []),
                            conditions_b=[],
                            value_a=_value_str(direct_claim.get("value", [])),
                            value_b=str(derived_value),
                            derivation_chain=chain,
                        ))
