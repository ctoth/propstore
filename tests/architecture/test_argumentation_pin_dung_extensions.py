from __future__ import annotations

import importlib

import pytest

from argumentation.bipolar import (
    BipolarArgumentationFramework,
    bipolar_complete_extensions,
    bipolar_grounded_extension,
)
from argumentation.dung import (
    ArgumentationFramework,
    eager_extension,
    indirect_attacks,
    prudent_admissible,
    semi_stable_extensions,
    stage2_extensions,
    stage_extensions,
)
from argumentation.labelling import (
    Label,
    Labelling,
    complete_labellings,
    legally_in,
    legally_out,
)


ARGUMENTATION_DUNG_EXTENSIONS_COMMIT = "c941fe4e3b795406003b64090529c9b2d7fc037b"


def af(args: set[str], defeats: set[tuple[str, str]]) -> ArgumentationFramework:
    return ArgumentationFramework(arguments=frozenset(args), defeats=frozenset(defeats))


def test_argumentation_pin_exposes_operational_labelling_and_dung_extensions() -> None:
    framework = af({"A", "B", "C"}, {("A", "B"), ("B", "C")})
    labelling = Labelling.from_statuses(
        arguments=framework.arguments,
        statuses={"A": Label.IN, "B": Label.OUT, "C": Label.IN},
    )

    assert legally_in(labelling, framework, "C") is True
    assert legally_out(labelling, framework, "B") is True
    assert {item.extension for item in complete_labellings(framework)} == {
        frozenset({"A", "C"})
    }


def test_argumentation_pin_contains_caminada_eager_and_semi_stable_behaviour() -> None:
    """Caminada 2006 p. 8 floating example; eager rejects undefended common `D`."""
    framework = af(
        {"A", "B", "C", "D"},
        {("A", "B"), ("B", "A"), ("A", "C"), ("B", "C"), ("C", "D")},
    )

    assert set(semi_stable_extensions(framework)) == {
        frozenset({"A", "D"}),
        frozenset({"B", "D"}),
    }
    assert eager_extension(framework) == frozenset()


def test_argumentation_pin_contains_stage2_and_prudent_surfaces() -> None:
    stage_framework = af({"a", "b", "c"}, {("a", "b"), ("b", "c"), ("c", "a")})
    prudent_framework = af({"a", "b", "c"}, {("a", "b"), ("b", "c")})

    assert set(stage2_extensions(stage_framework)) == set(stage_extensions(stage_framework))
    assert ("a", "c") in indirect_attacks(prudent_framework)
    assert prudent_admissible(prudent_framework, frozenset({"a", "c"})) is False


def test_argumentation_pin_contains_cayrol_bipolar_grounded_complete() -> None:
    framework = BipolarArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("b", "c")}),
        supports=frozenset({("a", "b")}),
    )

    assert bipolar_grounded_extension(framework) == frozenset({"a", "b"})
    assert frozenset({"a", "b"}) in bipolar_complete_extensions(framework)


def test_argumentation_pin_deleted_dung_z3_backend_and_records_commit() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("argumentation.dung_z3")

    pyproject_text = __import__("pathlib").Path("pyproject.toml").read_text(encoding="utf-8")
    assert ARGUMENTATION_DUNG_EXTENSIONS_COMMIT in pyproject_text
