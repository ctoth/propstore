"""Propositional Knowledge Store — hold disagreement, reason about it."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from propstore.world.bound import BoundWorld
    from propstore.world.overlay import OverlayWorld
    from propstore.world.model import WorldModel
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
    "BoundWorld": ("propstore.world.bound", "BoundWorld"),
    "DerivedResult": ("propstore.world.types", "DerivedResult"),
    "OverlayWorld": ("propstore.world.overlay", "OverlayWorld"),
    "ReasoningBackend": ("propstore.world.types", "ReasoningBackend"),
    "RenderPolicy": ("propstore.world.types", "RenderPolicy"),
    "ResolvedResult": ("propstore.world.types", "ResolvedResult"),
    "ResolutionStrategy": ("propstore.world.types", "ResolutionStrategy"),
    "SyntheticClaim": ("propstore.world.types", "SyntheticClaim"),
    "ValueResult": ("propstore.world.types", "ValueResult"),
    "WorldModel": ("propstore.world.model", "WorldModel"),
}

__all__ = [
    "BoundWorld",
    "DerivedResult",
    "OverlayWorld",
    "ReasoningBackend",
    "RenderPolicy",
    "ResolvedResult",
    "ResolutionStrategy",
    "SyntheticClaim",
    "ValueResult",
    "WorldModel",
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
