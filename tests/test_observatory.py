"""WS14 observatory deterministic-report tests.

The CLI-adapter, lazy-registration, and epistemic-OS documentation cases live
with the CLI/docs phases; this file covers the owner-layer observatory report
builders only.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
import pytest


def test_observatory_harness_exports_stable_traceable_reports() -> None:
    from propstore.observatory import (
        EvaluationScenario,
        SemanticTraceRecord,
        ObservatoryReport,
        evaluate_scenarios,
    )

    trace = SemanticTraceRecord(
        source_artifact_id="source:clark:figure-7",
        assertion_id="ps:assertion:claim-c1",
        projection_id="projection:micropublication-support",
        state_hash="state:abc",
        journal_entry_hash="journal:def",
    )
    scenarios = (
        EvaluationScenario(
            scenario_id="greenberg-transmutation",
            operator_family="citation-distortion",
            policy_id="policy:strict-provenance",
            replay_result_hash="replay:greenberg",
            falsification_ids=("citation-transmutation",),
            trace_records=(trace,),
        ),
        EvaluationScenario(
            scenario_id="clark-support-graph",
            operator_family="micropublication",
            policy_id="policy:strict-provenance",
            replay_result_hash="replay:clark",
            trace_records=(trace,),
        ),
    )

    first = evaluate_scenarios(reversed(scenarios))
    second = evaluate_scenarios(scenarios)
    restored = ObservatoryReport.from_dict(first.to_dict())

    assert first == second
    assert restored == first
    assert restored.content_hash == first.content_hash
    assert first.operator_summaries["citation-distortion"].falsification_count == 1
    assert first.scenario_results[0].trace_records[0].source_artifact_id == "source:clark:figure-7"
    assert first.scenario_results[0].trace_records[0].journal_entry_hash == "journal:def"


@pytest.mark.property
@given(
    scenario_id=st.text(min_size=1, max_size=24),
    policy_id=st.text(min_size=1, max_size=24),
    replay_hash=st.text(min_size=1, max_size=24),
)
@settings(max_examples=16)
def test_observatory_report_roundtrips_generated_fixtures(
    scenario_id: str,
    policy_id: str,
    replay_hash: str,
) -> None:
    from propstore.observatory import EvaluationScenario, ObservatoryReport, evaluate_scenarios

    report = evaluate_scenarios((
        EvaluationScenario(
            scenario_id=scenario_id,
            operator_family="generated",
            policy_id=policy_id,
            replay_result_hash=replay_hash,
        ),
    ))

    assert ObservatoryReport.from_dict(report.to_dict()).to_dict() == report.to_dict()
