from __future__ import annotations

import sqlite3

from argumentation.aspic import GroundAtom
from quire.documents import LoadedDocument

from propstore.families.documents.rules import (
    AtomDocument,
    BodyLiteralDocument,
    RuleDocument,
    RuleSourceDocument,
    RulesFileDocument,
    TermDocument,
)
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry
from propstore.rule_files import LoadedRuleFile
from propstore.sidecar.rules import (
    create_grounded_fact_table,
    populate_grounded_facts,
    read_grounded_bundle,
)


def _birds_fly_bundle():
    variable = TermDocument(kind="var", name="X")
    rule_file = LoadedRuleFile.from_loaded_document(
        LoadedDocument(
            filename="rules.yaml",
            source_path=None,
            knowledge_root=None,
            document=RulesFileDocument(
                source=RuleSourceDocument(paper="Garcia_2004_DefeasibleLogicProgramming"),
                rules=(
                    RuleDocument(
                        id="flies_if_bird",
                        kind="defeasible",
                        head=AtomDocument(predicate="flies", terms=(variable,)),
                        body=(
                            BodyLiteralDocument(
                                kind="positive",
                                atom=AtomDocument(predicate="bird", terms=(variable,)),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    return ground(
        (rule_file,),
        (GroundAtom("bird", ("tweety",)),),
        PredicateRegistry(()),
        return_arguments=True,
    )


def test_grounded_bundle_rehydrates_inputs_and_arguments() -> None:
    bundle = _birds_fly_bundle()

    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    populate_grounded_facts(conn, bundle)

    restored = read_grounded_bundle(conn)

    assert restored.source_rules == bundle.source_rules
    assert restored.source_facts == bundle.source_facts
    assert restored.sections == bundle.sections
    assert restored.arguments == bundle.arguments
    assert restored.grounding_inspection is not None


def test_grounded_bundle_persists_gunray_arguments_without_pickle() -> None:
    bundle = _birds_fly_bundle()

    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    populate_grounded_facts(conn, bundle)

    stored_payload = conn.execute(
        "SELECT payload FROM grounded_bundle_input WHERE kind = 'argument'"
    ).fetchone()[0]
    restored = read_grounded_bundle(conn)

    assert stored_payload.startswith(b"{")
    assert restored.arguments == bundle.arguments
