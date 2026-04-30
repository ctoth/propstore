"""Public projection facade for structured argumentation.

After the Phase 5 cutover, `build_structured_projection()` delegates to
`aspic_bridge.build_aspic_projection()` for full recursive ASPIC+
construction (Modgil & Prakken 2018 Defs 1-22). This module intentionally
retains the public projection dataclasses and thin delegation wrappers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from argumentation.aspic import GroundAtom
from argumentation.dung import (
    ArgumentationFramework,
    complete_extensions,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)

from propstore.core.active_claims import (
    ActiveClaimInput,
    coerce_active_claims,
)
from propstore.core.environment import StanceStore
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.labels import Label, SupportMetadata, SupportQuality
from propstore.core.reasoning import (
    ArgumentationSemantics,
    ReasoningBackend,
    validate_backend_semantics,
)
from propstore.core.results import AnalyzerResult
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.provenance.records import ProjectionFrameProvenanceRecord


@dataclass(frozen=True)
class ProjectionLossWitness:
    backend: str
    kind: str
    reason: str
    backend_atom_id: str | None = None


@dataclass(frozen=True)
class ProjectionAtom:
    backend: str
    backend_atom: GroundAtom
    backend_atom_id: str
    negated: bool
    source_assertion_ids: tuple[str, ...]
    provenance: ProjectionFrameProvenanceRecord | None = None
    loss: ProjectionLossWitness | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_assertion_ids",
            tuple(sorted({str(value) for value in self.source_assertion_ids})),
        )


class ProjectionLiftError(ValueError):
    """Raised when a backend result cannot lift to propstore assertion ids."""


@dataclass(frozen=True)
class LiftedProjectionResult:
    argument_id: str
    backend: str
    situated_assertion_ids: tuple[str, ...]
    provenance: ProjectionFrameProvenanceRecord


@dataclass(frozen=True)
class LiftedAnalyzerProjectionResult:
    backend: str
    semantics: str
    target_assertion_ids: tuple[str, ...]
    survivor_assertion_ids: tuple[str, ...]
    witness_assertion_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_assertion_ids", _sorted_unique(self.target_assertion_ids))
        object.__setattr__(self, "survivor_assertion_ids", _sorted_unique(self.survivor_assertion_ids))
        object.__setattr__(self, "witness_assertion_ids", _sorted_unique(self.witness_assertion_ids))


@dataclass(frozen=True)
class StructuredArgument:
    arg_id: str
    projection: ProjectionAtom
    claim_id: str | None
    conclusion_concept_id: str | None
    premise_claim_ids: tuple[str, ...]
    label: Label | None
    strength: float
    top_rule_kind: str
    attackable_kind: str
    subargument_ids: tuple[str, ...]
    support_quality: SupportQuality
    justification_id: str
    dependency_claim_ids: tuple[str, ...]


def lift_projected_argument(argument: StructuredArgument) -> LiftedProjectionResult:
    projection = argument.projection
    if projection.loss is not None:
        raise ProjectionLiftError(
            f"{projection.loss.kind}: {projection.loss.reason}"
        )
    if projection.provenance is None or not projection.source_assertion_ids:
        raise ProjectionLiftError(
            "missing_source_assertion: projection result has no situated assertion ids"
        )
    return LiftedProjectionResult(
        argument_id=argument.arg_id,
        backend=projection.backend,
        situated_assertion_ids=projection.source_assertion_ids,
        provenance=projection.provenance,
    )


def claim_source_assertion_ids_from_active_graph(
    active_graph: ActiveWorldGraph,
) -> dict[str, tuple[str, ...]]:
    active_claim_ids = set(active_graph.active_claim_ids)
    mapping: dict[str, tuple[str, ...]] = {}
    for claim in active_graph.compiled.claims:
        if claim.claim_id not in active_claim_ids:
            continue
        raw = dict(claim.attributes).get("source_assertion_ids")
        assertion_ids = _coerce_source_assertion_ids(raw)
        if assertion_ids:
            mapping[str(claim.claim_id)] = assertion_ids
    return mapping


def lift_analyzer_result_projection(
    result: AnalyzerResult,
    claim_assertion_ids: Mapping[str, Sequence[str]],
) -> LiftedAnalyzerProjectionResult:
    if result.projection is None:
        raise ProjectionLiftError(
            "missing_projection: analyzer result has no claim projection to lift"
        )
    projection = result.projection
    return LiftedAnalyzerProjectionResult(
        backend=result.backend,
        semantics=result.semantics,
        target_assertion_ids=_assertion_ids_for_claims(
            projection.target_claim_ids,
            claim_assertion_ids,
        ),
        survivor_assertion_ids=_assertion_ids_for_claims(
            projection.survivor_claim_ids,
            claim_assertion_ids,
        ),
        witness_assertion_ids=_assertion_ids_for_claims(
            projection.witness_claim_ids,
            claim_assertion_ids,
        ),
    )


def _sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(str(value) for value in values)))


def _coerce_source_assertion_ids(raw: object) -> tuple[str, ...]:
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, Sequence) and not isinstance(raw, str | bytes):
        return _sorted_unique(tuple(str(value) for value in raw))
    return ()


def _assertion_ids_for_claims(
    claim_ids: Sequence[str],
    claim_assertion_ids: Mapping[str, Sequence[str]],
) -> tuple[str, ...]:
    assertion_ids: list[str] = []
    missing: list[str] = []
    for claim_id in claim_ids:
        values = claim_assertion_ids.get(str(claim_id), ())
        if not values:
            missing.append(str(claim_id))
            continue
        assertion_ids.extend(str(value) for value in values)
    if missing:
        raise ProjectionLiftError(
            "missing_source_assertion: analyzer projection has no situated "
            f"assertion ids for claims {missing!r}"
        )
    return _sorted_unique(tuple(assertion_ids))


@dataclass(frozen=True)
class StructuredProjection:
    arguments: tuple[StructuredArgument, ...]
    framework: ArgumentationFramework
    claim_to_argument_ids: dict[str, tuple[str, ...]]
    argument_to_claim_id: dict[str, str]


def build_structured_projection(
    store: StanceStore,
    active_claims: Sequence[ActiveClaimInput],
    *,
    bundle: GroundedRulesBundle,
    support_metadata: SupportMetadata | None = None,
    comparison: str = "elitist",
    link: str = "last",
    active_graph: ActiveWorldGraph | None = None,
) -> StructuredProjection:
    """Build real structured arguments from canonical justifications.

    Delegates to the ASPIC+ bridge for full recursive argument construction.

    The caller must supply the grounded bundle explicitly. Grounding is part of
    the theory identity, so this wrapper no longer fabricates
    ``GroundedRulesBundle.empty()`` internally.
    """
    from propstore.aspic_bridge import build_aspic_projection

    return build_aspic_projection(
        store,
        coerce_active_claims(active_claims),
        bundle=bundle,
        support_metadata=support_metadata,
        comparison=comparison,
        link=link,
        active_graph=active_graph,
    )


def compute_structured_justified_arguments(
    projection: StructuredProjection,
    *,
    semantics: str = "grounded",
    backend: ReasoningBackend = ReasoningBackend.ASPIC,
) -> frozenset[str] | list[frozenset[str]]:
    """Compute justified structured arguments using existing Dung semantics."""
    _, normalized_semantics = validate_backend_semantics(
        backend,
        semantics,
    )
    framework = projection.framework
    if normalized_semantics in {
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.ASPIC_DIRECT_GROUNDED,
        ArgumentationSemantics.ASPIC_INCOMPLETE_GROUNDED,
    }:
        if backend == ReasoningBackend.ASPIC and framework.attacks is not None:
            complete = [frozenset(ext) for ext in complete_extensions(framework)]
            if not complete:
                return frozenset()
            return min(complete, key=lambda ext: (len(ext), tuple(sorted(ext))))
        return grounded_extension(framework)
    if normalized_semantics == ArgumentationSemantics.COMPLETE:
        return [frozenset(ext) for ext in complete_extensions(projection.framework)]
    if normalized_semantics == ArgumentationSemantics.PREFERRED:
        return [frozenset(ext) for ext in preferred_extensions(projection.framework)]
    if normalized_semantics == ArgumentationSemantics.STABLE:
        return [frozenset(ext) for ext in stable_extensions(projection.framework)]
    raise ValueError(
        f"{backend.value} does not support semantics '{normalized_semantics.value}'"
    )
