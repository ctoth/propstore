"""Sensitivity analysis for derived quantities.

Computes partial derivatives, numerical sensitivities, and elasticities
for parameterized concepts, answering: "which input most influences this output?"
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.environment import Environment
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.core.row_types import coerce_parameterization_row
from propstore.propagation import parse_cached, rewrite_parameterization_symbols


@dataclass
class SensitivityEntry:
    input_concept_id: ConceptId
    partial_derivative_expr: str  # symbolic string
    partial_derivative_value: float | None  # numerical at current inputs
    elasticity: float | None  # (df/dx * x/f) -- normalized sensitivity

    def __post_init__(self) -> None:
        self.input_concept_id = to_concept_id(self.input_concept_id)


@dataclass
class SensitivityResult:
    concept_id: ConceptId
    formula: str
    entries: list[SensitivityEntry] = field(default_factory=list)  # sorted by |elasticity| descending
    input_values: dict[ConceptId, float] = field(default_factory=dict)
    output_value: float | None = None

    def __post_init__(self) -> None:
        self.concept_id = to_concept_id(self.concept_id)
        self.entries = list(self.entries)
        self.input_values = {
            to_concept_id(concept_id): float(value)
            for concept_id, value in self.input_values.items()
        }


@dataclass(frozen=True)
class SensitivityRequest:
    concept_id: str
    bindings: Mapping[str, str]


@dataclass(frozen=True)
class SensitivityReport:
    concept_id: str
    result: SensitivityResult | None


def query_sensitivity(
    world: Any,
    request: SensitivityRequest,
) -> SensitivityReport:
    resolved = world.resolve_concept(request.concept_id) or request.concept_id
    bound = world.bind(Environment(bindings=dict(request.bindings)))
    return SensitivityReport(
        concept_id=resolved,
        result=analyze_sensitivity(world, resolved, bound),
    )


def analyze_sensitivity(
    world,
    concept_id: ConceptId | str,
    bound,
    *,
    override_values: Mapping[str, float] | None = None,
) -> SensitivityResult | None:
    """Analyze which input most influences a derived quantity.

    Parameters
    ----------
    world : WorldModel
        The world model providing parameterization data.
    concept_id : str
        The output concept to analyze.
    bound : BoundWorld
        A bound world for resolving input values and checking compatibility.
    override_values : dict, optional
        Force specific input values instead of resolving from claims.

    Returns
    -------
    SensitivityResult or None
        None if no compatible parameterization or inputs can't be resolved.
    """
    from sympy import Equality, Symbol, diff as sym_diff

    requested_concept_id = to_concept_id(concept_id)
    resolver = getattr(world, "resolve_concept", None)
    resolved_concept_id = (
        resolver(str(requested_concept_id))
        if callable(resolver)
        else None
    )
    lookup_concept_id = to_concept_id(resolved_concept_id or str(requested_concept_id))

    raw_params = world.parameterizations_for(str(lookup_concept_id))
    if not raw_params:
        return None
    params = [coerce_parameterization_row(param) for param in raw_params]

    # Find first compatible parameterization
    param = None
    for p in params:
        if bound.is_param_compatible(p.conditions_cel):
            param = p
            break

    if param is None:
        return None

    sympy_str = param.sympy
    if not sympy_str:
        return None

    input_ids = json.loads(param.concept_ids)
    effective_inputs: list[ConceptId] = []
    for input_id in input_ids:
        resolved_input_id = (
            resolver(str(input_id))
            if callable(resolver)
            else None
        )
        canonical_input_id = to_concept_id(resolved_input_id or str(input_id))
        if canonical_input_id != lookup_concept_id:
            effective_inputs.append(canonical_input_id)

    if not effective_inputs:
        return None

    def concept_symbol_candidates(resolved_id: ConceptId | str) -> tuple[str, ...]:
        getter = getattr(world, "get_concept", None)
        if not callable(getter):
            return ()
        concept = getter(str(resolved_id))
        if concept is None:
            return ()

        seen: set[str] = set()
        candidates: list[str] = []

        def add(candidate: object) -> None:
            if not isinstance(candidate, str) or not candidate or candidate in seen:
                return
            seen.add(candidate)
            candidates.append(candidate)

        if isinstance(concept, Mapping):
            add(concept.get("canonical_name"))
            logical_ids = concept.get("logical_ids")
        else:
            add(getattr(concept, "canonical_name", None))
            parsed_logical_ids = getattr(concept, "parsed_logical_ids", None)
            logical_ids = parsed_logical_ids() if callable(parsed_logical_ids) else None
            add(getattr(concept, "primary_logical_id", None))
        if isinstance(logical_ids, list):
            for entry in logical_ids:
                if not isinstance(entry, Mapping):
                    continue
                add(entry.get("value"))
                namespace = entry.get("namespace")
                value = entry.get("value")
                if isinstance(namespace, str) and isinstance(value, str) and namespace and value:
                    add(f"{namespace}:{value}")
        return tuple(candidates)

    output_key = "__out__"
    input_symbol_map = {
        input_id: f"__in_{index}__"
        for index, input_id in enumerate(effective_inputs)
    }
    rewritten_sympy = rewrite_parameterization_symbols(
        sympy_str,
        symbol_aliases={
            str(lookup_concept_id): concept_symbol_candidates(lookup_concept_id),
            **{
                str(input_id): concept_symbol_candidates(input_id)
                for input_id in effective_inputs
            },
        },
        symbol_targets={
            str(lookup_concept_id): output_key,
            **{
                str(input_id): symbol
                for input_id, symbol in input_symbol_map.items()
            },
        },
    )

    # Parse the expression in a safe symbol namespace.
    all_names = set(input_symbol_map.values()) | {output_key}
    parsed, symbols = parse_cached(rewritten_sympy, tuple(sorted(all_names)))

    # Handle Eq form: extract RHS
    if isinstance(parsed, Equality):
        expr = parsed.rhs
    else:
        expr = parsed

    # Resolve input values
    resolved_overrides: dict[ConceptId, float] = {}
    if override_values:
        for key, value in override_values.items():
            resolved_key = (
                resolver(str(key))
                if callable(resolver)
                else None
            )
            resolved_overrides[to_concept_id(resolved_key or str(key))] = float(value)

    input_values: dict[ConceptId, float] = {}
    for iid in effective_inputs:
        if iid in resolved_overrides:
            input_values[iid] = resolved_overrides[iid]
            continue

        # Try value_of
        vr = bound.value_of(iid)
        if vr.status == "determined":
            val = vr.claims[0].value if vr.claims else None
            if val is not None:
                input_values[iid] = float(val)
                continue

        # Try derived_value
        dr = bound.derived_value(iid)
        if dr.status == "derived" and dr.value is not None:
            input_values[iid] = dr.value
            continue

        # Can't resolve this input
        return None

    if len(input_values) != len(effective_inputs):
        return None

    # Compute output value
    subs_pairs: Any = [
        (symbols[input_symbol_map[input_id]], value)
        for input_id, value in input_values.items()
        if input_symbol_map[input_id] in symbols
    ]
    try:
        result: Any = expr.subs(subs_pairs)
        output_value = float(result)
    except (TypeError, ValueError, ZeroDivisionError):
        output_value = None

    # Compute partial derivatives and elasticities
    entries: list[SensitivityEntry] = []
    for iid in effective_inputs:
        input_symbol = input_symbol_map[iid]
        input_sym = symbols.get(input_symbol, Symbol(input_symbol))
        partial = sym_diff(expr, input_sym)
        partial_str = str(partial)

        # Evaluate numerically
        try:
            partial_result: Any = partial.subs(subs_pairs)
            partial_val = float(partial_result)
        except (TypeError, ValueError, ZeroDivisionError):
            partial_val = None

        # Compute elasticity: (df/dx) * (x / f)
        elasticity = None
        if partial_val is not None and output_value is not None and output_value != 0:
            x_val = input_values[iid]
            elasticity = partial_val * x_val / output_value

        entries.append(SensitivityEntry(
            input_concept_id=iid,
            partial_derivative_expr=partial_str,
            partial_derivative_value=partial_val,
            elasticity=elasticity,
        ))

    # Sort by |elasticity| descending
    entries.sort(key=lambda e: abs(e.elasticity) if e.elasticity is not None else -1, reverse=True)

    return SensitivityResult(
        concept_id=lookup_concept_id,
        formula=param.formula or sympy_str,
        entries=entries,
        input_values=input_values,
        output_value=output_value,
    )
