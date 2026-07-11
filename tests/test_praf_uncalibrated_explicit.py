from __future__ import annotations

from argumentation.core.bipolar import BipolarArgumentationFramework
from argumentation.core.dung import ArgumentationFramework

from propstore.core.analyzers import SharedAnalyzerInput, build_praf_from_shared_input
from propstore.families.claims import Claim
from propstore.probabilistic_relations import ClaimGraphRelations
from propstore.provenance import ProvenanceStatus


def test_uncalibrated_arguments_remain_vacuous_in_kernel_framework() -> None:
    """Missing calibration must not shrink the argument topology (non-commitment)."""

    shared = SharedAnalyzerInput(
        comparison="elitist",
        claims_by_id={
            "calibrated": Claim(claim_id="calibrated"),
            "unknown": Claim(claim_id="unknown"),
        },
        stances=(),
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
    assert praf.p_args["unknown"].opinion.u == 1.0
    assert praf.p_args["unknown"].provenance is not None
    assert praf.p_args["unknown"].provenance.status is ProvenanceStatus.VACUOUS
    assert "unknown" in praf.omitted_arguments
    assert ("calibrated", "unknown") in praf.omitted_relations
    assert praf.p_defeats[("calibrated", "unknown")].opinion.u == 1.0
