"""Calibration module — bridges raw model outputs to Opinion algebra.

Implements temperature scaling (Guo et al. 2017), corpus CDF calibration,
categorical-to-opinion mapping, and ECE computation.

This module depends only on propstore.opinion and stdlib.
"""

from __future__ import annotations

import bisect
import math
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from propstore.core.base_rates import BaseRateUnresolved
from propstore.core.id_types import AssertionId
from propstore.opinion import Opinion, from_evidence, from_probability
from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    compose_provenance,
)


# ---------------------------------------------------------------------------
# 1. Temperature Scaling
# ---------------------------------------------------------------------------


def _softmax(logits: list[float]) -> list[float]:
    """Numerically stable softmax."""
    max_z = max(logits)
    exps = [math.exp(z - max_z) for z in logits]
    total = sum(exps)
    return [e / total for e in exps]


def _entropy(probs: list[float]) -> float:
    """Shannon entropy H = -sum p log p."""
    return -sum(p * math.log(p) for p in probs if p > 0)


@dataclass
class TemperatureScaler:
    """Post-hoc calibration via temperature scaling (Guo et al. 2017, p.5).

    T > 1 softens (reduces overconfidence), T < 1 sharpens.
    T = 1 is identity. Does not change argmax (Guo 2017, p.5).
    """

    temperature: float = 1.0

    def __post_init__(self) -> None:
        if self.temperature <= 0:
            raise ValueError(f"Temperature must be > 0, got {self.temperature}")

    def calibrate_logits(self, logits: list[float]) -> list[float]:
        """Apply temperature scaling to logits, return calibrated probabilities.

        softmax(z / T) per Guo et al. 2017, p.5, Eq: q_i = max_k softmax(z_i/T)_k
        """
        scaled = [z / self.temperature for z in logits]
        return _softmax(scaled)

    @staticmethod
    def fit(logits_list: list[list[float]], labels: list[int]) -> TemperatureScaler:
        """Find optimal T by minimizing NLL on validation data.

        Per Guo et al. 2017, p.5: min_T -sum_i log(pi(y_i | z_i, T))
        Since this is 1D convex optimization, use simple line search.
        """
        if len(logits_list) != len(labels):
            raise ValueError("logits_list and labels must have same length")
        if len(logits_list) == 0:
            raise ValueError("Need at least one sample to fit")

        def nll(t: float) -> float:
            total = 0.0
            for logits, label in zip(logits_list, labels):
                probs = _softmax([z / t for z in logits])
                p = probs[label]
                total -= math.log(max(p, 1e-15))
            return total

        # Golden section search on [0.01, 10.0]
        a, b = 0.01, 10.0
        gr = (math.sqrt(5) + 1) / 2
        tol = 1e-5

        c = b - (b - a) / gr
        d = a + (b - a) / gr

        for _ in range(100):
            if abs(b - a) < tol:
                break
            if nll(c) < nll(d):
                b = d
            else:
                a = c
            c = b - (b - a) / gr
            d = a + (b - a) / gr

        best_t = (a + b) / 2
        return TemperatureScaler(temperature=best_t)


# ---------------------------------------------------------------------------
# 2. Corpus CDF Calibration
# ---------------------------------------------------------------------------


class CorpusCalibrator:
    """Calibrate embedding distances against corpus distribution.

    Converts model-specific distances to corpus-relative percentile ranks,
    addressing the problem that raw distances are unnormalized and model-
    dependent (noted in code survey: relate.py:52 interpolates raw distance
    into LLM prompt without normalization).

    Evidence model: corpus size measures how well we know the *distribution*
    of distances, not how much evidence we have for any *individual claim*.
    The effective sample size for a specific query is the number of reference
    distances within a local window — the local CDF density — capped at a
    maximum to prevent fabricated certainty.

    Per Sensoy et al. 2018 (p.3-4): evidence counts represent actual
    observations supporting a class, not corpus distribution statistics.
    Per Josang 2001 (p.8): vacuous opinion (0,0,1,a) honestly represents
    total ignorance; near-zero u fabricates certainty.
    """

    # Maximum effective evidence count. Even with dense local data, we cap
    # evidence to reflect that corpus calibration is indirect evidence for
    # claim truth — it measures distributional similarity, not ground truth.
    _MAX_N_EFF = 50

    def __init__(
        self,
        reference_distances: list[float],
        *,
        corpus_base_rate: float = 0.5,
    ) -> None:
        """Build CDF from reference corpus of pairwise distances.

        Args:
            reference_distances: Pairwise distances from the corpus.
                Sorted internally for CDF lookup.
        """
        if not reference_distances:
            raise ValueError("Need at least one reference distance")
        if corpus_base_rate <= 0.0 or corpus_base_rate >= 1.0:
            raise ValueError("corpus_base_rate must be in the open interval (0, 1)")
        self._sorted = sorted(reference_distances)
        self._n = len(self._sorted)
        self._base_rate = corpus_base_rate

    @classmethod
    def from_cdf(
        cls,
        corpus_cdf: list[float],
        *,
        corpus_base_rate: float = 0.5,
    ) -> CorpusCalibrator:
        return cls(corpus_cdf, corpus_base_rate=corpus_base_rate)

    def _provenance(self) -> Provenance:
        return Provenance(
            status=ProvenanceStatus.CALIBRATED,
            witnesses=(
                ProvenanceWitness(
                    asserter="propstore.calibrate.CorpusCalibrator",
                    timestamp=datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ",
                    ),
                    source_artifact_code="corpus_cdf_calibration",
                    method="corpus_cdf_calibration",
                ),
            ),
            operations=("corpus_cdf_calibration",),
        )

    def percentile(self, distance: float) -> float:
        """Return percentile rank of distance within corpus [0.0, 1.0].

        0.0 = most similar (smallest distance), 1.0 = most dissimilar.
        """
        pos = bisect.bisect_right(self._sorted, distance)
        return pos / self._n

    def _effective_sample_size(self, distance: float) -> float:
        """Compute local effective sample size around the query distance.

        Uses a kernel bandwidth h = 1/sqrt(n) to define a local window
        [distance - h, distance + h], then counts reference distances
        within that window. This reflects how many data points inform
        the CDF estimate at this specific location.

        The count is capped at _MAX_N_EFF because corpus distances are
        indirect evidence for claim truth — a large corpus tells us the
        distance metric is well-calibrated, not that we have strong
        evidence for any particular claim.

        Per Sensoy et al. 2018 (p.3-4): evidence counts should represent
        actual observations supporting a hypothesis.

        Returns:
            Effective sample size in [0, _MAX_N_EFF].
        """
        # Bandwidth: shrinks as corpus grows, but not as fast as 1/n
        # (which would make local counts ~1 for large n). 1/sqrt(n) is
        # the standard kernel density bandwidth scaling.
        h = 1.0 / math.sqrt(self._n)

        # Count points in [distance - h, distance + h] using binary search
        lo = bisect.bisect_left(self._sorted, distance - h)
        hi = bisect.bisect_right(self._sorted, distance + h)
        local_count = hi - lo

        # Corpus confidence: a corpus of 1-2 points tells us almost nothing
        # about the distance distribution. Scale local evidence by how much
        # we trust the corpus itself. We need ~10 points before the CDF
        # estimate becomes meaningful (asymptotic normality of the empirical
        # CDF requires sqrt(n) >> 1). This factor smoothly ramps from ~0
        # at n=1 to ~1 at n>=10.
        corpus_confidence = min(1.0, (self._n - 1) / 9.0)

        return min(float(local_count) * corpus_confidence, float(self._MAX_N_EFF))

    def to_opinion(self, raw_score: float) -> Opinion:
        """Convert distance to opinion via corpus calibration.

        The effective sample size is based on local CDF density — how many
        reference distances are near the query point — NOT the full corpus
        size. This prevents a 10,000-element corpus from fabricating
        near-dogmatic certainty (u ~ 0.0002).

        Per Sensoy et al. 2018 (p.3-4): r = p * n_eff, s = (1-p) * n_eff.
        Per Josang 2001 (p.20-21, Def 12): evidence maps to opinion via
            b = r/(r+s+W), d = s/(r+s+W), u = W/(r+s+W).
        """
        p = 1.0 - self.percentile(raw_score)  # similarity = 1 - percentile
        n_eff = self._effective_sample_size(raw_score)
        return from_probability(
            p,
            n_eff,
            self._base_rate,
            provenance=self._provenance(),
        )


# ---------------------------------------------------------------------------
# 3. Categorical-to-Opinion Mapping
# ---------------------------------------------------------------------------

_KNOWN_CATEGORIES = frozenset({"strong", "moderate", "weak", "none"})


class CalibrationSource(StrEnum):
    MEASURED = "measured"
    USER_DEFAULT = "user_default"
    MODULE_DEFAULT = "module_default"
    VACUOUS = "vacuous"


@dataclass(frozen=True)
class CategoryPrior:
    """Explicit provenance-bearing base rate for a categorical label."""

    category: str
    value: float
    source: CalibrationSource
    provenance: Provenance

    def __post_init__(self) -> None:
        normalized = self.category.lower()
        if normalized not in _KNOWN_CATEGORIES:
            raise ValueError(f"Unknown category {self.category!r}")
        if self.value <= 0.0 or self.value >= 1.0:
            raise ValueError("CategoryPrior.value must be in the open interval (0, 1)")
        object.__setattr__(self, "category", normalized)
        object.__setattr__(self, "source", CalibrationSource(self.source))


@dataclass(frozen=True)
class CategoryPriorRegistry:
    """Explicit lookup table for user- or measurement-supplied category priors."""

    priors: Mapping[str, CategoryPrior]

    def __post_init__(self) -> None:
        normalized: dict[str, CategoryPrior] = {}
        for category, prior in self.priors.items():
            key = str(category).lower()
            if key != prior.category:
                raise ValueError(
                    f"CategoryPrior key {category!r} does not match prior category {prior.category!r}"
                )
            normalized[key] = prior
        object.__setattr__(self, "priors", normalized)

    def get(self, category: str) -> CategoryPrior | None:
        return self.priors.get(category.lower())


def _provenance(status: ProvenanceStatus, operation: str) -> Provenance:
    return Provenance(status=status, witnesses=(), operations=(operation,))


def _validate_category(category: str) -> str:
    normalized = category.lower()
    if normalized not in _KNOWN_CATEGORIES:
        raise ValueError(
            f"Unknown category '{category}', expected one of {sorted(_KNOWN_CATEGORIES)}"
        )
    return normalized


def _resolve_prior(
    category: str,
    *,
    prior: CategoryPrior | None,
    prior_registry: CategoryPriorRegistry | None,
) -> CategoryPrior | None:
    if prior is not None and prior_registry is not None:
        raise ValueError("Specify either prior or prior_registry, not both")
    resolved = prior if prior is not None else None
    if resolved is None and prior_registry is not None:
        resolved = prior_registry.get(category)
    if resolved is not None and resolved.category != category:
        raise ValueError(
            f"CategoryPrior category {resolved.category!r} does not match category {category!r}"
        )
    return resolved


def load_calibration_counts(conn) -> dict[tuple[int, str], tuple[int, int]] | None:
    """Load calibration validation data from sidecar.

    Returns dict mapping (pass_number, category) to (correct, total),
    or None if no calibration data exists.
    Per Guo et al. (2017): raw outputs need calibration against validation data.
    """
    try:
        rows = conn.execute(
            "SELECT pass_number, category, correct_count, total_count "
            "FROM calibration_counts"
        ).fetchall()
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc).lower():
            raise
        return None
    if not rows:
        return None
    return {(row[0], row[1]): (row[2], row[3]) for row in rows}


def categorical_to_opinion(
    category: str,
    pass_number: int,
    *,
    calibration_counts: dict[tuple[int, str], tuple[int, int]] | None = None,
    prior: CategoryPrior | None = None,
    prior_registry: CategoryPriorRegistry | None = None,
) -> Opinion | BaseRateUnresolved:
    """Convert categorical LLM output to opinion.

    Without calibration data (calibration_counts=None), returns vacuous
    opinion -- honestly representing that we have no empirical basis for
    confidence. This replaces the fabricated lookup table at relate.py:76-83.
    Per Josang 2001 (p.8): vacuous opinion (0,0,1,a) is the correct
    representation of total ignorance.

    With calibration data, calibration_counts maps (pass_number, category)
    to (correct_count, total_count). These become evidence counts:
        r = correct_count (positive evidence)
        s = total_count - correct_count (negative evidence)
    Per Josang 2001 (p.20-21, Def 12): evidence maps to opinion via
        b = r/(r+s+2), d = s/(r+s+2), u = 2/(r+s+2)

    Args:
        category: "strong", "moderate", "weak", or "none"
        pass_number: 1 or 2
        calibration_counts: Optional dict of (pass, cat) -> (correct, total)
            from a validation set of human-judged stances.

    Returns:
        Opinion with an explicit base rate, or BaseRateUnresolved when no
        sourced CategoryPrior is supplied.
    """
    cat = _validate_category(category)
    resolved_prior = _resolve_prior(
        cat,
        prior=prior,
        prior_registry=prior_registry,
    )
    if resolved_prior is None:
        return BaseRateUnresolved(
            AssertionId(f"ps:assertion:category_prior:{cat}:pass:{pass_number}"),
            "missing_base_rate",
            ("category_prior",),
        )
    base_rate = resolved_prior.value
    prior_provenance = resolved_prior.provenance

    if calibration_counts is None:
        return Opinion.vacuous(a=base_rate, provenance=prior_provenance)

    key = (pass_number, cat)
    if key not in calibration_counts:
        return Opinion.vacuous(a=base_rate, provenance=prior_provenance)

    correct, total = calibration_counts[key]
    if total <= 0:
        return Opinion.vacuous(a=base_rate, provenance=prior_provenance)

    r = float(correct)
    s = float(total - correct)
    counts_provenance = _provenance(
        ProvenanceStatus.CALIBRATED,
        "categorical_calibration_counts",
    )
    return from_evidence(
        r,
        s,
        base_rate,
        provenance=compose_provenance(
            prior_provenance,
            counts_provenance,
            operation="categorical_calibration_counts",
        ),
    )


# ---------------------------------------------------------------------------
# 4. Probability-to-Opinion
# ---------------------------------------------------------------------------


def calibrated_probability_to_opinion(
    probability: float,
    effective_sample_size: float,
    base_rate: float = 0.5,
) -> Opinion:
    """Convert calibrated probability to opinion via Beta parameterization.

    Per Sensoy et al. 2018 (p.3-4): evidence e_k maps to Dirichlet alpha_k = e_k + 1.
    Per Josang 2001 (p.20-21, Def 12): r = 2b/u, s = 2d/u with prior weight W=2.
    Combined: r = p * n, s = (1-p) * n where n = effective_sample_size.

    When n=0, returns vacuous opinion (Josang 2001, p.8).
    When n is large, returns narrow opinion near probability.

    This is a thin wrapper around opinion.from_probability() with explicit
    documentation of the literature grounding.
    """
    if probability < 0.0 or probability > 1.0:
        raise ValueError(f"probability={probability} not in [0, 1]")
    if effective_sample_size < 0.0:
        raise ValueError(f"effective_sample_size={effective_sample_size} must be >= 0")
    return from_probability(probability, effective_sample_size, base_rate)


# ---------------------------------------------------------------------------
# 5. ECE Computation
# ---------------------------------------------------------------------------


def expected_calibration_error(
    confidences: list[float],
    correct: list[bool],
    n_bins: int = 15,
) -> float:
    """Compute Expected Calibration Error.

    Per Guo et al. 2017 (p.1): ECE = sum_m (|B_m|/n) * |acc(B_m) - conf(B_m)|
    where B_m is the set of samples in bin m.

    Standard metric for measuring miscalibration.
    """
    if len(confidences) != len(correct):
        raise ValueError("confidences and correct must have same length")
    n = len(confidences)
    if n == 0:
        return 0.0

    # Build uniform-width bins
    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    bin_correct: list[list[bool]] = [[] for _ in range(n_bins)]
    bin_confs: list[list[float]] = [[] for _ in range(n_bins)]

    for conf, cor in zip(confidences, correct):
        # Find bin index: [0/n_bins, 1/n_bins), [1/n_bins, 2/n_bins), ..., [(n-1)/n_bins, 1.0]
        idx = min(int(conf * n_bins), n_bins - 1)
        bin_correct[idx].append(cor)
        bin_confs[idx].append(conf)

    ece = 0.0
    for bc, bf in zip(bin_correct, bin_confs):
        if len(bc) == 0:
            continue
        acc = sum(1 for c in bc if c) / len(bc)
        avg_conf = sum(bf) / len(bf)
        ece += (len(bc) / n) * abs(acc - avg_conf)

    return ece
