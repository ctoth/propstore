"""COH rationality enforcement over opinion-valued argument expectations.

COH (Hunter 2013): an argument and an argument it attacks cannot both be
near-certain. :func:`enforce_coh` rescales violating expectations and rebuilds
each argument's opinion from its preserved evidence count. Dogmatic inputs (no
evidence count) are rejected, and non-convergence is loud — never silently
returned as if coherent.
"""

from __future__ import annotations

import pytest
from argumentation.core.dung import ArgumentationFramework
from argumentation.probabilistic.probabilistic import ProbabilisticAF
from doxa import Opinion

import propstore.praf.engine as praf_engine
from propstore.opinion_provenance import OpinionWithProvenance
from propstore.praf import (
    COHDivergenceError,
    COHDogmaticInputError,
    EnforceCohResult,
    PropstorePrAF,
    enforce_coh,
)
from propstore.provenance import Provenance, ProvenanceStatus

_STATED = Provenance(status=ProvenanceStatus.STATED)


def _owp(opinion: Opinion) -> OpinionWithProvenance:
    return OpinionWithProvenance(opinion=opinion, provenance=_STATED)


def _praf(
    opinions: dict[str, Opinion], *, edges: set[tuple[str, str]]
) -> PropstorePrAF:
    framework = ArgumentationFramework(
        arguments=frozenset(opinions),
        defeats=frozenset(edges),
        attacks=frozenset(edges),
    )
    p_args = {arg: _owp(op) for arg, op in opinions.items()}
    kernel = ProbabilisticAF(
        framework=framework,
        p_args={arg: op.expectation() for arg, op in opinions.items()},
        p_defeats={edge: 1.0 for edge in edges},
        p_attacks={edge: 1.0 for edge in edges},
    )
    return PropstorePrAF(
        kernel=kernel,
        p_args=p_args,
        p_defeats={
            edge: _owp(Opinion.from_probability(1.0, 20.0, 0.5)) for edge in edges
        },
    )


def test_enforce_coh_scales_violating_pair() -> None:
    praf = _praf(
        {
            "a": Opinion.from_probability(0.9, 20.0, 0.5),
            "b": Opinion.from_probability(0.9, 20.0, 0.5),
        },
        edges={("a", "b"), ("b", "a")},
    )
    result = enforce_coh(praf)
    assert isinstance(result, PropstorePrAF)
    e_a = result.p_args["a"].expectation()
    e_b = result.p_args["b"].expectation()
    assert e_a + e_b <= 1.0 + 1e-9


def test_enforce_coh_preserves_satisfying_pair() -> None:
    op_a = Opinion.from_probability(0.3, 20.0, 0.5)
    op_b = Opinion.from_probability(0.4, 20.0, 0.5)
    praf = _praf({"a": op_a, "b": op_b}, edges={("a", "b")})
    result = enforce_coh(praf)
    assert isinstance(result, PropstorePrAF)
    assert result.p_args["a"].opinion == op_a
    assert result.p_args["b"].opinion == op_b


def test_enforce_coh_is_idempotent() -> None:
    praf = _praf(
        {
            "a": Opinion.from_probability(0.9, 20.0, 0.5),
            "b": Opinion.from_probability(0.9, 20.0, 0.5),
        },
        edges={("a", "b"), ("b", "a")},
    )
    once = enforce_coh(praf)
    assert isinstance(once, PropstorePrAF)
    twice = enforce_coh(once)
    assert isinstance(twice, PropstorePrAF)
    for arg in ("a", "b"):
        assert once.p_args[arg].expectation() == pytest.approx(
            twice.p_args[arg].expectation()
        )


def test_enforce_coh_requires_explicit_attacks() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )
    praf = PropstorePrAF(
        kernel=ProbabilisticAF(
            framework=framework, p_args={"a": 0.5, "b": 0.5}, p_defeats={}
        ),
        p_args={"a": _owp(Opinion.vacuous(0.5)), "b": _owp(Opinion.vacuous(0.5))},
        p_defeats={},
    )
    with pytest.raises(praf_engine.PreferenceLayerError):
        enforce_coh(praf)


def test_enforce_coh_soft_returns_typed_nonconvergence() -> None:
    praf = _praf(
        {
            "a": Opinion.from_probability(0.9, 20.0, 0.5),
            "b": Opinion.from_probability(0.9, 20.0, 0.5),
        },
        edges={("a", "b"), ("b", "a")},
    )
    result = enforce_coh(praf, max_iterations=0, soft=True)
    assert isinstance(result, EnforceCohResult)
    assert result.converged is False
    assert result.iterations == 0
    assert result.max_violation > 0.0


def test_enforce_coh_rejects_dogmatic_argument_opinions() -> None:
    praf = _praf(
        {
            "a": Opinion.dogmatic_true(0.5),
            "b": Opinion.from_probability(0.7, 10.0, 0.5),
        },
        edges={("a", "b")},
    )
    with pytest.raises(COHDogmaticInputError):
        enforce_coh(praf)


def test_enforce_coh_iteration_cap_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    praf = _praf(
        {
            "a": Opinion.from_probability(0.8, 10.0, 0.5),
            "b": Opinion.from_probability(0.7, 10.0, 0.5),
        },
        edges={("a", "b"), ("b", "a")},
    )
    monkeypatch.setattr(praf_engine, "_COH_MAX_ITERATIONS", 0)
    with pytest.raises(COHDivergenceError):
        enforce_coh(praf)
