import pytest

from argumentation.dung import ArgumentationFramework
from argumentation.probabilistic import ProbabilisticAF
from propstore.opinion import Opinion, from_probability
from propstore.praf import PreferenceLayerError, PropstorePrAF, enforce_coh


def test_enforce_coh_requires_attacks() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"A", "B"}),
        defeats=frozenset({("A", "B")}),
        attacks=None,
    )
    praf = PropstorePrAF(
        kernel=ProbabilisticAF(
            framework=framework,
            p_args={"A": 0.8, "B": 0.7},
            p_defeats={("A", "B"): 1.0},
        ),
        p_args={"A": from_probability(0.8, 10), "B": from_probability(0.7, 10)},
        p_defeats={("A", "B"): Opinion.dogmatic_true()},
    )

    with pytest.raises(PreferenceLayerError):
        enforce_coh(praf)
