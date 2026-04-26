"""Shared analyzer pipeline over the canonical active graph."""

from __future__ import annotations

import math
from dataclasses import dataclass

from argumentation.bipolar import (
    BipolarArgumentationFramework,
    cayrol_derived_defeats as _cayrol_derived_defeats_impl,
)
from propstore.conflict_detector import ConflictClass
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.core.graph_relation_types import coerce_graph_relation_type
from propstore.core.id_types import ClaimId, to_claim_id, to_claim_ids, to_concept_id
from propstore.core.graph_types import (
    ActiveWorldGraph,
    ClaimNode,
    CompiledWorldGraph,
    ConflictWitness,
    ProvenanceRecord,
    RelationEdge,
)
from propstore.core.relation_types import (
    ATTACK_TYPES,
    GRAPH_RELATION_TYPES,
    PREFERENCE_SENSITIVE_ATTACK_TYPES,
    SUPPORT_TYPES,
    UNCONDITIONAL_ATTACK_TYPES,
)
from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
from argumentation.dung import ArgumentationFramework
from argumentation.preference import defeat_holds
from argumentation.semantics import extensions as argumentation_extensions

from propstore.preference import claim_strength
from propstore.probabilistic_relations import (
    ClaimGraphRelations,
    ProbabilisticRelation,
    relation_from_row,
    relation_map,
)
from propstore.core.environment import (
    WorldStore,
    CompiledGraphStore,
    ConflictStore,
    Environment,
)
from propstore.core.row_types import (
    ClaimRowInput,
    ConflictRowInput,
    StanceRowInput,
    coerce_claim_row,
    coerce_conflict_row,
    coerce_stance_row,
)
from propstore.world.types import (
    ArgumentationSemantics,
    ReasoningBackend,
    validate_backend_semantics,
)

_ATTACK_TYPES = ATTACK_TYPES
_UNCONDITIONAL_TYPES = UNCONDITIONAL_ATTACK_TYPES
_PREFERENCE_TYPES = PREFERENCE_SENSITIVE_ATTACK_TYPES
_SUPPORT_TYPES = SUPPORT_TYPES
_GRAPH_RELATION_TYPES = GRAPH_RELATION_TYPES
_REAL_CONFLICT_CLASSES = frozenset({"CONFLICT", "OVERLAP", "PARAM_CONFLICT"})


@dataclass(frozen=True)
class SharedAnalyzerInput:
    active_graph: ActiveWorldGraph
    comparison: str
    claims_by_id: dict[str, dict]
    stance_rows: tuple[dict, ...]
    relations: ClaimGraphRelations
    argumentation_framework: ArgumentationFramework
    bipolar_framework: BipolarArgumentationFramework


def _cayrol_derived_defeats(
    defeats: set[tuple[str, str]],
    supports: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    return set(_cayrol_derived_defeats_impl(frozenset(defeats), frozenset(supports)))


def _claim_mapping_from_node(claim: ClaimNode) -> dict:
    data = {
        "id": claim.claim_id,
        "value_concept_id": claim.value_concept_id,
        "type": claim.claim_type,
        "value": claim.scalar_value,
    }
    data.update(dict(claim.attributes))
    if claim.provenance is not None:
        if claim.provenance.paper is not None:
            data.setdefault("source_paper", claim.provenance.paper)
        if claim.provenance.page is not None:
            data.setdefault("provenance_page", claim.provenance.page)
    return data


def _row_identity_from_provenance(provenance: ProvenanceRecord | None) -> tuple[tuple[str, str], ...]:
    if provenance is None:
        return ()
    raw = dict(provenance.extras).get("row_identity")
    if isinstance(raw, tuple):
        return tuple((str(key), str(value)) for key, value in raw)
    return ()


def _stance_row_from_edge(edge: RelationEdge) -> dict:
    data = {
        "claim_id": edge.source_id,
        "target_claim_id": edge.target_id,
        "stance_type": edge.relation_type,
    }
    data.update(dict(edge.attributes))
    if edge.provenance is not None:
        if edge.provenance.source_table is not None:
            data.setdefault("source_table", edge.provenance.source_table)
        if edge.provenance.source_id is not None:
            data.setdefault("source_id", edge.provenance.source_id)
        row_identity = _row_identity_from_provenance(edge.provenance)
        for key, value in row_identity:
            data.setdefault(key, value)
    return data


def _conflict_row_from_witness(conflict: ConflictWitness) -> dict:
    details = dict(conflict.details)
    warning_class = details.get("warning_class") or details.get("conflict_class") or conflict.kind
    return {
        "claim_a_id": conflict.left_claim_id,
        "claim_b_id": conflict.right_claim_id,
        "warning_class": (
            warning_class.value if isinstance(warning_class, ConflictClass) else str(warning_class)
        ),
        **details,
    }


def _claim_node_from_row(row_input: ClaimRowInput | dict) -> ClaimNode:
    row = coerce_claim_row(row_input)
    attributes = tuple(
        (str(key), value)
        for key, value in row.to_dict().items()
        if key not in {"id", "target_concept", "type", "value"}
        and value is not None
    )
    return ClaimNode(
        claim_id=to_claim_id(row.claim_id),
        claim_type=coerce_claim_type(row.claim_type or "unknown") or ClaimType.UNKNOWN,
        value_concept_id=row.value_concept_id,
        scalar_value=row.value,
        attributes=attributes,
    )


def _relation_edge_from_row(row: StanceRowInput) -> RelationEdge:
    stance = coerce_stance_row(row)
    attributes = tuple(
        (str(key), value)
        for key, value in stance.to_dict().items()
        if key not in {"claim_id", "target_claim_id", "stance_type"}
        and value is not None
    )
    return RelationEdge(
        source_id=str(stance.claim_id),
        target_id=str(stance.target_claim_id),
        relation_type=coerce_graph_relation_type(stance.stance_type),
        provenance=ProvenanceRecord(
            source_table="relation_edge",
            source_id=(
                f"{stance.claim_id}->{stance.target_claim_id}:{stance.stance_type}"
            ),
        ),
        attributes=attributes,
    )


def _conflict_witness_from_row(row: ConflictRowInput) -> ConflictWitness:
    conflict = coerce_conflict_row(row)
    warning_class = conflict.warning_class or conflict.conflict_class or "conflict"
    details = tuple(
        (str(key), value)
        for key, value in conflict.to_dict().items()
        if key not in {"claim_a_id", "claim_b_id", "warning_class", "conflict_class"}
        and value is not None
    )
    return ConflictWitness(
        left_claim_id=to_claim_id(conflict.claim_a_id),
        right_claim_id=to_claim_id(conflict.claim_b_id),
        kind=warning_class.value if isinstance(warning_class, ConflictClass) else str(warning_class),
        details=details,
    )


def _minimal_compiled_graph(
    store: WorldStore,
    active_claim_ids: set[str],
) -> CompiledWorldGraph:
    claims = tuple(
        _claim_node_from_row(row)
        for row in store.claims_by_ids(active_claim_ids).values()
    )
    relations = tuple(
        _relation_edge_from_row(row)
        for row in store.stances_between(active_claim_ids)
    )
    conflicts = tuple(
        _conflict_witness_from_row(row)
        for row in (store.conflicts() if isinstance(store, ConflictStore) else ())
        if str(coerce_conflict_row(row).claim_a_id) in active_claim_ids
        and str(coerce_conflict_row(row).claim_b_id) in active_claim_ids
    )
    return CompiledWorldGraph(
        claims=claims,
        relations=relations,
        conflicts=conflicts,
    )


def _active_graph_from_store(
    store: WorldStore,
    active_claim_ids: set[str],
) -> ActiveWorldGraph:
    if isinstance(store, CompiledGraphStore):
        compiled = store.compiled_graph()
    else:
        compiled = _minimal_compiled_graph(store, active_claim_ids)
    all_claim_ids = {claim.claim_id for claim in compiled.claims}
    active_ids = set(to_claim_ids(active_claim_ids))
    return ActiveWorldGraph(
        compiled=compiled,
        environment=Environment(),
        active_claim_ids=tuple(active_ids),
        inactive_claim_ids=tuple(all_claim_ids - active_ids),
    )


def _active_claim_ids(active_graph: ActiveWorldGraph) -> set[str]:
    return {str(claim_id) for claim_id in active_graph.active_claim_ids}


def _graph_claim_rows(active_graph: ActiveWorldGraph) -> dict[str, dict]:
    active_ids = _active_claim_ids(active_graph)
    return {
        claim.claim_id: _claim_mapping_from_node(claim)
        for claim in active_graph.compiled.claims
        if claim.claim_id in active_ids
    }


def _graph_stance_rows(active_graph: ActiveWorldGraph) -> list[dict]:
    active_ids = _active_claim_ids(active_graph)
    return [
        _stance_row_from_edge(edge)
        for edge in active_graph.compiled.relations
        if edge.relation_type in _GRAPH_RELATION_TYPES
        and edge.source_id in active_ids
        and edge.target_id in active_ids
    ]


def _graph_conflict_rows(active_graph: ActiveWorldGraph) -> list[dict]:
    active_ids = _active_claim_ids(active_graph)
    return [
        _conflict_row_from_witness(conflict)
        for conflict in active_graph.compiled.conflicts
        if conflict.left_claim_id in active_ids
        and conflict.right_claim_id in active_ids
    ]


def _collect_claim_graph_relations(
    active_graph: ActiveWorldGraph,
    *,
    comparison: str,
) -> tuple[dict[str, dict], tuple[dict, ...], ClaimGraphRelations]:
    from propstore.praf import NoCalibration, p_relation_from_stance

    active_ids = _active_claim_ids(active_graph)
    claims_by_id = _graph_claim_rows(active_graph)
    stances = list(_graph_stance_rows(active_graph))
    conflicts = _graph_conflict_rows(active_graph)

    existing_stance_pairs = {
        (stance["claim_id"], stance["target_claim_id"])
        for stance in stances
    }
    existing_stance_undirected = {
        frozenset({stance["claim_id"], stance["target_claim_id"]})
        for stance in stances
    }
    existing_attack_undirected = {
        frozenset({stance["claim_id"], stance["target_claim_id"]})
        for stance in stances
        if stance["stance_type"] in _ATTACK_TYPES
    }
    claims_with_stances: set[str] = set()
    for stance in stances:
        claims_with_stances.add(stance["claim_id"])
        claims_with_stances.add(stance["target_claim_id"])

    for conflict in conflicts:
        warning_class = conflict.get("warning_class")
        warning_class_name = (
            warning_class.value if isinstance(warning_class, ConflictClass) else str(warning_class or "")
        )
        if warning_class_name not in _REAL_CONFLICT_CLASSES:
            continue
        left_id = conflict["claim_a_id"]
        right_id = conflict["claim_b_id"]
        pair_key = frozenset({left_id, right_id})
        if pair_key in existing_attack_undirected:
            continue
        if pair_key in existing_stance_undirected:
            for source_id, target_id in ((left_id, right_id), (right_id, left_id)):
                if (source_id, target_id) in existing_stance_pairs:
                    continue
                stances.append(
                    {
                        "claim_id": source_id,
                        "target_claim_id": target_id,
                        "stance_type": "rebuts",
                    }
                )
            continue
        for source_id, target_id in ((left_id, right_id), (right_id, left_id)):
            stances.append(
                {
                    "claim_id": source_id,
                    "target_claim_id": target_id,
                    "stance_type": "rebuts",
                }
            )

    attacks: set[tuple[str, str]] = set()
    direct_defeats: set[tuple[str, str]] = set()
    supports: set[tuple[str, str]] = set()
    attack_relations: list[ProbabilisticRelation] = []
    support_relations: list[ProbabilisticRelation] = []
    direct_defeat_relations: list[ProbabilisticRelation] = []

    for stance in stances:
        source_id = stance["claim_id"]
        target_id = stance["target_claim_id"]
        stance_type = stance["stance_type"]
        if source_id not in claims_by_id or target_id not in claims_by_id:
            continue
        if stance_type in _SUPPORT_TYPES:
            supports.add((source_id, target_id))
            support_opinion = p_relation_from_stance(stance)
            if not isinstance(support_opinion, NoCalibration):
                support_relations.append(
                    relation_from_row(
                        kind="support",
                        source=source_id,
                        target=target_id,
                        opinion=support_opinion,
                        row=stance,
                    )
                )
            continue
        if stance_type not in _ATTACK_TYPES:
            continue

        attacks.add((source_id, target_id))
        attack_opinion = p_relation_from_stance(stance)
        if not isinstance(attack_opinion, NoCalibration):
            attack_relations.append(
                relation_from_row(
                    kind="attack",
                    source=source_id,
                    target=target_id,
                    opinion=attack_opinion,
                    row=stance,
                )
            )

        if stance_type in _UNCONDITIONAL_TYPES:
            direct_defeats.add((source_id, target_id))
            if not isinstance(attack_opinion, NoCalibration):
                direct_defeat_relations.append(
                    relation_from_row(
                        kind="direct_defeat",
                        source=source_id,
                        target=target_id,
                        opinion=attack_opinion,
                        row=stance,
                    )
                )
            continue

        if stance_type in _PREFERENCE_TYPES:
            attacker_strength = claim_strength(claims_by_id[source_id])
            target_strength = claim_strength(claims_by_id[target_id])
            if defeat_holds(
                stance_type,
                list(attacker_strength.dimensions),
                list(target_strength.dimensions),
                comparison,
            ):
                direct_defeats.add((source_id, target_id))
                if not isinstance(attack_opinion, NoCalibration):
                    direct_defeat_relations.append(
                        relation_from_row(
                            kind="direct_defeat",
                            source=source_id,
                            target=target_id,
                            opinion=attack_opinion,
                            row=stance,
                        )
                    )

    relations = ClaimGraphRelations(
        arguments=frozenset(active_ids),
        attacks=frozenset(attacks),
        direct_defeats=frozenset(direct_defeats),
        supports=frozenset(supports),
        attack_relations=tuple(attack_relations),
        support_relations=tuple(support_relations),
        direct_defeat_relations=tuple(direct_defeat_relations),
    )
    return claims_by_id, tuple(stances), relations


def shared_analyzer_input_from_active_graph(
    active_graph: ActiveWorldGraph,
    *,
    comparison: str = "elitist",
) -> SharedAnalyzerInput:
    claims_by_id, stance_rows, relations = _collect_claim_graph_relations(
        active_graph,
        comparison=comparison,
    )
    defeats = set(relations.direct_defeats)
    if relations.supports and relations.direct_defeats:
        defeats |= _cayrol_derived_defeats(set(relations.direct_defeats), set(relations.supports))
    af = ArgumentationFramework(
        arguments=relations.arguments,
        defeats=frozenset(defeats),
        attacks=relations.attacks,
    )
    bipolar = BipolarArgumentationFramework(
        arguments=relations.arguments,
        defeats=relations.direct_defeats,
        supports=relations.supports,
    )
    return SharedAnalyzerInput(
        active_graph=active_graph,
        comparison=comparison,
        claims_by_id=claims_by_id,
        stance_rows=stance_rows,
        relations=relations,
        argumentation_framework=af,
        bipolar_framework=bipolar,
    )


def shared_analyzer_input_from_store(
    store: WorldStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> SharedAnalyzerInput:
    return shared_analyzer_input_from_active_graph(
        _active_graph_from_store(store, active_claim_ids),
        comparison=comparison,
    )


def _extension_results(name: str, extensions: list[frozenset[str]] | tuple[frozenset[str], ...]) -> tuple[ExtensionResult, ...]:
    return tuple(
        ExtensionResult(name=f"{name}:{index}", accepted_claim_ids=tuple(extension))
        for index, extension in enumerate(
            sorted(extensions, key=lambda item: tuple(sorted(item))),
            start=1,
        )
    )


def project_extension_result(
    extensions: tuple[ExtensionResult, ...],
    *,
    target_claim_ids: tuple[str, ...] | list[str] | set[str],
) -> ClaimProjection:
    target_ids = tuple(sorted(dict.fromkeys(str(claim_id) for claim_id in target_claim_ids)))
    if not extensions:
        return ClaimProjection(target_claim_ids=target_ids)

    accepted_sets = [set(extension.accepted_claim_ids) for extension in extensions]
    witness_claim_ids = set().union(*accepted_sets) & set(target_ids)
    survivor_claim_ids = set(accepted_sets[0]) & set(target_ids)
    for accepted in accepted_sets[1:]:
        survivor_claim_ids &= accepted
    return ClaimProjection(
        target_claim_ids=target_ids,
        survivor_claim_ids=tuple(sorted(survivor_claim_ids)),
        witness_claim_ids=tuple(sorted(witness_claim_ids)),
    )


def project_acceptance_result(
    acceptance_probs: dict[str, float],
    *,
    target_claim_ids: tuple[str, ...] | list[str] | set[str],
) -> ClaimProjection:
    target_ids = tuple(sorted(dict.fromkeys(str(claim_id) for claim_id in target_claim_ids)))
    if not target_ids:
        return ClaimProjection(target_claim_ids=target_ids)
    target_probs = {claim_id: acceptance_probs.get(claim_id, 0.0) for claim_id in target_ids}
    best_prob = max(target_probs.values())
    survivor_claim_ids = tuple(
        sorted(
            claim_id
            for claim_id, probability in target_probs.items()
            if math.isclose(probability, best_prob, rel_tol=1e-9)
        )
    )
    return ClaimProjection(
        target_claim_ids=target_ids,
        survivor_claim_ids=survivor_claim_ids,
        witness_claim_ids=target_ids,
    )


def analyze_claim_graph(
    shared: SharedAnalyzerInput,
    *,
    semantics: str = "grounded",
    target_claim_ids: tuple[str, ...] | list[str] | set[str] | None = None,
) -> AnalyzerResult:
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.CLAIM_GRAPH,
        semantics,
    )
    if normalized_semantics in {
        ArgumentationSemantics.D_PREFERRED,
        ArgumentationSemantics.S_PREFERRED,
        ArgumentationSemantics.C_PREFERRED,
        ArgumentationSemantics.BIPOLAR_STABLE,
    }:
        extension_sets = argumentation_extensions(
            shared.bipolar_framework,
            semantics=normalized_semantics.value,
        )
    elif normalized_semantics in {
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.PREFERRED,
        ArgumentationSemantics.STABLE,
    }:
        extension_sets = argumentation_extensions(
            shared.argumentation_framework,
            semantics=normalized_semantics.value,
        )
    else:
        raise ValueError(
            "claim_graph does not support semantics "
            f"'{normalized_semantics.value}'"
        )

    if normalized_semantics == ArgumentationSemantics.GROUNDED:
        extensions = (
            ExtensionResult(
                name=normalized_semantics.value,
                accepted_claim_ids=tuple(extension_sets[0]),
            ),
        )
    else:
        extensions = _extension_results(normalized_semantics.value, extension_sets)

    projection = (
        None
        if target_claim_ids is None
        else project_extension_result(extensions, target_claim_ids=target_claim_ids)
    )
    return AnalyzerResult(
        backend="claim_graph",
        semantics=normalized_semantics.value,
        extensions=extensions,
        projection=projection,
        metadata=(("comparison", shared.comparison),),
    )


def build_praf_from_shared_input(shared: SharedAnalyzerInput):
    from argumentation.probabilistic import ProbabilisticAF
    from propstore.praf import NoCalibration, PropstorePrAF, p_arg_from_claim

    p_args = {}
    omitted_arguments = {}
    for claim_id in shared.argumentation_framework.arguments:
        p_arg = p_arg_from_claim(shared.claims_by_id.get(claim_id, {"claim_id": claim_id}))
        if isinstance(p_arg, NoCalibration):
            omitted_arguments[claim_id] = p_arg
            continue
        p_args[claim_id] = p_arg

    active_args = frozenset(p_args)
    direct_defeat_map = relation_map(shared.relations.direct_defeat_relations)
    attack_map = relation_map(shared.relations.attack_relations)
    support_map = relation_map(shared.relations.support_relations)

    missing_relation_edges = (
        set(shared.relations.attacks - frozenset(attack_map))
        | set(shared.relations.direct_defeats - frozenset(direct_defeat_map))
        | set(shared.relations.supports - frozenset(support_map))
    )
    omitted_relations = {
        edge: NoCalibration(
            reason="missing_relation_calibration",
            missing_fields=(
                "opinion_belief",
                "opinion_disbelief",
                "opinion_uncertainty",
                "confidence",
            ),
        )
        for edge in missing_relation_edges
    }

    def calibrated_edge(edge: tuple[str, str]) -> bool:
        return (
            edge[0] in active_args
            and edge[1] in active_args
            and edge not in missing_relation_edges
        )

    defeats = frozenset(
        edge for edge in shared.argumentation_framework.defeats
        if calibrated_edge(edge)
    )
    attacks = (
        None
        if shared.argumentation_framework.attacks is None
        else frozenset(edge for edge in shared.argumentation_framework.attacks if calibrated_edge(edge))
    )
    supports = frozenset(edge for edge in shared.relations.supports if calibrated_edge(edge))
    base_defeats = frozenset(edge for edge in shared.relations.direct_defeats if calibrated_edge(edge))
    framework = ArgumentationFramework(
        arguments=active_args,
        defeats=defeats,
        attacks=attacks,
    )

    def keep_relation(relation):
        return relation.source in active_args and relation.target in active_args and relation.edge not in missing_relation_edges

    p_defeats = {edge: opinion for edge, opinion in direct_defeat_map.items() if calibrated_edge(edge)}
    p_attacks = {edge: opinion for edge, opinion in attack_map.items() if calibrated_edge(edge)}
    p_supports = {edge: opinion for edge, opinion in support_map.items() if calibrated_edge(edge)}
    kernel = ProbabilisticAF(
        framework=framework,
        p_args={arg: opinion.expectation() for arg, opinion in p_args.items()},
        p_defeats={edge: opinion.expectation() for edge, opinion in p_defeats.items()},
        p_attacks={edge: opinion.expectation() for edge, opinion in p_attacks.items()},
        supports=supports,
        p_supports={edge: opinion.expectation() for edge, opinion in p_supports.items()},
        base_defeats=base_defeats,
    )
    return PropstorePrAF(
        kernel=kernel,
        p_args=p_args,
        p_defeats=p_defeats,
        p_attacks=p_attacks,
        supports=supports,
        p_supports=p_supports,
        base_defeats=base_defeats,
        attack_relations=tuple(relation for relation in shared.relations.attack_relations if keep_relation(relation)),
        support_relations=tuple(relation for relation in shared.relations.support_relations if keep_relation(relation)),
        direct_defeat_relations=tuple(
            relation for relation in shared.relations.direct_defeat_relations if keep_relation(relation)
        ),
        omitted_arguments=omitted_arguments,
        omitted_relations=omitted_relations,
    )


def analyze_praf(
    shared: SharedAnalyzerInput,
    *,
    semantics: str = "grounded",
    strategy: str = "auto",
    query_kind: str = "argument_acceptance",
    inference_mode: str | None = "credulous",
    queried_set: tuple[str, ...] | list[str] | set[str] | None = None,
    mc_epsilon: float = 0.01,
    mc_confidence: float = 0.95,
    treewidth_cutoff: int = 12,
    rng_seed: int | None = None,
    target_claim_ids: tuple[str, ...] | list[str] | set[str] | None = None,
) -> AnalyzerResult:
    from argumentation.probabilistic import compute_probabilistic_acceptance

    praf = build_praf_from_shared_input(shared)
    praf_result = compute_probabilistic_acceptance(
        praf.kernel,
        semantics=semantics,
        strategy=strategy,
        query_kind=query_kind,
        inference_mode=inference_mode,
        queried_set=queried_set,
        mc_epsilon=mc_epsilon,
        mc_confidence=mc_confidence,
        treewidth_cutoff=treewidth_cutoff,
        rng_seed=rng_seed,
    )
    projection = (
        None
        if target_claim_ids is None or praf_result.acceptance_probs is None
        else project_acceptance_result(
            praf_result.acceptance_probs,
            target_claim_ids=target_claim_ids,
        )
    )
    return AnalyzerResult(
        backend="praf",
        semantics=semantics,
        projection=projection,
        metadata=(
            ("query_kind", praf_result.query_kind),
            ("inference_mode", praf_result.inference_mode),
            ("queried_set", praf_result.queried_set),
            ("acceptance_probs", praf_result.acceptance_probs),
            ("extension_probability", praf_result.extension_probability),
            ("strategy_used", praf_result.strategy_used),
            ("strategy_requested", praf_result.strategy_requested),
            ("downgraded_from", praf_result.downgraded_from),
            ("samples", praf_result.samples),
            ("confidence_interval_half", praf_result.confidence_interval_half),
            ("comparison", shared.comparison),
        ),
    )
