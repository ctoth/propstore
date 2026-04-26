"""Closed semantic condition IR for propstore conditions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from propstore.core.id_types import ConceptId, to_concept_id


@dataclass(frozen=True, order=True)
class ConditionSourceSpan:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError("condition source span start must be non-negative")
        if self.end < self.start:
            raise ValueError("condition source span end must be after start")


class ConditionValueKind(StrEnum):
    NUMERIC = "numeric"
    STRING = "string"
    BOOLEAN = "boolean"


class ConditionUnaryOp(StrEnum):
    NOT = "!"
    NEGATE = "-"


class ConditionBinaryOp(StrEnum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    AND = "&&"
    OR = "||"


@dataclass(frozen=True)
class ConditionLiteral:
    value: bool | int | float | str
    value_kind: ConditionValueKind
    span: ConditionSourceSpan

    def __post_init__(self) -> None:
        object.__setattr__(self, "value_kind", ConditionValueKind(self.value_kind))


@dataclass(frozen=True)
class ConditionReference:
    concept_id: ConceptId | str
    source_name: str
    value_kind: ConditionValueKind
    span: ConditionSourceSpan

    def __post_init__(self) -> None:
        concept_id = to_concept_id(self.concept_id)
        if str(concept_id) == "":
            raise ValueError("condition reference concept id must be non-empty")
        source_name = self.source_name.strip()
        if source_name == "":
            raise ValueError("condition reference source name must be non-empty")
        object.__setattr__(self, "concept_id", concept_id)
        object.__setattr__(self, "source_name", source_name)
        object.__setattr__(self, "value_kind", ConditionValueKind(self.value_kind))


@dataclass(frozen=True)
class ConditionUnary:
    op: ConditionUnaryOp
    operand: ConditionIR
    span: ConditionSourceSpan

    def __post_init__(self) -> None:
        object.__setattr__(self, "op", ConditionUnaryOp(self.op))


@dataclass(frozen=True)
class ConditionBinary:
    op: ConditionBinaryOp
    left: ConditionIR
    right: ConditionIR
    span: ConditionSourceSpan

    def __post_init__(self) -> None:
        object.__setattr__(self, "op", ConditionBinaryOp(self.op))


@dataclass(frozen=True)
class ConditionMembership:
    element: ConditionIR
    options: tuple[ConditionIR, ...]
    span: ConditionSourceSpan

    def __post_init__(self) -> None:
        object.__setattr__(self, "options", tuple(self.options))


@dataclass(frozen=True)
class ConditionChoice:
    condition: ConditionIR
    when_true: ConditionIR
    when_false: ConditionIR
    span: ConditionSourceSpan


ConditionIR = (
    ConditionLiteral
    | ConditionReference
    | ConditionUnary
    | ConditionBinary
    | ConditionMembership
    | ConditionChoice
)
