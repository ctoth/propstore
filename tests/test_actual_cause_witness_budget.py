from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from propstore.world.actual_cause import EnumerationExceeded, actual_cause
from propstore.world.intervention import InterventionWorld

from tests.intervention_world_helpers import bool_scm, equation


@pytest.mark.property
@given(st.integers(min_value=1, max_value=6))
def test_generated_witness_search_returns_verdict_or_budget_signal(n: int) -> None:
    variables = {f"X{i}" for i in range(n)}
    equations = {
        variable: equation(
            variable,
            (f"U_{variable}",),
            lambda values, variable=variable: values[f"U_{variable}"],
        )
        for variable in variables
    }
    equations["E"] = equation(
        "E",
        tuple(sorted(variables)),
        lambda values: all(values[variable] for variable in variables),
    )
    scm = bool_scm(
        endogenous={*variables, "E"},
        equations=equations,
        exogenous_assignment={f"U_X{i}": True for i in range(n)},
    )

    try:
        verdict = actual_cause(
            InterventionWorld(scm, {}),
            effect=lambda values: values["E"] is True,
            candidate_cause={"X0": True},
            max_witnesses=max(0, 2 ** (n - 1) - 1),
        )
    except EnumerationExceeded as exc:
        assert exc.examined > exc.max_witnesses
    else:
        assert verdict.criterion in {"AC1", "AC2", "AC3", "AC1+AC2+AC3"}
