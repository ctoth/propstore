from __future__ import annotations

from pathlib import Path

from argumentation import aba, adf
from argumentation.aba import ABAFramework, ABAPlusFramework, NotFlatABAError
from argumentation.adf import (
    AbstractDialecticalFramework,
    And,
    Atom,
    LinkType,
    Not,
    ThreeValued,
    True_,
    classify_link,
    grounded_interpretation,
    interpretation_from_mapping,
)
from argumentation.aspic import GroundAtom, Literal, Rule
from argumentation.iccma import parse_aba, write_aba


ARGUMENTATION_ABA_ADF_SHA = "ca1778cdcb16b1fa6360ab323bdae0af19c782fb"


def lit(name: str) -> Literal:
    return Literal(GroundAtom(name))


def test_argumentation_pin_exposes_flat_aba_and_adf_public_surface() -> None:
    assert aba is not None
    assert adf is not None

    alpha = lit("alpha")
    beta = lit("beta")
    leave = lit("leave")
    stay = lit("stay")
    base = ABAFramework(
        language=frozenset({alpha, beta, leave, stay}),
        rules=frozenset({Rule((alpha,), leave, "strict"), Rule((beta,), stay, "strict")}),
        assumptions=frozenset({alpha, beta}),
        contrary={alpha: stay, beta: leave},
    )

    assert aba.grounded_extension(base) == frozenset()
    assert parse_aba(write_aba(base)) == base

    try:
        ABAFramework(
            language=frozenset({alpha, beta}),
            rules=frozenset({Rule((alpha,), beta, "strict")}),
            assumptions=frozenset({alpha, beta}),
            contrary={alpha: beta, beta: alpha},
        )
    except NotFlatABAError:
        pass
    else:
        raise AssertionError("non-flat ABA must be rejected at construction")

    plus = ABAPlusFramework(base, preference_order=frozenset({(alpha, beta)}))
    assert not aba.attacks_with_preferences(plus, frozenset({alpha}), frozenset({beta}))
    assert aba.attacks_with_preferences(plus, frozenset({beta}), frozenset({alpha}))
    assert aba.grounded_extension(plus) == frozenset({beta})

    framework = AbstractDialecticalFramework(
        statements=frozenset({"a", "b", "c"}),
        links=frozenset({("a", "c"), ("b", "c")}),
        acceptance_conditions={
            "a": True_(),
            "b": True_(),
            "c": And((Atom("a"), Not(Atom("b")))),
        },
    )
    assert grounded_interpretation(framework) == interpretation_from_mapping(
        {"a": ThreeValued.T, "b": ThreeValued.T, "c": ThreeValued.F}
    )
    assert classify_link(framework, "a", "c") is LinkType.SUPPORTING
    assert classify_link(framework, "b", "c") is LinkType.ATTACKING
    assert not hasattr(adf.AcceptanceCondition, "from_callable")
    assert "__call__" not in adf.AcceptanceCondition.__dict__


def test_argumentation_pin_records_aba_adf_commit() -> None:
    root = Path(__file__).resolve().parents[2]

    assert ARGUMENTATION_ABA_ADF_SHA in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert ARGUMENTATION_ABA_ADF_SHA in (root / "uv.lock").read_text(encoding="utf-8")
