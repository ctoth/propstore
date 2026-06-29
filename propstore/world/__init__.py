"""propstore world layer — render-time queries over the semantic substrate.

Phase 7a-causal seeds this package with the causal-reasoning surface: the
``causal_models`` substrate package supplies the Pearl/Halpern kernel directly
(no propstore mirror), and :mod:`propstore.world.causal` supplies the
propstore-specific ``CompiledWorldGraph`` → SCM adapter. Later phases add the
world queries, resolution, and render policy.
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

from propstore.world.causal import from_compiled_graph

__all__ = [
    "ActualCauseCriterion",
    "ActualCauseVerdict",
    "ActualCauseWitness",
    "CausalValueResult",
    "CausalValueStatus",
    "EffectPredicate",
    "EnumerationExceeded",
    "InterventionDiffEntry",
    "InterventionWorld",
    "InterventionWorldUnavailable",
    "ObservationInconsistent",
    "ObservationWorld",
    "StructuralCausalModel",
    "StructuralEquation",
    "SupportsCausalModel",
    "actual_cause",
    "from_compiled_graph",
]
