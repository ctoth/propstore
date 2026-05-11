"""Application-layer world reasoning workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from propstore.reporting import JsonReportMixin
from propstore.app.world import bind_world, open_app_world_model
from propstore.repository import Repository
from propstore.world.types import GroundingBundleStore, normalize_reasoning_backend

if TYPE_CHECKING:
    from propstore.core.active_claims import ActiveClaim
    from propstore.core.graph_types import ActiveWorldGraph
    from propstore.core.labels import Label, SupportQuality
    from propstore.world import WorldQuery


class WorldReasoningAppError(Exception):
    """Base class for expected app-layer reasoning failures."""


class WorldExtensionsUnsupportedBackend(WorldReasoningAppError):
    def __init__(self, backend: str) -> None:
        super().__init__(
            f"backend '{backend}' does not expose Dung extensions; "
            "use worldline or resolve with reasoning_backend=atms instead."
        )
        self.backend = backend


@dataclass(frozen=True)
class AppWorldExtensionsRequest:
    bindings: Mapping[str, str]
    backend: str = "claim_graph"
    semantics: str = "grounded"
    set_comparison: str = "elitist"
    context: str | None = None
    praf_strategy: str = "auto"
    praf_epsilon: float = 0.01
    praf_confidence: float = 0.95
    praf_seed: int | None = None


@dataclass(frozen=True)
class WorldExtensionsStanceSummary:
    total_stances: int
    included_as_attacks: int
    vacuous_count: int
    excluded_non_attack: int
    models: tuple[str, ...]


@dataclass(frozen=True)
class WorldExtensionsClaimLine:
    claim_id: str
    claim_type: str
    concept_id: str | None
    concept_name: str | None
    value: object | None
    expression: str | None
    statement: str | None
    description: str | None


@dataclass(frozen=True)
class WorldExtensionsDefeatedClaim:
    claim_id: str
    defeater_claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorldExtensionsSet:
    claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorldExtensionsProbability:
    claim_id: str
    probability: float


@dataclass(frozen=True)
class WorldExtensionsReport(JsonReportMixin):
    backend: str
    semantics: str
    set_comparison: str
    active_claims: tuple[WorldExtensionsClaimLine, ...]
    stance_summary: WorldExtensionsStanceSummary
    accepted_claim_ids: tuple[str, ...] = ()
    defeated_claims: tuple[WorldExtensionsDefeatedClaim, ...] = ()
    extensions: tuple[WorldExtensionsSet, ...] = ()
    acceptance_probabilities: tuple[WorldExtensionsProbability, ...] = ()
    strategy_used: str | None = None
    samples: int | None = None
    extension_probability: float | None = None


def world_extensions(
    repo: Repository,
    request: AppWorldExtensionsRequest,
) -> WorldExtensionsReport | None:
    """Compute argumentation extension reports for a bound world."""

    from propstore.core.active_claims import coerce_active_claims
    from propstore.relation_analysis import stance_summary
    from propstore.world import ReasoningBackend

    with open_app_world_model(repo) as world:
        bound = bind_world(world, request.bindings, context_id=request.context)
        active = coerce_active_claims(bound.active_claims())
        if not active:
            return None

        claim_ids = {str(claim.claim_id) for claim in active}
        backend = normalize_reasoning_backend(request.backend)

        if backend is ReasoningBackend.ATMS:
            raise WorldExtensionsUnsupportedBackend(backend.value)

        active_lines = _claim_lines(world, active)
        summary = _stance_summary(stance_summary(world, claim_ids))

        if backend is ReasoningBackend.PRAF:
            return _praf_extensions(
                world,
                active,
                claim_ids,
                request,
                active_lines,
                summary,
            )

        if backend is ReasoningBackend.CLAIM_GRAPH:
            from propstore.claim_graph import (
                build_argumentation_framework,
                compute_claim_graph_justified_claims,
            )

            result = compute_claim_graph_justified_claims(
                world,
                claim_ids,
                semantics=request.semantics,
                comparison=request.set_comparison,
            )
            framework = build_argumentation_framework(
                world,
                claim_ids,
                comparison=request.set_comparison,
            )
            argument_to_claim = {claim_id: claim_id for claim_id in claim_ids}
        elif backend is ReasoningBackend.ASPIC:
            from propstore.aspic_bridge import build_aspic_projection
            from propstore.grounding.bundle import GroundedRulesBundle
            from propstore.structured_projection import (
                compute_structured_justified_arguments,
            )

            grounding_bundle = GroundedRulesBundle.empty()
            if isinstance(world, GroundingBundleStore):
                grounding_bundle = world.grounding_bundle()

            aspic_projection = build_aspic_projection(
                world,
                active,
                bundle=grounding_bundle,
                support_metadata=_support_metadata_for(bound, active),
                comparison=request.set_comparison,
                active_graph=_active_graph_for(bound),
            )
            result = compute_structured_justified_arguments(
                aspic_projection,
                semantics=request.semantics,
                backend=ReasoningBackend.ASPIC,
            )
            framework = aspic_projection.framework
            argument_to_claim = dict(aspic_projection.argument_to_claim_id)
        else:
            raise NotImplementedError(f"Unknown backend: {backend.value}")

        if request.semantics == "grounded":
            justified_claims = _grounded_claim_ids(
                result,
                backend=backend,
                argument_to_claim=argument_to_claim,
            )
            defeated = claim_ids - justified_claims
            defeated_claims = _defeated_claims(
                defeated,
                framework.defeats,
                argument_to_claim,
            )
            return WorldExtensionsReport(
                backend=backend.value,
                semantics=request.semantics,
                set_comparison=request.set_comparison,
                active_claims=active_lines,
                stance_summary=summary,
                accepted_claim_ids=tuple(sorted(justified_claims)),
                defeated_claims=defeated_claims,
            )

        extensions = _extension_sets(
            result,
            backend=backend,
            argument_to_claim=argument_to_claim,
        )
        return WorldExtensionsReport(
            backend=backend.value,
            semantics=request.semantics,
            set_comparison=request.set_comparison,
            active_claims=active_lines,
            stance_summary=summary,
            extensions=extensions,
        )


def _praf_extensions(
    world: "WorldQuery",
    active: Sequence["ActiveClaim"],
    claim_ids: set[str],
    request: AppWorldExtensionsRequest,
    active_lines: tuple[WorldExtensionsClaimLine, ...],
    summary: WorldExtensionsStanceSummary,
) -> WorldExtensionsReport:
    from argumentation.probabilistic import compute_probabilistic_acceptance
    from propstore.core.analyzers import praf_query_parameters
    from propstore.praf import build_praf

    praf = build_praf(world, claim_ids, comparison=request.set_comparison)
    query_parameters = praf_query_parameters(
        semantics=request.semantics,
        strategy=request.praf_strategy,
        query_kind="argument_acceptance",
        inference_mode="credulous",
        default_queried_set=claim_ids,
    )
    praf_result = compute_probabilistic_acceptance(
        praf.kernel,
        semantics=query_parameters.semantics,
        strategy=query_parameters.strategy,
        query_kind=query_parameters.query_kind,
        inference_mode=query_parameters.inference_mode,
        queried_set=query_parameters.queried_set,
        mc_epsilon=request.praf_epsilon,
        mc_confidence=request.praf_confidence,
        rng_seed=request.praf_seed,
    )
    acceptance_probs = (
        {}
        if praf_result.acceptance_probs is None
        else praf_result.acceptance_probs
    )
    return WorldExtensionsReport(
        backend="praf",
        semantics=request.semantics,
        set_comparison=request.set_comparison,
        active_claims=active_lines,
        stance_summary=summary,
        acceptance_probabilities=tuple(
            WorldExtensionsProbability(claim_id=str(claim_id), probability=float(prob))
            for claim_id, prob in sorted(
                acceptance_probs.items(),
                key=lambda item: -item[1],
            )
        ),
        strategy_used=str(praf_result.strategy_used),
        samples=praf_result.samples,
        extension_probability=praf_result.extension_probability,
    )


def _claim_lines(
    world: "WorldQuery",
    active: Sequence["ActiveClaim"],
) -> tuple[WorldExtensionsClaimLine, ...]:
    from propstore.core.row_types import coerce_concept_row

    lines: list[WorldExtensionsClaimLine] = []
    for claim in active:
        concept_id = None if claim.value_concept_id is None else str(claim.value_concept_id)
        concept_name = None
        if concept_id:
            concept = world.get_concept(concept_id)
            if concept is not None:
                concept_name = coerce_concept_row(concept).canonical_name
        lines.append(
            WorldExtensionsClaimLine(
                claim_id=str(claim.claim_id),
                claim_type=str(claim.claim_type or "unknown"),
                concept_id=concept_id,
                concept_name=concept_name,
                value=claim.value,
                expression=claim.expression,
                statement=claim.statement,
                description=claim.description,
            )
        )
    return tuple(lines)


def _int_summary_field(raw: Mapping[str, object], key: str, default: int = 0) -> int:
    value = raw.get(key, default)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int | float | str):
        return int(value)
    return int(str(value))


def _string_summary_items(raw: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = raw.get(key)
    if not isinstance(value, tuple | list | set):
        return ()
    return tuple(str(model) for model in value)


def _stance_summary(raw: Mapping[str, object]) -> WorldExtensionsStanceSummary:
    return WorldExtensionsStanceSummary(
        total_stances=_int_summary_field(raw, "total_stances"),
        included_as_attacks=_int_summary_field(raw, "included_as_attacks"),
        vacuous_count=_int_summary_field(raw, "vacuous_count"),
        excluded_non_attack=_int_summary_field(raw, "excluded_non_attack"),
        models=_string_summary_items(raw, "models"),
    )


def _grounded_claim_ids(
    result: object,
    *,
    backend: object,
    argument_to_claim: Mapping[str, str],
) -> set[str]:
    from propstore.world import ReasoningBackend

    if backend is ReasoningBackend.ASPIC:
        return {
            claim_id
            for arg_id in cast(frozenset[str], result)
            if (claim_id := argument_to_claim.get(arg_id)) is not None
        }
    return set(cast(frozenset[str], result))


def _extension_sets(
    result: object,
    *,
    backend: object,
    argument_to_claim: Mapping[str, str],
) -> tuple[WorldExtensionsSet, ...]:
    from propstore.world import ReasoningBackend

    extensions: list[WorldExtensionsSet] = []
    for extension in cast(list[frozenset[str]], result):
        if backend is ReasoningBackend.ASPIC:
            claim_ids = {
                claim_id
                for arg_id in extension
                if (claim_id := argument_to_claim.get(arg_id)) is not None
            }
        else:
            claim_ids = set(extension)
        extensions.append(WorldExtensionsSet(claim_ids=tuple(sorted(claim_ids))))
    return tuple(extensions)


def _defeated_claims(
    defeated: set[str],
    defeats: object,
    argument_to_claim: Mapping[str, str],
) -> tuple[WorldExtensionsDefeatedClaim, ...]:
    defeaters_map: dict[str, set[str]] = {}
    for src, tgt in cast(frozenset[tuple[str, str]], defeats):
        src_claim = argument_to_claim.get(src, src)
        tgt_claim = argument_to_claim.get(tgt, tgt)
        if tgt_claim in defeated:
            defeaters_map.setdefault(tgt_claim, set()).add(src_claim)
    return tuple(
        WorldExtensionsDefeatedClaim(
            claim_id=claim_id,
            defeater_claim_ids=tuple(sorted(defeaters_map.get(claim_id, ()))),
        )
        for claim_id in sorted(defeated)
    )


def _support_metadata_for(
    bound: object,
    active_claims: Sequence["ActiveClaim"],
) -> dict[str, tuple["Label | None", "SupportQuality"]]:
    from propstore.world.types import ClaimSupportView

    if not isinstance(bound, ClaimSupportView):
        return {}

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    for claim in active_claims:
        support_metadata[str(claim.claim_id)] = bound.claim_support(claim)
    return support_metadata


def _active_graph_for(bound: object) -> ActiveWorldGraph | None:
    from propstore.world.types import HasActiveGraph

    if isinstance(bound, HasActiveGraph):
        return bound._active_graph
    return None
