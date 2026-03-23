"""Sensitivity analysis for derived quantities.

Computes partial derivatives, numerical sensitivities, and elasticities
for parameterized concepts, answering: "which input most influences this output?"
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from propstore.propagation import parse_cached


@dataclass
class SensitivityEntry:
    input_concept_id: str
    partial_derivative_expr: str  # symbolic string
    partial_derivative_value: float | None  # numerical at current inputs
    elasticity: float | None  # (df/dx * x/f) -- normalized sensitivity


@dataclass
class SensitivityResult:
    concept_id: str
    formula: str
    entries: list[SensitivityEntry] = field(default_factory=list)  # sorted by |elasticity| descending
    input_values: dict[str, float] = field(default_factory=dict)
    output_value: float | None = None


def analyze_sensitivity(
    world,
    concept_id: str,
    bound,
    *,
    override_values: dict[str, float] | None = None,
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

    params = world.parameterizations_for(concept_id)
    if not params:
        return None

    # Find first compatible parameterization
    param = None
    for p in params:
        if bound.is_param_compatible(p.get("conditions_cel")):
            param = p
            break

    if param is None:
        return None

    sympy_str = param.get("sympy")
    if not sympy_str:
        return None

    input_ids = json.loads(param["concept_ids"])
    effective_inputs = [iid for iid in input_ids if iid != concept_id]

    if not effective_inputs:
        return None

    # Parse the expression
    all_names = set(effective_inputs) | {concept_id}
    parsed, symbols = parse_cached(sympy_str, tuple(sorted(all_names)))

    # Handle Eq form: extract RHS
    if isinstance(parsed, Equality):
        expr = parsed.rhs
    else:
        expr = parsed

    # Resolve input values
    input_values: dict[str, float] = {}
    for iid in effective_inputs:
        if override_values and iid in override_values:
            input_values[iid] = override_values[iid]
            continue

        # Try value_of
        vr = bound.value_of(iid)
        if vr.status == "determined":
            val = vr.claims[0].get("value") if vr.claims else None
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
    subs_pairs: Any = [(symbols[k], v) for k, v in input_values.items() if k in symbols]
    try:
        result: Any = expr.subs(subs_pairs)
        output_value = float(result)
    except (TypeError, ValueError, ZeroDivisionError):
        output_value = None

    # Compute partial derivatives and elasticities
    entries: list[SensitivityEntry] = []
    for iid in effective_inputs:
        input_sym = symbols.get(iid, Symbol(iid))
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
        concept_id=concept_id,
        formula=param.get("formula", sympy_str),
        entries=entries,
        input_values=input_values,
        output_value=output_value,
    )
