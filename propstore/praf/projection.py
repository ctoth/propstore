"""Store-based construction of probabilistic argumentation projections."""

from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.core.analyzers import (
    build_praf_from_shared_input,
    shared_analyzer_input_from_store,
)
from propstore.world.types import ArtifactStore

if TYPE_CHECKING:
    from .engine import ProbabilisticAF


def build_praf(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> "ProbabilisticAF":
    """Build a primitive-relation probabilistic model over the active claim graph.

    P_A comes from p_arg_from_claim(); missing calibration is omitted and
    surfaced on the returned ProbabilisticAF.
    Primitive attacks and supports carry opinion-derived existence probabilities.
    Direct defeats are the primitive semantic relation after preference filtering.
    Cayrol derived defeats remain world-derived consequences and are not stored
    as authoritative probabilistic inputs.

    Steps:
      1. Collect primitive attacks/supports and direct defeats
      2. Build the semantic AF envelope with Cayrol closure for deterministic evaluation
      3. Attach provenance-bearing primitive relation records
      4. Set P_A for each argument
      5. Return ProbabilisticAF
    """
    shared = shared_analyzer_input_from_store(
        store,
        active_claim_ids,
        comparison=comparison,
    )
    return build_praf_from_shared_input(shared)
