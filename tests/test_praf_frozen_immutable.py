from __future__ import annotations

import pytest
from argumentation.dung import ArgumentationFramework
from argumentation.probabilistic import ProbabilisticAF

from propstore.opinion import Opinion
from propstore.praf import NoCalibration, PropstorePrAF


def test_propstore_praf_omission_maps_are_actually_immutable():
    """Cluster F #15: frozen PrAF must not expose mutable omission dicts."""
    framework = ArgumentationFramework(arguments=frozenset({"a"}), defeats=frozenset())
    praf = PropstorePrAF(
        kernel=ProbabilisticAF(framework=framework, p_args={"a": 1.0}, p_defeats={}),
        p_args={"a": Opinion.vacuous(0.5)},
        p_defeats={},
        omitted_arguments={"a": NoCalibration("missing_claim_calibration")},
    )

    with pytest.raises(TypeError):
        praf.omitted_arguments["b"] = NoCalibration("mutated")  # type: ignore[index]
