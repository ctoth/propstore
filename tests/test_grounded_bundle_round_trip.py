from __future__ import annotations

import sqlite3

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
