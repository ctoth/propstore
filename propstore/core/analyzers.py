"""Shared analyzer pipeline over the canonical active graph."""

from __future__ import annotations

import math
from dataclasses import dataclass

from propstore.bipolar import (
    BipolarArgumentationFramework,
    c_preferred_extensions,
    cayrol_derived_defeats as _cayrol_derived_defeats_impl,
    d_preferred_extensions,
    s_preferred_extensions,
    stable_extensions as bipolar_stable_extensions,
)
from propstore.core.graph_types import (
    ActiveWorldGraph,
    ClaimNode,
    CompiledWorldGraph,
    ConflictWitness,
    ProvenanceRecord,
    RelationEdge,
)
from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
from propstore.dung import (
    ArgumentationFramework,
    grounded_extension,
    hybrid_grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.preference import claim_strength, defeat_holds
from propstore.probabilistic_relations import (
    ClaimGraphRelations,
    ProbabilisticRelation,
    relation_from_row,
    relation_map,
)
from propstore.core.environment import (
    ArtifactStore,
    CompiledGraphStore,
    ConflictStore,
    Environment,
)
from propstore.world.types import (
    ArgumentationSemantics,
    ReasoningBackend,
    validate_backend_semantics,
)

_ATTACK_TYPES = frozenset({"rebuts", "undercuts", "undermines", "supersedes"})
_UNCONDITIONAL_TYPES = frozenset({"undercuts", "supersedes"})
_PREFERENCE_TYPES = frozenset({"rebuts", "undermines"})
_SUPPORT_TYPES = frozenset({"supports", "explains"})
_NON_ATTACK_TYPES = frozenset({"supports", "explains", "none"})
_GRAPH_RELATION_TYPES = _ATTACK_TYPES | _SUPPORT_TYPES
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
        "concept_id": claim.concept_id,
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
        "warning_class": str(warning_class),
        **details,
    }


def _claim_node_from_row(row: dict) -> ClaimNode:
    attributes = tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in {"id", "concept_id", "target_concept", "type", "value"}
        and value is not None
    )
    return ClaimNode(
        claim_id=str(row["id"]),
        concept_id=str(row.get("concept_id") or row.get("target_concept") or ""),
        claim_type=str(row.get("type") or "unknown"),
        scalar_value=row.get("value"),
        attributes=attributes,
    )


def _relation_edge_from_row(row: dict) -> RelationEdge:
    attributes = tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in {"claim_id", "target_claim_id", "stance_type"}
        and value is not None
    )
    return RelationEdge(
        source_id=str(row["claim_id"]),
        target_id=str(row["target_claim_id"]),
        relation_type=str(row["stance_type"]),
        provenance=ProvenanceRecord(
            source_table="relation_edge",
            source_id=(
                f"{row['claim_id']}->{row['target_claim_id']}:{row['stance_type']}"
            ),
        ),
        attributes=attributes,
    )


def _conflict_witness_from_row(row: dict) -> ConflictWitness:
    warning_class = row.get("warning_class") or row.get("conflict_class") or "conflict"
    details = tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in {"claim_a_id", "claim_b_id", "warning_class", "conflict_class"}
        and value is not None
    )
    return ConflictWitness(
        left_claim_id=str(row["claim_a_id"]),
        right_claim_id=str(row["claim_b_id"]),
        kind=str(warning_class),
        details=details,
    )


def _minimal_compiled_graph(
    store: ArtifactStore,
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
        if row.get("claim_a_id") in active_claim_ids
        and row.get("claim_b_id") in active_claim_ids
    )
    return CompiledWorldGraph(
        claims=claims,
        relations=relations,
        conflicts=conflicts,
    )


def _active_graph_from_store(
    store: ArtifactStore,
    active_claim_ids: set[str],
) -> ActiveWorldGraph:
    if isinstance(store, CompiledGraphStore):
        compiled = store.compiled_graph()
    else:
        compiled = _minimal_compiled_graph(store, active_claim_ids)
    all_claim_ids = {claim.claim_id for claim in compiled.claims}
    return ActiveWorldGraph(
        compiled=compiled,
        environment=Environment(),
        active_claim_ids=tuple(active_claim_ids),
        inactive_claim_ids=tuple(all_claim_ids - set(active_claim_ids)),
    )


def _active_claim_ids(active_graph: ActiveWorldGraph) -> set[str]:
    return set(active_graph.active_claim_ids)


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
    include_conflict_stances: bool = False,
) -> tuple[dict[str, dict], tuple[dict, ...], ClaimGraphRelations]:
    from propstore.praf import p_relation_from_stance

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
        warning_class = str(conflict.get("warning_class", ""))
        if warning_class not in _REAL_CONFLICT_CLASSES:
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
                        "confidence": 0.5,
                        "opinion_belief": 0.0,
                        "opinion_disbelief": 0.0,
                        "opinion_uncertainty": 1.0,
                        "opinion_base_rate": 0.5,
                    }
                )
            continue
        if not include_conflict_stances and (
            left_id in claims_with_stances or right_id in claims_with_stances
        ):
            continue
        for source_id, target_id in ((left_id, right_id), (right_id, left_id)):
            stances.append(
                {
                    "claim_id": source_id,
                    "target_claim_id": target_id,
                    "stance_type": "rebuts",
                    "confidence": 0.5,
                    "opinion_belief": 0.0,
                    "opinion_disbelief": 0.0,
                    "opinion_uncertainty": 1.0,
                    "opinion_base_rate": 0.5,
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
            support_relations.append(
                relation_from_row(
                    kind="support",
                    source=source_id,
                    target=target_id,
                    opinion=p_relation_from_stance(stance),
                    row=stance,
                )
            )
            continue
        if stance_type not in _ATTACK_TYPES:
            continue

        attacks.add((source_id, target_id))
        attack_opinion = p_relation_from_stance(stance)
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
            if defeat_holds(stance_type, attacker_strength, target_strength, comparison):
                direct_defeats.add((source_id, target_id))
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
    include_conflict_stances: bool = False,
) -> SharedAnalyzerInput:
    claims_by_id, stance_rows, relations = _collect_claim_graph_relations(
        active_graph,
        comparison=comparison,
        include_conflict_stances=include_conflict_stances,
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
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
    include_conflict_stances: bool = False,
) -> SharedAnalyzerInput:
    return shared_analyzer_input_from_active_graph(
        _active_graph_from_store(store, active_claim_ids),
        comparison=comparison,
        include_conflict_stances=include_conflict_stances,
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
        hybrid_graph=(
            shared.argumentation_framework.attacks is not None
            and shared.argumentation_framework.attacks != shared.argumentation_framework.defeats
        ),
    )
    if normalized_semantics == ArgumentationSemantics.GROUNDED:
        extensions = (
            ExtensionResult(
                name=normalized_semantics.value,
                accepted_claim_ids=tuple(
                    grounded_extension(shared.argumentation_framework)
                ),
            ),
        )
    elif normalized_semantics in {
        ArgumentationSemantics.LEGACY_GROUNDED,
        ArgumentationSemantics.HYBRID_GROUNDED,
        ArgumentationSemantics.BIPOLAR_GROUNDED,
    }:
        extensions = (
            ExtensionResult(
                name=normalized_semantics.value,
                accepted_claim_ids=tuple(
                    hybrid_grounded_extension(shared.argumentation_framework)
                ),
            ),
        )
    elif normalized_semantics == ArgumentationSemantics.D_PREFERRED:
        extensions = _extension_results(
            normalized_semantics.value,
            [frozenset(ext) for ext in d_preferred_extensions(shared.bipolar_framework)],
        )
    elif normalized_semantics == ArgumentationSemantics.S_PREFERRED:
        extensions = _extension_results(
            normalized_semantics.value,
            [frozenset(ext) for ext in s_preferred_extensions(shared.bipolar_framework)],
        )
    elif normalized_semantics == ArgumentationSemantics.C_PREFERRED:
        extensions = _extension_results(
            normalized_semantics.value,
            [frozenset(ext) for ext in c_preferred_extensions(shared.bipolar_framework)],
        )
    elif normalized_semantics == ArgumentationSemantics.BIPOLAR_STABLE:
        extensions = _extension_results(
            normalized_semantics.value,
            [frozenset(ext) for ext in bipolar_stable_extensions(shared.bipolar_framework)],
        )
    elif normalized_semantics == ArgumentationSemantics.PREFERRED:
        extensions = _extension_results(
            normalized_semantics.value,
            [frozenset(ext) for ext in preferred_extensions(shared.argumentation_framework)],
        )
    elif normalized_semantics == ArgumentationSemantics.STABLE:
        extensions = _extension_results(
            normalized_semantics.value,
            [frozenset(ext) for ext in stable_extensions(shared.argumentation_framework)],
        )
    else:
        raise ValueError(
            "claim_graph does not support semantics "
            f"'{normalized_semantics.value}'"
        )

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
    from propstore.praf import ProbabilisticAF, p_arg_from_claim

    p_args = {
        claim_id: p_arg_from_claim(shared.claims_by_id.get(claim_id, {"claim_id": claim_id}))
        for claim_id in shared.argumentation_framework.arguments
    }
    return ProbabilisticAF(
        framework=shared.argumentation_framework,
        p_args=p_args,
        p_defeats=relation_map(shared.relations.direct_defeat_relations),
        p_attacks=relation_map(shared.relations.attack_relations),
        supports=shared.relations.supports,
        p_supports=relation_map(shared.relations.support_relations),
        base_defeats=shared.relations.direct_defeats,
        attack_relations=shared.relations.attack_relations,
        support_relations=shared.relations.support_relations,
        direct_defeat_relations=shared.relations.direct_defeat_relations,
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
    from propstore.praf import compute_praf_acceptance

    praf = build_praf_from_shared_input(shared)
    praf_result = compute_praf_acceptance(
        praf,
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
