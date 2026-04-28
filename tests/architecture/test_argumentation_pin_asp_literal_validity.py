from __future__ import annotations

import re

from argumentation.aspic import (
    ArgumentationSystem,
    ContrarinessFn,
    GroundAtom,
    KnowledgeBase,
    Literal,
    PreferenceConfig,
)
from argumentation.aspic_encoding import encode_aspic_theory


def test_argumentation_pin_encodes_literals_as_asp_constants() -> None:
    p = Literal(GroundAtom("P", (1, 2)))
    not_p = p.contrary
    system = ArgumentationSystem(
        language=frozenset({p, not_p}),
        contrariness=ContrarinessFn(frozenset({(p, not_p)})),
        strict_rules=frozenset(),
        defeasible_rules=frozenset(),
    )
    encoding = encode_aspic_theory(
        system,
        KnowledgeBase(axioms=frozenset({not_p}), premises=frozenset({p})),
        PreferenceConfig(frozenset(), frozenset(), comparison="elitist", link="last"),
    )

    literal_ids = {
        fact.removesuffix(").").split("(", 1)[1]
        for fact in encoding.facts
        if fact.startswith(("axiom(", "premise("))
    }

    assert literal_ids
    assert all(re.fullmatch(r"[a-z][A-Za-z0-9_]*", literal_id) for literal_id in literal_ids)
    assert set(encoding.literal_by_id) >= literal_ids
