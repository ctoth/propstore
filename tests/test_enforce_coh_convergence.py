from __future__ import annotations

import pytest
from argumentation.dung import ArgumentationFramework
from argumentation.probabilistic import ProbabilisticAF

from propstore.opinion import Opinion, from_probability
from propstore.praf import COHDogmaticInputError, PropstorePrAF, enforce_coh


def _praf() -> PropstorePrAF:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b"), ("b", "a")}),
        attacks=frozenset({("a", "b"), ("b", "a")}),
    )
    p_args = {
        "a": from_probability(0.9, 20.0, 0.5),
        "b": from_probability(0.9, 20.0, 0.5),
    }
    p_defeats = {
        ("a", "b"): from_probability(1.0, 20.0, 0.5),
        ("b", "a"): from_probability(1.0, 20.0, 0.5),
    }
    return PropstorePrAF(
        kernel=ProbabilisticAF(
            framework=framework,
            p_args={arg: opinion.expectation() for arg, opinion in p_args.items()},
            p_defeats={edge: opinion.expectation() for edge, opinion in p_defeats.items()},
            p_attacks={edge: opinion.expectation() for edge, opinion in p_defeats.items()},
        ),
        p_args=p_args,
        p_defeats=p_defeats,
        p_attacks=p_defeats,
    )


def test_enforce_coh_can_return_typed_soft_nonconvergence_result():
    """Cluster F #12: COH convergence state is explicit, not a silent loop cap."""
    from propstore.praf.engine import EnforceCohResult

    result = enforce_coh(_praf(), max_iterations=0, soft=True)

    assert isinstance(result, EnforceCohResult)
    assert result.converged is False
    assert result.iterations == 0
    assert result.max_violation > 0.0


def test_enforce_coh_rejects_dogmatic_inputs_without_magic_pseudo_n():
    framework = ArgumentationFramework(
        arguments=frozenset({"a"}),
        defeats=frozenset({("a", "a")}),
        attacks=frozenset({("a", "a")}),
    )
    praf = PropstorePrAF(
        kernel=ProbabilisticAF(
            framework=framework,
            p_args={"a": 1.0},
            p_defeats={("a", "a"): 1.0},
            p_attacks={("a", "a"): 1.0},
        ),
        p_args={"a": Opinion.dogmatic_true(0.5)},
        p_defeats={("a", "a"): Opinion.dogmatic_true(0.5)},
        p_attacks={("a", "a"): Opinion.dogmatic_true(0.5)},
    )

    with pytest.raises(COHDogmaticInputError):
        enforce_coh(praf)
