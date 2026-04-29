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
    prudent_conflict_free,
    prudent_grounded_extension,
    prudent_preferred_extensions,
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
    prudent_framework = af({"a", "b", "c", "d"}, {("a", "b"), ("b", "c"), ("c", "d")})

    assert set(stage2_extensions(stage_framework)) == set(stage_extensions(stage_framework))
    assert ("a", "c") not in indirect_attacks(prudent_framework)
    assert ("a", "d") in indirect_attacks(prudent_framework)
    assert prudent_conflict_free(prudent_framework, frozenset({"a", "c"})) is True
    assert prudent_conflict_free(prudent_framework, frozenset({"a", "d"})) is False


def test_argumentation_pin_contains_coste_marquis_prudent_grounded_example() -> None:
    """Coste-Marquis et al. 2005, pp. 1-3: AF1 prudent extension is {i,n}."""
    framework = af(
        {"a", "b", "c", "e", "n", "i"},
        {("b", "a"), ("c", "a"), ("n", "c"), ("i", "b"), ("e", "c"), ("i", "e")},
    )

    assert ("i", "a") in indirect_attacks(framework)
    assert prudent_conflict_free(framework, frozenset({"a", "i", "n"})) is False
    assert prudent_preferred_extensions(framework) == [frozenset({"i", "n"})]
    assert prudent_grounded_extension(framework) == frozenset({"i", "n"})


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
