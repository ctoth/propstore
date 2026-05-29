"""Form world-store embedded document structs.

The form family charters and their typed documents (``FormDocument`` /
``Form_algebraDocument``) are declarative ``@charter`` classes defined in
:mod:`propstore.families.forms.models` (so their generated documents report
that module, matching the contract manifest). This module owns only the two
embedded nested value types referenced by ``FormDocument`` as ``json=True``
fields; keeping them here preserves their manifest-pinned module path
(``...forms.declaration.FormAlternativeDocument`` / ``...FormExtraUnitDocument``).
"""

from __future__ import annotations

import msgspec

from quire.charter_class import CharterDoc


class FormAlternativeDocument(CharterDoc):
    unit: str
    type: str
    multiplier: float = 1.0
    offset: float = 0.0
    base: float = 10.0
    divisor: float = 1.0
    reference: float = 1.0


class FormExtraUnitDocument(CharterDoc):
    symbol: str
    dimensions: dict[str, int] = msgspec.field(default_factory=dict)
