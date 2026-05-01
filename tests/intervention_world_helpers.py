from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from propstore.world.scm import StructuralCausalModel, StructuralEquation


def equation(
    target: str,
    parents: tuple[str, ...],
    evaluate,
    *,
    domain: tuple[Any, ...] = (0, 1),
) -> StructuralEquation:
    return StructuralEquation(
        target=target,
        parents=parents,
        evaluate=evaluate,
        provenance=f"test:{target}",
        domain=domain,
    )


def simple_chain_scm() -> StructuralCausalModel:
    return StructuralCausalModel(
        exogenous=frozenset({"X"}),
        endogenous=frozenset({"Y", "Z"}),
        equations={
            "Y": equation("Y", ("X",), lambda values: values["X"] + 1, domain=(1, 6, 99)),
            "Z": equation("Z", ("Y",), lambda values: values["Y"] + 1, domain=(2, 7, 100)),
        },
        exogenous_assignment={"X": 0},
        domains={"X": (0, 5), "Y": (1, 6, 99), "Z": (2, 7, 100)},
    )


def bool_scm(
    *,
    endogenous: set[str],
    equations: Mapping[str, StructuralEquation],
    exogenous_assignment: Mapping[str, Any] | None = None,
) -> StructuralCausalModel:
    domains = {name: (False, True) for name in endogenous}
    if exogenous_assignment is not None:
        domains.update({name: (False, True) for name in exogenous_assignment})
    return StructuralCausalModel(
        exogenous=frozenset(exogenous_assignment or ()),
        endogenous=frozenset(endogenous),
        equations=dict(equations),
        exogenous_assignment=dict(exogenous_assignment or {}),
        domains=domains,
    )
