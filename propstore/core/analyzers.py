"""Shared analyzer pipeline over typed semantic owners.

This is the AF / BAF / PrAF assembly over canonical ``Claim`` and ``Stance``
charters, ``ConflictRecord`` values, and an active-id set. The relation math
(attacks / supports / direct-defeats, the invented ``rebuts`` edges from real
conflict classes, the preference-sensitive defeat test, the Cayrol-derived
defeats) and the analyzer entry points read those owners plus the
argumentation package's own framework types — never an ATMS environment or a
store. The module is deliberately store-free.

Every argument and relation enters the framework regardless of calibration
(CLAUDE.md non-commitment): uncalibrated argument/relation existence is carried
as an honest vacuous opinion with its omission recorded, never dropped, and the
filtering is a render-time concern over the resulting framework.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from argumentation.core.bipolar import (
    BipolarArgumentationFramework,
    cayrol_derived_defeats as _cayrol_derived_defeats_impl,
)
from argumentation.core.dung import ArgumentationFramework
from argumentation.core.preference import defeat_holds
from argumentation.semantics import extensions as argumentation_extensions
from argumentation.structured.aspic.aspic import (
    ArgumentationSystem,
    KnowledgeBase,
    PreferenceConfig,
)

from propstore.core.environment import (
    CompiledGraphStore,
    Environment,
    WorldStore,
)
from propstore.core.graph_types import (
    ActiveWorldGraph,
    CompiledWorldGraph,
)
from propstore.core.id_types import to_claim_ids
from propstore.core.reasoning import (
    ArgumentationSemantics,
    ReasoningBackend,
    validate_backend_semantics,
)
from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
from propstore.opinion_provenance import OpinionWithProvenance, opinion_or_vacuous
from propstore.praf import (
    NoCalibration,
    PropstorePrAF,
    p_arg_from_claim,
    p_relation_from_stance,
)
from propstore.preference import claim_strength
from propstore.probabilistic_relations import (
    ClaimGraphRelations,
    ProbabilisticRelation,
    relation_from_stance,
)
from propstore.conflict_detector.models import ConflictRecord
from propstore.families.claims import Claim
from propstore.families.relations import Stance
from propstore.stances import (
    ATTACK_TYPES,
    PREFERENCE_SENSITIVE_ATTACK_TYPES,
    SUPPORT_TYPES,
    UNCONDITIONAL_ATTACK_TYPES,
)

_ATTACK_TYPES = ATTACK_TYPES
_UNCONDITIONAL_TYPES = UNCONDITIONAL_ATTACK_TYPES
_PREFERENCE_TYPES = PREFERENCE_SENSITIVE_ATTACK_TYPES
_SUPPORT_TYPES = SUPPORT_TYPES
_REAL_CONFLICT_CLASSES = frozenset({"CONFLICT", "OVERLAP", "PARAM_CONFLICT"})

@dataclass(frozen=True)
class SharedAnalyzerInput:
    comparison: str
    claims_by_id: dict[str, Claim]
    stances: tuple[Stance, ...]
    relations: ClaimGraphRelations
    argumentation_framework: ArgumentationFramework
    bipolar_framework: BipolarArgumentationFramework
    active_graph: ActiveWorldGraph | None = None


@dataclass(frozen=True)
class PrAFQueryParameters:
    semantics: str
    strategy: str
    query_kind: str
    inference_mode: str | None
    queried_set: tuple[str, ...] | None


def _normalize_query_claim_ids(
    values: tuple[str, ...] | list[str] | set[str] | frozenset[str] | None,
) -> tuple[str, ...] | None:
    if values is None:
        return None
    return tuple(sorted(dict.fromkeys(str(value) for value in values)))


def praf_query_parameters(
    *,
    semantics: str | ArgumentationSemantics,
    strategy: str,
    query_kind: str,
    inference_mode: str | None,
    queried_set: tuple[str, ...] | list[str] | set[str] | frozenset[str] | None = None,
    target_claim_ids: tuple[str, ...] | list[str] | set[str] | frozenset[str] | None = None,
    default_queried_set: tuple[str, ...] | list[str] | set[str] | frozenset[str] | None = None,
) -> PrAFQueryParameters:
    semantics_value = semantics.value if isinstance(semantics, ArgumentationSemantics) else str(semantics)
    if semantics_value != ArgumentationSemantics.PRAF_PAPER_TD_COMPLETE.value:
        return PrAFQueryParameters(
            semantics=semantics_value,
            strategy=strategy,
            query_kind=query_kind,
            inference_mode=inference_mode,
            queried_set=_normalize_query_claim_ids(queried_set),
        )

    normalized_queried = (
        _normalize_query_claim_ids(queried_set)
        or _normalize_query_claim_ids(target_claim_ids)
        or _normalize_query_claim_ids(default_queried_set)
    )
    return PrAFQueryParameters(
        semantics=ArgumentationSemantics.COMPLETE.value,
        strategy="paper_td",
        query_kind="extension_probability",
        inference_mode=None,
        queried_set=normalized_queried,
    )


def _cayrol_derived_defeats(
    defeats: set[tuple[str, str]],
    supports: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    return set(_cayrol_derived_defeats_impl(frozenset(defeats), frozenset(supports)))


def _collect_claim_graph_relations(
    claims_by_id: dict[str, Claim],
    stances: list[Stance],
    conflicts: list[ConflictRecord],
    active_ids: set[str],
    *,
    comparison: str,
) -> tuple[dict[str, Claim], tuple[Stance, ...], ClaimGraphRelations]:
    existing_stance_pairs = {
        (stance.source_claim_id, stance.target_claim_id)
        for stance in stances
        if stance.source_claim_id is not None and stance.target_claim_id is not None
    }
    existing_stance_undirected = {
        frozenset((source_id, target_id))
        for source_id, target_id in existing_stance_pairs
    }
    existing_attack_undirected = {
        frozenset((stance.source_claim_id, stance.target_claim_id))
        for stance in stances
        if stance.source_claim_id is not None
        and stance.target_claim_id is not None
        and stance.stance_type in _ATTACK_TYPES
    }

    synthetic_rebuts: set[tuple[str, str]] = set()
    for conflict in conflicts:
        warning_class_name = conflict.warning_class.value
        if warning_class_name not in _REAL_CONFLICT_CLASSES:
            continue
        left_id = conflict.claim_a_id
        right_id = conflict.claim_b_id
        pair_key = frozenset({left_id, right_id})
        if pair_key in existing_attack_undirected:
            continue
        if pair_key in existing_stance_undirected:
            for source_id, target_id in ((left_id, right_id), (right_id, left_id)):
                if (source_id, target_id) in existing_stance_pairs:
                    continue
                synthetic_rebuts.add((source_id, target_id))
            continue
        for source_id, target_id in ((left_id, right_id), (right_id, left_id)):
            synthetic_rebuts.add((source_id, target_id))

    attacks: set[tuple[str, str]] = set()
    direct_defeats: set[tuple[str, str]] = set()
    supports: set[tuple[str, str]] = set()
    attack_relations: list[ProbabilisticRelation] = []
    support_relations: list[ProbabilisticRelation] = []
    direct_defeat_relations: list[ProbabilisticRelation] = []

    for stance in stances:
        source_id = stance.source_claim_id
        target_id = stance.target_claim_id
        stance_type = stance.stance_type
        if source_id is None or target_id is None or stance_type is None:
            continue
        if source_id not in claims_by_id or target_id not in claims_by_id:
            continue
        if stance_type in _SUPPORT_TYPES:
            supports.add((source_id, target_id))
            support_opinion = p_relation_from_stance(stance)
            if not isinstance(support_opinion, NoCalibration):
                support_relations.append(
                    relation_from_stance(
                        kind="support",
                        opinion=support_opinion.opinion,
                        stance=stance,
                    )
                )
            continue
        if stance_type not in _ATTACK_TYPES:
            continue

        attacks.add((source_id, target_id))
        attack_opinion = p_relation_from_stance(stance)
        if not isinstance(attack_opinion, NoCalibration):
            attack_relations.append(
                relation_from_stance(
                    kind="attack",
                    opinion=attack_opinion.opinion,
                    stance=stance,
                )
            )

        if stance_type in _UNCONDITIONAL_TYPES:
            direct_defeats.add((source_id, target_id))
            if not isinstance(attack_opinion, NoCalibration):
                direct_defeat_relations.append(
                    relation_from_stance(
                        kind="direct_defeat",
                        opinion=attack_opinion.opinion,
                        stance=stance,
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
                        relation_from_stance(
                            kind="direct_defeat",
                            opinion=attack_opinion.opinion,
                            stance=stance,
                        )
                    )

    for source_id, target_id in synthetic_rebuts:
        if source_id not in claims_by_id or target_id not in claims_by_id:
            continue
        attacks.add((source_id, target_id))
        attacker_strength = claim_strength(claims_by_id[source_id])
        target_strength = claim_strength(claims_by_id[target_id])
        if defeat_holds(
            "rebuts",
            list(attacker_strength.dimensions),
            list(target_strength.dimensions),
            comparison,
        ):
            direct_defeats.add((source_id, target_id))

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
    claims_by_id: dict[str, Claim],
    stances: list[Stance],
    conflicts: list[ConflictRecord],
    active_ids: set[str],
    *,
    comparison: str = "elitist",
) -> SharedAnalyzerInput:
    """Assemble shared AF / BAF inputs from typed semantic owners."""

    collected_claims, collected_stances, relations = _collect_claim_graph_relations(
        claims_by_id,
        stances,
        conflicts,
        active_ids,
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
        comparison=comparison,
        claims_by_id=collected_claims,
        stances=collected_stances,
        relations=relations,
        argumentation_framework=af,
        bipolar_framework=bipolar,
    )


# --- store / active-graph readers ------------------------------------------


def _active_claim_ids(active_graph: ActiveWorldGraph) -> set[str]:
    return {str(claim_id) for claim_id in active_graph.active_claim_ids}


def _minimal_compiled_graph(
    store: WorldStore,
    active_claim_ids: set[str],
) -> CompiledWorldGraph:
    """Read just the active claims, their stances, and conflicts from a store."""

    claims = tuple(store.claims_by_ids(active_claim_ids).values())
    stances = tuple(store.stances_between(active_claim_ids))
    conflicts = tuple(
        record for record in store.conflicts()
        if str(record.claim_a_id) in active_claim_ids
        and str(record.claim_b_id) in active_claim_ids
    )
    return CompiledWorldGraph(claims=claims, stances=stances, conflicts=conflicts)


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
        inactive_claim_ids=to_claim_ids(all_claim_ids - {str(item) for item in active_ids}),
    )


def shared_analyzer_input_from_graph(
    active_graph: ActiveWorldGraph,
    *,
    comparison: str = "elitist",
) -> SharedAnalyzerInput:
    """Assemble the shared AF inputs from an active world graph.

    Reads canonical semantic owners from the graph and re-attaches the graph to
    the assembled result.
    """

    shared = shared_analyzer_input_from_active_graph(
        {
            claim.claim_id: claim
            for claim in active_graph.compiled.claims
            if claim.claim_id in _active_claim_ids(active_graph)
        },
        [
            stance
            for stance in active_graph.compiled.stances
            if stance.source_claim_id in _active_claim_ids(active_graph)
            and stance.target_claim_id in _active_claim_ids(active_graph)
        ],
        [
            conflict
            for conflict in active_graph.compiled.conflicts
            if conflict.claim_a_id in _active_claim_ids(active_graph)
            and conflict.claim_b_id in _active_claim_ids(active_graph)
        ],
        _active_claim_ids(active_graph),
        comparison=comparison,
    )
    return replace(shared, active_graph=active_graph)


def shared_analyzer_input_from_store(
    store: WorldStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> SharedAnalyzerInput:
    """Read a charter-backed store into the shared AF inputs over its active claims."""

    return shared_analyzer_input_from_graph(
        _active_graph_from_store(store, active_claim_ids),
        comparison=comparison,
    )


def _extension_results(
    name: str, extensions: list[frozenset[str]] | tuple[frozenset[str], ...]
) -> tuple[ExtensionResult, ...]:
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
    witness_claim_ids = set[str]().union(*accepted_sets) & set(target_ids)
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


def project_extension_probability_result(
    extension_probability: float,
    *,
    queried_set: tuple[str, ...] | list[str] | set[str] | None,
    target_claim_ids: tuple[str, ...] | list[str] | set[str],
) -> ClaimProjection:
    target_ids = tuple(sorted(dict.fromkeys(str(claim_id) for claim_id in target_claim_ids)))
    witness_ids = tuple(sorted(dict.fromkeys(str(claim_id) for claim_id in (queried_set or target_ids))))
    survivor_ids = witness_ids if extension_probability > 0.0 else ()
    return ClaimProjection(
        target_claim_ids=target_ids,
        survivor_claim_ids=survivor_ids,
        witness_claim_ids=witness_ids,
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


def analyze_aspic_backend(
    system: ArgumentationSystem,
    kb: KnowledgeBase,
    pref: PreferenceConfig,
    *,
    backend: str = "materialized_reference",
    semantics: str = "grounded",
) -> AnalyzerResult:
    from argumentation.structured.aspic.aspic_encoding import solve_aspic_with_backend

    query_semantics = (
        "grounded"
        if semantics == ArgumentationSemantics.ASPIC_DIRECT_GROUNDED.value
        else semantics
    )
    package_result = solve_aspic_with_backend(
        system,
        kb,
        pref,
        backend=backend,
        semantics=query_semantics,
    )
    if package_result.status == "success":
        extensions = (
            ExtensionResult(
                name=package_result.semantics,
                accepted_claim_ids=tuple(
                    sorted(repr(conclusion) for conclusion in package_result.accepted_conclusions)
                ),
            ),
        )
    else:
        extensions = ()

    metadata: dict[str, object] = {
        "backend_requested": backend,
        "package_backend": package_result.backend,
        "package_status": package_result.status,
        "encoding_signature": package_result.encoding.signature,
        "encoding": package_result.encoding.metadata["encoding"],
    }
    if "reason" in package_result.metadata:
        metadata["reason"] = package_result.metadata["reason"]
    return AnalyzerResult(
        backend="aspic",
        semantics=package_result.semantics,
        extensions=extensions,
        metadata=tuple(metadata.items()),
    )


def build_praf_from_shared_input(shared: SharedAnalyzerInput) -> PropstorePrAF:
    from argumentation.probabilistic.probabilistic import ProbabilisticAF

    p_args: dict[str, OpinionWithProvenance] = {}
    omitted_arguments: dict[str, NoCalibration] = {}
    for claim_id in shared.argumentation_framework.arguments:
        claim = shared.claims_by_id.get(claim_id)
        p_arg = (
            NoCalibration(reason="missing_claim", missing_fields=("claim",))
            if claim is None
            else p_arg_from_claim(claim)
        )
        if isinstance(p_arg, NoCalibration):
            omitted_arguments[claim_id] = p_arg
            p_args[claim_id] = opinion_or_vacuous(None, base_rate=0.5, provenance=p_arg.provenance)
        else:
            p_args[claim_id] = p_arg

    active_args = frozenset(shared.argumentation_framework.arguments)

    # Re-derive the calibrated edge opinions (with provenance) from the stance
    # charters. The opinion of an edge is a property of the stance, independent of
    # which relation class (attack / defeat / support) it lands in, so a single
    # edge -> OpinionWithProvenance map serves every map below.
    edge_opinions: dict[tuple[str, str], OpinionWithProvenance] = {}
    for stance in shared.stances:
        owp = p_relation_from_stance(stance)
        if isinstance(owp, NoCalibration):
            continue
        if stance.source_claim_id is None or stance.target_claim_id is None:
            continue
        edge_opinions[(stance.source_claim_id, stance.target_claim_id)] = owp

    missing_relation_edges = (
        set(shared.relations.attacks - frozenset(edge_opinions))
        | set(shared.relations.direct_defeats - frozenset(edge_opinions))
        | set(shared.relations.supports - frozenset(edge_opinions))
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

    def edge_in_framework(edge: tuple[str, str]) -> bool:
        return edge[0] in active_args and edge[1] in active_args

    def vacuous_relation(edge: tuple[str, str]) -> OpinionWithProvenance:
        omitted = omitted_relations.get(edge)
        return opinion_or_vacuous(
            None,
            base_rate=0.5,
            provenance=None if omitted is None else omitted.provenance,
        )

    def relation_opinion(edge: tuple[str, str]) -> OpinionWithProvenance:
        return edge_opinions.get(edge) or vacuous_relation(edge)

    defeats = frozenset(
        edge for edge in shared.argumentation_framework.defeats
        if edge_in_framework(edge)
    )
    attacks = (
        None
        if shared.argumentation_framework.attacks is None
        else frozenset(edge for edge in shared.argumentation_framework.attacks if edge_in_framework(edge))
    )
    supports = frozenset(edge for edge in shared.relations.supports if edge_in_framework(edge))
    base_defeats = frozenset(edge for edge in shared.relations.direct_defeats if edge_in_framework(edge))
    framework = ArgumentationFramework(
        arguments=active_args,
        defeats=defeats,
        attacks=attacks,
    )

    def keep_relation(relation: ProbabilisticRelation) -> bool:
        return relation.source in active_args and relation.target in active_args

    p_defeats = {edge: relation_opinion(edge) for edge in base_defeats}
    p_attacks = {edge: relation_opinion(edge) for edge in (attacks or frozenset())}
    p_supports = {edge: relation_opinion(edge) for edge in supports}
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
    from argumentation.probabilistic.probabilistic import compute_probabilistic_acceptance

    praf = build_praf_from_shared_input(shared)
    query_parameters = praf_query_parameters(
        semantics=semantics,
        strategy=strategy,
        query_kind=query_kind,
        inference_mode=inference_mode,
        queried_set=queried_set,
        target_claim_ids=target_claim_ids,
        default_queried_set=praf.kernel.framework.arguments,
    )
    praf_result = compute_probabilistic_acceptance(
        praf.kernel,
        semantics=query_parameters.semantics,
        strategy=query_parameters.strategy,
        query_kind=query_parameters.query_kind,
        inference_mode=query_parameters.inference_mode,
        queried_set=query_parameters.queried_set,
        mc_epsilon=mc_epsilon,
        mc_confidence=mc_confidence,
        treewidth_cutoff=treewidth_cutoff,
        rng_seed=rng_seed,
    )
    if target_claim_ids is None:
        projection = None
    elif praf_result.acceptance_probs is not None:
        projection = project_acceptance_result(
            praf_result.acceptance_probs,
            target_claim_ids=target_claim_ids,
        )
    elif praf_result.extension_probability is not None:
        projection = project_extension_probability_result(
            praf_result.extension_probability,
            queried_set=praf_result.queried_set,
            target_claim_ids=target_claim_ids,
        )
    else:
        projection = None
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
            ("strategy_metadata", dict(praf_result.strategy_metadata or {})),
            ("samples", praf_result.samples),
            ("confidence_interval_half", praf_result.confidence_interval_half),
            ("omitted_arguments", tuple(sorted(praf.omitted_arguments or ()))),
            ("omitted_relations", tuple(sorted(praf.omitted_relations or ()))),
            ("comparison", shared.comparison),
        ),
    )
