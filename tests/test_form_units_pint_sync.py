"""Ported from the May-16 reference: form-declared extra units register with Pint.

In the rewrite, forms are charters, not YAML files, so registration consumes
``FormDefinition`` objects directly (no forms-directory scan).
"""

from __future__ import annotations

from condition_ir import KindType

from propstore import dimensions
from propstore.dimensions import ExtraUnitDefinition
from propstore.families.forms import FormDefinition
from propstore.unit_dimensions import (
    clear_symbol_table,
    register_form_units,
    resolve_unit_dimensions,
)


def test_form_extra_units_register_with_pint() -> None:
    form = FormDefinition(
        name="frequency",
        kind=KindType.QUANTITY,
        unit_symbol="Hz",
        dimensions={"T": -1},
        extra_units=(ExtraUnitDefinition(symbol="voice_cycle", dimensions={"T": -1}),),
    )
    clear_symbol_table()

    register_form_units([form])

    assert dimensions.can_convert_unit_to("voice_cycle", "Hz")
    assert resolve_unit_dimensions("voice_cycle") == {"T": -1}


def test_clear_symbol_table_removes_registered_form_units() -> None:
    form = FormDefinition(
        name="custom_form",
        kind=KindType.QUANTITY,
        unit_symbol="X",
        dimensions={"L": 1},
        extra_units=(ExtraUnitDefinition(symbol="cX", dimensions={"L": 1}),),
    )
    clear_symbol_table()
    register_form_units([form])
    assert resolve_unit_dimensions("cX") is not None

    clear_symbol_table()
    assert resolve_unit_dimensions("cX") is None
