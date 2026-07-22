"""Local sensitivity analysis for derived quantities.

For a concept whose value is parameterized by inputs, this answers "which input
most influences the output, and by how much?" via local one-at-a-time
sensitivity: the partial derivative of the output with respect to each input at
the current operating point, plus the dimensionless elasticity
``(df/dx) * (x / f)``.

The numeric evaluation is delegated, not re-implemented. propstore does not own a
SymPy boundary (CLAUDE.md substrate discipline: SymPy lives behind
``human-to-sympy``). Every output value here comes from
:meth:`BoundWorld.derived_value`, which evaluates the parameterization through
:func:`propstore.propagation.evaluate_parameterization` →
:func:`human_to_sympy.evaluate_numeric`. Partial derivatives are therefore taken
by a central finite difference over those evaluations — there is no direct
``import sympy`` and no symbolic differentiation in propstore.

When inputs cannot be resolved, or no compatible parameterization exists, the
analyzer returns ``None`` rather than fabricate a number (honest ignorance,
CLAUDE.md).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from propstore.core.graph_types import ParameterizationEdge
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.reporting import JsonReportMixin
from propstore.world.types import DerivedResult, ValueStatus

if TYPE_CHECKING:
    from propstore.world import WorldQuery

# Relative step floor for the central finite difference. The truncation error of a
# central difference is O(h^2); for the linear/multiplicative parameterizations the
# value layer evaluates, this is exact up to float rounding.
_RELATIVE_STEP = 1e-6


@runtime_checkable
class SensitivityWorld(Protocol):
    """The world-reader surface :func:`analyze_sensitivity` reads."""

    def resolve_concept(self, name: str) -> str | None: ...

    def parameterizations_for(
        self, concept_id: str
    ) -> Sequence[ParameterizationEdge]: ...


@runtime_checkable
class SensitivityBound(Protocol):
    """The bound-world surface :func:`analyze_sensitivity` evaluates against."""

    def is_param_compatible(self, parameterization: ParameterizationEdge) -> bool: ...

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: Mapping[str, float] | None = None,
    ) -> DerivedResult: ...

    def collect_known_values(
        self, variable_concepts: Sequence[ConceptId | str]
    ) -> dict[ConceptId, float]: ...


@dataclass
class SensitivityEntry:
    """One input's local sensitivity of the analyzed output."""

    input_concept_id: ConceptId
    partial_derivative_value: float | None  # df/dx at the current inputs
    elasticity: float | None  # (df/dx) * (x / f), the normalized sensitivity

    def __post_init__(self) -> None:
        self.input_concept_id = to_concept_id(self.input_concept_id)


@dataclass
class SensitivityResult:
    """Local sensitivity of one output concept, ranked by elasticity."""

    concept_id: ConceptId
    formula: str
    entries: list[SensitivityEntry] = field(default_factory=list[SensitivityEntry])
    input_values: dict[ConceptId, float] = field(default_factory=dict[ConceptId, float])
    output_value: float | None = None
    method: str = "local_oat"

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.entries = list(self.entries)
        self.input_values = {
            to_concept_id(concept_id): float(value)
            for concept_id, value in self.input_values.items()
        }


@dataclass
class GlobalSensitivityResult:
    """Sobol first-order and total sensitivity indices over an input box."""

    concept_id: ConceptId
    method: str
    first_order: dict[str, float]
    total: dict[str, float]

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.first_order = {
            str(concept_id): float(value)
            for concept_id, value in self.first_order.items()
        }
        self.total = {
            str(concept_id): float(value) for concept_id, value in self.total.items()
        }


@dataclass(frozen=True)
class SensitivityRequest:
    """A request to analyze the local sensitivity of one concept's value."""

    concept_id: str
    bindings: Mapping[str, str]


@dataclass(frozen=True)
class SensitivityReport(JsonReportMixin):
    """The owner-layer report wrapping a :class:`SensitivityResult`.

    ``result`` is ``None`` when no compatible parameterization exists or an input
    could not be resolved — honest ignorance, never a fabricated sensitivity.
    """

    concept_id: str
    result: SensitivityResult | None


def query_sensitivity(
    world: WorldQuery,
    request: SensitivityRequest,
) -> SensitivityReport:
    """Bind ``world`` under the request bindings and analyze concept sensitivity.

    The render-owner entry point the ``pks world sensitivity`` adapter calls: it
    resolves the concept, binds the world, and runs :func:`analyze_sensitivity`
    (finite-difference over ``BoundWorld.derived_value`` — no SymPy boundary in
    propstore). A concept with no parameterization yields ``result=None``.
    """

    from propstore.core.environment import Environment

    resolved = world.resolve_concept(request.concept_id) or request.concept_id
    bound = world.bind(Environment(bindings=dict(request.bindings)))
    return SensitivityReport(
        concept_id=resolved,
        result=analyze_sensitivity(world, resolved, bound),
    )


def _evaluate_output(
    bound: SensitivityBound,
    concept_id: ConceptId,
    overrides: Mapping[str, float],
) -> float | None:
    """Evaluate the output concept with every input pinned by ``overrides``."""

    result = bound.derived_value(
        str(concept_id),
        override_values={key: value for key, value in overrides.items()},
    )
    if result.status is ValueStatus.DERIVED and result.value is not None:
        return float(result.value)
    return None


def analyze_sensitivity(
    world: SensitivityWorld,
    concept_id: ConceptId | str,
    bound: SensitivityBound,
    *,
    override_values: Mapping[str, float] | None = None,
) -> SensitivityResult | None:
    """Analyze which input most influences a derived quantity.

    Returns ``None`` when no compatible parameterization exists or when any input
    value cannot be resolved (so the analyzer never reports a fabricated
    sensitivity over missing data).
    """

    requested_concept_id = to_concept_id(concept_id)
    resolved_concept_id = world.resolve_concept(str(requested_concept_id))
    lookup_concept_id = to_concept_id(resolved_concept_id or str(requested_concept_id))

    raw_params = world.parameterizations_for(str(lookup_concept_id))
    if not raw_params:
        return None

    param = next(
        (candidate for candidate in raw_params if bound.is_param_compatible(candidate)),
        None,
    )
    if param is None or not param.sympy:
        return None

    effective_inputs: list[ConceptId] = []
    for input_id in param.input_concept_ids:
        resolved_input_id = world.resolve_concept(str(input_id))
        canonical_input_id = to_concept_id(resolved_input_id or str(input_id))
        if canonical_input_id != lookup_concept_id:
            effective_inputs.append(canonical_input_id)

    if not effective_inputs:
        return None

    resolved_overrides: dict[ConceptId, float] = {}
    if override_values:
        for key, value in override_values.items():
            resolved_key = world.resolve_concept(str(key))
            resolved_overrides[to_concept_id(resolved_key or str(key))] = float(value)

    base_override_payload = {
        str(input_id): value for input_id, value in resolved_overrides.items()
    }

    input_values: dict[ConceptId, float] = {}
    for input_id in effective_inputs:
        if input_id in resolved_overrides:
            input_values[input_id] = resolved_overrides[input_id]
            continue

        known = bound.collect_known_values([input_id])
        if input_id in known:
            input_values[input_id] = float(known[input_id])
            continue

        derived = bound.derived_value(
            str(input_id),
            override_values=dict(base_override_payload),
        )
        if derived.status is ValueStatus.DERIVED and derived.value is not None:
            input_values[input_id] = float(derived.value)
            continue

        return None

    if len(input_values) != len(effective_inputs):
        return None

    base_overrides = {str(input_id): value for input_id, value in input_values.items()}
    output_value = _evaluate_output(bound, lookup_concept_id, base_overrides)

    entries: list[SensitivityEntry] = []
    for input_id in effective_inputs:
        x_value = input_values[input_id]
        step = _RELATIVE_STEP * (abs(x_value) if x_value != 0 else 1.0)

        forward = dict(base_overrides)
        forward[str(input_id)] = x_value + step
        backward = dict(base_overrides)
        backward[str(input_id)] = x_value - step

        f_forward = _evaluate_output(bound, lookup_concept_id, forward)
        f_backward = _evaluate_output(bound, lookup_concept_id, backward)

        partial_value: float | None = None
        if f_forward is not None and f_backward is not None:
            partial_value = (f_forward - f_backward) / (2.0 * step)

        elasticity: float | None = None
        if partial_value is not None and output_value is not None and output_value != 0:
            elasticity = partial_value * x_value / output_value

        entries.append(
            SensitivityEntry(
                input_concept_id=input_id,
                partial_derivative_value=partial_value,
                elasticity=elasticity,
            )
        )

    entries.sort(
        key=lambda entry: (
            abs(entry.elasticity) if entry.elasticity is not None else -1.0
        ),
        reverse=True,
    )

    return SensitivityResult(
        concept_id=lookup_concept_id,
        formula=param.formula or param.sympy,
        entries=entries,
        input_values=input_values,
        output_value=output_value,
        method="local_oat",
    )


def analyze_global_sensitivity(
    world: SensitivityWorld,
    concept_id: ConceptId | str,
    bound: SensitivityBound,
    *,
    bounds: Mapping[str, tuple[float, float]],
    n_samples: int = 256,
    method: str = "sobol_total",
) -> GlobalSensitivityResult | None:
    """Estimate Sobol first-order and total indices by Saltelli sampling.

    Saltelli 2008 frames global sensitivity as variance decomposition over the
    input space. This is separate from :func:`analyze_sensitivity`, whose
    derivative output is local one-at-a-time sensitivity at a single point. Every
    sample is evaluated through :func:`analyze_sensitivity`, so this too carries no
    direct SymPy dependency.
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

        for input_id in input_ids:
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
