from __future__ import annotations

from pathlib import Path


def test_workstream_h_named_gate_files_exist_and_budget_gate_is_marked():
    required = {
        "tests/test_praf_paper_td_complete_routing.py",
        "tests/test_praf_uncalibrated_explicit.py",
        "tests/test_praf_raw_confidence_not_dogmatic.py",
        "tests/test_defeat_summary_opinion_honest.py",
        "tests/test_enforce_coh_convergence.py",
        "tests/test_sensitivity_global_method_or_honest_naming.py",
        "tests/test_calibrate_brier_and_log_loss.py",
        "tests/test_praf_frozen_immutable.py",
        "tests/test_praf_argument_enumeration_budget.py",
        "tests/test_dfquad_attack_support_per_paper_contract.py",
    }

    for path in required:
        assert Path(path).exists(), path

    budget_gate = Path("tests/test_praf_argument_enumeration_budget.py").read_text()
    assert "WS-O-gun D-18" in budget_gate
    assert "ResultStatus.BUDGET_EXCEEDED" in budget_gate
