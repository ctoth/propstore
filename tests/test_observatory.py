"""WS14 observatory deterministic-report tests.

The CLI-adapter, lazy-registration, and epistemic-OS documentation cases live
with the CLI/docs phases; this file covers the owner-layer observatory report
builders only.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
import pytest
from quire.documents import (
    DocumentSchemaError,
    convert_document_value,
    document_to_payload,
)


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
    restored = convert_document_value(
        document_to_payload(first),
        ObservatoryReport,
        source="observatory report",
    )

    assert first == second
    assert restored == first
    assert restored.content_hash == first.content_hash
    citation_summary = next(
        summary
        for summary in first.operator_summaries
        if summary.operator_family == "citation-distortion"
    )
    assert citation_summary.falsification_count == 1
    assert (
        first.scenario_results[0].trace_records[0].source_artifact_id
        == "source:clark:figure-7"
    )
    assert (
        first.scenario_results[0].trace_records[0].journal_entry_hash == "journal:def"
    )


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
    from propstore.observatory import (
        EvaluationScenario,
        ObservatoryReport,
        evaluate_scenarios,
    )

    report = evaluate_scenarios(
        (
            EvaluationScenario(
                scenario_id=scenario_id,
                operator_family="generated",
                policy_id=policy_id,
                replay_result_hash=replay_hash,
            ),
        )
    )

    payload = document_to_payload(report)
    assert (
        document_to_payload(
            convert_document_value(
                payload,
                ObservatoryReport,
                source="generated observatory report",
            )
        )
        == payload
    )


def test_observatory_scenario_rejects_unknown_nested_trace_field() -> None:
    from propstore.observatory import EvaluationScenario

    with pytest.raises(DocumentSchemaError, match="unexpected"):
        convert_document_value(
            {
                "scenario_id": "s1",
                "operator_family": "family",
                "policy_id": "policy",
                "replay_result_hash": "replay",
                "schema_version": "propstore.evaluation_scenario.v2",
                "trace_records": [
                    {
                        "source_artifact_id": "source",
                        "assertion_id": "assertion",
                        "projection_id": "projection",
                        "state_hash": "state",
                        "journal_entry_hash": "journal",
                        "schema_version": "propstore.semantic_trace.v2",
                        "unexpected": True,
                    }
                ],
            },
            EvaluationScenario,
            source="scenario fixture",
        )


def test_observatory_scenario_rejects_v1_shape() -> None:
    from propstore.observatory import EvaluationScenario

    with pytest.raises(
        DocumentSchemaError, match="unsupported evaluation scenario version"
    ):
        convert_document_value(
            {
                "scenario_id": "s1",
                "operator_family": "family",
                "policy_id": "policy",
                "replay_result_hash": "replay",
                "schema_version": "propstore.evaluation_scenario.v1",
            },
            EvaluationScenario,
            source="scenario fixture",
        )
