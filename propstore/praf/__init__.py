"""Propstore probabilistic-argumentation adapters.

The formal PrAF kernel is ``argumentation.probabilistic.probabilistic``; this
package keeps the propstore-owned value/honesty deltas (opinion-and-provenance
pairings, COH enforcement, honest defeat-marginal summaries). Store-based
construction (``build_praf`` over the active claim graph) lands with the analyzer
assembly in a later slice; the engine surface below is store-free.
"""

from propstore.praf.engine import (
    COHDivergenceError,
    COHDogmaticInputError,
    EnforceCohResult,
    NoCalibration,
    PreferenceLayerError,
    PropstorePrAF,
    enforce_coh,
    p_arg_from_claim,
    p_defeat_from_stance,
    p_relation_from_stance,
    propstore_praf_kernel,
    summarize_defeat_relations,
)

__all__ = [
    "COHDivergenceError",
    "COHDogmaticInputError",
    "EnforceCohResult",
    "NoCalibration",
    "PreferenceLayerError",
    "PropstorePrAF",
    "enforce_coh",
    "p_arg_from_claim",
    "p_defeat_from_stance",
    "p_relation_from_stance",
    "propstore_praf_kernel",
    "summarize_defeat_relations",
]
