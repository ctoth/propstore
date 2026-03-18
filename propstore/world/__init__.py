"""propstore.world — modular world model package.

Re-exports all public names for backward compatibility.
"""

from propstore.world.bound import BoundWorld
from propstore.world.hypothetical import HypotheticalWorld
from propstore.world.model import WorldModel
from propstore.world.resolution import resolve
from propstore.world.types import (
    ChainResult,
    ChainStep,
    ClaimView,
    DerivedResult,
    ResolvedResult,
    ResolutionStrategy,
    SyntheticClaim,
    ValueResult,
)

__all__ = [
    "BoundWorld",
    "ChainResult",
    "ChainStep",
    "ClaimView",
    "DerivedResult",
    "HypotheticalWorld",
    "ResolvedResult",
    "ResolutionStrategy",
    "SyntheticClaim",
    "ValueResult",
    "WorldModel",
    "resolve",
]
