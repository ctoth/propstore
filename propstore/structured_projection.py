"""Projection result models and lifting helpers for structured argumentation.

ASPIC+ construction lives in ``propstore.aspic_bridge`` (``csaf_to_projection``).
This module owns the propstore-facing projection records and the extension
semantics computed over a constructed :class:`StructuredProjection`. The Dung
semantics themselves are the argumentation package's (CLAUDE.md substrate
boundary): this module selects among them, it does not re-implement them.

The store-reading helper that maps an active world graph to source-assertion ids
(``claim_source_assertion_ids_from_active_graph`` in the pre-rewrite tree) is
deferred to the world layer (Phase 7) because it needs ``ActiveWorldGraph``; it
is intentionally absent here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from argumentation.core.dung import (
    ArgumentationFramework,
    complete_extensions,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from argumentation.structured.aspic.aspic import GroundAtom

from propstore.core.labels import Label, SupportQuality
from propstore.core.reasoning import (
    ArgumentationSemantics,
    ReasoningBackend,
    validate_backend_semantics,
)
from propstore.core.results import AnalyzerResult
from propstore.provenance import ProjectionFrameProvenanceRecord


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
        object.__setattr__(
            self, "target_assertion_ids", _sorted_unique(self.target_assertion_ids)
        )
        object.__setattr__(
            self, "survivor_assertion_ids", _sorted_unique(self.survivor_assertion_ids)
        )
        object.__setattr__(
            self, "witness_assertion_ids", _sorted_unique(self.witness_assertion_ids)
        )


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
        raise ProjectionLiftError(f"{projection.loss.kind}: {projection.loss.reason}")
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
