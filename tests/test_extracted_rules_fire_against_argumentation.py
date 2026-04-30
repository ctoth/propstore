from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.families.registry import SourceRef
from propstore.repository import Repository

from tests.test_extracted_rules_lint_clean import TARGET_PAPERS


def test_extracted_rules_fire_against_ws_k_argumentation_pipeline(tmp_path) -> None:
    from propstore.heuristic.rule_corpus import synthetic_metadata_for_paper
    from propstore.source_trust_argumentation import calibrate_source_trust

    repo = Repository.init(tmp_path / "knowledge")
    source_ref = SourceRef("synthetic")

    fired_papers: set[str] = set()
    for paper in TARGET_PAPERS:
        repo.families.source_metadata.save(
            source_ref,
            synthetic_metadata_for_paper(paper),
            message=f"Set synthetic metadata for {paper}",
        )
        result = calibrate_source_trust(repo, "synthetic")
        fired = {firing.rule_id.split(":", 1)[0] for firing in result.derived_from}
        assert paper in fired
        fired_papers.update(fired)

    assert set(TARGET_PAPERS) <= fired_papers


@pytest.mark.property
@given(
    predicate=st.from_regex(r"[a-z_][a-z0-9_]{0,20}", fullmatch=True),
    value=st.one_of(
        st.booleans(),
        st.integers(min_value=0, max_value=1000),
        st.sampled_from(("replicated", "failed-replication", "hot", "cold")),
    ),
)
def test_generated_metadata_facts_fire_deterministically_through_consumer_api(
    predicate: str,
    value: object,
) -> None:
    from propstore.source_trust_argumentation import calibrate_source_trust

    rule_corpus = (
        {
            "id": "generated-paper:rule-001",
            "effect": "support",
            "weight": 0.25,
            "base_rate": 0.5,
            "conditions": {predicate: value},
        },
    )
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        first_repo = Repository.init(root / "first")
        second_repo = Repository.init(root / "second")
        first_repo.families.source_metadata.save(
            SourceRef("synthetic"),
            {predicate: value, "irrelevant": "first"},
            message="Set generated metadata",
        )
        second_repo.families.source_metadata.save(
            SourceRef("synthetic"),
            {"irrelevant": "second", predicate: value},
            message="Set generated metadata",
        )

        first = calibrate_source_trust(first_repo, "synthetic", rule_corpus=rule_corpus)
        second = calibrate_source_trust(second_repo, "synthetic", rule_corpus=rule_corpus)

    assert tuple(firing.rule_id for firing in first.derived_from) == (
        "generated-paper:rule-001",
    )
    assert tuple(firing.rule_id for firing in second.derived_from) == (
        "generated-paper:rule-001",
    )
    assert first.status == second.status
    assert first.prior_base_rate == second.prior_base_rate
    assert first.derived_from[0].facts == second.derived_from[0].facts
