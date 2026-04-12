"""Public projection facade for structured argumentation.

After the Phase 5 cutover, `build_structured_projection()` delegates to
`aspic_bridge.build_aspic_projection()` for full recursive ASPIC+
construction (Modgil & Prakken 2018 Defs 1-22). This module intentionally
retains the public projection dataclasses and thin delegation wrappers.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claims
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.environment import StanceStore
from propstore.dung import (
    ArgumentationFramework,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.core.labels import Label, SupportQuality
from propstore.world.types import (
    ArgumentationSemantics,
    ReasoningBackend,
    SupportMetadata,
    validate_backend_semantics,
)


@dataclass(frozen=True)
class StructuredArgument:
    arg_id: str
    claim_id: str
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
    active_claims: list[ActiveClaimInput],
    *,
    support_metadata: SupportMetadata | None = None,
    comparison: str = "elitist",
    link: str = "last",
    active_graph: ActiveWorldGraph | None = None,
) -> StructuredProjection:
    """Build real structured arguments from canonical justifications.

    Delegates to the ASPIC+ bridge for full recursive argument construction.

    Phase-1 call sites that enter through this wrapper do not exercise
    the grounded-rules pipeline (T2.5 is empty), so we pass
    ``GroundedRulesBundle.empty()`` here. Callers that need real
    grounding should call ``build_aspic_projection`` directly with
    their own bundle. Diller, Borg, Bex 2025 §3 Def 7 (p.3): the
    empty fact base is a legal Datalog program and its bundle is
    well defined — this is the identity element, not a shim.
    """
    from propstore.aspic_bridge import build_aspic_projection
    from propstore.grounding.bundle import GroundedRulesBundle

    return build_aspic_projection(
        store,
        coerce_active_claims(active_claims),
        bundle=GroundedRulesBundle.empty(),
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
        f"{backend.value} does not support semantics "
        f"'{normalized_semantics.value}'"
    )
