"""Calibration — bridge raw model outputs to the subjective-logic opinion algebra.

Corpus CDF calibration, categorical-to-opinion mapping, and calibrated-probability
mapping. Every probability produced here becomes a ``doxa.Opinion`` — the one
canonical opinion type (CLAUDE.md substrate-boundary rule) — and absence of
calibration data becomes a vacuous opinion (Jøsang 2001, p.8) or an explicit
:class:`~propstore.core.base_rates.BaseRateUnresolved`, never a fabricated number.

The generic calibration-quality metrics and temperature scaling (Guo et al. 2017)
live in the standalone ``calibration`` substrate package; this module imports and
re-exports them directly (no propstore re-spelling) so the propstore-specific
opinion glue and the package metrics share one canonical surface.

Opinions returned here are provenance-free ``doxa`` values; their typed provenance
is attached at the call site that stores them (the pairing-beside-opinion
discipline), so this module depends only on ``doxa`` and stdlib for its numerics.
"""

from __future__ import annotations

import bisect
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from calibration import (
    TemperatureScaler as TemperatureScaler,
)
from calibration import (
    brier_score as brier_score,
)
from calibration import (
    expected_calibration_error as expected_calibration_error,
)
from calibration import (
    log_loss as log_loss,
)
from doxa import Opinion

from propstore.core.base_rates import BaseRateUnresolved
from propstore.core.id_types import AssertionId
from propstore.provenance import Provenance


# ---------------------------------------------------------------------------
# Corpus CDF Calibration
# ---------------------------------------------------------------------------


class CorpusCalibrator:
    """Calibrate embedding distances against a corpus distance distribution.

    Converts model-specific distances to corpus-relative percentile ranks. The
    effective sample size for a query is the *local* CDF density (count of nearby
    reference distances), capped at :attr:`_MAX_N_EFF`, because corpus distances
    are indirect evidence for claim truth: a large corpus tells us the metric is
    well-calibrated, not that we have strong evidence for any individual claim.

    Per Sensoy et al. 2018 (p.3-4): evidence counts represent actual observations
    supporting a class, not corpus distribution statistics. Per Jøsang 2001 (p.8):
    a vacuous opinion ``(0,0,1,a)`` honestly represents total ignorance; a
    near-zero ``u`` fabricates certainty.
    """

    _MAX_N_EFF = 50

    def __init__(
        self,
        reference_distances: list[float],
        *,
        corpus_base_rate: float,
    ) -> None:
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
        corpus_base_rate: float,
    ) -> CorpusCalibrator:
        return cls(corpus_cdf, corpus_base_rate=corpus_base_rate)

    def percentile(self, distance: float) -> float:
        """Return percentile rank of ``distance`` within the corpus, in [0, 1].

        ``0.0`` = most similar (smallest distance), ``1.0`` = most dissimilar.
        """

        pos = bisect.bisect_right(self._sorted, distance)
        return pos / self._n

    def _effective_sample_size(self, distance: float) -> float:
        """Compute local effective sample size around the query distance.

        Uses kernel bandwidth ``h = 1/sqrt(n)`` to define a local window, counts
        reference distances within it, scales by corpus confidence, and caps at
        :attr:`_MAX_N_EFF`. Per Sensoy et al. 2018 (p.3-4): evidence counts should
        represent actual observations supporting a hypothesis.
        """

        h = 1.0 / math.sqrt(self._n)
        lo = bisect.bisect_left(self._sorted, distance - h)
        hi = bisect.bisect_right(self._sorted, distance + h)
        local_count = hi - lo

        # A corpus of 1-2 points tells us almost nothing about the distribution.
        # Ramp confidence from ~0 at n=1 to ~1 at n>=10 (asymptotic normality of
        # the empirical CDF requires sqrt(n) >> 1).
        corpus_confidence = min(1.0, (self._n - 1) / 9.0)

        return min(float(local_count) * corpus_confidence, float(self._MAX_N_EFF))

    def to_opinion(self, raw_score: float) -> Opinion:
        """Convert distance to a ``doxa.Opinion`` via corpus calibration.

        The effective sample size is local CDF density — NOT the full corpus size —
        so a 10,000-element corpus cannot fabricate near-dogmatic certainty. Per
        Jøsang 2001 (p.20-21, Def 12): evidence maps to ``b = r/(r+s+W)``,
        ``d = s/(r+s+W)``, ``u = W/(r+s+W)``.
        """

        p = 1.0 - self.percentile(raw_score)  # similarity = 1 - percentile
        n_eff = self._effective_sample_size(raw_score)
        return Opinion.from_probability(p, n_eff, self._base_rate)


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
                    f"CategoryPrior key {category!r} does not match prior category "
                    f"{prior.category!r}"
                )
            normalized[key] = prior
        object.__setattr__(self, "priors", normalized)

    def get(self, category: str) -> CategoryPrior | None:
        return self.priors.get(category.lower())


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
            f"CategoryPrior category {resolved.category!r} does not match category "
            f"{category!r}"
        )
    return resolved


def categorical_to_opinion(
    category: str,
    pass_number: int,
    *,
    calibration_counts: dict[tuple[int, str], tuple[int, int]] | None = None,
    prior: CategoryPrior | None = None,
    prior_registry: CategoryPriorRegistry | None = None,
) -> Opinion | BaseRateUnresolved:
    """Convert a categorical model label to a ``doxa.Opinion``.

    Without a sourced :class:`CategoryPrior`, the base rate is unknown and the
    result is :class:`BaseRateUnresolved` — never a fabricated ``a``. Without
    calibration counts, the opinion is vacuous (Jøsang 2001, p.8) over the sourced
    base rate. With counts mapping ``(pass_number, category)`` to ``(correct,
    total)``, those become evidence ``r = correct``, ``s = total - correct`` and
    map to an opinion via Jøsang 2001 (p.20-21, Def 12).
    """

    cat = _validate_category(category)
    resolved_prior = _resolve_prior(cat, prior=prior, prior_registry=prior_registry)
    if resolved_prior is None:
        return BaseRateUnresolved(
            AssertionId(f"ps:assertion:category_prior:{cat}:pass:{pass_number}"),
            "missing_base_rate",
            ("category_prior",),
        )
    base_rate = resolved_prior.value

    if calibration_counts is None:
        return Opinion.vacuous(base_rate)

    key = (pass_number, cat)
    if key not in calibration_counts:
        return Opinion.vacuous(base_rate)

    correct, total = calibration_counts[key]
    if total <= 0:
        return Opinion.vacuous(base_rate)

    r = float(correct)
    s = float(total - correct)
    return Opinion.from_evidence(r, s, base_rate)


# ---------------------------------------------------------------------------
# 4. Probability-to-Opinion
# ---------------------------------------------------------------------------


def calibrated_probability_to_opinion(
    probability: float,
    effective_sample_size: float,
    base_rate: float,
) -> Opinion:
    """Convert a calibrated probability to a ``doxa.Opinion`` via Beta evidence.

    Per Sensoy et al. 2018 (p.3-4) and Jøsang 2001 (p.20-21, Def 12), ``r = p*n``,
    ``s = (1-p)*n`` with ``n`` the effective sample size. ``n = 0`` yields a
    vacuous opinion (Jøsang 2001, p.8); large ``n`` yields a narrow opinion near
    the probability.
    """

    if probability < 0.0 or probability > 1.0:
        raise ValueError(f"probability={probability} not in [0, 1]")
    if effective_sample_size < 0.0:
        raise ValueError(
            f"effective_sample_size={effective_sample_size} must be >= 0"
        )
    return Opinion.from_probability(probability, effective_sample_size, base_rate)
