"""Owner-layer form show report (Phase 10-0b).

``show_form`` loads an authored :class:`FormDefinition` and renders it to its YAML
source. A missing form raises :class:`FormNotFoundError`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.app.forms import FormNotFoundError, FormShowReport, show_form
from propstore.dimensions import UnitConversion
from propstore.families.forms import FormDefinition, KindType
from propstore.repository import Repository


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.form.save(
        "frequency",
        FormDefinition(
            name="frequency",
            kind=KindType.QUANTITY,
            unit_symbol="Hz",
            conversions={
                "kHz": UnitConversion(
                    unit="kHz", type="multiplicative", multiplier=1000.0
                )
            },
        ),
        message="m",
    )
    return repo


def test_show_form_renders_yaml_and_typed_definition(tmp_path: Path) -> None:
    report = show_form(_repo(tmp_path), "frequency")

    assert isinstance(report, FormShowReport)
    assert "name: frequency" in report.yaml_text
    assert report.form.name == "frequency"
    assert report.form.unit_symbol == "Hz"
    assert "kHz" in report.form.conversions


def test_show_form_unknown_raises(tmp_path: Path) -> None:
    with pytest.raises(FormNotFoundError):
        show_form(_repo(tmp_path), "nonesuch")
