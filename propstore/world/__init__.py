"""propstore world layer — render-time queries over the semantic substrate.

This is the public render surface. The ``causal_models`` substrate package
supplies the Pearl/Halpern kernel directly (no propstore mirror) and
:mod:`propstore.world.causal` supplies the propstore-specific
``CompiledWorldGraph`` → SCM adapter; :mod:`propstore.world.model` adds the
``bind`` / ``chain_query`` / ``intervene`` / ``observe`` query glue over the
``WorldStore`` protocol; :mod:`propstore.world.bound` and
:mod:`propstore.world.overlay` are the bound and overlay belief spaces; and
:mod:`propstore.world.types` / :mod:`propstore.world.resolution` carry the render
policy and resolution strategies.

The concrete repo-backed ``WorldQuery`` reader is Phase 9: it will satisfy the
``WorldStore`` protocol and reuse the :mod:`propstore.world.model` glue, so it is
not re-exported here yet.
"""

from __future__ import annotations

from causal_models import (
    ActualCauseCriterion,
    ActualCauseVerdict,
    ActualCauseWitness,
    CausalValueResult,
    CausalValueStatus,
    EffectPredicate,
    EnumerationExceeded,
    InterventionDiffEntry,
    InterventionWorld,
    InterventionWorldUnavailable,
    ObservationInconsistent,
    ObservationWorld,
    StructuralCausalModel,
    StructuralEquation,
    SupportsCausalModel,
    actual_cause,
)

from propstore.world.bound import BoundWorld
from propstore.world.causal import from_compiled_graph
from propstore.world.model import (
    WorldQuery,
    active_graph,
    bind,
    chain_query,
    compiled_graph,
    intervene,
    observe,
    serialize_claim_atms_label,
)
from propstore.world.overlay import OverlayWorld
from propstore.world.resolution import resolve
from propstore.world.types import (
    BeliefSpace,
    ChainResult,
    ChainStep,
    DerivedResult,
    RenderPolicy,
    ResolutionStrategy,
    ResolvedResult,
    SyntheticClaim,
    ValueResult,
    ValueStatus,
)

__all__ = [
    "ActualCauseCriterion",
    "ActualCauseVerdict",
    "ActualCauseWitness",
    "BeliefSpace",
    "BoundWorld",
    "CausalValueResult",
    "CausalValueStatus",
    "ChainResult",
    "ChainStep",
    "DerivedResult",
    "EffectPredicate",
    "EnumerationExceeded",
    "InterventionDiffEntry",
    "InterventionWorld",
    "InterventionWorldUnavailable",
    "ObservationInconsistent",
    "ObservationWorld",
    "OverlayWorld",
    "RenderPolicy",
    "ResolutionStrategy",
    "ResolvedResult",
    "StructuralCausalModel",
    "StructuralEquation",
    "SupportsCausalModel",
    "SyntheticClaim",
    "ValueResult",
    "ValueStatus",
    "WorldQuery",
    "active_graph",
    "actual_cause",
    "bind",
    "chain_query",
    "compiled_graph",
    "from_compiled_graph",
    "intervene",
    "observe",
    "resolve",
    "serialize_claim_atms_label",
]
