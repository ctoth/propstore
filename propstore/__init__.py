"""propstore — a semantic operating system.

This is the post-decomposition rebuild: a thin semantic-composition layer over
substrate packages we own (quire, condition-ir, provenance-semiring, doxa,
belief-set, argumentation, assignment-selection, gunray, bridgman, cel-parser,
ast-equiv, eq-equiv, human-to-sympy, …). propstore composes them; it does not
re-implement or wrap them — a package boundary is an ``import``, not a membrane
(see CLAUDE.md "Substrate boundary discipline").

The build is sliced bottom-up per domain entity; each entity is ONE quire charter
class and its projections fall out of field annotations. See PLAN.md for the
phased execution plan and docs/rewrite/ for the targeting inventory + spec.
"""

from __future__ import annotations

from propstore.world import (
    InterventionWorld,
    ObservationWorld,
    StructuralCausalModel,
    StructuralEquation,
    actual_cause,
)

__version__ = "0.4.0"

__all__ = [
    "InterventionWorld",
    "ObservationWorld",
    "StructuralCausalModel",
    "StructuralEquation",
    "actual_cause",
]
