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
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
import functools
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
    DEFAULT_TOLERANCE,
    extract_interval as _extract_interval,
    intervals_compatible as _intervals_compatible,
    parse_numeric_values as _parse_numeric_values,
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
    _detect_param_conflicts(records, by_concept, concept_registry, claim_files)

    return records


def _detect_param_conflicts(
    records: list[ConflictRecord],
    by_concept: dict[str, list[dict]],
    concept_registry: dict[str, dict],
    claim_files: Sequence[LoadedClaimFile],
) -> None:
    """Detect PARAM_CONFLICT via parameterization relationships.

    For each concept with parameterization_relationships in the registry:
    - If exactness is 'exact'
    - Collect scalar claims for input concepts
    - Use SymPy to compute derived value
    - Compare with direct claims for the output concept
    """
    try:
        from sympy import Symbol as _Symbol
        from sympy.parsing.sympy_parser import parse_expr as _parse_expr
    except ImportError:
        return  # SymPy not available, skip param conflict detection

    @functools.lru_cache(maxsize=128)
    def _cached_parse(expr_str: str, input_ids: tuple[str, ...]):
        symbols = {inp_id: _Symbol(inp_id) for inp_id in input_ids}
        return _parse_expr(expr_str, local_dict=symbols)

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

            # Check all inputs are quantity kind (form is not category/structural/boolean)
            all_quantity = True
            for inp_id in inputs:
                inp_data = concept_registry.get(inp_id, {})
                inp_form = inp_data.get("form", "")
                if inp_form in ("category", "structural", "boolean", ""):
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
                    # Try named field first
                    interval = _extract_interval(claim)
                    if interval is not None:
                        center, lo, hi = interval
                        if abs(hi - lo) < DEFAULT_TOLERANCE:
                            # Point value
                            input_values[inp_id] = center
                            input_claim_ids[inp_id] = claim["id"]
                            break
                    else:
                        # Legacy fallback
                        vals = _parse_numeric_values(claim.get("value", []))
                        if len(vals) == 1:
                            input_values[inp_id] = vals[0]
                            input_claim_ids[inp_id] = claim["id"]
                            break

            if len(input_values) != len(inputs):
                continue  # Not all inputs have claims

            # Evaluate the SymPy expression
            try:
                assert isinstance(sympy_expr_str, str)
                expr = _cached_parse(sympy_expr_str, tuple(inputs))
                derived_value = float(expr.subs(input_values))
            except Exception:
                # SymPy can't simplify -> warn, don't error
                warnings.warn(
                    f"Could not evaluate parameterization for {concept_id}: {sympy_expr_str}",
                    stacklevel=2,
                )
                continue

            # Compare derived value with direct claims for this concept
            derived_claim = {"value": derived_value}
            direct_claims = all_param_claims.get(concept_id, [])
            for direct_claim in direct_claims:
                if _values_compatible(
                    direct_claim.get("value", []),
                    [derived_value],
                    claim_a=direct_claim,
                    claim_b=derived_claim,
                ):
                    continue

                chain_parts = [f"{inp_id}={input_values[inp_id]}" for inp_id in inputs]
                chain = f"{sympy_expr_str} with {', '.join(chain_parts)} => {derived_value}"

                records.append(ConflictRecord(
                    concept_id=concept_id,
                    claim_a_id=direct_claim["id"],
                    claim_b_id="+".join(input_claim_ids[inp] for inp in inputs),
                    warning_class=ConflictClass.PARAM_CONFLICT,
                    conditions_a=sorted(direct_claim.get("conditions") or []),
                    conditions_b=[],
                    value_a=_value_str(direct_claim.get("value", []), claim=direct_claim),
                    value_b=str(derived_value),
                    derivation_chain=chain,
                ))


def detect_transitive_conflicts(
    claim_files: Sequence[LoadedClaimFile],
    concept_registry: dict[str, dict],
) -> list[ConflictRecord]:
    """Detect multi-hop transitive conflicts via parameterization chains.

    Unlike _detect_param_conflicts which checks single-hop (direct inputs → output),
    this checks chains of 2+ hops (A → B → C) where we have direct claims for
    both endpoints but the chain shows they are inconsistent.

    Only emits conflicts for concepts reachable via 2+ hops to avoid duplicating
    the single-hop conflicts already found by _detect_param_conflicts.
    """
    from propstore.parameterization_groups import build_groups
    from propstore.propagation import evaluate_parameterization

    records: list[ConflictRecord] = []

    # Convert concept_registry to list[dict] for build_groups
    concept_list = []
    for cid, cdata in concept_registry.items():
        entry = dict(cdata)
        if "id" not in entry:
            entry["id"] = cid
        concept_list.append(entry)

    groups = build_groups(concept_list)
    all_param_claims = _collect_parameter_claims(claim_files)

    # Build a directed graph of parameterization edges:
    # output_concept -> list of (inputs, sympy_expr, conditions, exactness)
    param_edges: dict[str, list[dict]] = defaultdict(list)
    # Track which concepts have DIRECT parameterization (single-hop)
    direct_param_outputs: set[str] = set()

    for cid, cdata in concept_registry.items():
        for rel in cdata.get("parameterization_relationships", []):
            if rel.get("exactness") != "exact":
                continue
            inputs = rel.get("inputs", [])
            sympy_expr = rel.get("sympy")
            if not inputs or not sympy_expr:
                continue
            param_edges[cid].append({
                "inputs": inputs,
                "sympy": sympy_expr,
                "conditions": rel.get("conditions", []),
            })
            direct_param_outputs.add(cid)

    # For each group with 3+ concepts (multi-hop chain possible)
    for group in groups:
        if len(group) < 3:
            continue

        # Iterative resolution within the group: derive values from claims
        # Try all combinations of input claims to find transitive conflicts
        # For each concept in the group, collect scalar claim values
        concept_claim_values: dict[str, list[tuple[float, str, list[str]]]] = {}
        for cid in group:
            claims = all_param_claims.get(cid, [])
            for claim in claims:
                interval = _extract_interval(claim)
                if interval is not None:
                    center, lo, hi = interval
                    if abs(hi - lo) < DEFAULT_TOLERANCE:
                        if cid not in concept_claim_values:
                            concept_claim_values[cid] = []
                        concept_claim_values[cid].append(
                            (center, claim["id"], sorted(claim.get("conditions") or []))
                        )

        # Iterative forward propagation through the chain
        # resolved: concept_id -> list of (value, chain_desc, source_claim_ids, conditions)
        resolved: dict[str, list[tuple[float, str, list[str], list[str]]]] = {}

        # Seed with direct claims
        for cid in group:
            if cid in concept_claim_values:
                for val, claim_id, conds in concept_claim_values[cid]:
                    if cid not in resolved:
                        resolved[cid] = []
                    resolved[cid].append(
                        (val, f"{cid}={val}(claim:{claim_id})", [claim_id], conds)
                    )

        # Iterate: try to derive new values
        changed = True
        max_iterations = len(group) * 2
        iteration = 0
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            for cid in group:
                if cid not in param_edges:
                    continue
                for edge in param_edges[cid]:
                    inputs = edge["inputs"]
                    sympy_expr = edge["sympy"]
                    edge_conds = sorted(edge.get("conditions") or [])

                    # Check all inputs are resolved
                    all_resolved = all(inp in resolved for inp in inputs)
                    if not all_resolved:
                        continue

                    # Try all combinations of input values
                    # (For simplicity, use first available value per input)
                    input_vals: dict[str, float] = {}
                    chain_parts: list[str] = []
                    source_ids: list[str] = []
                    input_conds: list[list[str]] = []

                    for inp in inputs:
                        # Use first resolved value for this input
                        val, desc, src_ids, conds = resolved[inp][0]
                        input_vals[inp] = val
                        chain_parts.append(desc)
                        source_ids.extend(src_ids)
                        input_conds.append(conds)

                    # Evaluate
                    derived_val = evaluate_parameterization(
                        sympy_expr, input_vals, cid
                    )
                    if derived_val is None:
                        continue

                    chain_desc = (
                        f"{' + '.join(chain_parts)} -> {sympy_expr} -> {cid}={derived_val}"
                    )

                    # Check if this is a NEW derivation
                    already_have = False
                    if cid in resolved:
                        for existing_val, _, _, _ in resolved[cid]:
                            if abs(existing_val - derived_val) < DEFAULT_TOLERANCE:
                                already_have = True
                                break

                    if not already_have:
                        if cid not in resolved:
                            resolved[cid] = []
                        resolved[cid].append(
                            (derived_val, chain_desc, source_ids, edge_conds)
                        )
                        changed = True

        # Now check for transitive conflicts:
        # For each concept that has BOTH a direct claim AND a derived value
        # through a chain of 2+ hops, compare them.
        for cid in group:
            if cid not in concept_claim_values:
                continue
            if cid not in resolved:
                continue

            # Find derived values that came through chains (not direct claims)
            for val, chain_desc, src_ids, derived_conds in resolved[cid]:
                # Skip if this is just a direct claim (source is a single claim for this concept)
                if len(src_ids) == 1 and src_ids[0] in {
                    claim_id for _, claim_id, _ in concept_claim_values[cid]
                }:
                    continue

                # Skip single-hop derivations (already handled by _detect_param_conflicts)
                # A single-hop means the source claims are all direct inputs of this concept
                is_single_hop = False
                if cid in param_edges:
                    for edge in param_edges[cid]:
                        edge_input_ids = set()
                        for inp in edge["inputs"]:
                            if inp in concept_claim_values:
                                edge_input_ids.update(
                                    cid2 for _, cid2, _ in concept_claim_values[inp]
                                )
                        if set(src_ids) <= edge_input_ids:
                            is_single_hop = True
                            break
                if is_single_hop:
                    continue

                # Compare derived value against direct claims
                derived_claim = {"value": val}
                for direct_val, direct_claim_id, direct_conds in concept_claim_values[cid]:
                    direct_claim_dict = {"value": direct_val}
                    if _values_compatible(
                        direct_val, val,
                        claim_a=direct_claim_dict,
                        claim_b=derived_claim,
                    ):
                        continue

                    records.append(ConflictRecord(
                        concept_id=cid,
                        claim_a_id=direct_claim_id,
                        claim_b_id="+".join(src_ids),
                        warning_class=ConflictClass.PARAM_CONFLICT,
                        conditions_a=direct_conds,
                        conditions_b=derived_conds,
                        value_a=str(direct_val),
                        value_b=str(val),
                        derivation_chain=chain_desc,
                    ))

    return records
