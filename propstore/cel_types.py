"""Typed carriers for CEL source, checked expressions, and condition sets."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any, NewType

if TYPE_CHECKING:
    from propstore.cel_checker import ASTNode, CelError


CelExpr = NewType("CelExpr", str)
CelRegistryFingerprint = NewType("CelRegistryFingerprint", str)

_CHECKED_EXPR_TOKEN = object()


def to_cel_expr(value: object) -> CelExpr:
    """Brand raw authored text as CEL source."""
    if not isinstance(value, str):
        raise TypeError("CEL expression source must be a string")
    return CelExpr(value)


def to_cel_exprs(values: Iterable[object]) -> tuple[CelExpr, ...]:
    return tuple(to_cel_expr(value) for value in values)


@dataclass(frozen=True)
class ParsedCelExpr:
    """Syntax-valid CEL source plus its parsed AST."""

    source: CelExpr
    ast: ASTNode


@dataclass(frozen=True)
class CheckedCelExpr:
    """CEL source that parsed and type-checked against a registry fingerprint."""

    source: CelExpr
    ast: ASTNode
    registry_fingerprint: CelRegistryFingerprint
    warnings: tuple[CelError, ...] = ()
    _token: InitVar[object | None] = field(default=None, repr=False)

    def __post_init__(self, _token: object | None) -> None:
        if _token is not _CHECKED_EXPR_TOKEN:
            raise TypeError("CheckedCelExpr must be created by the CEL checker")

    @classmethod
    def _create(
        cls,
        *,
        source: CelExpr,
        ast: ASTNode,
        registry_fingerprint: CelRegistryFingerprint,
        warnings: Iterable[CelError] = (),
    ) -> CheckedCelExpr:
        return cls(
            source=source,
            ast=ast,
            registry_fingerprint=registry_fingerprint,
            warnings=tuple(warnings),
            _token=_CHECKED_EXPR_TOKEN,
        )


@dataclass(frozen=True)
class CheckedCelConditionSet:
    """Canonical conjunction of checked CEL expressions."""

    conditions: tuple[CheckedCelExpr, ...]
    registry_fingerprint: CelRegistryFingerprint

    def __post_init__(self) -> None:
        normalized = _normalize_checked_conditions(self.conditions)
        for condition in normalized:
            if condition.registry_fingerprint != self.registry_fingerprint:
                raise ValueError(
                    "all checked CEL conditions must share the condition-set registry fingerprint"
                )
        object.__setattr__(self, "conditions", normalized)

    @property
    def sources(self) -> tuple[CelExpr, ...]:
        return tuple(condition.source for condition in self.conditions)


def _normalize_checked_conditions(
    conditions: Iterable[CheckedCelExpr],
) -> tuple[CheckedCelExpr, ...]:
    by_source: dict[str, CheckedCelExpr] = {}
    for condition in conditions:
        source = str(condition.source)
        existing = by_source.get(source)
        if existing is not None:
            if existing.registry_fingerprint != condition.registry_fingerprint:
                raise ValueError(
                    f"duplicate CEL condition {source!r} has multiple registry fingerprints"
                )
            continue
        by_source[source] = condition
    return tuple(by_source[source] for source in sorted(by_source))


def checked_condition_set(
    conditions: Iterable[CheckedCelExpr],
) -> CheckedCelConditionSet:
    normalized = _normalize_checked_conditions(conditions)
    if not normalized:
        return CheckedCelConditionSet(
            conditions=(),
            registry_fingerprint=CelRegistryFingerprint("empty"),
        )
    fingerprint = normalized[0].registry_fingerprint
    return CheckedCelConditionSet(
        conditions=normalized,
        registry_fingerprint=fingerprint,
    )

