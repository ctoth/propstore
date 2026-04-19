"""Public projection facade for structured argumentation.

After the Phase 5 cutover, `build_structured_projection()` delegates to
`aspic_bridge.build_aspic_projection()` for full recursive ASPIC+
construction (Modgil & Prakken 2018 Defs 1-22). This module intentionally
retains the public projection dataclasses and thin delegation wrappers.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from argumentation.dung import (
    ArgumentationFramework,
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
from propstore.core.labels import Label, SupportQuality
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.world.types import (
    ArgumentationSemantics,
    ReasoningBackend,
    SupportMetadata,
    validate_backend_semantics,
)


@dataclass(frozen=True)
class StructuredArgument:
    arg_id: str
    conclusion_key: str
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
    if normalized_semantics == ArgumentationSemantics.GROUNDED:
        return grounded_extension(framework)
    if normalized_semantics == ArgumentationSemantics.PREFERRED:
        return [frozenset(ext) for ext in preferred_extensions(projection.framework)]
    if normalized_semantics == ArgumentationSemantics.STABLE:
        return [frozenset(ext) for ext in stable_extensions(projection.framework)]
    raise ValueError(
        f"{backend.value} does not support semantics '{normalized_semantics.value}'"
    )
