from __future__ import annotations

import csv
from pathlib import Path

from tests.test_extracted_rules_lint_clean import TARGET_PAPERS


def test_workstream_k2_done_acceptance_log_and_artifacts() -> None:
    acceptance_log = Path("reviews/2026-04-26-claude/workstreams/WS-K2-acceptance-log.csv")
    rejection_log = Path("reviews/2026-04-26-claude/workstreams/WS-K2-rejection-log.csv")
    prompt_iteration = Path(
        "reviews/2026-04-26-claude/workstreams/WS-K2-prompt-iterations/v2.md"
    )

    assert acceptance_log.exists()
    assert rejection_log.exists()
    assert prompt_iteration.exists()

    rows = list(csv.DictReader(acceptance_log.read_text(encoding="utf-8").splitlines()))
    assert {row["paper"] for row in rows} == set(TARGET_PAPERS)
    proposed = sum(int(row["rules_proposed"]) for row in rows)
    accepted = sum(int(row["rules_accepted"]) for row in rows)
    assert accepted / proposed >= 0.70
    for row in rows:
        assert int(row["rules_accepted"]) / int(row["rules_proposed"]) >= 0.50

    for paper in TARGET_PAPERS:
        assert Path("knowledge/predicates", paper, "declarations.yaml").exists()
        assert Path("knowledge/rules", paper).is_dir()
