"""Shared types for explicit semantic pass pipelines."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Generic, Literal, Protocol, TypeVar

from propstore.families.registry import PropstoreFamily


StageId = StrEnum


DiagnosticLevel = Literal["warning", "error"]


@dataclass(frozen=True)
class PassDiagnostic:
    level: DiagnosticLevel
    code: str
    message: str
    family: PropstoreFamily
    stage: StageId
    filename: str | None = None
    artifact_id: str | None = None
    pass_name: str | None = None

    @property
    def is_error(self) -> bool:
        return self.level == "error"

    @property
    def is_warning(self) -> bool:
        return self.level == "warning"

    def render(self) -> str:
        prefix: list[str] = []
        if self.filename:
            prefix.append(self.filename)
        if self.artifact_id:
            prefix.append(self.artifact_id)
        if prefix:
            return f"{': '.join(prefix)}: {self.message}"
        return self.message

    def __str__(self) -> str:
        return self.render()

    def lower(self) -> str:
        return self.render().lower()

    def __contains__(self, item: str) -> bool:
        return item in self.render()


T = TypeVar("T")


@dataclass(frozen=True)
class PassResult(Generic[T]):
    output: T | None
    diagnostics: tuple[PassDiagnostic, ...] = ()

    @classmethod
    def ok(cls, output: T) -> "PassResult[T]":
        return cls(output=output)

    @property
    def errors(self) -> tuple[PassDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.is_error)

    @property
    def warnings(self) -> tuple[PassDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.is_warning)

    @property
    def succeeded(self) -> bool:
        return not self.errors and self.output is not None


@dataclass(frozen=True)
class PipelineResult(Generic[T]):
    family: PropstoreFamily
    stage: StageId
    output: T | None
    diagnostics: tuple[PassDiagnostic, ...]

    @property
    def errors(self) -> tuple[PassDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.is_error)

    @property
    def warnings(self) -> tuple[PassDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.is_warning)

    @property
    def ok(self) -> bool:
        return not self.errors and self.output is not None


InT = TypeVar("InT", contravariant=True)
OutT = TypeVar("OutT")


class SemanticPass(Protocol[InT, OutT]):
    family: PropstoreFamily
    name: str
    version: str
    input_stage: StageId
    output_stage: StageId

    def run(self, value: InT, context: object) -> PassResult[OutT]:
        ...


@dataclass(frozen=True)
class FamilyPipeline:
    family: PropstoreFamily
    start_stage: StageId
    target_stage: StageId
    passes: Sequence[type[Any]]
