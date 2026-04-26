"""WS14 observatory and public-surface tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st


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


def test_observatory_cli_adapter_builds_typed_app_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from propstore.cli.observatory import observatory
    from propstore.observatory import EvaluationScenario, evaluate_scenarios

    fixture = tmp_path / "scenario.json"
    fixture.write_text(
        json.dumps(
            EvaluationScenario(
                scenario_id="api-cli-equivalence",
                operator_family="surface",
                policy_id="policy:surface",
                replay_result_hash="replay:surface",
            ).to_dict()
        ),
        encoding="utf-8",
    )
    calls = []

    def fake_run_observatory(repo: object, request: object):
        calls.append((repo, request))
        return evaluate_scenarios(request.scenarios)

    monkeypatch.setattr("propstore.cli.observatory.run_observatory", fake_run_observatory)
    repo = MagicMock()
    result = CliRunner().invoke(
        observatory,
        ["run", "--fixture", str(fixture), "--format", "json"],
        obj={"repo": repo},
    )

    assert result.exit_code == 0, result.output
    assert calls[0][0] is repo
    assert calls[0][1].scenarios[0].scenario_id == "api-cli-equivalence"
    assert '"scenario_id": "api-cli-equivalence"' in result.output


def test_root_cli_registers_observatory_lazily() -> None:
    root_cli = Path("propstore/cli/__init__.py").read_text(encoding="utf-8")

    assert '"observatory": ("propstore.cli.observatory", "observatory"' in root_cli
    assert "from propstore.cli.observatory" not in root_cli


def test_epistemic_os_documentation_maps_artifact_to_journal() -> None:
    doc = Path("docs/epistemic-operating-system.md")

    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "source artifact -> assertion -> projection -> state -> journal" in text
    assert "Micropublication" in text
    assert "Observatory" in text
