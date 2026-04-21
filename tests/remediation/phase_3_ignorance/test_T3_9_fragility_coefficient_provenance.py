from __future__ import annotations

from itertools import chain
from types import MappingProxyType

from quire.documents import LoadedDocument

from propstore.families.documents.rules import (
    AtomDocument,
    RuleDocument,
    RuleSourceDocument,
    RulesFileDocument,
    TermDocument,
)
from propstore.fragility_contributors import (
    collect_bridge_undercut_interventions,
    collect_ground_fact_interventions,
    collect_grounded_rule_interventions,
)
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.rule_files import LoadedRuleFile


def _var(name: str) -> TermDocument:
    return TermDocument(kind="var", name=name)


def _atom(predicate: str, terms=(), *, negated: bool = False) -> AtomDocument:
    return AtomDocument(predicate=predicate, terms=tuple(terms), negated=negated)


def _rule_doc(rule_id: str, kind: str, head: AtomDocument, *, body=()) -> RuleDocument:
    return RuleDocument(id=rule_id, kind=kind, head=head, body=tuple(body))


def _rule_file(rules: tuple[RuleDocument, ...]) -> LoadedRuleFile:
    loaded = LoadedDocument(
        filename="fragility-coefficients.yaml",
        source_path=None,
        knowledge_root=None,
        document=RulesFileDocument(
            source=RuleSourceDocument(paper="T3.9"),
            rules=rules,
        ),
    )
    return LoadedRuleFile.from_loaded_document(loaded)


def _bundle(*, rules=(), definitely=None) -> GroundedRulesBundle:
    return GroundedRulesBundle(
        source_rules=tuple([_rule_file(tuple(rules))] if rules else []),
        source_facts=(),
        sections=MappingProxyType(
            {
                "definitely": MappingProxyType(
                    {} if definitely is None else {
                        key: frozenset(value)
                        for key, value in definitely.items()
                    }
                ),
                "defeasibly": MappingProxyType({}),
                "not_defeasibly": MappingProxyType({}),
                "undecided": MappingProxyType({}),
            }
        ),
    )


def test_fragility_coefficient_interventions_carry_cited_provenance_notes() -> None:
    target_rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    defeater_rule = _rule_doc(
        "rule:broken-wing",
        "defeater",
        _atom("flies", (_var("X"),), negated=True),
        body=(_atom("broken_wing", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(target_rule, defeater_rule),
        definitely={
            "bird": frozenset({("tweety",)}),
            "broken_wing": frozenset({("tweety",)}),
        },
    )

    interventions = tuple(
        chain(
            collect_ground_fact_interventions(bundle),
            collect_grounded_rule_interventions(bundle),
            collect_bridge_undercut_interventions(bundle, (), [], ()),
        )
    )

    assert interventions
    for intervention in interventions:
        notes = intervention.target.provenance.notes
        assert notes
        assert any("citation=" in note for note in notes)
