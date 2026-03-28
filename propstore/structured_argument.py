"""Structured arguments built from canonical claim justifications.

After the Phase 5 cutover, build_structured_projection delegates to
aspic_bridge.build_aspic_projection for full recursive ASPIC+ argument
construction (Modgil & Prakken 2018 Defs 1-22).  This module retains
the public dataclasses and thin delegation wrappers.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.core.graph_types import ActiveWorldGraph
from propstore.dung import (
    ArgumentationFramework,
    grounded_extension,
    hybrid_grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.world.labelled import Label, SupportQuality
from propstore.world.types import ArtifactStore


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
    store: ArtifactStore,
    active_claims: list[dict],
    *,
    support_metadata: dict[str, tuple[Label | None, SupportQuality]] | None = None,
    comparison: str = "elitist",
    link: str = "last",
    active_graph: ActiveWorldGraph | None = None,
) -> StructuredProjection:
    """Build real structured arguments from canonical justifications.

    Delegates to the ASPIC+ bridge for full recursive argument construction.
    """
    from propstore.aspic_bridge import build_aspic_projection

    return build_aspic_projection(
        store,
        active_claims,
        support_metadata=support_metadata,
        comparison=comparison,
        link=link,
        active_graph=active_graph,
    )


def compute_structured_justified_arguments(
    projection: StructuredProjection,
    *,
    semantics: str = "grounded",
) -> frozenset[str] | list[frozenset[str]]:
    """Compute justified structured arguments using existing Dung semantics."""
    if semantics == "grounded":
        # Use hybrid when framework has attacks (ASPIC+ bridge produces both)
        if projection.framework.attacks is not None:
            return hybrid_grounded_extension(projection.framework)
        return grounded_extension(projection.framework)
    if semantics == "preferred":
        return [frozenset(ext) for ext in preferred_extensions(projection.framework)]
    if semantics == "stable":
        return [frozenset(ext) for ext in stable_extensions(projection.framework)]
    raise ValueError(f"Unknown semantics: {semantics}")

