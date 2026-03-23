"""Shared conflict detector models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConflictClass(Enum):
    COMPATIBLE = "COMPATIBLE"
    PHI_NODE = "PHI_NODE"
    CONFLICT = "CONFLICT"
    OVERLAP = "OVERLAP"
    PARAM_CONFLICT = "PARAM_CONFLICT"
    CONTEXT_PHI_NODE = "CONTEXT_PHI_NODE"


@dataclass
class ConflictRecord:
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    warning_class: ConflictClass
    conditions_a: list[str]
    conditions_b: list[str]
    value_a: str
    value_b: str
    derivation_chain: str | None = None
