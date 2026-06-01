"""Sensitivity analysis for derived quantities.

Computes partial derivatives, numerical sensitivities, and elasticities
for parameterized concepts, answering: "which input most influences this output?"
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.reporting import JsonReportMixin
from propstore.core.environment import Environment
from propstore.core.id_types import ConceptId
from propstore.propagation import parse_cached, rewrite_parameterization_symbols


@dataclass
class SensitivityEntry:
    input_concept_id: ConceptId
    partial_derivative_expr: str  # symbolic string
    partial_derivative_value: float | None  # numerical at current inputs
    elasticity: float | None  # (df/dx * x/f) -- normalized sensitivity

    def __post_init__(self) -> None:
        self.input_concept_id = ConceptId(self.input_concept_id)


@dataclass
class SensitivityResult:
    concept_id: ConceptId
    formula: str
    entries: list[SensitivityEntry] = field(
        default_factory=list
    )  # sorted by |elasticity| descending
    input_values: dict[ConceptId, float] = field(default_factory=dict)
    output_value: float | None = None
    method: str = "local_oat"

    def __post_init__(self) -> None:
        self.concept_id = ConceptId(self.concept_id)
        self.entries = list(self.entries)
        self.input_values = {
            ConceptId(concept_id): float(value)
            for concept_id, value in self.input_values.items()
        }


@dataclass
class GlobalSensitivityResult:
    concept_id: ConceptId | str
    method: str
    first_order: dict[str, float]
    total: dict[str, float]

    def __post_init__(self) -> None:
        self.concept_id = ConceptId(self.concept_id)
        self.first_order = {
            str(concept_id): float(value)
            for concept_id, value in self.first_order.items()
        }
        self.total = {
            str(concept_id): float(value) for concept_id, value in self.total.items()
        }


@dataclass(frozen=True)
class SensitivityRequest:
    concept_id: str
    bindings: Mapping[str, str]


@dataclass(frozen=True)
class SensitivityReport(JsonReportMixin):
    concept_id: str
    result: SensitivityResult | None


def query_sensitivity(
    world: Any,
    request: SensitivityRequest,
) -> SensitivityReport:
    concept = world.get_concept(request.concept_id)
    resolved = str(concept.id) if concept is not None else request.concept_id
    bound = world.bind(Environment(bindings=dict(request.bindings)))
    return SensitivityReport(
        concept_id=resolved,
        result=analyze_sensitivity(world, resolved, bound),
    )


def analyze_global_sensitivity(
    world,
    concept_id: ConceptId | str,
    bound,
    *,
    bounds: Mapping[str, tuple[float, float]],
    n_samples: int = 256,
    method: str = "sobol_total",
) -> GlobalSensitivityResult | None:
    """Estimate Sobol first-order and total indices by Saltelli sampling.

    Saltelli 2008 frames global sensitivity as variance decomposition over
    the input space. This API is separate from `analyze_sensitivity`, whose
    derivative output is local one-at-a-time sensitivity at one point.
    """
    if n_samples < 2:
        raise ValueError("n_samples must be at least 2")
    if method not in {"sobol_first_order", "sobol_total"}:
        raise ValueError("method must be 'sobol_first_order' or 'sobol_total'")

    midpoint_overrides = {
        key: (float(low) + float(high)) / 2.0 for key, (low, high) in bounds.items()
    }
    local = analyze_sensitivity(
        world,
        concept_id,
        bound,
        override_values=midpoint_overrides,
    )
    if local is None:
        return None

    input_ids = [str(input_id) for input_id in local.input_values]
    if not input_ids:
        return None
    missing_bounds = [input_id for input_id in input_ids if input_id not in bounds]
    if missing_bounds:
        raise ValueError(f"missing bounds for inputs: {', '.join(missing_bounds)}")

    def unit_sample(row: int, column: int) -> float:
        # Deterministic low-discrepancy-ish grid with distinct column phases.
        return ((row * (column * 2 + 1)) % n_samples + 0.5) / n_samples

    def scaled_sample(row: int, column: int, source: int) -> float:
        input_id = input_ids[column]
        low, high = bounds[input_id]
        unit = unit_sample(row + source * 17, column + source)
        return float(low) + (float(high) - float(low)) * unit

    def evaluate(overrides: Mapping[str, float]) -> float | None:
        result = analyze_sensitivity(
            world,
            concept_id,
            bound,
            override_values=overrides,
        )
        return None if result is None else result.output_value

    samples_a: list[float] = []
    samples_b: list[float] = []
    cross_samples: dict[str, list[float]] = {input_id: [] for input_id in input_ids}

    for row in range(n_samples):
        a_values = {
            input_id: scaled_sample(row, column, 0)
            for column, input_id in enumerate(input_ids)
        }
        b_values = {
            input_id: scaled_sample(row, column, 1)
            for column, input_id in enumerate(input_ids)
        }
        f_a = evaluate(a_values)
        f_b = evaluate(b_values)
        if f_a is None or f_b is None:
            return None
        samples_a.append(f_a)
        samples_b.append(f_b)

        for column, input_id in enumerate(input_ids):
            mixed = dict(a_values)
            mixed[input_id] = b_values[input_id]
            f_mixed = evaluate(mixed)
            if f_mixed is None:
                return None
            cross_samples[input_id].append(f_mixed)

    combined = samples_a + samples_b
    mean = sum(combined) / len(combined)
    variance = sum((value - mean) ** 2 for value in combined) / len(combined)
    if variance <= 1e-15:
        zeros = {input_id: 0.0 for input_id in input_ids}
        return GlobalSensitivityResult(
            concept_id=local.concept_id,
            method=method,
            first_order=zeros,
            total=zeros,
        )

    first_order: dict[str, float] = {}
    total: dict[str, float] = {}
    for input_id in input_ids:
        mixed_values = cross_samples[input_id]
        first_order[input_id] = sum(
            b * (mixed - a) for a, b, mixed in zip(samples_a, samples_b, mixed_values)
        ) / (n_samples * variance)
        total[input_id] = sum(
            (a - mixed) ** 2 for a, mixed in zip(samples_a, mixed_values)
        ) / (2.0 * n_samples * variance)

    return GlobalSensitivityResult(
        concept_id=local.concept_id,
        method=method,
        first_order=first_order,
        total=total,
    )
