"""Propstore adapters for probabilistic argumentation.

The formal PrAF algorithms live in `argumentation.probabilistic`. This module
keeps propstore-owned calibration, opinion, provenance, and diagnostic surfaces.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from argumentation.probabilistic import (
    PrAFResult,
    ProbabilisticAF as ProbabilisticArgumentationFramework,
    summarize_defeat_relations as _summarize_defeat_probabilities,
)

from propstore.core.row_types import ClaimRow, ClaimRowInput, coerce_claim_row
from propstore.opinion import Opinion, W, discount, from_probability
from propstore.probabilistic_relations import ProbabilisticRelation, relation_from_row
from propstore.provenance import Provenance, ProvenanceStatus


@dataclass(frozen=True)
class NoCalibration:
    """Sentinel for probability-bearing inputs that lack calibration."""

    reason: str
    missing_fields: tuple[str, ...] = ()
    provenance: Provenance | None = None


class PreferenceLayerError(ValueError):
    pass


@dataclass(frozen=True)
class PropstorePrAF:
    """Propstore-owned PrAF adapter with opinion and provenance metadata."""

    kernel: ProbabilisticArgumentationFramework
    p_args: dict[str, Opinion]
    p_defeats: dict[tuple[str, str], Opinion]
    p_attacks: dict[tuple[str, str], Opinion] | None = None
    supports: frozenset[tuple[str, str]] = frozenset()
    p_supports: dict[tuple[str, str], Opinion] | None = None
    base_defeats: frozenset[tuple[str, str]] | None = None
    attack_relations: tuple[ProbabilisticRelation, ...] = ()
    support_relations: tuple[ProbabilisticRelation, ...] = ()
    direct_defeat_relations: tuple[ProbabilisticRelation, ...] = ()
    omitted_arguments: dict[str, NoCalibration] | None = None
    omitted_relations: dict[tuple[str, str], NoCalibration] | None = None

    @property
    def framework(self):
        return self.kernel.framework

    def __post_init__(self) -> None:
        object.__setattr__(self, "omitted_arguments", dict(self.omitted_arguments or {}))
        object.__setattr__(self, "omitted_relations", dict(self.omitted_relations or {}))


def _opinion_expectation_map(
    opinions: Mapping[Any, Opinion] | None,
) -> dict[Any, float] | None:
    if opinions is None:
        return None
    return {key: opinion.expectation() for key, opinion in opinions.items()}


def propstore_praf_kernel(praf: PropstorePrAF | ProbabilisticArgumentationFramework) -> ProbabilisticArgumentationFramework:
    if isinstance(praf, PropstorePrAF):
        return praf.kernel
    return praf


def _praf_provenance(status: ProvenanceStatus, operation: str) -> Provenance:
    return Provenance(status=status, witnesses=(), operations=(operation,))


def _defeat_summary_opinion(probability: float) -> Opinion:
    p = max(0.0, min(1.0, float(probability)))
    provenance = _praf_provenance(
        ProvenanceStatus.CALIBRATED,
        "defeat_distribution_variance",
    )
    variance = p * (1.0 - p)
    if variance <= 1e-12:
        return Opinion(
            p,
            1.0 - p,
            0.0,
            0.5,
            provenance,
            allow_dogmatic=True,  # tautology citation: Josang 2001 dogmatic opinion has u=0.
        )

    dogmatic = Opinion(
        p,
        1.0 - p,
        0.0,
        0.5,
        allow_dogmatic=True,  # tautology citation: Josang 2001 dogmatic opinion has u=0.
    )
    max_uncertainty = dogmatic.maximize_uncertainty().u
    normalized_variance = min(1.0, variance / 0.25)
    uncertainty = max_uncertainty * normalized_variance
    belief = p - 0.5 * uncertainty
    disbelief = 1.0 - belief - uncertainty
    return Opinion(belief, disbelief, uncertainty, 0.5, provenance)


def _missing_calibration(reason: str, *missing_fields: str) -> NoCalibration:
    return NoCalibration(
        reason=reason,
        missing_fields=tuple(missing_fields),
        provenance=_praf_provenance(ProvenanceStatus.VACUOUS, reason),
    )


def _opinion_from_payload(
    payload: Mapping[str, Any],
    *,
    prefix: str,
    operation: str,
) -> Opinion | None:
    b = payload.get(f"{prefix}belief")
    d = payload.get(f"{prefix}disbelief")
    u = payload.get(f"{prefix}uncertainty")
    a = payload.get(f"{prefix}base_rate", 0.5)
    if b is None or d is None or u is None:
        return None
    return Opinion(
        float(b),
        float(d),
        float(u),
        float(a),
        _praf_provenance(ProvenanceStatus.STATED, operation),
    )


def p_arg_from_claim(claim: ClaimRowInput | dict) -> Opinion | NoCalibration:
    """Derive argument-existence opinion from a calibrated claim row."""
    if isinstance(claim, ClaimRow):
        claim_opinion = _opinion_from_payload(
            claim.attributes,
            prefix="opinion_",
            operation="claim_opinion_columns",
        )
        if claim_opinion is not None:
            return claim_opinion

        source_trust = None if claim.source is None else claim.source.trust
        prior_base_rate = (
            None if source_trust is None else source_trust.prior_base_rate
        )
        claim_probability = claim.attributes.get("claim_probability")
        effective_sample_size = claim.attributes.get("effective_sample_size", claim.sample_size)
        if claim_probability is None and claim.attributes.get("confidence") is not None:
            claim_probability = claim.attributes.get("confidence")
        quality_opinion = None if source_trust is None else source_trust.quality

        has_structured_fields = (
            prior_base_rate is not None
            or claim_probability is not None
            or quality_opinion is not None
        )
        if not has_structured_fields:
            return _missing_calibration(
                "missing_claim_calibration",
                "source_prior_base_rate",
                "claim_probability",
                "source_quality_opinion",
            )

        prior = 0.5 if prior_base_rate is None else float(prior_base_rate)
        omega_prior = Opinion.vacuous(
            a=prior,
            provenance=_praf_provenance(ProvenanceStatus.VACUOUS, "claim_prior"),
        )
        if claim_probability is not None and effective_sample_size is not None:
            omega_claim = from_probability(
                float(claim_probability),
                float(effective_sample_size),
                prior,
                provenance=_praf_provenance(ProvenanceStatus.CALIBRATED, "claim_evidence"),
            )
        else:
            omega_claim = omega_prior
        if quality_opinion is None:
            return omega_claim
        return discount(quality_opinion, omega_claim)

    if not isinstance(claim, dict):
        claim = coerce_claim_row(claim)
        return p_arg_from_claim(claim)

    source = claim.get("source")
    claim_opinion = _opinion_from_payload(
        claim,
        prefix="opinion_",
        operation="claim_opinion_columns",
    )
    if claim_opinion is not None:
        return claim_opinion

    source_trust = source.get("trust") if isinstance(source, dict) else None
    prior_base_rate = claim.get("source_prior_base_rate")
    if prior_base_rate is None and isinstance(source_trust, dict):
        prior_base_rate = source_trust.get("prior_base_rate")

    claim_probability = claim.get("claim_probability")
    effective_sample_size = claim.get("effective_sample_size")
    if claim_probability is None and claim.get("confidence") is not None:
        claim_probability = claim.get("confidence")
    if effective_sample_size is None and claim.get("sample_size") is not None:
        effective_sample_size = claim.get("sample_size")

    quality_payload = claim.get("source_quality_opinion")
    if quality_payload is None and isinstance(source_trust, dict):
        quality_payload = source_trust.get("quality")

    has_structured_fields = (
        prior_base_rate is not None
        or claim_probability is not None
        or quality_payload is not None
    )
    if not has_structured_fields:
        return _missing_calibration(
            "missing_claim_calibration",
            "source_prior_base_rate",
            "claim_probability",
            "source_quality_opinion",
        )

    prior = 0.5 if prior_base_rate is None else float(prior_base_rate)
    omega_prior = Opinion.vacuous(
        a=prior,
        provenance=_praf_provenance(ProvenanceStatus.VACUOUS, "claim_prior"),
    )
    if claim_probability is not None and effective_sample_size is not None:
        omega_claim = from_probability(
            float(claim_probability),
            float(effective_sample_size),
            prior,
            provenance=_praf_provenance(ProvenanceStatus.CALIBRATED, "claim_evidence"),
        )
    else:
        omega_claim = omega_prior

    if quality_payload is None:
        return omega_claim
    if not isinstance(quality_payload, dict):
        raise ValueError("source_quality_opinion must be a mapping with b/d/u/a")
    required = {"b", "d", "u", "a"}
    if not required.issubset(quality_payload):
        raise ValueError("source_quality_opinion must contain b, d, u, and a")
    omega_source_quality = Opinion(
        float(quality_payload["b"]),
        float(quality_payload["d"]),
        float(quality_payload["u"]),
        float(quality_payload["a"]),
        _praf_provenance(ProvenanceStatus.CALIBRATED, "source_quality"),
    )
    return discount(omega_source_quality, omega_claim)


def p_relation_from_stance(stance: dict) -> Opinion | NoCalibration:
    """Derive an edge-existence opinion from a stance's opinion columns."""
    opinion = _opinion_from_payload(
        stance,
        prefix="opinion_",
        operation="stance_opinion_columns",
    )
    if opinion is not None:
        return opinion

    confidence = stance.get("confidence")
    a = float(stance.get("opinion_base_rate", 0.5))
    if confidence is not None:
        confidence_value = float(confidence)
        if confidence_value <= 1e-12:
            return _missing_calibration(
                "zero_confidence_without_opinion",
                "opinion_belief",
                "opinion_disbelief",
                "opinion_uncertainty",
            )
        if confidence_value >= 1.0 - 1e-12:
            return Opinion.dogmatic_true(
                a,
                provenance=_praf_provenance(ProvenanceStatus.STATED, "stance_confidence"),
            )
        return from_probability(
            confidence_value,
            1,
            a,
            provenance=_praf_provenance(ProvenanceStatus.STATED, "stance_confidence"),
        )

    return _missing_calibration(
        "missing_relation_calibration",
        "opinion_belief",
        "opinion_disbelief",
        "opinion_uncertainty",
        "confidence",
    )


def p_defeat_from_stance(stance: dict) -> Opinion | NoCalibration:
    return p_relation_from_stance(stance)


def enforce_coh(praf: PropstorePrAF) -> PropstorePrAF:
    """Enforce COH rationality on propstore opinion-valued argument probabilities."""
    attacks = praf.framework.attacks
    if attacks is None:
        raise PreferenceLayerError("enforce_coh requires explicit pre-preference attacks")

    expectations: dict[str, float] = {}
    evidence_n: dict[str, float] = {}
    base_rates: dict[str, float] = {}

    for arg, op in praf.p_args.items():
        if not isinstance(op, Opinion):
            raise TypeError("propstore enforce_coh requires Opinion-valued p_args")
        expectations[arg] = op.expectation()
        base_rates[arg] = op.a
        if op.u > 1e-9:
            evidence_n[arg] = W * (1.0 / op.u - 1.0)
        else:
            evidence_n[arg] = 10.0

    changed = False
    for _ in range(100):
        any_violation = False
        for src, tgt in attacks:
            if src == tgt:
                if expectations[src] > 0.5 + 1e-12:
                    expectations[src] = 0.5
                    any_violation = True
                    changed = True
            else:
                total = expectations[src] + expectations[tgt]
                if total > 1.0 + 1e-12:
                    factor = 1.0 / total
                    expectations[src] *= factor
                    expectations[tgt] *= factor
                    any_violation = True
                    changed = True
        if not any_violation:
            break

    if not changed:
        return praf

    new_p_args: dict[str, Opinion] = {}
    for arg in praf.p_args:
        original = praf.p_args[arg]
        if not isinstance(original, Opinion):
            raise TypeError("propstore enforce_coh requires Opinion-valued p_args")
        if abs(expectations[arg] - original.expectation()) < 1e-12:
            new_p_args[arg] = original
        else:
            n = evidence_n[arg]
            a = base_rates[arg]
            e_target = expectations[arg]
            p = (e_target * (n + W) - a * W) / n if n > 1e-12 else e_target
            p = max(0.0, min(1.0, p))
            new_p_args[arg] = from_probability(p, n, a)

    kernel = ProbabilisticArgumentationFramework(
        framework=praf.kernel.framework,
        p_args={arg: opinion.expectation() for arg, opinion in new_p_args.items()},
        p_defeats={edge: opinion.expectation() for edge, opinion in praf.p_defeats.items()},
        p_attacks=_opinion_expectation_map(praf.p_attacks),
        supports=praf.supports,
        p_supports=_opinion_expectation_map(praf.p_supports),
        base_defeats=praf.base_defeats,
    )
    return PropstorePrAF(
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


def summarize_defeat_relations(
    praf: PropstorePrAF | ProbabilisticArgumentationFramework,
    *,
    include_derived: bool = True,
) -> tuple[ProbabilisticRelation, ...]:
    """Compute exact defeat marginals as provenance-bearing relation records."""
    kernel = propstore_praf_kernel(praf)
    probabilities = _summarize_defeat_probabilities(
        kernel,
        include_derived=include_derived,
    )
    direct_defeats = kernel.base_defeats if kernel.base_defeats is not None else kernel.framework.defeats
    records: list[ProbabilisticRelation] = []
    for edge, probability in probabilities.items():
        kind = "direct_defeat" if edge in direct_defeats else "derived_defeat"
        records.append(
            relation_from_row(
                kind=kind,
                source=edge[0],
                target=edge[1],
                opinion=_defeat_summary_opinion(probability),
                row=None,
                derived_from=(),
            )
        )
    return tuple(records)
