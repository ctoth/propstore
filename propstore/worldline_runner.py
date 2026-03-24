"""Worldline materialization engine.

Takes a WorldlineDefinition and a WorldModel, computes results by:
1. Binding conditions and passing overrides as dicts to derived_value()
2. Resolving each target concept (value_of -> resolved_value -> derived_value -> chain)
3. Tracking which claims were consulted during resolution (flat dependency set)
4. Computing a SHA-256 content hash over the full result payload for staleness detection

Dependencies are accumulated into a flat set[str] of claim IDs -- every claim
consulted during resolution is added, not just the minimal necessary set.

Overrides are float/string dicts passed to derived_value() as override_values,
bypassing the belief space entirely. They are NOT injected as synthetic claims.

The content hash covers the full materialized result: values, steps,
dependencies, sensitivity, and argumentation state.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

from propstore.worldline import (
    WorldlineDefinition,
    WorldlineResult,
    compute_worldline_content_hash,
)


def run_worldline(
    definition: WorldlineDefinition,
    world,
) -> WorldlineResult:
    """Materialize a worldline: compute results for all targets.

    Parameters
    ----------
    definition : WorldlineDefinition
        The question — inputs, policy, targets.
    world : WorldModel
        The compiled knowledge base to query against.

    Returns
    -------
    WorldlineResult
        The answer — values, steps, dependencies, content hash.
    """
    from propstore.world import (
        Environment,
        ReasoningBackend,
        RenderPolicy,
        ResolutionStrategy,
    )

    # ── 1. Build the query environment ─────────────────────────────
    bindings = dict(definition.inputs.bindings)
    context_id = definition.inputs.context
    overrides = dict(definition.inputs.overrides)

    # Build policy
    strategy = None
    if definition.policy.strategy:
        strategy = ResolutionStrategy(definition.policy.strategy)
    policy = RenderPolicy(
        reasoning_backend=ReasoningBackend(definition.policy.reasoning_backend),
        strategy=strategy,
        semantics=definition.policy.semantics,
        comparison=definition.policy.comparison,
        decision_criterion=definition.policy.decision_criterion,
        pessimism_index=definition.policy.pessimism_index,
        show_uncertainty_interval=definition.policy.show_uncertainty_interval,
        praf_strategy=definition.policy.praf_strategy,
        praf_mc_epsilon=definition.policy.praf_mc_epsilon,
        praf_mc_confidence=definition.policy.praf_mc_confidence,
        praf_treewidth_cutoff=definition.policy.praf_treewidth_cutoff,
        praf_mc_seed=definition.policy.praf_mc_seed,
    )

    # Bind the world with conditions and context
    environment = Environment(bindings=bindings, context_id=context_id)
    bound = world.bind(environment, policy=policy)

    # ── 2. Resolve override concept names to IDs ─────────────────
    # Overrides are handled via override_values in derived_value(),
    # not via SyntheticClaims. This avoids conflicts with existing
    # claims for the same concept (Martins 1983: overrides are
    # context-local hypotheses that supersede, not compete with,
    # stored beliefs).
    override_concept_ids: dict[str, float | str] = {}

    for name, value in overrides.items():
        concept_id = _resolve_concept_name(world, name)
        if concept_id is None:
            continue
        override_concept_ids[concept_id] = value

    query_world = bound

    # ── 3. Resolve each target ─────────────────────────────────────
    values: dict[str, dict[str, Any]] = {}
    all_steps: list[dict[str, Any]] = []
    dependency_claims: set[str] = set()

    # Record binding steps
    for key, val in bindings.items():
        all_steps.append({"concept": key, "value": val, "source": "binding"})

    # Record override steps
    for name, val in overrides.items():
        all_steps.append({"concept": name, "value": val, "source": "override"})

    # Resolve target canonical names to concept IDs
    target_map: dict[str, str] = {}  # canonical_name → concept_id
    for target in definition.targets:
        concept_id = _resolve_concept_name(world, target)
        if concept_id is not None:
            target_map[target] = concept_id

    # Pre-resolve conflicted concepts that may be needed as derivation
    # inputs. derived_value can recursively derive undetermined inputs,
    # but it can't resolve conflicted ones (it has no access to policy).
    # This pass uses the resolution strategy to settle conflicts before
    # derivation, adding resolved values to override_concept_ids.
    if strategy is not None:
        _pre_resolve_conflicts(
            query_world, world, target_map, override_concept_ids,
            policy, dependency_claims, all_steps,
        )

    # Main pass: resolve each target using claims, overrides, resolution,
    # and recursive derivation (value_resolver.py).
    for target_name, concept_id in target_map.items():
        result_entry = _resolve_target(
            query_world, world, concept_id, target_name,
            override_concept_ids, policy, dependency_claims,
            all_steps,
        )
        values[target_name] = result_entry

    # Fill in any targets we couldn't resolve (name resolution failed)
    for target in definition.targets:
        if target not in values:
            values[target] = {
                "status": "underspecified",
                "reason": f"concept '{target}' not found in knowledge base",
            }

    # ── 4. Sensitivity analysis for derived targets ──────────────
    sensitivity_results: dict[str, Any] | None = None
    float_overrides = {k: float(v) for k, v in override_concept_ids.items()
                       if isinstance(v, (int, float))}
    for target_name, concept_id in target_map.items():
        val = values.get(target_name, {})
        if val.get("status") == "derived":
            try:
                from propstore.sensitivity import analyze_sensitivity
                sr = analyze_sensitivity(
                    world, concept_id, bound,
                    override_values=float_overrides,
                )
                if sr is not None and sr.entries:
                    if sensitivity_results is None:
                        sensitivity_results = {}
                    sensitivity_results[target_name] = [
                        {
                            "input": _concept_name(world, e.input_concept_id),
                            "elasticity": e.elasticity,
                            "partial_derivative": e.partial_derivative_value,
                        }
                        for e in sr.entries
                        if e.elasticity is not None
                    ]
            except Exception:
                logger.warning("sensitivity analysis failed for %s", target_name, exc_info=True)

    # ── 5. Argumentation state (if strategy=argumentation) ─────
    argumentation_state: dict[str, Any] | None = None
    stance_dependencies: list[str] = []
    if strategy is not None and strategy.value == "argumentation":
        try:
            active = bound.active_claims()
            active_ids = {c["id"] for c in active}
            reasoning_backend = definition.policy.reasoning_backend
            if (
                reasoning_backend == "claim_graph"
                and world.has_table("claim_stance")
            ):
                from propstore.argumentation import compute_claim_graph_justified_claims

                justified = compute_claim_graph_justified_claims(
                    world, active_ids,
                    semantics=definition.policy.semantics,
                    comparison=definition.policy.comparison,
                )
                if isinstance(justified, frozenset):
                    defeated = active_ids - justified
                    argumentation_state = {
                        "justified": sorted(justified),
                        "defeated": sorted(defeated),
                    }
            elif (
                reasoning_backend == "structured_projection"
                and world.has_table("claim_stance")
            ):
                from propstore.structured_argument import (
                    build_structured_projection,
                    compute_structured_justified_arguments,
                )

                support_metadata: dict[str, tuple[object | None, object]] = {}
                claim_support = getattr(bound, "claim_support", None)
                if callable(claim_support):
                    for claim in active:
                        claim_id = claim.get("id")
                        if claim_id:
                            support_metadata[claim_id] = claim_support(claim)

                projection = build_structured_projection(
                    world,
                    active,
                    support_metadata=support_metadata,
                    comparison=definition.policy.comparison,
                )
                justified_args = compute_structured_justified_arguments(
                    projection,
                    semantics=definition.policy.semantics,
                )
                if isinstance(justified_args, frozenset):
                    justified = {
                        projection.argument_to_claim_id[arg_id]
                        for arg_id in justified_args
                    }
                    defeated = active_ids - justified
                    argumentation_state = {
                        "backend": "structured_projection",
                        "justified": sorted(justified),
                        "defeated": sorted(defeated),
                    }
            elif reasoning_backend == "atms":
                atms_engine = getattr(bound, "atms_engine", None)
                if callable(atms_engine):
                    argumentation_state = atms_engine().argumentation_state(
                        queryables=definition.policy.future_queryables,
                        future_limit=definition.policy.future_limit or 8,
                    )

            if argumentation_state is not None:
                for cid in active_ids:
                    dependency_claims.add(cid)
                if (
                    argumentation_state.get("backend") != "atms"
                    and hasattr(world, "stances_between")
                    and world.has_table("claim_stance")
                ):
                    stance_rows = world.stances_between(active_ids)
                    stance_dependencies = sorted(
                        _stance_dependency_key(row)
                        for row in stance_rows
                    )
        except Exception:
            logger.warning("argumentation capture failed", exc_info=True)

    # ── 6. Compute dependency hash ─────────────────────────────────
    context_dependencies = _context_dependencies(bound, context_id)
    dependencies = {
        "claims": sorted(dependency_claims),
        "stances": stance_dependencies,
        "contexts": context_dependencies,
    }
    content_hash = compute_worldline_content_hash(
        values=values,
        steps=all_steps,
        dependencies=dependencies,
        sensitivity=sensitivity_results,
        argumentation=argumentation_state,
    )

    return WorldlineResult(
        computed=datetime.now(timezone.utc).isoformat(),
        content_hash=content_hash,
        values=values,
        steps=all_steps,
        dependencies=dependencies,
        sensitivity=sensitivity_results,
        argumentation=argumentation_state,
    )


def _pre_resolve_conflicts(
    query_world,
    world,
    target_map: dict[str, str],
    override_concept_ids: dict[str, float | str],
    policy,
    dependency_claims: set[str],
    all_steps: list[dict[str, Any]],
) -> None:
    """Resolve conflicted concepts that derivation chains may need as inputs.

    Walks the parameterization graph from each target (via shared
    parameterization_walk.reachable_concepts), collecting all input
    concepts. For any that are conflicted and not already overridden,
    applies the resolution strategy and adds the resolved value to
    override_concept_ids so derived_value can use it.

    This is necessary because ActiveClaimResolver.derived_value() can
    recursively derive undetermined inputs but cannot resolve conflicted
    ones (it has no access to resolution policy).
    """
    from propstore.parameterization_walk import reachable_concepts
    from propstore.world import resolve

    # Collect all concepts reachable via parameterization from targets
    param_fn = getattr(world, 'parameterizations_for', lambda _: [])
    needs_check = reachable_concepts(set(target_map.values()), param_fn)

    # Resolve any conflicted concepts
    for cid in needs_check:
        if cid in override_concept_ids:
            continue

        vr = query_world.value_of(cid)
        if vr.status == "conflicted":
            rr = resolve(query_world, cid, policy=policy, world=world)
            if rr.status == "resolved" and rr.value is not None:
                override_concept_ids[cid] = rr.value
                for claim in rr.claims:
                    claim_id = claim.get("id")
                    if claim_id and not claim_id.startswith("__override_"):
                        dependency_claims.add(claim_id)

                concept = world.get_concept(cid)
                cname = concept["canonical_name"] if concept else cid
                all_steps.append({
                    "concept": cname,
                    "value": rr.value,
                    "source": "resolved",
                    "strategy": rr.strategy,
                    "reason": rr.reason,
                    "claim_id": rr.winning_claim_id,
                })


def _concept_name(world, concept_id: str) -> str:
    """Get canonical name for a concept ID, falling back to the ID itself."""
    concept = world.get_concept(concept_id)
    return concept["canonical_name"] if concept else concept_id


def _resolve_concept_name(world, name: str) -> str | None:
    """Resolve a canonical name or alias to a concept ID."""
    if hasattr(world, "resolve_concept"):
        resolved = world.resolve_concept(name)
        if resolved:
            return resolved

    # Try alias first
    if hasattr(world, "resolve_alias"):
        resolved = world.resolve_alias(name)
        if resolved:
            return resolved

    # Try as concept ID directly
    if hasattr(world, "get_concept"):
        concept = world.get_concept(name)
        if concept:
            return name

    if hasattr(world, "_conn"):
        row = world._conn.execute(
            "SELECT id FROM concept WHERE canonical_name = ?",
            (name,),
        ).fetchone()
        if row:
            return row["id"]

    return None


def _resolve_target(
    query_world,
    world,
    concept_id: str,
    target_name: str,
    override_values: dict[str, float | str],
    policy,
    dependency_claims: set[str],
    all_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve a single target concept to a value result."""
    from propstore.world import resolve

    # Check if this concept is overridden
    if concept_id in override_values:
        return {
            "status": "determined",
            "value": override_values[concept_id],
            "source": "override",
        }

    # Try value_of (direct claim lookup)
    vr = query_world.value_of(concept_id)

    if vr.status == "determined":
        claim = vr.claims[0] if vr.claims else {}
        claim_id = claim.get("id")
        if claim_id and not claim_id.startswith("__override_"):
            dependency_claims.add(claim_id)
        claim_payload = _claim_payload(claim)
        step = {"concept": target_name, "source": "claim"}
        step.update(claim_payload)
        if claim_id:
            step["claim_id"] = claim_id
        all_steps.append(step)
        result = {
            "status": "determined",
            "source": "claim",
            "claim_id": claim_id,
        }
        result.update(claim_payload)
        return result

    # If conflicted and strategy given, try resolution
    if vr.status == "conflicted" and policy.strategy is not None:
        rr = resolve(query_world, concept_id, policy=policy, world=world)
        if rr.status == "resolved" and rr.value is not None:
            for claim in rr.claims:
                claim_id = claim.get("id")
                if claim_id and not claim_id.startswith("__override_"):
                    dependency_claims.add(claim_id)
            all_steps.append({
                "concept": target_name,
                "value": rr.value,
                "source": "resolved",
                "strategy": rr.strategy,
                "reason": rr.reason,
            })
            return {
                "status": "resolved",
                "value": rr.value,
                "source": "resolved",
                "winning_claim_id": rr.winning_claim_id,
                "strategy": rr.strategy,
                "reason": rr.reason,
            }

    # Try derived_value with override values
    # Convert override_values to float dict for derivation
    float_overrides = {k: float(v) for k, v in override_values.items()
                       if isinstance(v, (int, float))}
    dr = query_world.derived_value(concept_id, override_values=float_overrides) if hasattr(query_world, 'derived_value') else None

    if dr is not None and dr.status == "derived" and dr.value is not None:
        # Track input dependencies
        inputs_used: dict[str, dict[str, Any]] = {}
        if dr.input_values:
            for input_cid, input_val in dr.input_values.items():
                inputs_used[input_cid] = _trace_input_source(
                    query_world,
                    world,
                    input_cid,
                    override_values,
                    policy,
                    dependency_claims,
                )
                inputs_used[input_cid].setdefault("value", input_val)

        # Record each input as a step in the derivation trace,
        # skipping inputs already recorded (from pre-resolve or overrides)
        seen_concepts = {s["concept"] for s in all_steps}
        for input_cid, input_info in inputs_used.items():
            concept = world.get_concept(input_cid) if hasattr(world, 'get_concept') else None
            input_name = concept["canonical_name"] if concept else input_cid
            if input_name in seen_concepts:
                continue
            step: dict[str, Any] = {
                "concept": input_name,
                "value": input_info.get("value"),
                "source": input_info.get("source", "unknown"),
            }
            if input_info.get("claim_id"):
                step["claim_id"] = input_info["claim_id"]
            if input_info.get("formula"):
                step["formula"] = input_info["formula"]
            all_steps.append(step)

        all_steps.append({
            "concept": target_name,
            "value": dr.value,
            "source": "derived",
            "formula": dr.formula,
        })

        return {
            "status": "derived",
            "value": dr.value,
            "source": "derived",
            "formula": dr.formula,
            "inputs_used": inputs_used,
        }

    # Try chain_query for multi-step derivation (iterative fixpoint
    # across parameterization groups — resolves chains like
    # g_earth → gravitational_acceleration → acceleration → force)
    strategy_enum = policy.strategy if policy.strategy is not None else None
    chain_bindings = {}
    if hasattr(query_world, '_bindings'):
        chain_bindings = dict(query_world._bindings)
    chain_error: str | None = None
    try:
        chain_result = world.chain_query(
            concept_id,
            strategy=strategy_enum,
            **chain_bindings,
        )
        cr = chain_result.result
        if hasattr(cr, 'value') and cr.value is not None and cr.status in ("derived", "determined"):
            # Extract dependencies from chain steps
            for step in chain_result.steps:
                if step.source == "claim":
                    # Find the claim ID for this concept
                    step_vr = query_world.value_of(step.concept_id)
                    if step_vr.claims:
                        dep_id = step_vr.claims[0].get("id")
                        if dep_id and not dep_id.startswith("__override_"):
                            dependency_claims.add(dep_id)

            # Record chain steps
            for step in chain_result.steps:
                if step.concept_id != concept_id and step.source != "binding":
                    cpt = world.get_concept(step.concept_id)
                    step_name = cpt["canonical_name"] if cpt else step.concept_id
                    all_steps.append({
                        "concept": step_name,
                        "value": step.value,
                        "source": step.source,
                    })

            formula = None
            if hasattr(cr, 'formula'):
                formula = cr.formula

            all_steps.append({
                "concept": target_name,
                "value": cr.value,
                "source": "derived",
                "formula": formula,
            })

            inputs_used = {}
            if hasattr(cr, 'input_values') and cr.input_values:
                for k, v in cr.input_values.items():
                    inputs_used[k] = _trace_input_source(
                        query_world,
                        world,
                        k,
                        override_values,
                        policy,
                        dependency_claims,
                    )
                    inputs_used[k].setdefault("value", v)

            return {
                "status": "derived",
                "value": cr.value,
                "source": "derived",
                "formula": formula,
                "inputs_used": inputs_used,
            }
    except Exception as exc:
        chain_error = f"chain query failed: {exc}"

    if chain_error is not None:
        all_steps.append({
            "concept": target_name,
            "value": None,
            "source": "error",
            "reason": chain_error,
        })
        return {
            "status": "error",
            "reason": chain_error,
        }

    # Underspecified — report what we know
    reason = f"status={vr.status}"
    if vr.status == "no_claims":
        reason = "no claims and no override provided"
    elif vr.status == "no_values":
        reason = "claims exist but none have scalar values"
    elif vr.status == "conflicted":
        reason = "conflicted with no resolution strategy"
    elif vr.status == "underdetermined":
        reason = "underdetermined"

    all_steps.append({
        "concept": target_name,
        "value": None,
        "source": "underspecified",
        "reason": reason,
    })

    return {
        "status": "underspecified",
        "reason": reason,
    }


def _claim_payload(claim: dict[str, Any]) -> dict[str, Any]:
    """Preserve non-scalar claim payloads in worldline results."""
    payload: dict[str, Any] = {}
    value = claim.get("value")
    if value is not None:
        payload["value"] = value

    claim_type = claim.get("type")
    if claim_type:
        payload["claim_type"] = claim_type

    for field in ("statement", "expression", "body", "name", "canonical_ast"):
        field_value = claim.get(field)
        if field_value:
            payload[field] = field_value

    variables_json = claim.get("variables_json")
    if variables_json:
        try:
            payload["variables"] = json.loads(variables_json)
        except (TypeError, json.JSONDecodeError):
            payload["variables"] = variables_json

    return payload


def _trace_input_source(
    query_world,
    world,
    concept_id: str,
    override_values: dict[str, float | str],
    policy,
    dependency_claims: set[str],
    seen: set[str] | None = None,
) -> dict[str, Any]:
    """Trace where an input value came from, recursing through derived inputs."""
    from propstore.world import resolve

    if concept_id in override_values:
        return {
            "value": override_values[concept_id],
            "source": "override",
        }

    if seen is None:
        seen = set()
    if concept_id in seen:
        return {"source": "cycle"}
    seen.add(concept_id)

    try:
        vr = query_world.value_of(concept_id)
        if vr.status == "determined":
            claim = vr.claims[0] if vr.claims else {}
            claim_id = claim.get("id")
            if claim_id and not claim_id.startswith("__override_"):
                dependency_claims.add(claim_id)
            result = {
                "value": claim.get("value"),
                "source": "claim",
            }
            if claim_id:
                result["claim_id"] = claim_id
            return result

        if vr.status == "conflicted" and policy.strategy is not None:
            rr = resolve(query_world, concept_id, policy=policy, world=world)
            if rr.status == "resolved" and rr.value is not None:
                for claim in rr.claims:
                    claim_id = claim.get("id")
                    if claim_id and not claim_id.startswith("__override_"):
                        dependency_claims.add(claim_id)
                result = {
                    "value": rr.value,
                    "source": "resolved",
                    "strategy": rr.strategy,
                }
                if rr.winning_claim_id:
                    result["claim_id"] = rr.winning_claim_id
                if rr.reason:
                    result["reason"] = rr.reason
                return result

        float_overrides = {
            key: float(val)
            for key, val in override_values.items()
            if isinstance(val, (int, float))
        }
        dr = query_world.derived_value(concept_id, override_values=float_overrides)
        if dr.status == "derived" and dr.value is not None:
            nested_inputs: dict[str, dict[str, Any]] = {}
            for input_cid, input_val in dr.input_values.items():
                nested_inputs[input_cid] = _trace_input_source(
                    query_world,
                    world,
                    input_cid,
                    override_values,
                    policy,
                    dependency_claims,
                    seen,
                )
                nested_inputs[input_cid].setdefault("value", input_val)
            result = {
                "value": dr.value,
                "source": "derived",
            }
            if dr.formula:
                result["formula"] = dr.formula
            if nested_inputs:
                result["inputs_used"] = nested_inputs
            return result

        return {"source": "unknown"}
    finally:
        seen.discard(concept_id)


def _stance_dependency_key(row: dict[str, Any]) -> str:
    """Serialize a stance row into a stable dependency key."""
    return json.dumps(
        {key: row.get(key) for key in sorted(row)},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _context_dependencies(bound, context_id: str | None) -> list[str]:
    """Collect context-scoped inputs that affect a worldline materialization."""
    if not context_id:
        return []

    dependencies = [context_id]
    environment = getattr(bound, "_environment", None)
    assumptions = getattr(environment, "effective_assumptions", ())
    for assumption in assumptions:
        dependencies.append(f"assumption:{assumption}")
    return dependencies
