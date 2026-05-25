"""Form family model and document protocol types."""

from __future__ import annotations

from typing import Any, Protocol

from quire.charters import FamilyModel


class FormAlternativeProtocol(Protocol):
    unit: str
    type: str
    multiplier: float
    offset: float
    base: float
    divisor: float
    reference: float


class FormExtraUnitProtocol(Protocol):
    symbol: str
    dimensions: dict[str, int]


class FormDocumentProtocol(Protocol):
    name: str
    dimensionless: bool
    base: str | None
    unit_symbol: str | None
    qudt: str | None
    parameters: dict[str, Any] | None
    common_alternatives: tuple[FormAlternativeProtocol, ...] | None
    delta_alternatives: tuple[FormAlternativeProtocol, ...] | None
    kind: str | None
    note: str | None
    dimensions: dict[str, int] | None
    extra_units: tuple[FormExtraUnitProtocol, ...] | None
    min: float | None
    max: float | None


class Form(FamilyModel):
    pass


class FormAlgebra(FamilyModel):
    pass
