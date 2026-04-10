"""Parameterization conflict detection for propstore.

Detects PARAM_CONFLICT via single-hop and multi-hop parameterization chains:
- _detect_param_conflicts: single-hop derivation conflict detection
- detect_transitive_conflicts: multi-hop chain conflict detection
"""

from __future__ import annotations

import enum
import re
import warnings
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.claim_documents import LoadedClaimFile
from propstore.conflict_detector.collectors import _collect_parameter_claims
from propstore.conflict_detector.context import _claim_context, _classify_pair_context
from propstore.conflict_detector.models import ConflictClass, ConflictRecord
from propstore.value_comparison import (
    DEFAULT_TOLERANCE,
    extract_interval as _extract_interval,
    value_str as _value_str,
    values_compatible as _values_compatible,
)

if TYPE_CHECKING:
    from propstore.form_utils import FormDefinition
    from propstore.context_hierarchy import ContextHierarchy


def _normalize_claim_value(
    value: float,
    claim: dict,
    concept_id: str,
    concept_registry: dict[str, dict],
    forms: dict[str, FormDefinition] | None,
) -> float:
    """Normalize a claim's value to SI using the concept's form, if available."""
    if forms is None:
        return value
    unit = claim.get("unit")
    if unit is None:
        return value
    form_name = concept_registry.get(concept_id, {}).get("form")
    if form_name is None or form_name not in forms:
        return value
    from propstore.form_utils import normalize_to_si
    form_def = forms[form_name]
    if unit == form_def.unit_symbol:
        return value
    return normalize_to_si(value, unit, form_def)


class _Sentinel(enum.Enum):
    INCOHERENT_CONTEXT = "INCOHERENT_CONTEXT"


_INCOHERENT_CONTEXT = _Sentinel.INCOHERENT_CONTEXT
_SAFE_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _representative_source_claim_id(source_ids: Sequence[str]) -> str:
    """Choose a stable concrete claim id for conflict records.

    Conflict records store a single `claim_b_id` with a foreign-key constraint,
    while parameterized derivations may depend on multiple source claims.
    We keep the full chain in `derivation_chain` and use the first source claim
    as the representative edge endpoint.
    """
    return source_ids[0]


def _iter_unique_concepts(concept_registry: dict[str, dict]) -> list[tuple[str, dict]]:
    unique: list[tuple[str, dict]] = []
    seen_ids: set[str] = set()
    for _registry_key, concept_data in concept_registry.items():
        if not isinstance(concept_data, dict):
            continue
        concept_id = concept_data.get("artifact_id") or concept_data.get("id")
        if not isinstance(concept_id, str) or not concept_id or concept_id in seen_ids:
            continue
        seen_ids.add(concept_id)
        unique.append((concept_id, concept_data))
    return unique


def _concept_symbol_candidates(concept_data: dict) -> tuple[str, ...]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(candidate: object) -> None:
        if not isinstance(candidate, str) or not candidate:
            return
        if not _SAFE_SYMBOL_RE.match(candidate):
            return
        if candidate in seen:
            return
        seen.add(candidate)
        candidates.append(candidate)

    add(concept_data.get("canonical_name"))
    for logical_id in concept_data.get("logical_ids", []) or []:
        if not isinstance(logical_id, dict):
            continue
        add(logical_id.get("value"))
    return tuple(candidates)


def _evaluate_parameterization_with_registry(
    sympy_expr: str,
    input_values: dict[str, float],
    output_concept_id: str,
    concept_registry: dict[str, dict],
) -> float | None:
    from propstore.propagation import evaluate_parameterization

    output_data = concept_registry.get(output_concept_id, {})
    input_aliases = {
        concept_id: _concept_symbol_candidates(concept_registry.get(concept_id, {}))
        for concept_id in input_values
    }
    output_aliases = _concept_symbol_candidates(output_data)

    rewritten = sympy_expr
    for alias in output_aliases:
        rewritten = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
            "__out__",
            rewritten,
        )

    safe_values: dict[str, float] = {}
    for index, (concept_id, value) in enumerate(input_values.items()):
        safe_symbol = f"__in_{index}__"
        safe_values[safe_symbol] = value
        for alias in input_aliases.get(concept_id, ()):
            rewritten = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
                safe_symbol,
                rewritten,
            )

    if rewritten == sympy_expr:
        return evaluate_parameterization(sympy_expr, input_values, output_concept_id)
    return evaluate_parameterization(rewritten, safe_values, "__out__")


def _merge_contexts_for_derivation(
    contexts: Sequence[str | None],
    hierarchy: ContextHierarchy | None,
) -> str | None | _Sentinel:
    concrete = [context for context in contexts if context]
    if not concrete:
        return None
    if hierarchy is None:
        return concrete[0] if len(set(concrete)) == 1 else None
    if any(
        hierarchy.are_excluded(ctx_a, ctx_b)
        for index, ctx_a in enumerate(concrete)
        for ctx_b in concrete[index + 1:]
    ):
        return _INCOHERENT_CONTEXT

    candidates = [
        candidate
        for candidate in concrete
        if all(candidate == other or hierarchy.is_visible(candidate, other) for other in concrete)
    ]
    if not candidates:
        return _INCOHERENT_CONTEXT
    return max(candidates, key=lambda context_id: len(hierarchy.ancestors(context_id)))


def _detect_param_conflicts(
    records: list[ConflictRecord],
    by_concept: dict[str, list[dict]],
    concept_registry: dict[str, dict],
    claim_files: Sequence[LoadedClaimFile],
    *,
    forms: dict[str, FormDefinition] | None = None,
) -> None:
    """Detect PARAM_CONFLICT via parameterization relationships.

    For each concept with parameterization_relationships in the registry:
    - If exactness is 'exact'
    - Collect scalar claims for input concepts
    - Use SymPy to compute derived value
    - Compare with direct claims for the output concept
    """
    # Rebuild by_concept from all claim files if needed (may already have it)
    all_param_claims = by_concept
    if not all_param_claims:
        all_param_claims = _collect_parameter_claims(claim_files)

    for concept_id, concept_data in _iter_unique_concepts(concept_registry):
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
                            # Point value — normalize to SI if forms available
                            input_values[inp_id] = _normalize_claim_value(
                                center, claim, inp_id, concept_registry, forms,
                            )
                            input_claim_ids[inp_id] = claim["id"]
                            break

            if len(input_values) != len(inputs):
                continue  # Not all inputs have claims

            # Evaluate the SymPy expression
            try:
                assert isinstance(sympy_expr_str, str)
                derived_value = _evaluate_parameterization_with_registry(
                    sympy_expr_str,
                    input_values,
                    concept_id,
                    concept_registry,
                )
                if derived_value is None:
                    raise ValueError("parameterization evaluation returned no result")
            except (TypeError, ValueError, ZeroDivisionError, AssertionError, ImportError):
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
                    claim_b_id=_representative_source_claim_id(
                        [input_claim_ids[inp] for inp in inputs]
                    ),
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
    *,
    context_hierarchy: ContextHierarchy | None = None,
    forms: dict[str, FormDefinition] | None = None,
) -> list[ConflictRecord]:
    """Detect multi-hop transitive conflicts via parameterization chains.

    Unlike _detect_param_conflicts which checks single-hop (direct inputs -> output),
    this checks chains of 2+ hops (A -> B -> C) where we have direct claims for
    both endpoints but the chain shows they are inconsistent.

    Only emits conflicts for concepts reachable via 2+ hops to avoid duplicating
    the single-hop conflicts already found by _detect_param_conflicts.
    """
    from propstore.parameterization_groups import build_groups

    records: list[ConflictRecord] = []
    unique_registry = {concept_id: concept_data for concept_id, concept_data in _iter_unique_concepts(concept_registry)}

    # Convert concept_registry to list[dict] for build_groups
    concept_list = []
    for cid, cdata in unique_registry.items():
        entry = dict(cdata)
        if "id" not in entry:
            entry["id"] = cid
        concept_list.append(entry)

    groups = build_groups(concept_list)
    all_param_claims = _collect_parameter_claims(claim_files)

    # Build a directed graph of parameterization edges using shared utility
    from propstore.parameterization_walk import parameterization_edges_from_registry

    param_edges = parameterization_edges_from_registry(
        unique_registry,
        exactness_filter={"exact", "approximate"},
    )
    direct_param_outputs = set(param_edges.keys())

    # For each group with 3+ concepts (multi-hop chain possible)
    for group in groups:
        if len(group) < 3:
            continue

        # Iterative resolution within the group: derive values from claims
        # Try all combinations of input claims to find transitive conflicts
        # For each concept in the group, collect scalar claim values
        concept_claim_values: dict[str, list[tuple[float, str, list[str], str | None]]] = {}
        for cid in group:
            claims = all_param_claims.get(cid, [])
            for claim in claims:
                interval = _extract_interval(claim)
                if interval is not None:
                    center, lo, hi = interval
                    if abs(hi - lo) < DEFAULT_TOLERANCE:
                        # Normalize to SI if forms available
                        normalized = _normalize_claim_value(
                            center, claim, cid, concept_registry, forms,
                        )
                        if cid not in concept_claim_values:
                            concept_claim_values[cid] = []
                        concept_claim_values[cid].append(
                            (
                                normalized,
                                claim["id"],
                                sorted(claim.get("conditions") or []),
                                _claim_context(claim),
                            )
                        )

        # Iterative forward propagation through the chain
        # resolved: concept_id -> list of
        # (value, chain_desc, source_claim_ids, conditions, derivation_context)
        resolved: dict[str, list[tuple[float, str, list[str], list[str], str | None]]] = {}

        # Seed with direct claims
        for cid in group:
            if cid in concept_claim_values:
                for val, claim_id, conds, claim_context in concept_claim_values[cid]:
                    if cid not in resolved:
                        resolved[cid] = []
                    resolved[cid].append(
                        (val, f"{cid}={val}(claim:{claim_id})", [claim_id], conds, claim_context)
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
                    input_contexts: list[str | None] = []

                    for inp in inputs:
                        # Use first resolved value for this input
                        val, desc, src_ids, conds, source_context = resolved[inp][0]
                        input_vals[inp] = val
                        chain_parts.append(desc)
                        source_ids.extend(src_ids)
                        input_conds.append(conds)
                        input_contexts.append(source_context)

                    derived_context = _merge_contexts_for_derivation(
                        input_contexts,
                        context_hierarchy,
                    )
                    if derived_context is _INCOHERENT_CONTEXT:
                        continue
                    assert not isinstance(derived_context, _Sentinel)  # narrowed above

                    # Evaluate
                    derived_val = _evaluate_parameterization_with_registry(
                        sympy_expr,
                        input_vals,
                        cid,
                        unique_registry,
                    )
                    if derived_val is None:
                        continue

                    chain_desc = (
                        f"{' + '.join(chain_parts)} -> {sympy_expr} -> {cid}={derived_val}"
                    )

                    # Check if this is a NEW derivation
                    already_have = False
                    if cid in resolved:
                        for existing_val, _, _, _, _ in resolved[cid]:
                            if abs(existing_val - derived_val) < DEFAULT_TOLERANCE:
                                already_have = True
                                break

                    if not already_have:
                        if cid not in resolved:
                            resolved[cid] = []
                        resolved[cid].append(
                            (
                                derived_val,
                                chain_desc,
                                source_ids,
                                edge_conds,
                                derived_context,
                            )
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
            for val, chain_desc, src_ids, derived_conds, derived_context in resolved[cid]:
                # Skip if this is just a direct claim (source is a single claim for this concept)
                if len(src_ids) == 1 and src_ids[0] in {
                    claim_id for _, claim_id, _, _ in concept_claim_values[cid]
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
                                    cid2 for _, cid2, _, _ in concept_claim_values[inp]
                                )
                        if set(src_ids) <= edge_input_ids:
                            is_single_hop = True
                            break
                if is_single_hop:
                    continue

                # Compare derived value against direct claims
                derived_claim = {"value": val}
                for direct_val, direct_claim_id, direct_conds, direct_context in concept_claim_values[cid]:
                    direct_claim_dict = {"value": direct_val}
                    if _values_compatible(
                        direct_val, val,
                        claim_a=direct_claim_dict,
                        claim_b=derived_claim,
                    ):
                        continue
                    context_class = _classify_pair_context(
                        direct_context,
                        derived_context,
                        context_hierarchy,
                    )
                    if context_class is not None:
                        records.append(ConflictRecord(
                            concept_id=cid,
                            claim_a_id=direct_claim_id,
                            claim_b_id=_representative_source_claim_id(src_ids),
                            warning_class=context_class,
                            conditions_a=direct_conds,
                            conditions_b=derived_conds,
                            value_a=str(direct_val),
                            value_b=str(val),
                            derivation_chain=chain_desc,
                        ))
                        continue

                    records.append(ConflictRecord(
                        concept_id=cid,
                        claim_a_id=direct_claim_id,
                        claim_b_id=_representative_source_claim_id(src_ids),
                        warning_class=ConflictClass.PARAM_CONFLICT,
                        conditions_a=direct_conds,
                        conditions_b=derived_conds,
                        value_a=str(direct_val),
                        value_b=str(val),
                        derivation_chain=chain_desc,
                    ))

    return records
