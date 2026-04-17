"""Typed fragility contributors by intervention family."""

from __future__ import annotations

import json
import warnings
from collections.abc import Mapping, Sequence

from propstore.aspic import conc, top_rule
from propstore.aspic_bridge.build import build_bridge_csaf, compile_bridge_context
from propstore.aspic_bridge.extract import _extract_justifications, _extract_stance_rows
from propstore.aspic_bridge.grounding import _decode_grounded_predicate, grounded_rules_to_rules
from propstore.core.row_types import coerce_parameterization_row
from propstore.fragility_scoring import FragilityWarning, score_conflict, weighted_epistemic_score
from propstore.fragility_types import (
    AssumptionTarget,
    BridgeUndercutTarget,
    ConflictTarget,
    FragilityWorld,
    GroundFactTarget,
    GroundedRuleTarget,
    InterventionFamily,
    InterventionKind,
    InterventionProvenance,
    InterventionTarget,
    MissingMeasurementTarget,
    RankedIntervention,
    RankingPolicy,
)
from propstore.world.types import QueryableAssumption, ValueStatus, coerce_queryable_assumptions


def _typed_scalar_key(value: object) -> dict[str, object]:
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "str", "value": str(value)}


def _typed_row_key(row: Sequence[object]) -> str:
    return json.dumps(
        [_typed_scalar_key(item) for item in row],
        sort_keys=True,
        separators=(",", ":"),
    )


def _in_extension(current_status: object) -> bool:
    try:
        normalized = ValueStatus(str(current_status))
    except ValueError as exc:
        raise ValueError(f"Unknown value status for extension membership: {current_status!r}") from exc
    return normalized in {
        ValueStatus.DETERMINED,
        ValueStatus.DERIVED,
        ValueStatus.RESOLVED,
    }


def _parameterizations_to_queryables(
    bound: FragilityWorld,
) -> tuple[QueryableAssumption, ...]:
    queryables: list[str | QueryableAssumption] = []
    for parameterization_input in bound._store.all_parameterizations():
        parameterization = coerce_parameterization_row(parameterization_input)
        if not parameterization.conditions_cel:
            continue
        decoded = json.loads(parameterization.conditions_cel)
        if isinstance(decoded, str):
            queryables.append(decoded)
            continue
        for item in decoded:
            if isinstance(item, str):
                queryables.append(item)
    return coerce_queryable_assumptions(queryables)


def derive_scored_concepts(bound: FragilityWorld) -> list[str]:
    try:
        concepts: set[str] = {
            str(coerce_parameterization_row(row).output_concept_id)
            for row in bound._store.all_parameterizations()
        }
        for claim in bound.active_claims():
            if hasattr(claim, "concept_id"):
                concepts.add(str(claim.concept_id))
            elif isinstance(claim, Mapping) and "concept_id" in claim:
                concepts.add(str(claim["concept_id"]))
        return sorted(concepts)
    except Exception as exc:
        warnings.warn(
            f"Fragility concept discovery failed: {exc}",
            FragilityWarning,
            stacklevel=2,
        )
        return []


def collect_assumption_interventions(
    bound: FragilityWorld,
    concept_ids: Sequence[str],
    queryables: Sequence[QueryableAssumption] | None,
    *,
    atms_limit: int,
) -> tuple[RankedIntervention, ...]:
    normalized_queryables = (
        coerce_queryable_assumptions(queryables)
        if queryables is not None
        else _parameterizations_to_queryables(bound)
    )
    if not normalized_queryables:
        return ()

    engine = bound.atms_engine()
    contributions: dict[str, dict[str, object]] = {}

    for concept_id in concept_ids:
        try:
            stability = engine.concept_stability(concept_id, normalized_queryables, limit=atms_limit)
        except Exception as exc:
            warnings.warn(
                f"ATMS fragility failed for {concept_id}: {exc}",
                FragilityWarning,
                stacklevel=2,
            )
            continue

        witnesses = stability.get("witnesses", [])
        consistent_future_count = int(stability.get("consistent_future_count", 0))
        concept_score = weighted_epistemic_score(
            witnesses,
            consistent_future_count,
            current_in_extension=_in_extension(stability.get("current_status")),
        )
        for witness in witnesses:
            for qcel in witness.get("queryable_cels", []):
                qcel_text = str(qcel)
                queryable = next(
                    (candidate for candidate in normalized_queryables if candidate.cel == qcel_text),
                    QueryableAssumption.from_cel(qcel_text),
                )
                entry = contributions.setdefault(
                    str(queryable.assumption_id),
                    {
                        "queryable": queryable,
                        "concepts": set(),
                        "witness_count": 0,
                        "consistent_future_count": consistent_future_count,
                        "max_score": 0.0,
                    },
                )
                entry["concepts"].add(str(concept_id))
                entry["witness_count"] = int(entry["witness_count"]) + 1
                entry["consistent_future_count"] = max(
                    int(entry["consistent_future_count"]),
                    consistent_future_count,
                )
                entry["max_score"] = max(float(entry["max_score"]), concept_score)

    ranked: list[RankedIntervention] = []
    for queryable_id, entry in sorted(contributions.items()):
        queryable = entry["queryable"]
        assert isinstance(queryable, QueryableAssumption)
        concepts = tuple(sorted(str(item) for item in entry["concepts"]))
        local_fragility = float(entry["max_score"])
        target = InterventionTarget(
            intervention_id=f"assumption:{queryable_id}",
            kind=InterventionKind.ASSUMPTION,
            family=InterventionFamily.ATMS,
            subject_id=None,
            description=f"Resolve assumption {queryable.cel}",
            cost_tier=1,
            provenance=InterventionProvenance(
                family=InterventionFamily.ATMS,
                source_ids=(str(queryable.assumption_id),),
                subject_concept_ids=concepts,
            ),
            payload=AssumptionTarget(
                queryable_id=str(queryable.assumption_id),
                cel=queryable.cel,
                stabilizes_concepts=concepts,
                witness_count=int(entry["witness_count"]),
                consistent_future_count=int(entry["consistent_future_count"]),
            ),
        )
        ranked.append(
            RankedIntervention(
                target=target,
                local_fragility=local_fragility,
                roi=local_fragility / target.cost_tier,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation=f"max ATMS flip score across {len(concepts)} concepts",
            )
        )
    return tuple(ranked)


def collect_missing_measurement_interventions(
    bound: FragilityWorld,
    concept_ids: Sequence[str],
) -> tuple[RankedIntervention, ...]:
    downstream_by_input: dict[str, set[str]] = {}
    parameterizations_by_input: dict[str, set[str]] = {}

    for parameterization_input in bound._store.all_parameterizations():
        parameterization = coerce_parameterization_row(parameterization_input)
        output_concept_id = str(parameterization.output_concept_id)
        if concept_ids and output_concept_id not in set(concept_ids):
            continue
        decoded = json.loads(parameterization.concept_ids)
        if not isinstance(decoded, list):
            continue
        for input_id in decoded:
            if not isinstance(input_id, str):
                continue
            if bound.active_claims(input_id):
                continue
            downstream_by_input.setdefault(input_id, set()).add(output_concept_id)
            parameterizations_by_input.setdefault(input_id, set()).add(output_concept_id)

    if not downstream_by_input:
        return ()

    max_downstream = max(len(subjects) for subjects in downstream_by_input.values())
    ranked: list[RankedIntervention] = []
    for concept_id, subjects in sorted(downstream_by_input.items()):
        local_fragility = len(subjects) / max_downstream
        target = InterventionTarget(
            intervention_id=f"missing_measurement:{concept_id}",
            kind=InterventionKind.MISSING_MEASUREMENT,
            family=InterventionFamily.DISCOVERY,
            subject_id=concept_id,
            description=f"Measure {concept_id}",
            cost_tier=3,
            provenance=InterventionProvenance(
                family=InterventionFamily.DISCOVERY,
                source_ids=tuple(sorted(parameterizations_by_input[concept_id])),
                subject_concept_ids=tuple(sorted(subjects)),
            ),
            payload=MissingMeasurementTarget(
                concept_id=concept_id,
                discovered_from_parameterizations=tuple(sorted(parameterizations_by_input[concept_id])),
                downstream_subjects=tuple(sorted(subjects)),
            ),
        )
        ranked.append(
            RankedIntervention(
                target=target,
                local_fragility=local_fragility,
                roi=local_fragility / target.cost_tier,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation=f"used by {len(subjects)} downstream subjects",
            )
        )
    return tuple(ranked)


def collect_conflict_interventions(
    bound: FragilityWorld,
    concept_ids: Sequence[str],
) -> tuple[RankedIntervention, ...]:
    active_graph = getattr(bound, "_active_graph", None)
    if active_graph is None:
        return ()

    from propstore.core.analyzers import shared_analyzer_input_from_active_graph

    try:
        framework = shared_analyzer_input_from_active_graph(active_graph).argumentation_framework
    except Exception as exc:
        warnings.warn(
            f"Conflict fragility failed to build framework: {exc}",
            FragilityWarning,
            stacklevel=2,
        )
        return ()

    aggregated: dict[tuple[str, str], dict[str, object]] = {}
    for concept_id in concept_ids:
        for conflict in bound.conflicts(concept_id):
            claim_a_id = str(conflict.claim_a_id)
            claim_b_id = str(conflict.claim_b_id)
            pair = (min(claim_a_id, claim_b_id), max(claim_a_id, claim_b_id))
            entry = aggregated.setdefault(pair, {"concepts": set(), "max_score": 0.0})
            entry["concepts"].add(str(conflict.concept_id or concept_id))
            entry["max_score"] = max(
                float(entry["max_score"]),
                score_conflict(framework, claim_a_id, claim_b_id),
            )

    ranked: list[RankedIntervention] = []
    for pair, entry in sorted(aggregated.items()):
        concepts = tuple(sorted(str(item) for item in entry["concepts"]))
        target = InterventionTarget(
            intervention_id=f"conflict:{pair[0]}:{pair[1]}",
            kind=InterventionKind.CONFLICT,
            family=InterventionFamily.CONFLICT,
            subject_id=(concepts[0] if len(concepts) == 1 else None),
            description=f"Resolve conflict {pair[0]} vs {pair[1]}",
            cost_tier=2,
            provenance=InterventionProvenance(
                family=InterventionFamily.CONFLICT,
                source_ids=pair,
                subject_concept_ids=concepts,
            ),
            payload=ConflictTarget(
                claim_a_id=pair[0],
                claim_b_id=pair[1],
                affected_concept_ids=concepts,
            ),
        )
        local_fragility = float(entry["max_score"])
        ranked.append(
            RankedIntervention(
                target=target,
                local_fragility=local_fragility,
                roi=local_fragility / target.cost_tier,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation="max grounded-extension delta for the canonical pair",
            )
        )
    return tuple(ranked)


_SECTION_FRAGILITY = {
    "definitely": 0.25,
    "defeasibly": 0.75,
    "not_defeasibly": 0.5,
    "undecided": 1.0,
}


def collect_ground_fact_interventions(bundle) -> tuple[RankedIntervention, ...]:
    _strict_rules, defeasible_rules, _literals = grounded_rules_to_rules(bundle, {})
    dependency_counts: dict[tuple[str, bool, tuple[object, ...]], int] = {}
    for rule in defeasible_rules:
        if "->" in (rule.name or ""):
            continue
        for antecedent in rule.antecedents:
            dependency_key = (
                antecedent.atom.predicate,
                antecedent.negated,
                tuple(antecedent.atom.arguments),
            )
            dependency_counts[dependency_key] = dependency_counts.get(dependency_key, 0) + 1

    ranked: list[RankedIntervention] = []
    for section_name, section in sorted(bundle.sections.items()):
        for predicate_id, rows in sorted(section.items()):
            predicate_name, negated = _decode_grounded_predicate(predicate_id)
            for row in sorted(rows):
                row_key = _typed_row_key(row)
                dependency_count = dependency_counts.get(
                    (predicate_name, negated, tuple(row)),
                    0,
                )
                local_fragility = min(
                    1.0,
                    _SECTION_FRAGILITY.get(section_name, 0.5) + (0.1 * min(dependency_count, 3)),
                )
                target = InterventionTarget(
                    intervention_id=f"ground_fact:{section_name}:{predicate_id}:{row_key}",
                    kind=InterventionKind.GROUND_FACT,
                    family=InterventionFamily.GROUNDING,
                    subject_id=None,
                    description=f"Inspect grounded fact {predicate_id}{tuple(row)} in {section_name}",
                    cost_tier=2,
                    provenance=InterventionProvenance(
                        family=InterventionFamily.GROUNDING,
                        source_ids=(predicate_id, row_key),
                        subject_concept_ids=(),
                    ),
                    payload=GroundFactTarget(
                        section=section_name,
                        predicate_id=predicate_id,
                        row=tuple(row),
                    ),
                )
                ranked.append(
                    RankedIntervention(
                        target=target,
                        local_fragility=local_fragility,
                        roi=local_fragility / target.cost_tier,
                        ranking_policy=RankingPolicy.HEURISTIC_ROI,
                        score_explanation=(
                            f"section={section_name}; antecedent_dependency_count={dependency_count}"
                        ),
                    )
                )
    return tuple(ranked)


def collect_grounded_rule_interventions(bundle) -> tuple[RankedIntervention, ...]:
    strict_rules, defeasible_rules, _literals = grounded_rules_to_rules(bundle, {})
    del strict_rules
    undercut_counts: dict[str, int] = {}
    for rule in defeasible_rules:
        if rule.name is None or "->" not in rule.name:
            continue
        _defeater, _separator, target_rule_name = rule.name.partition("->")
        undercut_counts[target_rule_name] = undercut_counts.get(target_rule_name, 0) + 1

    ranked: list[RankedIntervention] = []
    for rule in sorted(defeasible_rules, key=lambda candidate: candidate.name or ""):
        if rule.name is None or "->" in rule.name:
            continue
        _base, _, substitution_key = rule.name.partition("#")
        undercut_count = undercut_counts.get(rule.name, 0)
        local_fragility = min(
            1.0,
            0.3 + (0.1 * len(rule.antecedents)) + (0.25 * min(undercut_count, 2)),
        )
        head_literal = repr(rule.consequent)
        target = InterventionTarget(
            intervention_id=f"grounded_rule:{rule.name}",
            kind=InterventionKind.GROUNDED_RULE,
            family=InterventionFamily.GROUNDING,
            subject_id=None,
            description=f"Inspect grounded rule {rule.name}",
            cost_tier=2,
            provenance=InterventionProvenance(
                family=InterventionFamily.GROUNDING,
                source_ids=(rule.name,),
                subject_concept_ids=(),
            ),
            payload=GroundedRuleTarget(
                rule_name=rule.name,
                substitution_key=substitution_key,
                head_literal=head_literal,
            ),
        )
        ranked.append(
            RankedIntervention(
                target=target,
                local_fragility=local_fragility,
                roi=local_fragility / target.cost_tier,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation=(
                    f"antecedent_count={len(rule.antecedents)}; undercut_count={undercut_count}"
                ),
            )
        )
    return tuple(ranked)


def collect_bridge_undercut_interventions(
    bundle,
    active_claims,
    justifications,
    stance_rows,
) -> tuple[RankedIntervention, ...]:
    compiled = compile_bridge_context(
        active_claims,
        justifications,
        stance_rows,
        bundle=bundle,
    )
    csaf = build_bridge_csaf(
        active_claims,
        justifications,
        stance_rows,
        bundle=bundle,
    )
    attack_counts: dict[str, int] = {}
    defeat_counts: dict[str, int] = {}
    for attack in csaf.attacks:
        attacker_top = top_rule(attack.attacker)
        if attacker_top is None or attacker_top.name is None or "->" not in attacker_top.name:
            continue
        attack_counts[attacker_top.name] = attack_counts.get(attacker_top.name, 0) + 1
    for attacker, _target in csaf.defeats:
        attacker_top = top_rule(attacker)
        if attacker_top is None or attacker_top.name is None or "->" not in attacker_top.name:
            continue
        defeat_counts[attacker_top.name] = defeat_counts.get(attacker_top.name, 0) + 1

    ranked: list[RankedIntervention] = []
    for rule in sorted(compiled.system.defeasible_rules, key=lambda candidate: candidate.name or ""):
        if rule.name is None or "->" not in rule.name or not rule.consequent.negated:
            continue
        defeater_name, _, target_rule_name = rule.name.partition("->")
        undercut_literal_key = str(rule.consequent.atom.predicate)
        attack_count = attack_counts.get(rule.name, 0)
        defeat_count = defeat_counts.get(rule.name, 0)
        local_fragility = min(1.0, 0.3 + (0.25 * min(attack_count, 2)) + (0.35 * min(defeat_count, 2)))
        target = InterventionTarget(
            intervention_id=f"bridge_undercut:{rule.name}",
            kind=InterventionKind.BRIDGE_UNDERCUT,
            family=InterventionFamily.BRIDGE,
            subject_id=None,
            description=f"Inspect bridge undercut {rule.name}",
            cost_tier=2,
            provenance=InterventionProvenance(
                family=InterventionFamily.BRIDGE,
                source_ids=(rule.name,),
                subject_concept_ids=(),
            ),
            payload=BridgeUndercutTarget(
                defeater_rule_name=defeater_name,
                target_rule_name=target_rule_name,
                undercut_literal_key=undercut_literal_key,
            ),
        )
        ranked.append(
            RankedIntervention(
                target=target,
                local_fragility=local_fragility,
                roi=local_fragility / target.cost_tier,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation=f"attack_count={attack_count}; defeat_count={defeat_count}",
            )
        )
    return tuple(ranked)


def build_bound_bridge_inputs(bound: FragilityWorld):
    active_claims = tuple(bound.active_claims())
    active_by_id = {str(claim.claim_id): claim for claim in active_claims}
    active_graph = getattr(bound, "_active_graph", None)
    stance_rows = _extract_stance_rows(bound._store, active_by_id, active_graph=active_graph)
    justifications = _extract_justifications(
        active_by_id,
        stance_rows,
        active_graph=active_graph,
    )
    return active_claims, justifications, stance_rows
