from __future__ import annotations


def test_proposal_rules_family_is_registered(tmp_path) -> None:
    from propstore.families.registry import PROPOSAL_RULES_FAMILY, RuleProposalRef
    from propstore.repository import Repository

    repo = Repository.init(tmp_path / "knowledge")
    ref = RuleProposalRef(
        source_paper="Ioannidis_2005_WhyMostPublishedResearch",
        rule_id="rule-001",
    )

    assert repo.families.proposal_rules.artifact_family is PROPOSAL_RULES_FAMILY
    assert repo.families.proposal_rules.address(ref).require_path() == (
        "rules/Ioannidis_2005_WhyMostPublishedResearch/rule-001.yaml"
    )


def test_rule_proposal_document_is_typed() -> None:
    from propstore.families.documents.rules import (
        AtomDocument,
        RuleDocument,
        RuleExtractionProvenance,
        RuleProposalDocument,
    )

    rule = RuleDocument(
        id="rule-001",
        kind="defeasible",
        head=AtomDocument(predicate="low_trust", terms=()),
        body=(),
    )
    document = RuleProposalDocument(
        source_paper="Ioannidis_2005_WhyMostPublishedResearch",
        rule_id="rule-001",
        proposed_rule=rule,
        predicates_referenced=("sample_size/2",),
        extraction_provenance=RuleExtractionProvenance(
            operations=("rule_extraction",),
            agent="codex",
            model="test-model",
            prompt_sha="abc123",
            notes_sha="def456",
            predicates_sha="ghi789",
            status="CALIBRATED",
        ),
        extraction_date="2026-04-29",
        page_reference="Ioannidis 2005 p. 0697",
    )

    assert document.proposed_rule.id == "rule-001"
    assert document.predicates_referenced == ("sample_size/2",)
