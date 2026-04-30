from __future__ import annotations

from propstore.repository import Repository

from tests.test_extracted_rules_lint_clean import TARGET_PAPERS


def test_extracted_rules_fire_against_ws_k_argumentation_pipeline(tmp_path) -> None:
    from propstore.heuristic.rule_corpus import synthetic_metadata_for_paper
    from propstore.source_trust_argumentation import calibrate_source_trust

    repo = Repository.init(tmp_path / "knowledge")
    source_ref = __import__(
        "propstore.families.registry",
        fromlist=["SourceRef"],
    ).SourceRef("synthetic")

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
