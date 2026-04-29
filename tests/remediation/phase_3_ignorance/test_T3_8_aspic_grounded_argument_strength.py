from __future__ import annotations

from types import MappingProxyType

from argumentation.aspic import GroundAtom
from quire.documents import LoadedDocument

from propstore.aspic_bridge import build_bridge_csaf, csaf_to_projection
from propstore.families.documents.rules import (
    AtomDocument,
    BodyLiteralDocument,
    RuleDocument,
    RuleSourceDocument,
    RulesFileDocument,
    TermDocument,
)
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.rule_files import LoadedRuleFile


def _rule_file(rule: RuleDocument) -> LoadedRuleFile:
    loaded = LoadedDocument(
        filename="grounded-strength.yaml",
        source_path=None,
        knowledge_root=None,
        document=RulesFileDocument(
            source=RuleSourceDocument(paper="T3.8"),
            rules=(rule,),
        ),
    )
    return LoadedRuleFile.from_loaded_document(loaded)


def test_grounded_argument_strength_not_zero() -> None:
    rule = RuleDocument(
        id="grounded_fly",
        kind="defeasible",
        head=AtomDocument(
            predicate="fly",
            terms=(TermDocument(kind="var", name="X"),),
        ),
        body=(
            BodyLiteralDocument(
                kind="positive",
                atom=AtomDocument(
                    predicate="bird",
                    terms=(TermDocument(kind="var", name="X"),),
                ),
            ),
        ),
    )
    bundle = GroundedRulesBundle(
        source_rules=(_rule_file(rule),),
        source_facts=(),
        sections=MappingProxyType(
            {
                "yes": MappingProxyType({"bird": frozenset({("tweety",)})}),
                "no": MappingProxyType({}),
                "undecided": MappingProxyType({}),
                "unknown": MappingProxyType({}),
            }
        ),
    )
    csaf = build_bridge_csaf([], [], [], bundle=bundle)

    projection = csaf_to_projection(csaf, [])
    fly_argument = next(
        argument
        for argument in projection.arguments
        if argument.projection.backend_atom == GroundAtom("fly", ("tweety",))
    )

    assert fly_argument.strength == 0.7
    assert fly_argument.strength != 0.0
