from __future__ import annotations

from argumentation import aba, adf
from argumentation.aba import ABAFramework
from argumentation.aspic import GroundAtom, Literal, Rule
from argumentation.dung import grounded_extension as dung_grounded_extension

interpretation_from_json_payload = getattr(adf, "interpretation_from_mapping")


def lit(name: str) -> Literal:
    return Literal(GroundAtom(name))


def argument_label(support: frozenset[Literal], conclusion: Literal) -> str:
    support_text = ",".join(sorted(repr(assumption) for assumption in support))
    return f"{{{support_text}}} |- {conclusion!r}"


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
