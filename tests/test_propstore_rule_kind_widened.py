"""WS-O-gun-garcia propstore schema closure tests.

Garcia & Simari 2004 p. 110 Defs. 4.1-4.2 distinguish proper and
blocking defeaters, and pp. 125-126 Defs. 6.1-6.3 distinguish default
negation from strong negation. The propstore authored-rule schema must
carry those distinctions instead of the old collapsed ``defeater`` kind.
"""

from __future__ import annotations

import msgspec
import msgspec.yaml

from propstore.families.documents.rules import (
    AtomDocument,
    BodyLiteralDocument,
    RuleDocument,
    TermDocument,
)
from propstore.grounding.translator import translate_to_theory
from propstore.stances import StanceType


def _var(name: str) -> TermDocument:
    return TermDocument(kind="var", name=name)


def _atom(predicate: str, *, negated: bool = False) -> AtomDocument:
    return AtomDocument(predicate=predicate, terms=(_var("X"),), negated=negated)


def test_rule_document_rejects_legacy_defeater_kind() -> None:
    legacy_yaml = b"""
id: rule:legacy-defeater
kind: defeater
head:
  predicate: flies
body: []
"""

    try:
        msgspec.yaml.decode(legacy_yaml, type=RuleDocument, strict=True)
    except msgspec.ValidationError as exc:
        assert "defeater" in str(exc)
    else:
        raise AssertionError("legacy kind='defeater' decoded successfully")


def test_rule_document_accepts_proper_and_blocking_defeater_kinds() -> None:
    head = AtomDocument(predicate="flies")
    proper = RuleDocument(
        id="rule:proper",
        kind="proper_defeater",
        head=head,
    )
    blocking = RuleDocument(
        id="rule:blocking",
        kind="blocking_defeater",
        head=head,
    )

    assert proper.kind == "proper_defeater"
    assert blocking.kind == "blocking_defeater"


def test_default_negation_body_literal_round_trips_distinct_from_strong_negation() -> None:
    doc = RuleDocument(
        id="rule:default-negation",
        kind="defeasible",
        head=_atom("flies"),
        body=(
            BodyLiteralDocument(kind="positive", atom=_atom("bird")),
            BodyLiteralDocument(kind="default_negated", atom=_atom("injured")),
            BodyLiteralDocument(kind="positive", atom=_atom("grounded", negated=True)),
        ),
    )

    encoded = msgspec.yaml.encode(doc)
    decoded = msgspec.yaml.decode(encoded, type=RuleDocument, strict=True)

    assert tuple(literal.kind for literal in decoded.body) == (
        "positive",
        "default_negated",
        "positive",
    )
    assert decoded.body[1].atom.negated is False
    assert decoded.body[2].atom.negated is True


def test_translate_default_negation_to_gunray_not_surface() -> None:
    from quire.documents import LoadedDocument
    from propstore.families.documents.rules import RuleSourceDocument, RulesFileDocument
    from propstore.rule_files import LoadedRuleFile

    rule = RuleDocument(
        id="rule:default-negation",
        kind="defeasible",
        head=_atom("flies"),
        body=(
            BodyLiteralDocument(kind="positive", atom=_atom("bird")),
            BodyLiteralDocument(kind="default_negated", atom=_atom("injured")),
            BodyLiteralDocument(kind="positive", atom=_atom("grounded", negated=True)),
        ),
    )
    loaded = LoadedRuleFile.from_loaded_document(
        LoadedDocument(
            filename="rules",
            source_path=None,
            knowledge_root=None,
            document=RulesFileDocument(
                source=RuleSourceDocument(paper="Garcia_2004_DefeasibleLogicProgramming"),
                rules=(rule,),
            ),
        )
    )

    theory = translate_to_theory([loaded], (), registry=None)  # type: ignore[arg-type]

    assert theory.defeasible_rules[0].body == (
        "bird(X)",
        "not injured(X)",
        "~grounded(X)",
    )


def test_stance_type_exposes_proper_and_blocking_defeater_analogs() -> None:
    assert StanceType.PROPER_DEFEATER.value == "proper_defeater"
    assert StanceType.BLOCKING_DEFEATER.value == "blocking_defeater"
