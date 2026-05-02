from __future__ import annotations

from propstore import dimensions
from propstore.core.conditions.registry import KindType
from propstore.conflict_detector import detect_conflicts
from propstore.families.forms.stages import FormDefinition
from tests.conftest import make_cel_registry, make_concept_registry

from tests.test_conflict_detector import make_claim_file, make_parameter_claim


def _registry_with_frequency_khz() -> dict[str, dict]:
    registry = make_concept_registry()
    frequency_concept = next(
        value
        for value in registry.values()
        if value.get("canonical_name") == "fundamental_frequency"
    )
    frequency_concept["_form_definition"] = FormDefinition(
        name="frequency",
        kind=KindType.QUANTITY,
        unit_symbol="Hz",
        allowed_units={"Hz", "kHz"},
        dimensions={"T": -1},
        conversions={
            "kHz": dimensions.UnitConversion(
                unit="kHz",
                type="multiplicative",
                multiplier=1000.0,
            )
        },
    )
    return registry


def test_parameter_conflict_detection_normalizes_units_on_main_path() -> None:
    registry = _registry_with_frequency_khz()
    claims = make_claim_file(
        [
            make_parameter_claim("claim1", "concept1", 200.0, unit="Hz"),
            make_parameter_claim("claim2", "concept1", 0.2, unit="kHz"),
        ]
    )

    records = detect_conflicts(claims, registry, make_cel_registry(registry))

    assert records == []


def test_parameter_conflict_detection_still_reports_real_si_difference() -> None:
    registry = _registry_with_frequency_khz()
    claims = make_claim_file(
        [
            make_parameter_claim("claim1", "concept1", 200.0, unit="Hz"),
            make_parameter_claim("claim2", "concept1", 300.0, unit="Hz"),
        ]
    )

    records = detect_conflicts(claims, registry, make_cel_registry(registry))

    assert len(records) == 1
