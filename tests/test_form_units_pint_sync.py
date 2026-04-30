from __future__ import annotations

import yaml

from propstore import dimensions
from propstore.unit_dimensions import clear_symbol_table, register_form_units


def test_form_extra_units_register_with_pint(tmp_path) -> None:
    forms_dir = tmp_path / "forms"
    forms_dir.mkdir()
    (forms_dir / "frequency.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "frequency",
                "dimensionless": False,
                "kind": "quantity",
                "unit_symbol": "Hz",
                "dimensions": {"T": -1},
                "extra_units": [
                    {"symbol": "voice_cycle", "dimensions": {"T": -1}},
                ],
            }
        ),
        encoding="utf-8",
    )
    clear_symbol_table()

    register_form_units(forms_dir)

    assert dimensions.can_convert_unit_to("voice_cycle", "Hz")
