"""Propstore probabilistic-argumentation adapters over the formal PrAF kernel.

The probabilistic-argumentation algorithms (Li, Oren & Norman 2011; Hunter 2013)
live in :mod:`argumentation.probabilistic.probabilistic` — propstore imports that
``ProbabilisticAF`` kernel and uses it directly (CLAUDE.md substrate boundary; no
mirror type). This module keeps only the propstore-owned deltas:

* the *value/honesty* layer — argument- and relation-existence opinions derived
  from calibrated claim/stance fields, each a ``doxa.Opinion`` paired with typed
  :class:`~propstore.provenance.Provenance` (an :class:`OpinionWithProvenance`,
  never a re-spelled opinion). Missing calibration is an explicit
  :class:`NoCalibration`, never a fabricated number;
* :func:`enforce_coh` — the COH rationality fixed point over argument
  expectations (Hunter 2013, the COH constraint that an argument and its attacker
  cannot both be near-certain), expressed propstore-side because it reasons over
  the opinion evidence counts, not just the kernel floats;
* :func:`summarize_defeat_relations` — exact defeat marginals reported as
  *vacuous* opinions: an uncalibrated marginal carries ``u = 1`` and
  ``VACUOUS`` provenance, so the system never claims calibrated evidence it does
  not have (CLAUDE.md honest ignorance).

The kernel is fed plain ``float`` expectations; ``PropstorePrAF`` carries the
opinion-and-provenance pairings beside it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, TypeVar

from argumentation.probabilistic.probabilistic import (
    ProbabilisticAF,
    summarize_defeat_relations as _kernel_summarize_defeat_relations,
)
from doxa import Opinion
from doxa.opinion import W

from propstore.opinion_provenance import OpinionWithProvenance
from propstore.probabilistic_relations import ProbabilisticRelation
from propstore.provenance import Provenance, ProvenanceStatus
from propstore.families.claims import Claim
from propstore.families.relations import Stance

_DOGMATIC_TOL = 1e-9
_COH_MAX_ITERATIONS = 100
_COH_TOLERANCE = 1e-12

_K = TypeVar("_K")


def _empty_arg_omissions() -> dict[str, NoCalibration]:
    return {}


def _empty_edge_omissions() -> dict[tuple[str, str], NoCalibration]:
    return {}


@dataclass(frozen=True)
class NoCalibration:
    """Sentinel for a probability-bearing input that lacks calibration.

    Honest ignorance (CLAUDE.md): rather than fabricate an opinion, the value
    layer returns this with the *reason* it could not calibrate and the fields
    that were missing. ``provenance`` records the absence as ``VACUOUS`` when set.
    """

    reason: str
    missing_fields: tuple[str, ...] = ()
    provenance: Provenance | None = None


class PreferenceLayerError(ValueError):
    """A propstore preference/COH layer precondition was violated."""


class COHDivergenceError(PreferenceLayerError):
    """COH enforcement did not reach a coherent fixed point in the iteration cap."""


class COHDogmaticInputError(PreferenceLayerError):
    """COH enforcement was given a dogmatic (``u ≈ 0``) argument opinion.

    A dogmatic opinion carries no evidence count, so its expectation cannot be
    honestly rescaled; the input is rejected rather than assigned a magic count.
    """


@dataclass(frozen=True)
class PropstorePrAF:
    """The PrAF kernel paired with opinion-and-provenance value records.

    :attr:`kernel` is the formal ``ProbabilisticAF`` fed plain float
    expectations. The ``p_*`` maps carry the :class:`OpinionWithProvenance`
    pairing each float was projected from, and the ``omitted_*`` maps record
    which arguments/edges had no calibration (kept as honest signals, never
    dropped). The omission maps are immutable.
    """

    kernel: ProbabilisticAF
    p_args: dict[str, OpinionWithProvenance]
    p_defeats: dict[tuple[str, str], OpinionWithProvenance]
    p_attacks: dict[tuple[str, str], OpinionWithProvenance] | None = None
    supports: frozenset[tuple[str, str]] = frozenset()
    p_supports: dict[tuple[str, str], OpinionWithProvenance] | None = None
    base_defeats: frozenset[tuple[str, str]] | None = None
    attack_relations: tuple[ProbabilisticRelation, ...] = ()
    support_relations: tuple[ProbabilisticRelation, ...] = ()
    direct_defeat_relations: tuple[ProbabilisticRelation, ...] = ()
    omitted_arguments: Mapping[str, NoCalibration] = field(default_factory=_empty_arg_omissions)
    omitted_relations: Mapping[tuple[str, str], NoCalibration] = field(
        default_factory=_empty_edge_omissions
    )

    @property
    def framework(self) -> Any:
        """The underlying Dung framework of the PrAF kernel."""

        return self.kernel.framework

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "omitted_arguments", MappingProxyType(dict(self.omitted_arguments))
        )
        object.__setattr__(
            self, "omitted_relations", MappingProxyType(dict(self.omitted_relations))
        )


@dataclass(frozen=True)
class EnforceCohResult:
    """Soft-mode COH enforcement result with explicit convergence state."""

    praf: PropstorePrAF
    converged: bool
    iterations: int
    max_violation: float


def propstore_praf_kernel(praf: PropstorePrAF | ProbabilisticAF) -> ProbabilisticAF:
    """Return the formal PrAF kernel from a propstore or kernel value."""

    return praf.kernel if isinstance(praf, PropstorePrAF) else praf


def _prov(status: ProvenanceStatus, *operations: str) -> Provenance:
    return Provenance(status=status, operations=operations)


def _owp(opinion: Opinion, status: ProvenanceStatus, *operations: str) -> OpinionWithProvenance:
    return OpinionWithProvenance(opinion=opinion, provenance=_prov(status, *operations))


def _missing_calibration(reason: str, *missing_fields: str) -> NoCalibration:
    return NoCalibration(
        reason=reason,
        missing_fields=missing_fields,
        provenance=_prov(ProvenanceStatus.VACUOUS, reason),
    )


def _defeat_summary_opinion(probability: float) -> OpinionWithProvenance:
    """An honest vacuous opinion carrying a defeat marginal as its base rate.

    The exact marginal is a *probability*, not calibrated belief evidence, so the
    opinion is vacuous (``u = 1``) with the marginal as its base rate and
    ``VACUOUS`` provenance (CLAUDE.md honest ignorance; Jøsang 2001, p.8). It
    never manufactures belief/disbelief mass.
    """

    p = max(0.0, min(1.0, float(probability)))
    base_rate = max(1e-9, min(1.0 - 1e-9, p))
    return OpinionWithProvenance(
        opinion=Opinion.vacuous(base_rate),
        provenance=_prov(ProvenanceStatus.VACUOUS, "defeat_probability_uncalibrated"),
    )


def p_arg_from_claim(claim: Claim) -> OpinionWithProvenance | NoCalibration:
    """Report that the canonical claim charter lacks a typed calibration prior."""

    _ = claim
    return _missing_calibration(
        "missing_claim_calibration",
        "source_prior_base_rate",
        "claim_probability",
        "source_quality_opinion",
    )


def p_relation_from_stance(stance: Stance) -> OpinionWithProvenance | NoCalibration:
    """Derive an edge-existence opinion from a stance's opinion/confidence fields.

    Explicit opinion columns win. A bare ``confidence`` is *not* evidence on its
    own: a confidence of 1.0 is not dogmatic certainty, and any confidence needs a
    base rate plus an effective sample size before it becomes a calibrated opinion
    (CLAUDE.md honest ignorance). Each missing piece yields a typed
    :class:`NoCalibration`.
    """

    belief = stance.opinion_belief
    disbelief = stance.opinion_disbelief
    uncertainty = stance.opinion_uncertainty
    base_rate = stance.opinion_base_rate
    if (
        belief is not None
        and disbelief is not None
        and uncertainty is not None
        and base_rate is not None
    ):
        return _owp(
            Opinion(
                belief,
                disbelief,
                uncertainty,
                base_rate,
                allow_dogmatic=uncertainty <= _DOGMATIC_TOL,
            ),
            ProvenanceStatus.STATED,
            "stance_opinion_columns",
        )
    if belief is not None or disbelief is not None or uncertainty is not None:
        return _missing_calibration("missing_base_rate", "opinion_base_rate")

    confidence = stance.confidence
    if confidence is None:
        return _missing_calibration(
            "missing_relation_calibration",
            "opinion_belief",
            "opinion_disbelief",
            "opinion_uncertainty",
            "confidence",
        )

    confidence_value = float(confidence)
    if confidence_value <= 1e-12:
        return _missing_calibration(
            "zero_confidence_without_opinion",
            "opinion_belief",
            "opinion_disbelief",
            "opinion_uncertainty",
        )
    if stance.opinion_base_rate is None:
        return _missing_calibration("missing_base_rate", "opinion_base_rate")
    if confidence_value >= 1.0 - 1e-12:
        return _missing_calibration(
            "raw_confidence_not_evidence", "effective_sample_size", "sample_size"
        )
    return _missing_calibration(
        "missing_evidence_count", "effective_sample_size", "sample_size"
    )


def p_defeat_from_stance(stance: Stance) -> OpinionWithProvenance | NoCalibration:
    """A defeat-existence opinion is derived the same way as any relation edge."""

    return p_relation_from_stance(stance)


def _required_expectation_map(
    opinions: Mapping[_K, OpinionWithProvenance],
) -> dict[_K, float]:
    return {key: pairing.expectation() for key, pairing in opinions.items()}


def _optional_expectation_map(
    opinions: Mapping[_K, OpinionWithProvenance] | None,
) -> dict[_K, float] | None:
    if opinions is None:
        return None
    return _required_expectation_map(opinions)


def _max_coh_violation(
    expectations: Mapping[str, float],
    attacks: frozenset[tuple[str, str]],
) -> float:
    max_violation = 0.0
    for src, tgt in attacks:
        if src == tgt:
            max_violation = max(max_violation, expectations[src] - 0.5)
        elif expectations[src] + expectations[tgt] > 1.0 + _COH_TOLERANCE:
            max_violation = max(
                max_violation, expectations[src] + expectations[tgt] - 1.0
            )
    return max(0.0, max_violation)


def enforce_coh(
    praf: PropstorePrAF,
    *,
    max_iterations: int | None = None,
    soft: bool = False,
) -> PropstorePrAF | EnforceCohResult:
    """Enforce COH rationality on opinion-valued argument expectations.

    COH (Hunter 2013): an argument and an argument it attacks cannot both be
    near-certain — their expectations must sum to at most one, and a self-attacker
    is capped at one half. This rescales violating expectations and reconstructs
    each argument's opinion from its preserved evidence count. A dogmatic input
    (no evidence count) is rejected (:class:`COHDogmaticInputError`); failure to
    converge within the cap raises :class:`COHDivergenceError` (or, in ``soft``
    mode, returns a non-converged :class:`EnforceCohResult`).
    """

    if max_iterations is None:
        max_iterations = _COH_MAX_ITERATIONS

    attacks = praf.framework.attacks
    if attacks is None:
        raise PreferenceLayerError("enforce_coh requires explicit pre-preference attacks")

    expectations: dict[str, float] = {}
    evidence_n: dict[str, float] = {}
    base_rates: dict[str, float] = {}
    for arg, pairing in praf.p_args.items():
        opinion = pairing.opinion
        expectations[arg] = opinion.expectation()
        base_rates[arg] = opinion.base_rate
        if opinion.uncertainty <= _DOGMATIC_TOL:
            raise COHDogmaticInputError(
                "enforce_coh cannot reconstruct dogmatic argument opinions "
                "without a paper-defined evidence count"
            )
        evidence_n[arg] = W * (1.0 / opinion.uncertainty - 1.0)

    changed = False
    iterations = 0
    for _ in range(max_iterations):
        any_violation = False
        for src, tgt in attacks:
            if src == tgt:
                if expectations[src] > 0.5 + _COH_TOLERANCE:
                    expectations[src] = 0.5
                    any_violation = True
                    changed = True
            else:
                total = expectations[src] + expectations[tgt]
                if total > 1.0 + _COH_TOLERANCE:
                    factor = 1.0 / total
                    expectations[src] *= factor
                    expectations[tgt] *= factor
                    any_violation = True
                    changed = True
        if not any_violation:
            break
        iterations += 1

    max_violation = _max_coh_violation(expectations, attacks)
    converged = max_violation <= _COH_TOLERANCE
    if not converged:
        if soft:
            return EnforceCohResult(praf, False, iterations, max_violation)
        raise COHDivergenceError(
            f"enforce_coh did not converge within {max_iterations} iterations"
        )
    if not changed:
        return EnforceCohResult(praf, True, iterations, max_violation) if soft else praf

    new_p_args: dict[str, OpinionWithProvenance] = {}
    for arg, pairing in praf.p_args.items():
        original = pairing.opinion
        if abs(expectations[arg] - original.expectation()) < 1e-12:
            new_p_args[arg] = pairing
            continue
        n = evidence_n[arg]
        a = base_rates[arg]
        e_target = expectations[arg]
        p = (e_target * (n + W) - a * W) / n if n > 1e-12 else e_target
        p = max(0.0, min(1.0, p))
        new_p_args[arg] = _owp(
            Opinion.from_probability(p, n, a),
            ProvenanceStatus.CALIBRATED,
            "coh_rescaled",
        )

    kernel = ProbabilisticAF(
        framework=praf.kernel.framework,
        p_args=_required_expectation_map(new_p_args),
        p_defeats=_required_expectation_map(praf.p_defeats),
        p_attacks=_optional_expectation_map(praf.p_attacks),
        supports=praf.supports,
        p_supports=_optional_expectation_map(praf.p_supports),
        base_defeats=praf.base_defeats,
    )
    enforced = PropstorePrAF(
        kernel=kernel,
        p_args=new_p_args,
        p_defeats=praf.p_defeats,
        p_attacks=praf.p_attacks,
        supports=praf.supports,
        p_supports=praf.p_supports,
        base_defeats=praf.base_defeats,
        attack_relations=praf.attack_relations,
        support_relations=praf.support_relations,
        direct_defeat_relations=praf.direct_defeat_relations,
        omitted_arguments=praf.omitted_arguments,
        omitted_relations=praf.omitted_relations,
    )
    return EnforceCohResult(enforced, True, iterations, max_violation) if soft else enforced


def summarize_defeat_relations(
    praf: PropstorePrAF | ProbabilisticAF,
    *,
    include_derived: bool = True,
) -> tuple[ProbabilisticRelation, ...]:
    """Report exact defeat marginals as provenance-bearing relation records.

    Each marginal is carried as a *vacuous* opinion (see
    :func:`_defeat_summary_opinion`): the system never claims calibrated evidence
    for a computed probability. Direct (base) defeats are distinguished from
    Cayrol-derived defeats by ``kind``.
    """

    kernel = propstore_praf_kernel(praf)
    probabilities = _kernel_summarize_defeat_relations(kernel, include_derived=include_derived)
    direct_defeats = (
        kernel.base_defeats if kernel.base_defeats is not None else kernel.framework.defeats
    )
    return tuple(
        ProbabilisticRelation(
            kind="direct_defeat" if edge in direct_defeats else "derived_defeat",
            source=edge[0],
            target=edge[1],
            opinion=_defeat_summary_opinion(probability).opinion,
            derived_from=(),
        )
        for edge, probability in probabilities.items()
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
