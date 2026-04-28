from __future__ import annotations

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
    model_models,
    stable_models,
)
from argumentation.aspic import GroundAtom, Literal, Rule
from argumentation.dung import grounded_extension as dung_grounded_extension
from argumentation.iccma import parse_aba, write_aba


def lit(name: str) -> Literal:
    return Literal(GroundAtom(name))


def argument_label(support: frozenset[Literal], conclusion: Literal) -> str:
    support_text = ",".join(sorted(repr(assumption) for assumption in support))
    return f"{{{support_text}}} |- {conclusion!r}"


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


def test_argumentation_pin_uses_brewka_stable_reduct_semantics() -> None:
    framework = AbstractDialecticalFramework(
        statements=frozenset({"a"}),
        links=frozenset({("a", "a")}),
        acceptance_conditions={"a": Atom("a")},
    )
    false_model = interpretation_from_mapping({"a": ThreeValued.F})
    self_supported_model = interpretation_from_mapping({"a": ThreeValued.T})

    assert model_models(framework) == (false_model, self_supported_model)
    assert stable_models(framework) == (false_model,)


def test_argumentation_pin_projects_flat_aba_joint_support_attacks() -> None:
    alpha = lit("alpha")
    beta = lit("beta")
    gamma = lit("gamma")
    block_gamma = lit("block_gamma")
    not_alpha = lit("not_alpha")
    not_beta = lit("not_beta")
    framework = ABAFramework(
        language=frozenset({alpha, beta, gamma, block_gamma, not_alpha, not_beta}),
        rules=frozenset({Rule((alpha, beta), block_gamma, "strict")}),
        assumptions=frozenset({alpha, beta, gamma}),
        contrary={alpha: not_alpha, beta: not_beta, gamma: block_gamma},
    )
    dung = aba.aba_to_dung(framework)

    assert argument_label(frozenset({alpha, beta}), block_gamma) in dung.arguments
    grounded = dung_grounded_extension(dung)
    assert argument_label(frozenset({alpha}), alpha) in grounded
    assert argument_label(frozenset({beta}), beta) in grounded
    assert argument_label(frozenset({gamma}), gamma) not in grounded
