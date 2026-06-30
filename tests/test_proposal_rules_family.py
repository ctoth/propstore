from __future__ import annotations


def test_proposal_rules_family_is_registered(tmp_path) -> None:
    from propstore.families.registry import (
        PROPSTORE_FAMILY_REGISTRY,
        PropstoreFamily,
        RuleProposalRef,
    )
    from propstore.repository import Repository

    repo = Repository.init(tmp_path / "knowledge")
    ref = RuleProposalRef(
        source_paper="Ioannidis_2005_WhyMostPublishedResearch",
        rule_id="rule-001",
    )

    assert repo.families.proposal_rules.family is (
        PROPSTORE_FAMILY_REGISTRY.by_key(PropstoreFamily.PROPOSAL_RULES).artifact_family
    )
    assert repo.families.proposal_rules.address(ref).require_path() == (
        "rules/Ioannidis_2005_WhyMostPublishedResearch/rule-001.yaml"
    )


def test_rule_proposal_document_is_typed() -> None:
    from propstore.families.rules import (
        Atom,
        ProposedRule,
        RuleExtractionProvenance,
        RuleProposal,
    )

    rule = ProposedRule(
        id="rule-001",
        kind="defeasible",
        head=Atom(predicate="low_trust", terms=()),
        body=(),
    )
    document = RuleProposal(
        rule_id="rule-001",
        source_paper="Ioannidis_2005_WhyMostPublishedResearch",
        proposed_rule=rule,
        predicates_referenced=("sample_size/2",),
        extraction_provenance=RuleExtractionProvenance(
            operations=("rule_extraction",),
            agent="codex",
            model="test-model",
            prompt_sha="abc123",
            notes_sha="def456",
            predicates_sha="ghi789",
            status="stated",
        ),
        extraction_date="2026-04-29",
        page_reference="Ioannidis 2005 p. 0697",
    )

    assert document.proposed_rule is not None
    assert document.proposed_rule.id == "rule-001"
    assert document.predicates_referenced == ("sample_size/2",)
