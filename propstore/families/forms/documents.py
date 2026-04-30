from __future__ import annotations

from typing import Any

import msgspec

from quire.documents import DocumentStruct


class FormAlternativeDocument(DocumentStruct):
    unit: str
    type: str
    multiplier: float = 1.0
    offset: float = 0.0
    base: float = 10.0
    divisor: float = 1.0
    reference: float = 1.0


class FormExtraUnitDocument(DocumentStruct):
    symbol: str
    dimensions: dict[str, int] = msgspec.field(default_factory=dict)


class FormDocument(DocumentStruct):
    name: str
    dimensionless: bool
    base: str | None = None
    unit_symbol: str | None = None
    qudt: str | None = None
    parameters: dict[str, Any] = msgspec.field(default_factory=dict)
    common_alternatives: tuple[FormAlternativeDocument, ...] = ()
    delta_alternatives: tuple[FormAlternativeDocument, ...] = ()
    kind: str | None = None
    note: str | None = None
    dimensions: dict[str, int] | None = None
    extra_units: tuple[FormExtraUnitDocument, ...] = ()
