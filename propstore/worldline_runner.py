"""Worldline materialization engine.

Takes a WorldlineDefinition and a WorldModel, computes results by:
1. Binding conditions and injecting overrides as synthetic claims
2. Resolving each target concept (value_of → resolved_value → derived_value → chain)
3. Tracking which claims contributed to each result (dependency set)
4. Computing a content hash over dependencies for staleness detection

The dependency tracking follows de Kleer 1986 (ATMS): every derived datum
carries its minimal assumption set. Here, "assumptions" are the claims
whose values were used. Soundness (P2) requires every dependency to be
necessary; completeness (P3) requires no missing dependencies.

Override precedence follows Martins 1983 (belief spaces): overrides are
synthetic claims injected into the belief space that take priority over
stored claims, analogous to hypotheses in a belief space context.

Content hashing for staleness follows Green 2007 (provenance semirings):
the hash is a coarse projection of the full dependency polynomial.
A finer projection (tracking which claims combine how) is left for
future work.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from propstore.worldline import WorldlineDefinition, WorldlineResult


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
        HypotheticalWorld,
        RenderPolicy,
        ResolutionStrategy,
        SyntheticClaim,
        resolve,
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
        strategy=strategy,
        semantics=definition.policy.semantics,
        comparison=definition.policy.comparison,
        confidence_threshold=definition.policy.confidence_threshold,
    )

    # Bind the world with conditions and context
    bound = world.bind(context_id=context_id, policy=policy, **bindings)

    # ── 2. Inject overrides as synthetic claims ────────────────────
    # Overrides map canonical_name → value. We need to resolve to concept IDs.
    synthetic_claims: list[SyntheticClaim] = []
    override_concept_ids: dict[str, float | str] = {}

    for name, value in overrides.items():
        # Resolve canonical name to concept ID
        concept_id = _resolve_concept_name(world, name)
        if concept_id is None:
            continue
        override_concept_ids[concept_id] = value
        synthetic_claims.append(SyntheticClaim(
            id=f"__override_{name}",
            concept_id=concept_id,
            type="parameter",
            value=value,
        ))

    # Create hypothetical world with overrides if any
    if synthetic_claims:
        query_world = HypotheticalWorld(bound, add=synthetic_claims)
    else:
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

    # ── 4. Compute dependency hash ─────────────────────────────────
    content_hash = _compute_hash(world, sorted(dependency_claims))

    return WorldlineResult(
        computed=datetime.now(timezone.utc).isoformat(),
        content_hash=content_hash,
        values=values,
        steps=all_steps,
        dependencies={
            "claims": sorted(dependency_claims),
            "stances": [],  # TODO: track stance dependencies for argumentation
            "contexts": [context_id] if context_id else [],
        },
    )


def _resolve_concept_name(world, name: str) -> str | None:
    """Resolve a canonical name or alias to a concept ID."""
    # Try alias first
    resolved = world.resolve_alias(name)
    if resolved:
        return resolved

    # Try as concept ID directly
    concept = world.get_concept(name)
    if concept:
        return name

    # Try canonical name lookup via concept table
    conn = world._conn
    row = conn.execute(
        "SELECT id FROM concept WHERE canonical_name = ?", (name,)
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
    from propstore.world import DerivedResult, ResolutionStrategy, resolve

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
        step = {"concept": target_name, "value": claim.get("value"), "source": "claim"}
        if claim_id:
            step["claim_id"] = claim_id
        all_steps.append(step)
        return {
            "status": "determined",
            "value": claim.get("value"),
            "source": "claim",
            "claim_id": claim_id,
        }

    # If conflicted and strategy given, try resolution
    if vr.status == "conflicted" and policy.strategy is not None:
        rr = resolve(query_world, concept_id, policy=policy, world=world)
        if rr.status == "resolved" and rr.value is not None:
            if rr.winning_claim_id:
                dependency_claims.add(rr.winning_claim_id)
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
                # Check if this input came from an override or a claim
                if input_cid in override_values:
                    # Find the canonical name for this concept ID
                    concept = world.get_concept(input_cid)
                    cname = concept["canonical_name"] if concept else input_cid
                    inputs_used[input_cid] = {"value": input_val, "source": "override"}
                else:
                    # This came from a claim — track the dependency
                    input_vr = query_world.value_of(input_cid)
                    if input_vr.claims:
                        input_claim_id = input_vr.claims[0].get("id")
                        if input_claim_id and not input_claim_id.startswith("__override_"):
                            dependency_claims.add(input_claim_id)
                        inputs_used[input_cid] = {
                            "value": input_val,
                            "source": "claim",
                            "claim_id": input_claim_id,
                        }
                    else:
                        inputs_used[input_cid] = {"value": input_val, "source": "unknown"}

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

    # Underspecified — report what we know
    reason = f"status={vr.status}"
    if vr.status == "no_claims":
        reason = "no claims and no override provided"
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


def _compute_hash(world, claim_ids: list[str]) -> str:
    """Compute a content hash over the current state of dependency claims.

    This is a coarse projection of the full provenance polynomial
    (Green 2007): we hash the claim IDs and their content hashes,
    losing the algebraic structure but retaining change detection.
    """
    h = hashlib.sha256()
    for cid in claim_ids:
        claim = world.get_claim(cid)
        if claim is not None:
            h.update(cid.encode())
            content_hash = claim.get("content_hash", "")
            if content_hash:
                h.update(str(content_hash).encode())
            else:
                h.update(str(claim.get("value", "")).encode())
    return h.hexdigest()[:16]
