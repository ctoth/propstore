"""Parameterization conflict detection for propstore.

Detects PARAM_CONFLICT via single-hop and multi-hop parameterization chains:
- _detect_param_conflicts: single-hop derivation conflict detection
- detect_transitive_conflicts: multi-hop chain conflict detection
"""

from __future__ import annotations

import functools
import warnings
from collections import defaultdict
from collections.abc import Sequence

from propstore.conflict_detector import (
    ConflictClass,
    ConflictRecord,
    _collect_parameter_claims,
)
from propstore.validate_claims import LoadedClaimFile
from propstore.value_comparison import (
    DEFAULT_TOLERANCE,
    extract_interval as _extract_interval,
    parse_numeric_values as _parse_numeric_values,
    value_str as _value_str,
    values_compatible as _values_compatible,
)


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

    Unlike _detect_param_conflicts which checks single-hop (direct inputs -> output),
    this checks chains of 2+ hops (A -> B -> C) where we have direct claims for
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
