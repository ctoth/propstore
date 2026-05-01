"""Propositional Knowledge Store — hold disagreement, reason about it."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from propstore.world.bound import BoundWorld
    from propstore.world.actual_cause import actual_cause
    from propstore.world.intervention import InterventionWorld, ObservationWorld
    from propstore.world.overlay import OverlayWorld
    from propstore.world.model import WorldQuery
    from propstore.world.scm import StructuralCausalModel, StructuralEquation
    from propstore.world.types import (
        DerivedResult,
        ReasoningBackend,
        RenderPolicy,
        ResolvedResult,
        ResolutionStrategy,
        SyntheticClaim,
        ValueResult,
    )

_EXPORTS: dict[str, tuple[str, str]] = {
    "actual_cause": ("propstore.world.actual_cause", "actual_cause"),
    "BoundWorld": ("propstore.world.bound", "BoundWorld"),
    "DerivedResult": ("propstore.world.types", "DerivedResult"),
    "InterventionWorld": ("propstore.world.intervention", "InterventionWorld"),
    "ObservationWorld": ("propstore.world.intervention", "ObservationWorld"),
    "OverlayWorld": ("propstore.world.overlay", "OverlayWorld"),
    "ReasoningBackend": ("propstore.world.types", "ReasoningBackend"),
    "RenderPolicy": ("propstore.world.types", "RenderPolicy"),
    "ResolvedResult": ("propstore.world.types", "ResolvedResult"),
    "ResolutionStrategy": ("propstore.world.types", "ResolutionStrategy"),
    "StructuralCausalModel": ("propstore.world.scm", "StructuralCausalModel"),
    "StructuralEquation": ("propstore.world.scm", "StructuralEquation"),
    "SyntheticClaim": ("propstore.world.types", "SyntheticClaim"),
    "ValueResult": ("propstore.world.types", "ValueResult"),
    "WorldQuery": ("propstore.world.model", "WorldQuery"),
}

__all__ = [
    "actual_cause",
    "BoundWorld",
    "DerivedResult",
    "InterventionWorld",
    "ObservationWorld",
    "OverlayWorld",
    "ReasoningBackend",
    "RenderPolicy",
    "ResolvedResult",
    "ResolutionStrategy",
    "StructuralCausalModel",
    "StructuralEquation",
    "SyntheticClaim",
    "ValueResult",
    "WorldQuery",
]


def __getattr__(name: str) -> Any:
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
