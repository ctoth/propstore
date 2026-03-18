"""Data classes, enums, and protocols for the world model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


@dataclass
class ValueResult:
    concept_id: str
    status: str  # "determined" | "conflicted" | "underdetermined" | "no_claims"
    claims: list[dict] = field(default_factory=list)


@dataclass
class DerivedResult:
    concept_id: str
    status: str  # "derived" | "underspecified" | "no_relationship" | "conflicted"
    value: float | None = None
    formula: str | None = None
    input_values: dict[str, float] = field(default_factory=dict)
    exactness: str | None = None


class ResolutionStrategy(Enum):
    RECENCY = "recency"
    SAMPLE_SIZE = "sample_size"
    STANCE = "stance"
    OVERRIDE = "override"


@dataclass
class ResolvedResult:
    concept_id: str
    status: str  # "determined" | "conflicted" | "no_claims" | "resolved"
    value: float | str | None = None
    claims: list[dict] = field(default_factory=list)
    winning_claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None


@dataclass
class SyntheticClaim:
    id: str
    concept_id: str
    type: str = "parameter"
    value: float | str | None = None
    conditions: list[str] = field(default_factory=list)


@dataclass
class ChainStep:
    concept_id: str
    value: float | str | None
    source: str  # "binding" | "claim" | "derived" | "resolved"


@dataclass
class ChainResult:
    target_concept_id: str
    result: ValueResult | DerivedResult
    steps: list[ChainStep] = field(default_factory=list)
    bindings_used: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ClaimView(Protocol):
    def active_claims(self, concept_id: str | None = None) -> list[dict]: ...
    def inactive_claims(self, concept_id: str | None = None) -> list[dict]: ...
    def value_of(self, concept_id: str) -> ValueResult: ...
    def derived_value(self, concept_id: str) -> DerivedResult: ...
    def is_determined(self, concept_id: str) -> bool: ...
