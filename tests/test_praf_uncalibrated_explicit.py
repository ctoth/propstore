from __future__ import annotations

from argumentation.bipolar import BipolarArgumentationFramework
from argumentation.dung import ArgumentationFramework

from propstore.core.analyzers import SharedAnalyzerInput, build_praf_from_shared_input
from propstore.probabilistic_relations import ClaimGraphRelations
from propstore.provenance import ProvenanceStatus


def test_uncalibrated_arguments_remain_vacuous_in_kernel_framework():
    """Codex #15: missing calibration must not shrink the argument topology."""
    shared = SharedAnalyzerInput(
        active_graph=None,  # type: ignore[arg-type]
        comparison="elitist",
        claims_by_id={
            "calibrated": {
                "id": "calibrated",
                "opinion_belief": 0.8,
                "opinion_disbelief": 0.1,
                "opinion_uncertainty": 0.1,
                "opinion_base_rate": 0.5,
            },
            "unknown": {"id": "unknown"},
        },
        stance_rows=(),
        relations=ClaimGraphRelations(
            arguments=frozenset({"calibrated", "unknown"}),
            attacks=frozenset({("calibrated", "unknown")}),
            direct_defeats=frozenset({("calibrated", "unknown")}),
            supports=frozenset(),
        ),
        argumentation_framework=ArgumentationFramework(
            arguments=frozenset({"calibrated", "unknown"}),
            defeats=frozenset({("calibrated", "unknown")}),
            attacks=frozenset({("calibrated", "unknown")}),
        ),
        bipolar_framework=BipolarArgumentationFramework(
            arguments=frozenset({"calibrated", "unknown"}),
            defeats=frozenset({("calibrated", "unknown")}),
            supports=frozenset(),
        ),
    )

    praf = build_praf_from_shared_input(shared)

    assert praf.framework.arguments == frozenset({"calibrated", "unknown"})
    assert ("calibrated", "unknown") in praf.framework.defeats
    assert "unknown" in praf.p_args
    assert praf.p_args["unknown"].u == 1.0
    assert praf.p_args["unknown"].provenance is not None
    assert praf.p_args["unknown"].provenance.status is ProvenanceStatus.VACUOUS
    assert "unknown" in praf.omitted_arguments
    assert ("calibrated", "unknown") in praf.omitted_relations
    assert praf.p_defeats[("calibrated", "unknown")].u == 1.0
