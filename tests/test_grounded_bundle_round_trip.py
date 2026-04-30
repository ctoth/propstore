from __future__ import annotations

import sqlite3

import gunray
from argumentation.aspic import GroundAtom

from propstore.grounding.bundle import GroundedRulesBundle
from propstore.sidecar.rules import (
    create_grounded_fact_table,
    populate_grounded_facts,
    read_grounded_bundle,
)


def test_grounded_bundle_rehydrates_inputs_and_arguments() -> None:
    sections = {
        "yes": {"bird": frozenset({("tweety",)})},
        "no": {},
        "undecided": {},
        "unknown": {},
    }
    bundle = GroundedRulesBundle(
        source_rules=("rule-file:birds-fly",),  # type: ignore[arg-type]
        source_facts=(GroundAtom("bird", ("tweety",)),),
        sections=sections,
        arguments=("argument:flies-tweety",),  # type: ignore[arg-type]
    )

    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    populate_grounded_facts(conn, bundle)

    restored = read_grounded_bundle(conn)

    assert restored.source_rules == bundle.source_rules
    assert restored.source_facts == bundle.source_facts
    assert restored.sections == bundle.sections
    assert restored.arguments == bundle.arguments


def test_grounded_bundle_persists_gunray_arguments_without_pickle() -> None:
    fact = gunray.GroundAtom("bird", ("tweety",))
    conclusion = gunray.GroundAtom("flies", ("tweety",))
    rule = gunray.GroundDefeasibleRule(
        rule_id="flies_if_bird",
        kind="defeasible",
        head=conclusion,
        body=(fact,),
    )
    argument = gunray.Argument(rules=frozenset({rule}), conclusion=conclusion)
    bundle = GroundedRulesBundle(
        source_rules=(),
        source_facts=(),
        sections={
            "yes": {"flies": frozenset({("tweety",)})},
            "no": {},
            "undecided": {},
            "unknown": {},
        },
        arguments=(argument,),
    )

    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    populate_grounded_facts(conn, bundle)

    stored_payload = conn.execute(
        "SELECT payload FROM grounded_bundle_input WHERE kind = 'argument'"
    ).fetchone()[0]
    restored = read_grounded_bundle(conn)

    assert stored_payload.startswith(b"{")
    assert restored.arguments == (argument,)
