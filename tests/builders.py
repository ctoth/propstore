from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceClaimSpec:
    local_id: str
    claim_type: str
    page: int
    statement: str | None = None
    concept: str | None = None
    concepts: tuple[str, ...] = ()
    value: float | None = None
    unit: str | None = None


@dataclass(frozen=True)
class SourceJustificationSpec:
    local_id: str
    conclusion: str
    premises: tuple[str, ...]
    rule_kind: str
    page: int


@dataclass(frozen=True)
class SourceStanceSpec:
    source_claim: str
    target: str
    stance_type: str
    note: str | None = None
    strength: str | None = None
