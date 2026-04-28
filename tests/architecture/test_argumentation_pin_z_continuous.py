from __future__ import annotations

from argumentation.dung import ArgumentationFramework
from argumentation.probabilistic import ProbabilisticAF, compute_probabilistic_acceptance


def test_argumentation_pin_mc_confidence_accepts_non_lookup_value() -> None:
    praf = ProbabilisticAF(
        framework=ArgumentationFramework(arguments=frozenset({"a"}), defeats=frozenset()),
        p_args={"a": 0.5},
        p_defeats={},
    )

    result = compute_probabilistic_acceptance(
        praf,
        semantics="grounded",
        strategy="mc",
        query_kind="argument_acceptance",
        inference_mode="credulous",
        mc_confidence=0.975,
        mc_epsilon=0.5,
        rng_seed=1,
    )

    assert result.strategy_used == "mc"
    assert 0.0 <= result.acceptance_probs["a"] <= 1.0
