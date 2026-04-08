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
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from propstore.core.id_types import ClaimId, ConceptId, ContextId, to_claim_id, to_concept_id
from propstore.core.environment import (
    ArtifactStore,
    Environment,
    ParameterizationLookupStore,
    StanceStore,
)
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.row_types import StanceRow, coerce_stance_row
from propstore.core.labels import Label, SupportQuality
from propstore.world.types import (
    BeliefSpace,
    ClaimSupportView,
    DerivedResult,
    HasATMSEngine,
    RenderPolicy,
    ValueResult,
    coerce_queryable_assumptions,
    validate_backend_semantics,
)

logger = logging.getLogger(__name__)

from propstore.worldline import (
    WorldlineDefinition,
    WorldlineResult,
    compute_worldline_content_hash,
)


class _WorldlineBoundView(BeliefSpace, Protocol):
    pass


@runtime_checkable
class _HasBindings(Protocol):
    _bindings: Mapping[str, Any]


@runtime_checkable
class _HasEnvironment(Protocol):
    _environment: Environment


@runtime_checkable
class _HasActiveGraph(Protocol):
    _active_graph: ActiveWorldGraph | None


class _WorldlineStore(ArtifactStore, Protocol):
    def bind(
        self,
        environment: Environment | None = None,
        *,
        policy: RenderPolicy | None = None,
        **conditions: Any,
    ) -> _WorldlineBoundView: ...


def _display_claim_id(world: ArtifactStore, claim_id: str | None) -> str | None:
    if claim_id is None:
        return None
    getter = getattr(world, "get_claim", None)
    if callable(getter):
        claim = getter(claim_id)
        if isinstance(claim, Mapping):
            logical_id = claim.get("logical_id") or claim.get("primary_logical_id")
            if isinstance(logical_id, str) and logical_id:
                return logical_id.split(":", 1)[1] if ":" in logical_id else logical_id
            logical_ids = claim.get("logical_ids")
            if isinstance(logical_ids, list):
                for entry in logical_ids:
                    if not isinstance(entry, Mapping):
                        continue
                    value = entry.get("value")
                    if isinstance(value, str) and value:
                        return value
    return claim_id


def run_worldline(
    definition: WorldlineDefinition,
    world: _WorldlineStore,
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
    from propstore.world import ReasoningBackend, ResolutionStrategy

    # ── 1. Build the query environment ─────────────────────────────
    environment = definition.inputs.environment
    bindings = dict(environment.bindings)
    context_id = environment.context_id
    overrides = dict(definition.inputs.overrides)

    policy = definition.policy
    strategy = policy.strategy

    # Bind the world with conditions and context
    bound = world.bind(environment, policy=policy)

    # ── 2. Resolve override concept names to IDs ─────────────────
    # Overrides are handled via override_values in derived_value(),
    # not via SyntheticClaims. This avoids conflicts with existing
    # claims for the same concept (Martins 1983: overrides are
    # context-local hypotheses that supersede, not compete with,
    # stored beliefs).
    override_concept_ids: dict[ConceptId, float | str] = {}

    for name, value in overrides.items():
        concept_id = _resolve_concept_name(world, name)
        if concept_id is None:
            continue
        override_concept_ids[concept_id] = value

    query_world = bound

    # ── 3. Resolve each target ─────────────────────────────────────
    values: dict[str, dict[str, Any]] = {}
    all_steps: list[dict[str, Any]] = []
    dependency_claims: set[ClaimId] = set()

    # Record binding steps
    for key, val in bindings.items():
        all_steps.append({"concept": key, "value": val, "source": "binding"})

    # Record override steps
    for name, val in overrides.items():
        all_steps.append({"concept": name, "value": val, "source": "override"})

    # Resolve target canonical names to concept IDs
    target_map: dict[str, ConceptId] = {}
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
    float_overrides = {
        str(concept_id): float(value)
        for concept_id, value in override_concept_ids.items()
        if isinstance(value, (int, float))
    }
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
            except Exception as exc:
                logger.warning("sensitivity analysis failed for %s", target_name, exc_info=True)
                if sensitivity_results is None:
                    sensitivity_results = {}
                sensitivity_results[target_name] = {
                    "error": f"sensitivity analysis failed: {exc}",
                }

    # ── 5. Argumentation state (if strategy=argumentation) ─────
    argumentation_state: dict[str, Any] | None = None
    stance_dependencies: list[str] = []
    if strategy == ResolutionStrategy.ARGUMENTATION:
        try:
            active = bound.active_claims()
            active_ids = {
                to_claim_id(claim_id)
                for claim in active
                if (claim_id := claim.get("id"))
            }
            active_graph = bound._active_graph if isinstance(bound, _HasActiveGraph) else None
            reasoning_backend = definition.policy.reasoning_backend
            _, normalized_semantics = validate_backend_semantics(
                reasoning_backend,
                definition.policy.semantics,
            )
            if (
                reasoning_backend == ReasoningBackend.CLAIM_GRAPH
                and world.has_table("relation_edge")
            ):
                justified_claims: frozenset[ClaimId] | None = None
                if active_graph is not None:
                    from propstore.core.analyzers import (
                        analyze_claim_graph,
                        shared_analyzer_input_from_active_graph,
                    )

                    analyzer_result = analyze_claim_graph(
                        shared_analyzer_input_from_active_graph(
                            active_graph,
                            comparison=definition.policy.comparison,
                        ),
                        semantics=normalized_semantics,
                    )
                    if len(analyzer_result.extensions) == 1:
                        justified_claims = frozenset(
                            to_claim_id(claim_id)
                            for claim_id in analyzer_result.extensions[0].accepted_claim_ids
                        )
                else:
                    from propstore.argumentation import compute_claim_graph_justified_claims

                    current = compute_claim_graph_justified_claims(
                        world, {str(claim_id) for claim_id in active_ids},
                        semantics=normalized_semantics,
                        comparison=definition.policy.comparison,
                    )
                    if isinstance(current, frozenset):
                        justified_claims = frozenset(
                            to_claim_id(claim_id)
                            for claim_id in current
                        )

                if justified_claims is not None:
                    defeated = active_ids - justified_claims
                    argumentation_state = {
                        "justified": sorted(justified_claims),
                        "defeated": sorted(defeated),
                    }
            elif (
                reasoning_backend == ReasoningBackend.ASPIC
                and world.has_table("relation_edge")
            ):
                from propstore.structured_argument import (
                    build_structured_projection,
                    compute_structured_justified_arguments,
                )

                support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
                if isinstance(bound, ClaimSupportView):
                    for claim in active:
                        claim_id = claim.get("id")
                        if claim_id:
                            support_metadata[claim_id] = bound.claim_support(claim)

                aspic_projection = build_structured_projection(
                    world,
                    active,
                    support_metadata=support_metadata,
                    comparison=definition.policy.comparison,
                    link=definition.policy.link,
                    active_graph=active_graph,
                )
                aspic_justified_args = compute_structured_justified_arguments(
                    aspic_projection,
                    semantics=normalized_semantics,
                    backend=ReasoningBackend.ASPIC,
                )
                if isinstance(aspic_justified_args, frozenset):
                    justified_claim_ids = {
                        to_claim_id(aspic_projection.argument_to_claim_id[arg_id])
                        for arg_id in aspic_justified_args
                    }
                    defeated = active_ids - justified_claim_ids
                    argumentation_state = {
                        "backend": "aspic",
                        "justified": sorted(justified_claim_ids),
                        "defeated": sorted(defeated),
                    }
            elif reasoning_backend == ReasoningBackend.ATMS:
                if isinstance(bound, HasATMSEngine):
                    argumentation_state = bound.atms_engine().argumentation_state(
                        queryables=coerce_queryable_assumptions(
                            definition.policy.future_queryables
                        ),
                        future_limit=definition.policy.future_limit or 8,
                    )
            elif (
                reasoning_backend == ReasoningBackend.PRAF
                and world.has_table("relation_edge")
            ):
                # Extract PrAF parameters from policy (same as resolution.py)
                praf_strategy = definition.policy.praf_strategy or "auto"
                praf_mc_epsilon = definition.policy.praf_mc_epsilon or 0.01
                praf_mc_confidence = definition.policy.praf_mc_confidence or 0.95
                praf_treewidth_cutoff = definition.policy.praf_treewidth_cutoff or 12
                praf_mc_seed = definition.policy.praf_mc_seed

                if active_graph is not None:
                    from propstore.core.analyzers import (
                        analyze_praf,
                        shared_analyzer_input_from_active_graph,
                    )

                    analyzer_result = analyze_praf(
                        shared_analyzer_input_from_active_graph(
                            active_graph,
                            comparison=definition.policy.comparison or "elitist",
                        ),
                        semantics=normalized_semantics,
                        strategy=praf_strategy,
                        query_kind="argument_acceptance",
                        inference_mode="credulous",
                        mc_epsilon=praf_mc_epsilon,
                        mc_confidence=praf_mc_confidence,
                        treewidth_cutoff=praf_treewidth_cutoff,
                        rng_seed=praf_mc_seed,
                    )
                    metadata = dict(analyzer_result.metadata)
                    acceptance_probs = dict(metadata["acceptance_probs"])
                    strategy_used = metadata["strategy_used"]
                    samples = metadata["samples"]
                    confidence_interval_half = metadata["confidence_interval_half"]
                else:
                    # Li et al. (2012): PrAF = (A, P_A, D, P_D).
                    # Build probabilistic AF and compute acceptance probabilities.
                    from propstore.argumentation import build_praf
                    from propstore.praf import compute_praf_acceptance

                    praf = build_praf(
                        world, {str(claim_id) for claim_id in active_ids},
                        comparison=definition.policy.comparison or "elitist",
                    )
                    praf_result = compute_praf_acceptance(
                        praf,
                        semantics=normalized_semantics,
                        strategy=praf_strategy,
                        query_kind="argument_acceptance",
                        inference_mode="credulous",
                        mc_epsilon=praf_mc_epsilon,
                        mc_confidence=praf_mc_confidence,
                        treewidth_cutoff=praf_treewidth_cutoff,
                        rng_seed=praf_mc_seed,
                    )
                    acceptance_probs = dict(praf_result.acceptance_probs or {})
                    strategy_used = praf_result.strategy_used
                    samples = praf_result.samples
                    confidence_interval_half = praf_result.confidence_interval_half

                argumentation_state = {
                    "backend": "praf",
                    "acceptance_probs": acceptance_probs,
                    "strategy_used": strategy_used,
                    "samples": samples,
                    "confidence_interval_half": confidence_interval_half,
                    "semantics": normalized_semantics.value,
                }

            if argumentation_state is not None:
                for cid in active_ids:
                    dependency_claims.add(cid)
                if (
                    argumentation_state.get("backend") != "atms"
                ):
                    stance_dependencies = _active_stance_dependencies(
                        bound,
                        world,
                        active_ids,
                    )
        except Exception as exc:
            logger.warning("argumentation capture failed", exc_info=True)
            argumentation_state = {
                "status": "error",
                "error": f"argumentation capture failed: {exc}",
            }

    # ── 6. Revision state (if explicit revision query present) ──
    revision_state: dict[str, Any] | None = None
    if definition.revision is not None:
        try:
            revision_state = _capture_revision_state(bound, definition.revision)
        except Exception as exc:
            logger.warning("revision capture failed", exc_info=True)
            revision_state = {
                "operation": definition.revision.operation,
                "status": "error",
                "error": f"revision capture failed: {exc}",
            }

    # ── 7. Compute dependency hash ─────────────────────────────────
    context_dependencies = _context_dependencies(bound, context_id)
    dependencies = {
        "claims": sorted(
            _display_claim_id(world, str(claim_id)) or str(claim_id)
            for claim_id in dependency_claims
        ),
        "stances": stance_dependencies,
        "contexts": context_dependencies,
    }
    content_hash = compute_worldline_content_hash(
        values=values,
        steps=all_steps,
        dependencies=dependencies,
        sensitivity=sensitivity_results,
        argumentation=argumentation_state,
        revision=revision_state,
    )

    return WorldlineResult(
        computed=datetime.now(timezone.utc).isoformat(),
        content_hash=content_hash,
        values=values,
        steps=all_steps,
        dependencies=dependencies,
        sensitivity=sensitivity_results,
        argumentation=argumentation_state,
        revision=revision_state,
    )


def _capture_revision_state(bound, revision_query) -> dict[str, Any]:
    from propstore.revision.iterated import epistemic_state_payload

    operation = revision_query.operation
    if operation == "expand":
        result = bound.expand(revision_query.atom)
        return {
            "operation": operation,
            "input_atom_id": _query_atom_id(revision_query.atom),
            "target_atom_ids": [],
            "result": _revision_result_payload(result),
        }
    if operation == "contract":
        result = bound.contract(revision_query.target)
        return {
            "operation": operation,
            "input_atom_id": None,
            "target_atom_ids": _query_target_atom_ids(revision_query.target),
            "result": _revision_result_payload(result),
        }
    if operation == "revise":
        result = bound.revise(revision_query.atom, conflicts=revision_query.conflicts)
        return {
            "operation": operation,
            "input_atom_id": _query_atom_id(revision_query.atom),
            "target_atom_ids": _query_conflict_target_atom_ids(revision_query),
            "result": _revision_result_payload(result),
        }
    if operation == "iterated_revise":
        result, state = bound.iterated_revise(
            revision_query.atom,
            conflicts=revision_query.conflicts,
            operator=revision_query.operator or "restrained",
        )
        return {
            "operation": operation,
            "input_atom_id": _query_atom_id(revision_query.atom),
            "target_atom_ids": _query_conflict_target_atom_ids(revision_query),
            "result": _revision_result_payload(result),
            "state": epistemic_state_payload(state),
        }
    raise ValueError(f"Unknown revision operation: {operation}")


def _revision_result_payload(result) -> dict[str, Any]:
    return {
        "accepted_atom_ids": list(result.accepted_atom_ids),
        "rejected_atom_ids": list(result.rejected_atom_ids),
        "incision_set": list(result.incision_set),
        "explanation": dict(result.explanation),
    }


def _query_atom_id(atom: dict[str, Any] | None) -> str | None:
    if not atom:
        return None
    kind = str(atom.get("kind") or "claim")
    if kind == "claim":
        claim_id = atom.get("id") or atom.get("claim_id")
        if claim_id:
            return f"claim:{claim_id}"
    if kind == "assumption":
        assumption_id = atom.get("assumption_id") or atom.get("id")
        if assumption_id:
            return f"assumption:{assumption_id}"
    atom_id = atom.get("atom_id")
    return str(atom_id) if atom_id else None


def _query_target_atom_ids(target: Any) -> list[str]:
    if target is None:
        return []
    if isinstance(target, str):
        if ":" in target:
            return [target]
        return [f"claim:{target}"]
    return [str(target)]


def _query_conflict_target_atom_ids(revision_query) -> list[str]:
    input_atom_id = _query_atom_id(revision_query.atom)
    if input_atom_id is None:
        return []
    targets = revision_query.conflicts.get(input_atom_id, ())
    return [
        target if ":" in target else f"claim:{target}"
        for target in targets
    ]


def _pre_resolve_conflicts(
    query_world: _WorldlineBoundView,
    world: ArtifactStore,
    target_map: Mapping[str, ConceptId],
    override_concept_ids: dict[ConceptId, float | str],
    policy: RenderPolicy,
    dependency_claims: set[ClaimId],
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
    parameterizations_for = (
        world.parameterizations_for
        if isinstance(world, ParameterizationLookupStore)
        else (lambda _concept_id: [])
    )
    needs_check = reachable_concepts(
        {str(concept_id) for concept_id in target_map.values()},
        parameterizations_for,
    )

    # Resolve any conflicted concepts
    for cid in needs_check:
        normalized_cid = to_concept_id(cid)
        if normalized_cid in override_concept_ids:
            continue

        vr = query_world.value_of(normalized_cid)
        if vr.status == "conflicted":
            rr = resolve(query_world, normalized_cid, policy=policy, world=world)
            if rr.status == "resolved" and rr.value is not None:
                override_concept_ids[normalized_cid] = rr.value
                for claim in rr.claims:
                    claim_id = claim.get("id")
                    if claim_id and not claim_id.startswith("__override_"):
                        dependency_claims.add(to_claim_id(claim_id))

                concept = world.get_concept(normalized_cid)
                cname = concept["canonical_name"] if concept else normalized_cid
                all_steps.append({
                    "concept": cname,
                    "value": rr.value,
                    "source": "resolved",
                    "strategy": rr.strategy,
                    "reason": rr.reason,
                    "claim_id": rr.winning_claim_id,
                })


def _concept_name(world: ArtifactStore, concept_id: ConceptId | str) -> str:
    """Get canonical name for a concept ID, falling back to the ID itself."""
    concept = world.get_concept(concept_id)
    return concept["canonical_name"] if concept else concept_id


def _resolve_concept_name(world: ArtifactStore, name: str) -> ConceptId | None:
    """Resolve a canonical name or alias to a concept ID.

    Delegates to WorldModel.resolve_concept() which handles alias lookup,
    direct ID lookup, and canonical name lookup.
    """
    resolved = world.resolve_concept(name)
    return None if resolved is None else to_concept_id(resolved)


def _resolve_target(
    query_world: _WorldlineBoundView,
    world: ArtifactStore,
    concept_id: ConceptId,
    target_name: str,
    override_values: Mapping[ConceptId, float | str],
    policy: RenderPolicy,
    dependency_claims: set[ClaimId],
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
            dependency_claims.add(to_claim_id(claim_id))
        claim_payload = _claim_payload(claim)
        step = {"concept": target_name, "source": "claim"}
        step.update(claim_payload)
        if claim_id:
            step["claim_id"] = _display_claim_id(world, claim_id) or claim_id
        all_steps.append(step)
        result = {
            "status": "determined",
            "source": "claim",
            "claim_id": _display_claim_id(world, claim_id) if claim_id else None,
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
                    dependency_claims.add(to_claim_id(claim_id))
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
                "winning_claim_id": (
                    _display_claim_id(world, rr.winning_claim_id)
                    if rr.winning_claim_id
                    else None
                ),
                "strategy": rr.strategy,
                "reason": rr.reason,
            }

    # Try derived_value with override values
    # Convert override_values to float dict for derivation
    float_overrides: dict[str, float | str | None] = {
        str(key): float(value)
        for key, value in override_values.items()
        if isinstance(value, (int, float))
    }
    dr = query_world.derived_value(concept_id, override_values=float_overrides)

    if dr.status == "derived" and dr.value is not None:
        # Track input dependencies
        inputs_used: dict[ConceptId, dict[str, Any]] = {}
        if dr.input_values:
            for input_cid, input_val in dr.input_values.items():
                normalized_input_cid = to_concept_id(input_cid)
                inputs_used[normalized_input_cid] = _trace_input_source(
                    query_world,
                    world,
                    normalized_input_cid,
                    override_values,
                    policy,
                    dependency_claims,
                )
                inputs_used[normalized_input_cid].setdefault("value", input_val)

        # Record each input as a step in the derivation trace,
        # skipping inputs already recorded (from pre-resolve or overrides)
        seen_concepts = {s["concept"] for s in all_steps}
        for input_cid, input_info in inputs_used.items():
            concept = world.get_concept(input_cid)
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
    chain_bindings = (
        dict(query_world._bindings)
        if isinstance(query_world, _HasBindings)
        else {}
    )
    chain_error: str | None = None
    try:
        chain_result = world.chain_query(
            concept_id,
            strategy=strategy_enum,
            **chain_bindings,
        )
        cr = chain_result.result
        chain_value: float | str | None
        formula: str | None = None
        input_values: dict[ConceptId, float] = {}
        if isinstance(cr, DerivedResult):
            chain_value = cr.value
            formula = cr.formula
            input_values = {
                to_concept_id(input_cid): value
                for input_cid, value in cr.input_values.items()
            }
        else:
            chain_value = cr.claims[0].get("value") if cr.claims else None

        if chain_value is not None and cr.status in ("derived", "determined"):
            # Extract dependencies from chain steps
            for chain_step in chain_result.steps:
                if chain_step.source == "claim":
                    # Find the claim ID for this concept
                    step_vr = query_world.value_of(chain_step.concept_id)
                    if step_vr.claims:
                        dep_id = step_vr.claims[0].get("id")
                        if dep_id and not dep_id.startswith("__override_"):
                            dependency_claims.add(to_claim_id(dep_id))

            # Record chain steps
            for chain_step in chain_result.steps:
                if chain_step.concept_id != concept_id and chain_step.source != "binding":
                    cpt = world.get_concept(chain_step.concept_id)
                    step_name = cpt["canonical_name"] if cpt else chain_step.concept_id
                    all_steps.append({
                        "concept": step_name,
                        "value": chain_step.value,
                        "source": chain_step.source,
                    })

            all_steps.append({
                "concept": target_name,
                "value": chain_value,
                "source": "derived",
                "formula": formula,
            })

            inputs_used = {}
            if input_values:
                for k, v in input_values.items():
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
                "value": chain_value,
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
    query_world: _WorldlineBoundView,
    world: ArtifactStore,
    concept_id: ConceptId,
    override_values: Mapping[ConceptId, float | str],
    policy: RenderPolicy,
    dependency_claims: set[ClaimId],
    seen: set[ConceptId] | None = None,
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
                dependency_claims.add(to_claim_id(claim_id))
            result = {
                "value": claim.get("value"),
                "source": "claim",
            }
            if claim_id:
                result["claim_id"] = _display_claim_id(world, claim_id) or claim_id
            return result

        if vr.status == "conflicted" and policy.strategy is not None:
            rr = resolve(query_world, concept_id, policy=policy, world=world)
            if rr.status == "resolved" and rr.value is not None:
                for claim in rr.claims:
                    claim_id = claim.get("id")
                    if claim_id and not claim_id.startswith("__override_"):
                        dependency_claims.add(to_claim_id(claim_id))
                result = {
                    "value": rr.value,
                    "source": "resolved",
                    "strategy": rr.strategy,
                }
                if rr.winning_claim_id:
                    result["claim_id"] = (
                        _display_claim_id(world, rr.winning_claim_id)
                        or rr.winning_claim_id
                    )
                if rr.reason:
                    result["reason"] = rr.reason
                return result

        float_overrides: dict[str, float | str | None] = {
            str(key): float(val)
            for key, val in override_values.items()
            if isinstance(val, (int, float))
        }
        dr = query_world.derived_value(concept_id, override_values=float_overrides)
        if dr.status == "derived" and dr.value is not None:
            nested_inputs: dict[ConceptId, dict[str, Any]] = {}
            for input_cid, input_val in dr.input_values.items():
                normalized_input_cid = to_concept_id(input_cid)
                nested_inputs[normalized_input_cid] = _trace_input_source(
                    query_world,
                    world,
                    normalized_input_cid,
                    override_values,
                    policy,
                    dependency_claims,
                    seen,
                )
                nested_inputs[normalized_input_cid].setdefault("value", input_val)
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


def _stance_dependency_key(row: StanceRow) -> str:
    """Serialize a stance row into a stable dependency key."""
    return json.dumps(
        row.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _active_stance_dependencies(
    bound: _WorldlineBoundView,
    world: ArtifactStore,
    active_ids: set[ClaimId],
) -> list[str]:
    """Collect active stance dependencies from the graph core when available."""
    active_graph = bound._active_graph if isinstance(bound, _HasActiveGraph) else None
    graph_relation_types = {"rebuts", "undercuts", "undermines", "supersedes", "supports", "explains"}

    if active_graph is not None:
        stance_rows: list[StanceRow] = []
        for edge in active_graph.compiled.relations:
            if edge.relation_type not in graph_relation_types:
                continue
            if to_claim_id(edge.source_id) not in active_ids or to_claim_id(edge.target_id) not in active_ids:
                continue
            stance_rows.append(
                StanceRow.from_mapping(
                    {
                        "claim_id": edge.source_id,
                        "target_claim_id": edge.target_id,
                        "stance_type": edge.relation_type,
                        **dict(edge.attributes),
                    }
                )
            )
        return sorted(_stance_dependency_key(row) for row in stance_rows)

    if isinstance(world, StanceStore) and world.has_table("relation_edge"):
        return sorted(
            _stance_dependency_key(coerce_stance_row(row))
            for row in world.stances_between({str(claim_id) for claim_id in active_ids})
        )
    return []


def _context_dependencies(
    bound: _WorldlineBoundView,
    context_id: ContextId | None,
) -> list[str]:
    """Collect context-scoped inputs that affect a worldline materialization."""
    if not context_id:
        return []

    dependencies = [str(context_id)]
    if isinstance(bound, _HasEnvironment):
        for assumption in bound._environment.effective_assumptions:
            dependencies.append(f"assumption:{assumption}")
    return dependencies
