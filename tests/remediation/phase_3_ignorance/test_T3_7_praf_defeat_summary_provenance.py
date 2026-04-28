from __future__ import annotations

import pytest

from argumentation.dung import ArgumentationFramework
from argumentation.probabilistic import ProbabilisticAF

from propstore.praf import summarize_defeat_relations
from propstore.provenance import ProvenanceStatus


def test_summarized_defeat_opinions_are_vacuous_without_calibration() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )
    praf = ProbabilisticAF(
        framework=framework,
        p_args={"a": 1.0, "b": 1.0},
        p_defeats={("a", "b"): 0.25},
    )

    relations = summarize_defeat_relations(praf)

    assert len(relations) == 1
    opinion = relations[0].opinion
    assert opinion.provenance is not None
    assert opinion.provenance.status is ProvenanceStatus.VACUOUS
    assert "defeat_probability_uncalibrated" in opinion.provenance.operations
    assert opinion.b == pytest.approx(0.0)
    assert opinion.d == pytest.approx(0.0)
    assert opinion.u == pytest.approx(1.0)
    assert opinion.expectation() == pytest.approx(0.25)
