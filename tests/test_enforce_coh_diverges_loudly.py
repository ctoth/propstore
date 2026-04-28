"""COH enforcement failure modes.

Hunter & Thimm (2017, p.9) defines COH as the attack-pair constraint
P(A) + P(B) <= 1. The paper does not define reconstructing dogmatic
subjective-logic opinions through a fabricated evidence count.
"""

from __future__ import annotations

import pytest

from argumentation.dung import ArgumentationFramework
from argumentation.probabilistic import ProbabilisticAF
from propstore.opinion import Opinion, from_probability
from propstore.praf import engine as praf_engine


def _praf_with_args(p_args: dict[str, Opinion]) -> praf_engine.PropstorePrAF:
    framework = ArgumentationFramework(
        arguments=frozenset(p_args),
        defeats=frozenset({("A", "B")}),
        attacks=frozenset({("A", "B")}),
    )
    return praf_engine.PropstorePrAF(
        kernel=ProbabilisticAF(
            framework=framework,
            p_args={arg: opinion.expectation() for arg, opinion in p_args.items()},
            p_defeats={("A", "B"): 1.0},
        ),
        p_args=p_args,
        p_defeats={("A", "B"): Opinion.dogmatic_true(0.5)},
    )


def test_enforce_coh_rejects_dogmatic_argument_opinions() -> None:
    praf = _praf_with_args(
        {
            "A": Opinion.dogmatic_true(0.5),
            "B": from_probability(0.7, 10, 0.5),
        }
    )

    with pytest.raises(praf_engine.COHDogmaticInputError):
        praf_engine.enforce_coh(praf)


def test_enforce_coh_iteration_cap_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    praf = _praf_with_args(
        {
            "A": from_probability(0.8, 10, 0.5),
            "B": from_probability(0.7, 10, 0.5),
        }
    )
    monkeypatch.setattr(praf_engine, "_COH_MAX_ITERATIONS", 0)

    with pytest.raises(praf_engine.COHDivergenceError):
        praf_engine.enforce_coh(praf)
